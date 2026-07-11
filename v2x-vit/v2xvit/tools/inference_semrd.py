"""
Inference / evaluation script for SemRD-V2X.

Computes:
  - AP@0.5, AP@0.7 (3D vehicle detection, IoU-based)
  - Bandwidth (MB/frame) — measured from the actual core mask
  - Core mass (measured P_A)
  - Inference latency (ms/frame)
  - (Optional) Closure fidelity proxy — Jaccard similarity between
    feature-mask closures of original and reconstructed (TODO)

The eval loop is structurally identical to v2x-vit's inference.py.
Differences:
  1. Uses the SemRD model class.
  2. Times each forward pass for latency.
  3. Accumulates core_mass and bandwidth statistics across the dataset.

Place at:  v2xvit/tools/inference_semrd.py
Run with:  python v2xvit/tools/inference_semrd.py \
                --model_dir logs/point_pillar_v2xvit_semrd_XXX/ \
                --fusion_method intermediate
"""

import argparse
import json
import os
import time
from collections import defaultdict

import torch
from torch.utils.data import DataLoader

import v2xvit.hypes_yaml.yaml_utils as yaml_utils
from v2xvit.tools import train_utils, infrence_utils
from v2xvit.data_utils.datasets import build_dataset
from v2xvit.utils import eval_utils


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_dir', type=str, required=True)
    parser.add_argument('--fusion_method', default='intermediate', type=str)
    parser.add_argument('--save_metrics', default='', type=str,
                        help='path to save metrics JSON (default: model_dir/metrics.json)')
    return parser.parse_args()


def main():
    opt = parse_args()
    assert opt.fusion_method in ['late', 'early', 'intermediate']

    hypes = yaml_utils.load_yaml(None, opt)

    print('Dataset Building')
    opencood_dataset = build_dataset(hypes, visualize=False, train=False)
    # HARD-CODED num_workers=0: docker /dev/shm only 64MB. Set NUM_WORKERS env to override.
    num_workers = int(os.environ.get('NUM_WORKERS', 0))
    data_loader = DataLoader(opencood_dataset,
                             batch_size=1,
                             num_workers=num_workers,
                             collate_fn=opencood_dataset.collate_batch_test,
                             shuffle=False, pin_memory=False, drop_last=False)

    print('Creating Model')
    model = train_utils.create_model(hypes)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)

    print('Loading Model from', opt.model_dir)
    _, model = train_utils.load_saved_model(opt.model_dir, model)
    model.eval()

    result_stat = {0.3: {'tp': [], 'fp': [], 'gt': 0},
                   0.5: {'tp': [], 'fp': [], 'gt': 0},
                   0.7: {'tp': [], 'fp': [], 'gt': 0}}

    # extra metric accumulators
    bandwidth_list = []
    core_mass_list = []
    latency_list = []

    for i, batch_data in enumerate(data_loader):
        with torch.no_grad():
            torch.cuda.synchronize()
            t0 = time.time()
            batch_data = train_utils.to_device(batch_data, device)

            if opt.fusion_method == 'intermediate':
                pred_box_tensor, pred_score, gt_box_tensor = \
                    infrence_utils.inference_intermediate_fusion(
                        batch_data, model, opencood_dataset)
            else:
                raise NotImplementedError(
                    'Only intermediate fusion is supported for SemRD-V2X.')

            torch.cuda.synchronize()
            latency_ms = (time.time() - t0) * 1000.0

            # record extra metrics — note these are read AFTER the inference
            # utility's forward pass
            if hasattr(model, '_last_bandwidth_bytes') and model._last_bandwidth_bytes is not None:
                bandwidth_list.append(model._last_bandwidth_bytes)
            if hasattr(model, '_last_core_mass') and model._last_core_mass is not None:
                cm = model._last_core_mass
                if torch.is_tensor(cm):
                    core_mass_list.append(float(cm.item()))
                else:
                    core_mass_list.append(float(cm))
            latency_list.append(latency_ms)

            eval_utils.caluclate_tp_fp(pred_box_tensor, pred_score, gt_box_tensor,
                                       result_stat, 0.3)
            eval_utils.caluclate_tp_fp(pred_box_tensor, pred_score, gt_box_tensor,
                                       result_stat, 0.5)
            eval_utils.caluclate_tp_fp(pred_box_tensor, pred_score, gt_box_tensor,
                                       result_stat, 0.7)

            if (i + 1) % 50 == 0:
                print(f"Processed {i + 1}/{len(data_loader)} frames, "
                      f"last latency: {latency_ms:.2f} ms")

    # ---- print & save metrics ----
    print("\n========= AP results =========")
    eval_utils.eval_final_results(result_stat, opt.model_dir)

    if bandwidth_list:
        avg_bw_mb = sum(bandwidth_list) / len(bandwidth_list) / (1024 * 1024)
        print(f"Avg bandwidth:    {avg_bw_mb:.3f} MB/frame")
    if core_mass_list:
        avg_cm = sum(core_mass_list) / len(core_mass_list)
        print(f"Avg core mass P_A: {avg_cm:.3f}")
    if latency_list:
        avg_lat = sum(latency_list) / len(latency_list)
        print(f"Avg latency:      {avg_lat:.2f} ms/frame")

    # save JSON
    save_path = opt.save_metrics or os.path.join(opt.model_dir, 'metrics.json')
    ap_results = {iou: result_stat[iou] for iou in [0.3, 0.5, 0.7]}
    metrics = {
        'num_frames': len(data_loader),
        'ap_at_0.3': result_stat[0.3],
        'ap_at_0.5': result_stat[0.5],
        'ap_at_0.7': result_stat[0.7],
        'avg_bandwidth_MB_per_frame': avg_bw_mb if bandwidth_list else None,
        'avg_core_mass': avg_cm if core_mass_list else None,
        'avg_latency_ms_per_frame': avg_lat if latency_list else None,
    }
    with open(save_path, 'w') as f:
        json.dump(metrics, f, indent=2, default=str)
    print(f"\nMetrics saved to {save_path}")


if __name__ == '__main__':
    main()