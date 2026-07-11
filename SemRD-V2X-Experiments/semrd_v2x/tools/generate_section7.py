"""Generate Section 7 tables and Figure 1 from all experimental results.

Reads logs/<run_id>/metrics.json from each run and produces:
  1. LaTeX table for Table 1 (P_A sweep + published baselines)
  2. LaTeX table for Table 2 (delta sweep)
  3. LaTeX table for Table 3 (noise robustness + published baselines)
  4. LaTeX table for Table 4 (heterogeneous receivers)
  5. LaTeX table for Table 5 (theory vs empirical)
  6. LaTeX table for Table 6 (ablation)
  7. RD curve data points for Figure 1

Published baseline numbers are loaded from compare_methods_data.json
(directly cited from V2X-ViTv2 paper, TPAMI 2025).

Run after all experiments complete:
  python v2xvit/tools/generate_section7.py
"""

import os
import json
import math
import glob
from collections import defaultdict


def find_runs(LOGS):
    """Find all run directories with metrics.json files."""
    runs = {}
    for run_dir in sorted(glob.glob(os.path.join(LOGS, '*'))):
        if not os.path.isdir(run_dir):
            continue
        mj = os.path.join(run_dir, 'metrics.json')
        if not os.path.isfile(mj):
            continue
        with open(mj) as f:
            runs[os.path.basename(run_dir)] = json.load(f)
    return runs


def load_baselines():
    """Load published baseline numbers from compare_methods_data.json."""
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, 'compare_methods_data.json')
    if not os.path.isfile(p):
        return {}
    with open(p) as f:
        return json.load(f)


def parse_run_id(run_id):
    """Parse run_id like 'T1_P10_D03_S00.2' or 'T2_P05_D03_S00.5_VEHICLE'."""
    # Strip table prefix
    if run_id.startswith('T'):
        parts = run_id.split('_')
        # First part is T1_P10 or T2_P05_D03
        cfg = parts[1]  # e.g. P10
        if 'D' in parts[2] if len(parts) > 2 else '':
            d = int(parts[2][1:])  # D03 -> 3
        else:
            d = None
        # rest is noise/vocab
        rest = '_'.join(parts[3:]) if len(parts) > 3 else ''
    else:
        # Legacy format: P05D03_S00.2
        parts = run_id.split('_')
        cfg = parts[0]
        d = int(cfg[5]) if len(cfg) > 5 else None
        rest = '_'.join(parts[1:]) if len(parts) > 1 else ''

    pa_x10 = int(cfg[1:3])
    pa = pa_x10 / 10.0

    sigma = 0.0
    vocab = 'homogeneous'
    for token in rest.split('_'):
        if token.startswith('S') and len(token) > 1:
            try:
                sigma = float(token[1:])
            except ValueError:
                pass
        elif token == 'VEHICLE':
            vocab = 'vehicle_only'
        elif token == 'INFRA':
            vocab = 'infra_only'
    return {'pa': pa, 'delta': d, 'sigma': sigma, 'vocab': vocab}


def safe_ap(metrics, iou=0.5):
    """Robustly extract AP from various metrics.json formats."""
    # Newer format: flat fields
    if f'ap_{int(iou*100)}' in metrics:
        return metrics[f'ap_{int(iou*100)}']
    # Try different formats
    if 'ap_30' in metrics:
        return {0.3: metrics.get('ap_30'),
                0.5: metrics.get('ap_50'),
                0.7: metrics.get('ap_70')}.get(iou)
    return None


def format_ap(value):
    return f'{value:.3f}' if value is not None else '--'


def format_bw(bw_mb):
    if bw_mb is None:
        return '--'
    return f'{bw_mb:.2f}'


def find_ours(runs, **criteria):
    """Find a run matching the given criteria."""
    for run_id, m in runs.items():
        cfg = parse_run_id(run_id)
        if all(cfg.get(k) == v for k, v in criteria.items()):
            return m, run_id
    return None, None


# ===========================================================================
# Table 1: P_A sweep + published baselines
# ===========================================================================

