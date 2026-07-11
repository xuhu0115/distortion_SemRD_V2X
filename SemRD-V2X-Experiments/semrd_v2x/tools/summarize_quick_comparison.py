#!/usr/bin/env python
"""
Summarize the 4 quick-comparison runs into a single table.

Usage (from v2x-vit root):
    python v2xvit/tools/summarize_quick_comparison.py

Reads:
  logs/point_pillar_v2xvit_semrd_*/training_log.csv
  logs/point_pillar_v2xvit_semrd_*/metrics.json  (if available after inference)

Prints a comparison table covering:
  - Per-method: AP@0.5 / AP@0.7, runtime, peak GPU, bandwidth
"""

import csv
import glob
import json
import os
import sys

V2XVIT_ROOT = os.environ.get('V2XVIT_ROOT', os.getcwd())
LOGS_DIR = os.path.join(V2XVIT_ROOT, 'logs')


def load_csv(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return list(csv.DictReader(f))


def load_metrics(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def main():
    # Find all log directories
    log_dirs = sorted(glob.glob(os.path.join(LOGS_DIR, 'point_pillar_v2xvit_semrd_*')))
    if not log_dirs:
        print(f'No log directories found in {LOGS_DIR}')
        sys.exit(1)

    print(f'Found {len(log_dirs)} log directories:\n')

    rows = []
    for d in log_dirs:
        name = os.path.basename(d)
        csv_path = os.path.join(d, 'training_log.csv')
        metrics_path = os.path.join(d, 'metrics.json')
        train_log = load_csv(csv_path)
        metrics = load_metrics(metrics_path)

        if not train_log:
            print(f'  [skip] {name}: no training_log.csv')
            continue

        # average over all epochs
        n_epochs = len(train_log)
        avg_train_loss = sum(float(r['train_loss']) for r in train_log) / n_epochs
        total_time = sum(float(r['epoch_time_s']) for r in train_log)
        peak_gpu = max(float(r['peak_gpu_MB']) for r in train_log)
        avg_core = sum(float(r['avg_core_mass']) for r in train_log) / n_epochs
        avg_bw = sum(float(r['avg_bw_MB']) for r in train_log) / n_epochs
        final_train_loss = float(train_log[-1]['train_loss'])

        # extract P_A, delta, setting from log name (best effort)
        # name format: point_pillar_v2xvit_semrd_YYYY_MM_DD_HH_MM_SS
        # we rely on the user to label each dir; for now just use metrics if exists

        ap05 = metrics.get('ap_at_0.5', 'N/A') if metrics else 'N/A'
        ap07 = metrics.get('ap_at_0.7', 'N/A') if metrics else 'N/A'
        bw_mb_frame = metrics.get('avg_bandwidth_MB_per_frame', 'N/A') if metrics else 'N/A'

        rows.append({
            'name': name,
            'epochs': n_epochs,
            'avg_train_loss': avg_train_loss,
            'final_train_loss': final_train_loss,
            'total_time_h': total_time / 3600.0,
            'peak_gpu_gb': peak_gpu / 1024.0,
            'avg_core': avg_core,
            'avg_bw_train': avg_bw,
            'ap_05': ap05,
            'ap_07': ap07,
            'bw_inf': bw_mb_frame,
        })

    if not rows:
        print('No valid training logs found.')
        sys.exit(1)

    # print comparison table
    print('=' * 110)
    print(f'{"Name":<48} {"Epochs":>6} {"FinalLoss":>10} '
          f'{"Time(h)":>8} {"GPU(GB)":>8} {"CoreMass":>8} {"BW(MB)":>8}')
    print('-' * 110)
    for r in rows:
        print(f'{r["name"]:<48} {r["epochs"]:>6} {r["final_train_loss"]:>10.4f} '
              f'{r["total_time_h"]:>8.2f} {r["peak_gpu_gb"]:>8.2f} '
              f'{r["avg_core"]:>8.3f} {r["avg_bw_train"]:>8.2f}')
    print('=' * 110)

    # if any has AP results, print them too
    has_ap = any(r['ap_05'] != 'N/A' for r in rows)
    if has_ap:
        print()
        print('AP results (from metrics.json — run inference_semrd.py to fill in):')
        print(f'{"Name":<48} {"AP@0.5":>8} {"AP@0.7":>8} {"BW(MB/f)":>10}')
        print('-' * 80)
        for r in rows:
            ap05 = f'{r["ap_05"]:.3f}' if r['ap_05'] != 'N/A' else 'N/A'
            ap07 = f'{r["ap_07"]:.3f}' if r['ap_07'] != 'N/A' else 'N/A'
            bw_inf = f'{r["bw_inf"]:.2f}' if r['bw_inf'] != 'N/A' else 'N/A'
            print(f'{r["name"]:<48} {ap05:>8} {ap07:>8} {bw_inf:>10}')

    print()
    print('Note: AP/BW-Inf fields are "N/A" until you run inference_semrd.py on each checkpoint.')
    print('The training_log.csv is written by train_semrd.py; the metrics.json is written by inference_semrd.py.')


if __name__ == '__main__':
    main()
