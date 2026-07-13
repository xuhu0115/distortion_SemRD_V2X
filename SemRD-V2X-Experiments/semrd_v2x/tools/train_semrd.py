"""
Training script for SemRD-V2X.

Identical to v2x-vit's train.py except:
  1. Loads point_pillar_v2xvit_semrd model (via core_method in yaml).
  2. Adds the rate_loss (from output_dict['rate_loss']) to detection loss.
  3. Anneals Gumbel temperature across epochs.
  4. Logs extra metrics: core_mass, bandwidth_bytes, rate_loss.

Place at:  v2xvit/tools/train_semrd.py
Run with:  python v2xvit/tools/train_semrd.py \
                --hypes_yaml v2xvit/hypes_yaml/point_pillar_v2xvit_semrd.yaml
"""

import argparse
import os
import statistics
import time
import json

import torch
import tqdm
from torch.utils.data import DataLoader
from tensorboardX import SummaryWriter

import v2xvit.hypes_yaml.yaml_utils as yaml_utils
from v2xvit.tools import train_utils
from v2xvit.data_utils.datasets import build_dataset


def train_parser():
    parser = argparse.ArgumentParser(description="SemRD-V2X training")
    parser.add_argument("--hypes_yaml", type=str, required=True)
    parser.add_argument('--model_dir', default='',
                        help='Continued training path')
    parser.add_argument("--half", action='store_true')
    return parser.parse_args()