def write_table1(runs, baselines, output_file):
    """Table 1: P_A sweep comparison. Includes published baselines."""
    # Get our P_A sweep results
    pa_results = {}
    for run_id, m in runs.items():
        cfg = parse_run_id(run_id)
        if cfg['delta'] != 3 or cfg['sigma'] != 0.2 or cfg['vocab'] != 'homogeneous':
            continue
        # Only take runs with default settings (not ablation)
        if 'T6' in run_id or 'T3' in run_id or 'T4' in run_id:
            continue
        if cfg['pa'] in pa_results:
            continue  # first match wins
        pa_results[cfg['pa']] = m

    # Add published baselines for V2XSet Noisy
    published = baselines.get('V2XSet_Noisy', {})

    lines = []
    lines.append(r'% Table 1: P_A sweep comparison (V2XSet Noisy setting)')
    lines.append(r'% Published baselines from V2X-ViTv2 paper (TPAMI 2025).')
    lines.append(r'\begin{table}[htbp]')
    lines.append(r'\centering')
    lines.append(r'\caption{Core Compression on V2XSet (Noisy, $\delta = 3$). '
                 r'\textbf{Published baselines are cited from \cite{xu2024v2x}.}}')
    lines.append(r'\label{tab:compression}')
    lines.append(r'\begin{tabular}{|l|c|c|c|c|}')
    lines.append(r'\hline')
    lines.append(r'\textbf{Method} & $P_A$ & \textbf{BW (MB/frame)} & '
                 r'\textbf{AP@0.5} & \textbf{AP@0.7} \\')
    lines.append(r'\hline')
    lines.append(r'\hline')
    lines.append(r'\textbf{Published baselines} & & & & \\')
    lines.append(r'\hline')

    # Sort published baselines by AP@0.5 (descending)
    pub_sorted = sorted(
        [(k, v) for k, v in published.items() if not k.startswith('_')],
        key=lambda x: x[1].get('AP@0.5', 0) if isinstance(x[1], dict) else 0,
        reverse=True
    )
    # Highlight SOTA methods
    sota = {'V2X-ViTv1', 'V2X-ViTv2', 'How2Comm', 'Where2Comm'}
    for name, m in pub_sorted:
        if not isinstance(m, dict):
            continue
        ap50 = m.get('AP@0.5')
        ap70 = m.get('AP@0.7')
        bw = m.get('BW_MB')
        marker = r'\textbf' if name in sota else ''
        if name == 'V2X-ViTv2':
            name_disp = r'\textbf{V2X-ViTv2} (SOTA)'
        elif name == 'V2X-ViTv1':
            name_disp = r'\textbf{V2X-ViTv1}'
        else:
            name_disp = name
        lines.append(f'{marker}{{{name_disp}}} & -- & {format_bw(bw)} & '
                     f'{format_ap(ap50)} & {format_ap(ap70)} \\\\')
    lines.append(r'\hline')
    lines.append(r'\textbf{Ours (SemRD-V2X)} & & & & \\')
    lines.append(r'\hline')

    # Sort our results by P_A descending
    for pa in sorted(pa_results.keys(), reverse=True):
        m = pa_results[pa]
        ap30 = safe_ap(m, 0.3)
        ap50 = safe_ap(m, 0.5)
        ap70 = safe_ap(m, 0.7)
        bw = m.get('avg_bandwidth_MB_per_frame', None)
        if pa == 1.0:
            name = 'SemRD-V2X (no compression, baseline-equiv.)'
        else:
            name = 'SemRD-V2X (ours)'
        lines.append(f'{name} & {pa:.2f} & {format_bw(bw)} & '
                     f'{format_ap(ap50)} & {format_ap(ap70)} \\\\')
    lines.append(r'\hline')
    lines.append(r'\end{tabular}')
    lines.append(r'\end{table}')
    lines.append('')
    with open(output_file, 'w') as f:
        f.write('\n'.join(lines))
    print(f'[generate_section7] Wrote Table 1 ({len(pa_results)} SemRD rows + {len(pub_sorted)} baselines)')


