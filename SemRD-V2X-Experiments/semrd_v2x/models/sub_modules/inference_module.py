"""
Differentiable Inference Module (IM) for SemRD-V2X.

Implements the closure operator approximation Cn_V2X via spatial depth-limited
message passing. Corresponds to the bounded inference-depth δ in Theorem 4.6
of main.tex (Section 4.4 — Rate-Depth-Distortion).

Each IM layer is:
    x_{t+1} = x_t + Conv_kxk(GroupNorm(ReLU(x_t)))

The mask enforces that core positions (mask=1, transmitted) keep their
original value, while redundant positions (mask=0) get filled in by the
spatial diffusion.

This implementation corresponds to inference rule R1 (Neighborhood Propagation)
in the paper's main.tex Section 4.2. Rules R2-R4 (multi-view, semantic
completion, infra-to-vehicle) are out of scope for the POC.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class DifferentiableInferenceModule(nn.Module):
    """
    Depth-bounded spatial diffusion for closure reconstruction.

    Args:
        dim: feature channels (default 256)
        depth: δ — number of stacked diffusion layers
        kernel_size: spatial kernel size (3 = Chebyshev-1 neighborhood)
        groups: GroupNorm groups
    """

    def __init__(self,
                 dim: int = 256,
                 depth: int = 3,
                 kernel_size: int = 3,
                 groups: int = 8):
        super().__init__()
        self.dim = dim
        self.depth = depth
        self.kernel_size = kernel_size

        layers = []
        for _ in range(depth):
            layers.append(nn.Sequential(
                nn.Conv2d(dim, dim, kernel_size=kernel_size,
                          padding=kernel_size // 2, bias=False),
                nn.GroupNorm(groups, dim),
                nn.GELU(),
            ))
        self.layers = nn.ModuleList(layers)

    def forward(self,
                x: torch.Tensor,
                mask: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (B, L, C, H, W) — padded per-agent features (from regroup)
            mask: (B, L, 1, H, W) — 1=core (received, keep), 0=redundant (to reconstruct)

        Returns:
            x_reconstructed: (B, L, C, H, W) — same shape as input
        """
        B, L, C, H, W = x.shape
        x_flat = x.reshape(B * L, C, H, W)
        mask_flat = mask.reshape(B * L, 1, H, W)
        # cache the original (transmitted) feature at core positions
        x_original = x_flat * mask_flat

        for layer in self.layers:
            # diffusion update
            x_flat = x_flat + layer(x_flat)
            # re-anchor core positions to their original (transmitted) value
            # this prevents the network from "drifting" away from the actual data
            x_flat = x_flat * (1.0 - mask_flat) + x_original

        return x_flat.reshape(B, L, C, H, W)