def main():
    opt = train_parser()
    hypes = yaml_utils.load_yaml(opt.hypes_yaml, opt)

    print('Dataset Building')
    opencood_train_dataset = build_dataset(hypes, visualize=False, train=True)
    opencood_validate_dataset = build_dataset(hypes, visualize=False, train=False)

    # Save collate fns BEFORE wrapping in Subset (Subset doesn't carry methods)
    train_collate = opencood_train_dataset.collate_batch_train
    val_collate = opencood_train_dataset.collate_batch_train  # same in v2x-vit

    # ----- Subset support for quick POC -----
    # Use train_subset (yaml or env TRAIN_SUBSET) to use only a fraction of
    # training data. Evenly-spaced sampling preserves diversity.
    import numpy as np
    from torch.utils.data import Subset
    train_subset = float(os.environ.get(
        'TRAIN_SUBSET',
        hypes['train_params'].get('train_subset', 1.0)))
    val_subset = float(os.environ.get(
        'VAL_SUBSET',
        hypes['train_params'].get('val_subset', 1.0)))
    if train_subset < 1.0:
        n_total = len(opencood_train_dataset)
        n_sub = max(1, int(n_total * train_subset))
        idx = np.linspace(0, n_total - 1, n_sub, dtype=int).tolist()
        print(f'[Subset] train: {n_sub}/{n_total} = {train_subset*100:.1f}%')
        opencood_train_dataset = Subset(opencood_train_dataset, idx)
    if val_subset < 1.0:
        n_total = len(opencood_validate_dataset)
        n_sub = max(1, int(n_total * val_subset))
        idx = np.linspace(0, n_total - 1, n_sub, dtype=int).tolist()
        print(f'[Subset] val:   {n_sub}/{n_total} = {val_subset*100:.1f}%')
        opencood_validate_dataset = Subset(opencood_validate_dataset, idx)

    # num_workers: set NUM_WORKERS env var to override. Default 8 for new server
    # (assumes /dev/shm >= 4GB). On Docker (64MB /dev/shm) use NUM_WORKERS=0.
    num_workers = int(os.environ.get('NUM_WORKERS', 8))
    print(f'DataLoader num_workers = {num_workers} (override via NUM_WORKERS env)')
    train_loader = DataLoader(opencood_train_dataset,
                              batch_size=hypes['train_params']['batch_size'],
                              num_workers=num_workers,
                              collate_fn=train_collate,
                              shuffle=True, pin_memory=False, drop_last=True,
                              persistent_workers=False,
                              multiprocessing_context=None)
    val_loader = DataLoader(opencood_validate_dataset,
                            batch_size=hypes['train_params']['batch_size'],
                            num_workers=num_workers,
                            collate_fn=val_collate,
                            shuffle=False, pin_memory=False, drop_last=True,
                            persistent_workers=False,
                            multiprocessing_context=None)

    print('Creating Model')
    model = train_utils.create_model(hypes)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)

    criterion = train_utils.create_loss(hypes)
    optimizer = train_utils.setup_optimizer(hypes, model)
    scheduler = train_utils.setup_lr_schedular(hypes, optimizer)

    if opt.model_dir:
        saved_path = opt.model_dir
        init_epoch, model = train_utils.load_saved_model(saved_path, model)
    else:
        init_epoch = 0
        saved_path = train_utils.setup_train(hypes)

    writer = SummaryWriter(saved_path)

    # Gumbel temperature schedule
    semrd_cfg = hypes['model']['args'].get('semrd', {})
    tau_start = float(semrd_cfg.get('gumbel_temperature_init', 5.0))
    tau_end = float(semrd_cfg.get('gumbel_temperature_end', 0.5))
    epoches = hypes['train_params']['epoches']

    def gumbel_tau_for_epoch(epoch):
        if epoches <= 1:
            return tau_start
        frac = epoch / max(epoches - 1, 1)
        return tau_start + (tau_end - tau_start) * frac

    print('Training start')
    # CSV-style log file: one row per epoch
    csv_path = os.path.join(saved_path, 'training_log.csv')
    with open(csv_path, 'w') as f:
        f.write('epoch,train_loss,val_loss,epoch_time_s,peak_gpu_MB,'
                'avg_core_mass,avg_bw_MB,gumbel_tau,lr\n')

    for epoch in range(init_epoch, max(epoches, init_epoch)):
        scheduler.step(epoch)
        for param_group in optimizer.param_groups:
            print('learning rate %f' % param_group["lr"])
        # anneal Gumbel temperature
        if hasattr(model, 'set_gumbel_temperature'):
            model.set_gumbel_temperature(gumbel_tau_for_epoch(epoch))
            print('Gumbel temperature:', model.core_selector.gumbel_tau
                  if model.core_selector is not None else 'N/A')

        # reset GPU memory peak counter at start of each epoch
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()

        epoch_start = time.time()
        train_losses = []
        epoch_core_masses = []
        epoch_bandwidths = []
        pbar2 = tqdm.tqdm(total=len(train_loader), leave=True)
        for i, batch_data in enumerate(train_loader):
            model.train()
            model.zero_grad()
            optimizer.zero_grad()
            batch_data = train_utils.to_device(batch_data, device)

            ouput_dict = model(batch_data['ego'])
            det_loss = criterion(ouput_dict, batch_data['ego']['label_dict'])
            rate_loss = ouput_dict.get('rate_loss', torch.tensor(0.0, device=device))
            final_loss = det_loss + rate_loss

            # log
            core_mass = ouput_dict.get('core_mass', torch.tensor(1.0))
            bandwidth_bytes = ouput_dict.get('bandwidth_bytes', 0.0)
            # Fallback for V2X-ViT baseline (no CSM, no bandwidth field):
            # compute bandwidth from record_len (number of agents per sample)
            if bandwidth_bytes == 0.0 or bandwidth_bytes is None:
                record_len = batch_data['record_len']
                N_agents = int(record_len.sum().item())
                # C=256, H=48, W=176 (from shrink_conv output)
                bandwidth_bytes = float(N_agents) * 256 * 48 * 176 * 4
            core_mass_f = float(core_mass.item()) if torch.is_tensor(core_mass) else 1.0
            bw_mb = float(bandwidth_bytes) / (1024 * 1024) \
                if isinstance(bandwidth_bytes, (int, float)) else 0.0
            train_losses.append(det_loss.item())
            epoch_core_masses.append(core_mass_f)
            epoch_bandwidths.append(bw_mb)

            writer.add_scalar('Train/rate_loss', float(rate_loss.item())
                              if rate_loss.requires_grad or rate_loss.item() != 0
                              else 0.0, epoch * len(train_loader) + i)
            writer.add_scalar('Train/core_mass', core_mass_f,
                              epoch * len(train_loader) + i)
            writer.add_scalar('Train/bandwidth_MB', bw_mb,
                              epoch * len(train_loader) + i)

            # extended loss logging
            pbar2.set_description(
                "[epoch %d][%d/%d] Det: %.4f Rate: %.4f Core: %.3f BW: %.2fMB"
                % (epoch, i + 1, len(train_loader),
                   det_loss.item(),
                   rate_loss.item() if rate_loss.requires_grad else 0.0,
                   float(core_mass.item()) if torch.is_tensor(core_mass) else 1.0,
                   float(bandwidth_bytes) / (1024 * 1024)
                   if isinstance(bandwidth_bytes, (int, float))
                   else float(bandwidth_bytes) / (1024 * 1024)))
            pbar2.update(1)

            final_loss.backward()
            optimizer.step()

        # end of epoch: compute summary metrics
        epoch_time = time.time() - epoch_start
        train_ave_loss = statistics.mean(train_losses)
        avg_core_mass = statistics.mean(epoch_core_masses) if epoch_core_masses else 1.0
        avg_bw_mb = statistics.mean(epoch_bandwidths) if epoch_bandwidths else 0.0
        if torch.cuda.is_available():
            peak_gpu_mb = torch.cuda.max_memory_allocated() / (1024 * 1024)
        else:
            peak_gpu_mb = 0.0
        tau_now = (model.core_selector.gumbel_tau
                   if hasattr(model, 'core_selector') and model.core_selector is not None
                   else float('nan'))
        lr_now = optimizer.param_groups[0]['lr']
        print(f'[Epoch {epoch}] train_loss={train_ave_loss:.4f} '
              f'time={epoch_time:.1f}s peak_gpu={peak_gpu_mb:.0f}MB '
              f'core={avg_core_mass:.3f} bw={avg_bw_mb:.2f}MB '
              f'tau={tau_now:.2f} lr={lr_now:.5f}')

        if epoch % hypes['train_params']['eval_freq'] == 0:
            valid_ave_loss = []
            with torch.no_grad():
                for i, batch_data in enumerate(val_loader):
                    model.eval()
                    batch_data = train_utils.to_device(batch_data, device)
                    ouput_dict = model(batch_data['ego'])
                    final_loss = criterion(ouput_dict,
                                           batch_data['ego']['label_dict'])
                    valid_ave_loss.append(final_loss.item())
            valid_ave_loss = statistics.mean(valid_ave_loss)
            print('At epoch %d, the validation loss is %f' % (epoch, valid_ave_loss))
            writer.add_scalar('Validate_Loss', valid_ave_loss, epoch)
        else:
            valid_ave_loss = float('nan')

        # append a row to the CSV log
        with open(csv_path, 'a') as f:
            f.write(f'{epoch},{train_ave_loss:.4f},{valid_ave_loss:.4f},'
                    f'{epoch_time:.1f},{peak_gpu_mb:.0f},'
                    f'{avg_core_mass:.3f},{avg_bw_mb:.2f},'
                    f'{tau_now:.2f},{lr_now:.5f}\n')

        if epoch % hypes['train_params']['save_freq'] == 0:
            torch.save(model.state_dict(),
                       os.path.join(saved_path,
                                    'net_epoch%d.pth' % (epoch + 1)))

    print('Training Finished, checkpoints saved to %s' % saved_path)


if __name__ == '__main__':
    main()