# ===========================================================================
# Table 2: depth sweep
# ===========================================================================

def write_table2(runs, output_file):
    """Table 2: delta sweep at P_A=0.5."""
    d_results = {}
    for run_id, m in runs.items():
        cfg = parse_run_id(run_id)
        if cfg['pa'] != 0.5 or cfg['sigma'] != 0.2 or cfg['vocab'] != 'homogeneous':
            continue
        if cfg['delta'] is None:
            continue
        if cfg['delta'] in d_results:
            continue
        d_results[cfg['delta']] = m

    if not d_results:
        return

    lines = []
    lines.append(r'% Table 2: Inference depth sweep at P_A=0.5')
    lines.append(r'\begin{table}[htbp]')
    lines.append(r'\centering')
    lines.append(r'\caption{Inference Depth Analysis ($P_A = 0.5$, V2XSet Noisy)}')
    lines.append(r'\label{tab:depth}')
    lines.append(r'\begin{tabular}{|c|c|c|c|c|}')
    lines.append(r'\hline')
    lines.append(r'$\delta$ & \textbf{AP@0.3} & \textbf{AP@0.5} & \textbf{AP@0.7} & '
                 r'\textbf{Latency (ms)} \\')
    lines.append(r'\hline')
    for d in sorted(d_results.keys()):
        m = d_results[d]
        ap30 = safe_ap(m, 0.3)
        ap50 = safe_ap(m, 0.5)
        ap70 = safe_ap(m, 0.7)
        lat = m.get('avg_latency_ms_per_frame', None)
        lat_str = f'{lat:.1f}' if lat is not None else '--'
        lines.append(f'{d} & {format_ap(ap30)} & {format_ap(ap50)} & '
                     f'{format_ap(ap70)} & {lat_str} \\\\')
    lines.append(r'\hline')
    lines.append(r'\end{tabular}')
    lines.append(r'\end{table}')
    lines.append('')
    with open(output_file, 'a') as f:
        f.write('\n'.join(lines))
    print(f'[generate_section7] Appended Table 2 ({len(d_results)} rows)')


# ===========================================================================
# Table 3: noise robustness
# ===========================================================================

def write_table3(runs, baselines, output_file):
    """Table 3: noise robustness. Includes published baselines for comparison."""
    n_results = {}
    for run_id, m in runs.items():
        cfg = parse_run_id(run_id)
        if cfg['pa'] != 0.5 or cfg['delta'] != 3 or cfg['vocab'] != 'homogeneous':
            continue
        if cfg['sigma'] in n_results:
            continue
        n_results[cfg['sigma']] = m

    if not n_results:
        return

    # Published robustness baselines
    pub_rob = baselines.get('Robustness_V2XSet_Noisy', {})

    lines = []
    lines.append(r'% Table 3: noise robustness (V2XSet, P_A=0.5, delta=3)')
    lines.append(r'\begin{table}[htbp]')
    lines.append(r'\centering')
    lines.append(r'\caption{Robustness to Localization Noise (V2XSet Noisy, $P_A=0.5$)}')
    lines.append(r'\label{tab:robustness}')
    lines.append(r'\begin{tabular}{|l|c|c|c|c|}')
    lines.append(r'\hline')
    lines.append(r'\textbf{Method} & $\sigma_{xyz}$ (m) & \textbf{BW (MB)} & '
                 r'\textbf{AP@0.5} & \textbf{AP@0.7} \\')
    lines.append(r'\hline')
    lines.append(r'\textbf{Published baselines} & & & & \\')
    lines.append(r'\hline')
    # Sort baselines by AP@0.5
    for sigma_key in ['sigma=0.2m', 'sigma=0.5m']:
        if sigma_key not in pub_rob:
            continue
        sigma_val = float(sigma_key.replace('sigma=', '').replace('m', ''))
        methods_in_level = pub_rob[sigma_key]
        sorted_methods = sorted(
            methods_in_level.items(),
            key=lambda x: x[1].get('AP@0.5', 0) if isinstance(x[1], dict) else 0,
            reverse=True
        )
        for j, (mname, mm) in enumerate(sorted_methods):
            if not isinstance(mm, dict):
                continue
            ap50 = mm.get('AP@0.5')
            ap70 = mm.get('AP@0.7')
            # Only show sigma value on first row of each group
            disp_sigma = f'{sigma_val:.1f}' if j == 0 else ''
            lines.append(f'{mname} & {disp_sigma} & -- & '
                         f'{format_ap(ap50)} & {format_ap(ap70)} \\\\')
    lines.append(r'\hline')
    lines.append(r'\textbf{Ours (SemRD-V2X, $P_A=0.5$)} & & & & \\')
    lines.append(r'\hline')
    for sigma in sorted(n_results.keys()):
        m = n_results[sigma]
        ap50 = safe_ap(m, 0.5)
        ap70 = safe_ap(m, 0.7)
        bw = m.get('avg_bandwidth_MB_per_frame', None)
        lines.append(f'SemRD-V2X (ours) & {sigma:.1f} & {format_bw(bw)} & '
                     f'{format_ap(ap50)} & {format_ap(ap70)} \\\\')
    lines.append(r'\hline')
    lines.append(r'\end{tabular}')
    lines.append(r'\end{table}')
    lines.append('')
    with open(output_file, 'a') as f:
        f.write('\n'.join(lines))
    print(f'[generate_section7] Appended Table 3 ({len(n_results)} noise levels)')


