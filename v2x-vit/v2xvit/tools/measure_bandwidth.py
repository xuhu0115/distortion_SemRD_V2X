"""
Standalone bandwidth measurement utility for SemRD-V2X.

Computes the theoretical transmission bandwidth for V2X cooperative perception
under core-based compression, *without* needing a full V2X-ViT forward pass.

Useful for:
  1. Quick estimation of bandwidth at different P_A values
  2. Sanity checking the per-frame bandwidth reported by inference_semrd.py
  3. Computing the theoretical R(D) lower bound for the rate-distortion plot

Usage:
    python measure_bandwidth.py --P_A 0.5
    python measure_bandwidth.py --P_A 0.2 --num_agents 5 --C 256 --H 48 --W 176
"""

import argparse


def compute_bandwidth(num_agents, P_A, C, H, W, bytes_per_element=4):
    """
    Compute per-frame transmission bandwidth in MB.

    Args:
        num_agents: number of collaborating agents (including ego)
        P_A: target core mass (fraction of positions transmitted)
        C, H, W: feature channels, height, width (default v2x-vit shrink output)
        bytes_per_element: float32 = 4 bytes

    Returns:
        dict with bandwidth_mb, elements_transmitted, total_elements_baseline
    """
    total_positions = H * W
    core_positions = int(P_A * total_positions)
    # We only transmit non-ego agents' features (ego already has its own)
    non_ego_agents = max(num_agents - 1, 1)

    # only non-ego agents transmit; ego has its own features
    elements_transmitted = core_positions * C * non_ego_agents
    bytes_transmitted = elements_transmitted * bytes_per_element
    bandwidth_mb = bytes_transmitted / (1024 * 1024)

    # baseline (P_A = 1.0)
    baseline_elements = total_positions * C * non_ego_agents * bytes_per_element
    baseline_mb = baseline_elements / (1024 * 1024)

    return {
        'bandwidth_mb': bandwidth_mb,
        'baseline_mb': baseline_mb,
        'compression_ratio': bandwidth_mb / baseline_mb if baseline_mb > 0 else 0,
        'elements_transmitted': elements_transmitted,
        'core_positions_per_agent': core_positions,
        'total_positions_per_agent': total_positions,
    }


def main():
    parser = argparse.ArgumentParser(description="SemRD-V2X bandwidth estimator")
    parser.add_argument('--P_A', type=float, required=True,
                        help='Target core mass (0 < P_A <= 1)')
    parser.add_argument('--num_agents', type=int, default=5,
                        help='Number of agents in the scene')
    parser.add_argument('--C', type=int, default=256, help='Feature channels')
    parser.add_argument('--H', type=int, default=48, help='BEV height (after shrink)')
    parser.add_argument('--W', type=int, default=176, help='BEV width (after shrink)')
    parser.add_argument('--sweep', action='store_true',
                        help='Sweep P_A from 0.1 to 1.0 and print a table')
    args = parser.parse_args()

    if args.sweep:
        print(f"\n{'P_A':>6} {'Bandwidth (MB)':>16} {'Compression Ratio':>20}")
        print("-" * 50)
        for p in [0.1, 0.2, 0.3, 0.5, 0.75, 1.0]:
            res = compute_bandwidth(args.num_agents, p, args.C, args.H, args.W)
            print(f"{p:>6.2f} {res['bandwidth_mb']:>16.4f} {res['compression_ratio']:>20.4f}")
    else:
        res = compute_bandwidth(args.num_agents, args.P_A, args.C, args.H, args.W)
        print(f"\nBandwidth @ P_A={args.P_A}:")
        for k, v in res.items():
            print(f"  {k}: {v}")


if __name__ == '__main__':
    main()