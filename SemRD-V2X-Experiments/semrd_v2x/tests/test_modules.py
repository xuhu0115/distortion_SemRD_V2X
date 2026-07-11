"""
Unit tests for SemRD-V2X modules.

These tests use synthetic random data and DO NOT require v2x-vit / GPU.
After `bash install.sh` (which places the new modules under v2xvit/),
run from the v2x-vit repo root:
    python -m v2xvit.tests.test_modules
or:
    python v2xvit/tests/test_modules.py

Tests:
  T1. CoreSelectionModule forward shape + core mass correctness
  T2. DifferentiableInferenceModule forward shape + mask preservation
  T3. rate_regularization: zero when probs are delta
  T4. End-to-end: simulate the per-agent forward (no fusion_net, no v2x-vit)
  T5. Bandwidth measurement: linear scaling with P_A
"""

import sys
import os

# Allow running as standalone without `pip install -e .`:
#   __file__ is v2x-vit/v2xvit/tests/test_modules.py
#   We need PYTHONPATH to point at v2x-vit/ (the parent of the v2xvit/ package)
#   That's 2 levels up from the test file's directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import torch
import torch.nn.functional as F


def test_csm():
    # After install, the modules live under v2xvit.models.sub_modules
    from v2xvit.models.sub_modules.core_selection import CoreSelectionModule
    print("T1. CoreSelectionModule ... ", end="")
    csm = CoreSelectionModule(in_dim=64, metadata_dim=5, hidden=32,
                              target_mass=0.5, gumbel_tau=2.0)
    # synthetic input: 3 agents, 64 channels, 12x16 BEV
    x = torch.randn(3, 64, 12, 16)
    csm.train()
    masked, mask, mass, logits = csm(x)
    assert masked.shape == x.shape
    assert mask.shape == (3, 1, 12, 16)
    assert logits.shape == (3, 12 * 16)
    # 0.4 <= mass <= 0.6 (allow some slop for small grids)
    assert 0.3 < float(mass) < 0.7, f"mass out of range: {mass}"
    # eval mode uses hard top-k
    csm.eval()
    masked, mask, mass, _ = csm(x, hard=True)
    assert 0.3 < float(mass) < 0.7, f"hard mass out of range: {mass}"
    print(f"OK (mass={float(mass):.3f})")


def test_im():
    from v2xvit.models.sub_modules.inference_module import DifferentiableInferenceModule
    print("T2. DifferentiableInferenceModule ... ", end="")
    im = DifferentiableInferenceModule(dim=64, depth=2, kernel_size=3)
    B, L, C, H, W = 2, 3, 64, 12, 16
    x = torch.randn(B, L, C, H, W)
    # mask shape (B, L, 1, H, W) broadcasts naturally to (B, L, C, H, W)
    mask = torch.zeros(B, L, 1, H, W)
    mask[:, :, :, :6, :8] = 1.0  # upper-left quadrant is "core"
    out = im(x, mask)
    assert out.shape == x.shape
    # core positions should be exactly preserved
    # NO unsqueeze needed — mask shape is (B, L, 1, H, W) already, broadcasts on C dim
    diff_core = (out * mask - x * mask).abs().max()
    assert diff_core < 1e-5, f"core positions drifted by {diff_core}"
    print("OK (core positions preserved)")


def test_rr():
    from v2xvit.models.sub_modules.rate_regularizer import rate_regularization
    print("T3. rate_regularization ... ", end="")
    # delta distribution: H = 0, so rate_loss = 0
    logits = torch.tensor([[10.0, 0.0, 0.0, 0.0]])  # peaked
    probs = F.softmax(logits, dim=-1)
    cm = torch.tensor(0.5)
    loss = rate_regularization(cm, probs, lambda_rate=1.0)
    assert float(loss) < 1e-3, f"loss should be ~0, got {loss}"
    # uniform distribution: H = log(N), max entropy
    probs_uniform = torch.full((1, 4), 0.25)
    loss = rate_regularization(cm, probs_uniform, lambda_rate=1.0)
    # use math.log for Python scalars (torch's .log() needs a tensor)
    import math
    expected = 1.0 * 0.5 * (-4 * 0.25 * math.log(0.25 + 1e-8))
    assert abs(float(loss) - float(expected)) < 1e-3, f"loss {loss} != expected {expected}"
    print(f"OK (uniform H={float(loss/0.5):.3f})")


def test_end_to_end_synthetic():
    """Simulate the per-agent forward without v2x-vit dependencies.

    Builds: x -> CSM -> masked -> regroup -> IM -> masked_2
    """
    from v2xvit.models.sub_modules.core_selection import CoreSelectionModule
    from v2xvit.models.sub_modules.inference_module import DifferentiableInferenceModule
    from v2xvit.models.sub_modules.rate_regularizer import rate_regularization
    from v2xvit.models.point_pillar_v2xvit_semrd import _regroup_mask
    print("T4. End-to-end synthetic ... ", end="")

    B, L, C, H, W = 2, 3, 64, 12, 16
    N = B * L  # assuming all samples have L agents (worst case)
    x = torch.randn(N, C, H, W)
    record_len = torch.tensor([L] * B)  # all samples have L agents

    # Stage 1: CSM
    csm = CoreSelectionModule(in_dim=C, target_mass=0.5)
    csm.train()
    masked, mask, mass, logits = csm(x)
    assert masked.shape == x.shape

    # Stage 2: regroup mask
    regrouped_mask = _regroup_mask(mask, record_len, L)
    assert regrouped_mask.shape == (B, L, 1, H, W)

    # Stage 3: regroup features (mimicking v2x-vit's regroup)
    # For simplicity, we treat the masked features as already grouped
    regrouped_feat = masked.view(B, L, C, H, W)

    # Stage 4: IM
    im = DifferentiableInferenceModule(dim=C, depth=2)
    out = im(regrouped_feat, regrouped_mask)
    assert out.shape == (B, L, C, H, W)

    # Stage 5: rate loss
    probs = F.softmax(logits, dim=-1)
    rate_loss = rate_regularization(mass, probs, lambda_rate=0.05)
    assert float(rate_loss) >= 0
    print(f"OK (mass={float(mass):.3f}, rate_loss={float(rate_loss):.4f})")


def test_bandwidth():
    # measure_bandwidth.py is installed at v2xvit/tools/measure_bandwidth.py
    from v2xvit.tools.measure_bandwidth import compute_bandwidth
    print("T5. Bandwidth scaling ... ", end="")
    bw_10 = compute_bandwidth(num_agents=5, P_A=0.1, C=256, H=48, W=176)['bandwidth_mb']
    bw_50 = compute_bandwidth(num_agents=5, P_A=0.5, C=256, H=48, W=176)['bandwidth_mb']
    bw_100 = compute_bandwidth(num_agents=5, P_A=1.0, C=256, H=48, W=176)['bandwidth_mb']
    # 0.1 * 5 == 0.5 of 0.5*5 == 0.1 of 1.0*5
    assert abs(bw_10 / bw_50 - 0.2) < 1e-3
    assert abs(bw_50 / bw_100 - 0.5) < 1e-3
    print(f"OK (0.1->{bw_10:.3f}MB, 0.5->{bw_50:.3f}MB, 1.0->{bw_100:.3f}MB)")


if __name__ == '__main__':
    print("=" * 60)
    print("SemRD-V2X unit tests (synthetic data, no v2x-vit required)")
    print("=" * 60)
    test_csm()
    test_im()
    test_rr()
    test_end_to_end_synthetic()
    test_bandwidth()
    print("=" * 60)
    print("All tests passed.")