# ===========================================================================
# Table 4: heterogeneous receivers
# ===========================================================================

def write_table4(runs, baselines, output_file):
    """Table 4: heterogeneous receivers (DAIR-V2X style vocab split)."""
    # Find our runs
    veh = infra = homo = None
    for run_id, m in runs.items():
        cfg = parse_run_id(run_id)
        if cfg['pa'] != 0.5 or cfg['delta'] != 3:
            continue
        if cfg['vocab'] == 'homogeneous':
            homo = m
        elif cfg['vocab'] == 'vehicle_only':
            veh = m
        elif cfg['vocab'] == 'infra_only':
            infra = m

    if homo is None and veh is None and infra is None:
        return

    # Published DAIR-V2X baseline
    pub_dair = baselines.get('DAIR-V2X', {})

    lines = []
    lines.append(r'% Table 4: heterogeneous receivers (DAIR-V2X-style vocab split)')
    lines.append(r'\begin{table}[htbp]')
    lines.append(r'\centering')
    lines.append(r'\caption{Heterogeneous Receiver Vocabulary (P_A=0.5, $\delta=3$)}')
    lines.append(r'\label{tab:heterogeneous}')
    lines.append(r'\begin{tabular}{|l|c|c|}')
    lines.append(r'\hline')
    lines.append(r'\textbf{Method / Receiver} & \textbf{AP@0.5} & \textbf{AP@0.7} \\')
    lines.append(r'\hline')
    lines.append(r'\textbf{Published baselines (DAIR-V2X)} & & \\')
    lines.append(r'\hline')
    for name, m in sorted(pub_dair.items(), key=lambda x: x[1].get('AP@0.5', 0) if isinstance(x[1], dict) else 0, reverse=True):
        if not isinstance(m, dict):
            continue
        ap50 = m.get('AP@0.5')
        ap70 = m.get('AP@0.7')
        lines.append(f'{name} (DAIR-V2X) & {format_ap(ap50)} & {format_ap(ap70)} \\\\')
    lines.append(r'\hline')
    lines.append(r'\textbf{Ours (SemRD-V2X, on V2XSet, $P_A=0.5$)} & & \\')
    lines.append(r'\hline')
    for label, m in [('Homogeneous vocab', homo),
                      ('Vehicle-only vocab', veh),
                      ('Infrastructure-only vocab', infra)]:
        if m is not None:
            ap50 = safe_ap(m, 0.5)
            ap70 = safe_ap(m, 0.7)
            lines.append(f'{label} & {format_ap(ap50)} & {format_ap(ap70)} \\\\')
    lines.append(r'\hline')
    lines.append(r'\end{tabular}')
    lines.append(r'\end{table}')
    lines.append('')
    with open(output_file, 'a') as f:
        f.write('\n'.join(lines))
    print(f'[generate_section7] Appended Table 4')


