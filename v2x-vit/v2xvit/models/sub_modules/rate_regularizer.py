"""
Rate Regularizer (RR) for SemRD-V2X.

Implements the loss term that approximates the theoretical zero-distortion
rate bound R(0) = P_A · H(π_A) from Theorem 4.3 of main.tex (Section 4.3).

Penalizes:
    1. Large core mass P_A (encourages compression)
    2. High entropy of the score distribution (encourages the network to be
       "decisive" about which positions are core — the soft Gumbel output
       should approach a peaked distribution)

Total: L_rate = λ · P_A · H(score_probs)

The entropy is computed from the Gumbel-Softmax output (soft mask), not
from the raw score logits — this is the closest differentiable proxy for
H(π_A) on the irredundant core.
"""

import torch
import torch.nn.functional as F


def rate_regularization(core_mass: torch.Tensor,
                        score_probs: torch.Tensor,
                        lambda_rate: float = 0.05) -> torch.Tensor:
    """
    Compute the rate regularizer.

    Args:
        core_mass: scalar tensor — measured P_A (after hard or soft selection)
        score_probs: (N, H*W) tensor — probabilities over positions (e.g., from
            Gumbel-Softmax or softmax over scores). Should sum to 1 along last dim.
        lambda_rate: weight λ for the rate loss

    Returns:
        scalar tensor — the rate regularization loss
    """
    # normalize probs to be a proper distribution
    probs = score_probs / (score_probs.sum(dim=-1, keepdim=True) + 1e-8)
    # per-row entropy: H(p) = -Σ p log p
    entropy = -(probs * (probs + 1e-8).log()).sum(dim=-1)  # (N,)
    entropy_mean = entropy.mean()
    return lambda_rate * core_mass * entropy_mean