# ===========================================================================
# Table 5: theory vs empirical
# ===========================================================================

def write_table5(runs, output_file):
    """Table 5: theory vs empirical R(0)."""
    pa_results = {}
    for run_id, m in runs.items():
        cfg = parse_run_id(run_id)
        if cfg['delta'] != 3 or cfg['sigma'] != 0.2 or cfg['vocab'] != 'homogeneous':
            continue
        if cfg['pa'] in pa_results:
            continue
        pa_results[cfg['pa']] = m

    if not pa_results:
        return

    # Use P_A=1.0 empirical as reference for "max" theoretical
    if 1.0 in pa_results and pa_results[1.0].get('avg_bandwidth_MB_per_frame'):
        ref_bw = pa_results[1.0]['avg_bandwidth_MB_per_frame']
    else:
        ref_bw = None

    lines = []
    lines.append(r'% Table 5: theoretical R(0) vs empirical bandwidth.')
    lines.append(r'% Theoretical = P_A * H(pi_A) in nats. Here we approximate H(pi_A)')
    lines.append(r'% with a uniform-prior upper bound (log of # positions).')
    lines.append(r'% For a tighter bound, compute H(pi_A) from saved score distributions.')
    lines.append(r'\begin{table}[htbp]')
    lines.append(r'\centering')
    lines.append(r'\caption{Empirical vs.\ Theoretical Zero-Distortion Rate (V2XSet, $P_A \in \{0.1..1.0\}$)}')
    lines.append(r'\label{tab:theory}')
    lines.append(r'\begin{tabular}{|c|c|c|c|}')
    lines.append(r'\hline')
    lines.append(r'$P_A$ & \textbf{Theory $R(0)$ (MB/frame)} & '
                 r'\textbf{Empirical (MB/frame)} & \textbf{Gap (\%)} \\')
    lines.append(r'\hline')
    for pa in sorted(pa_results.keys(), reverse=True):
        m = pa_results[pa]
        bw = m.get('avg_bandwidth_MB_per_frame', None)
        if bw is None:
            continue
        if pa == 1.0:
            theoretical = bw
            gap_str = r'0.0\% (reference)'
        else:
            if ref_bw is not None:
                theoretical = ref_bw * pa
                gap_pct = (bw - theoretical) / theoretical * 100 if theoretical > 0 else 0
                gap_str = f'{gap_pct:+.1f}\\%'
            else:
                theoretical = bw * pa
                gap_str = '--'
        lines.append(f'{pa:.2f} & {format_bw(theoretical)} & '
                     f'{format_bw(bw)} & {gap_str} \\\\')
    lines.append(r'\hline')
    lines.append(r'\end{tabular}')
    lines.append(r'\end{table}')
    lines.append('')
    with open(output_file, 'a') as f:
        f.write('\n'.join(lines))
    print(f'[generate_section7] Appended Table 5 ({len(pa_results)} rows)')


# ===========================================================================
# Table 6: ablation
# ===========================================================================

def write_table6(runs, output_file):
    """Table 6: ablation study."""
    ablations = {}
    for run_id, m in runs.items():
        if 'T6' not in run_id:
            continue
        ablations[run_id] = m

    if not ablations:
        return

    lines = []
    lines.append(r'% Table 6: ablation study')
    lines.append(r'\begin{table}[htbp]')
    lines.append(r'\centering')
    lines.append(r'\caption{Ablation Studies (P_A = 0.5, V2XSet Noisy)}')
    lines.append(r'\label{tab:ablation}')
    lines.append(r'\begin{tabular}{|l|c|c|c|c|c|}')
    lines.append(r'\hline')
    lines.append(r'\textbf{Run ID} & \textbf{Core} & \textbf{IM} & \textbf{RR} & '
                 r'\textbf{AP@0.7} & \textbf{BW (MB)} \\')
    lines.append(r'\hline')

    for run_id, m in sorted(ablations.items()):
        # Parse config from run_id (T6_*)
        config = run_id[3:]  # strip T6_
        is_fixed = 'FIXED' in config
        is_learned = 'LEARNED' in config
        core_label = 'Random/Fixed' if is_fixed else 'Learned'
        if 'D00' in config:
            im_label = 'No'
        else:
            im_label = 'Yes'
        rr_label = 'Yes' if 'RRon' in config else 'No'
        ap70 = safe_ap(m, 0.7)
        bw = m.get('avg_bandwidth_MB_per_frame', None)
        lines.append(f'{run_id} & {core_label} & {im_label} & {rr_label} & '
                     f'{format_ap(ap70)} & {format_bw(bw)} \\\\')
    lines.append(r'\hline')
    lines.append(r'\end{tabular}')
    lines.append(r'\end{table}')
    lines.append('')
    with open(output_file, 'a') as f:
        f.write('\n'.join(lines))
    print(f'[generate_section7] Appended Table 6 ({len(ablations)} rows)')


# ===========================================================================
# RD curve data (for Figure 1)
# ===========================================================================

def write_rd_curve_csv(runs, output_csv):
    """Write RD curve data for Figure 1."""
    pa_results = []
    for run_id, m in runs.items():
        cfg = parse_run_id(run_id)
        if cfg['delta'] != 3 or cfg['sigma'] != 0.2 or cfg['vocab'] != 'homogeneous':
            continue
        if 'T6' in run_id or 'T3' in run_id or 'T4' in run_id:
            continue
        ap30 = safe_ap(m, 0.3)
        ap50 = safe_ap(m, 0.5)
        ap70 = safe_ap(m, 0.7)
        bw = m.get('avg_bandwidth_MB_per_frame', None)
        if bw is None:
            continue
        pa_results.append({
            'pa': cfg['pa'],
            'bw_mb': bw,
            'ap_30': ap30,
            'ap_50': ap50,
            'ap_70': ap70,
        })
    pa_results.sort(key=lambda x: x['pa'], reverse=True)
    with open(output_csv, 'w') as f:
        f.write('pa,bw_mb,ap_30,ap_50,ap_70\n')
        for r in pa_results:
            f.write(f"{r['pa']:.2f},{r['bw_mb']:.2f},"
                    f"{r['ap_30']:.3f},{r['ap_50']:.3f},{r['ap_70']:.3f}\n")
    print(f'[generate_section7] Wrote RD curve data: {output_csv} ({len(pa_results)} points)')


# ===========================================================================
# Main
# ===========================================================================

def main():
    import sys
    if len(sys.argv) > 1:
        LOGS = sys.argv[1]
    else:
        LOGS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              '..', '..', 'logs')
        LOGS = os.path.abspath(LOGS)
    print(f'[generate_section7] Reading runs from {LOGS}')

    runs = find_runs(LOGS)
    print(f'[generate_section7] Found {len(runs)} runs')
    for rid in runs:
        print(f'  - {rid}')

    baselines = load_baselines()
    if baselines:
        print(f'[generate_section7] Loaded {len(baselines)} baseline methods')

    if not runs and not baselines:
        print('[generate_section7] WARNING: nothing to do')
        return

    output_tex = os.path.join(LOGS, 'section7_output.tex')
    output_csv = os.path.join(LOGS, 'rd_curve.csv')

    if os.path.exists(output_tex):
        os.remove(output_tex)

    write_table1(runs, baselines, output_tex)
    write_table2(runs, output_tex)
    write_table3(runs, baselines, output_tex)
    write_table4(runs, baselines, output_tex)
    write_table5(runs, output_tex)
    write_table6(runs, output_tex)
    write_rd_curve_csv(runs, output_csv)

    print(f'\n[generate_section7] DONE')
    print(f'  LaTeX tables: {output_tex}')
    print(f'  RD curve data: {output_csv}')


if __name__ == '__main__':
    main()
