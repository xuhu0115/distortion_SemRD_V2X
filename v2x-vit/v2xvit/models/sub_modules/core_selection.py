"""
Core Selection Module (CSM) for SemRD-V2X.

Implements the per-agent learned spatial gating mechanism that approximates
the irredundant perceptual core A ⊆ S (cf. Definition 4.2 in main.tex,
Section 4.3).

Pipeline (during training):
    feature_map (N, C, H, W)
        ↓
    build_metadata (N, M, H, W)
        ↓
    score_mlp(feat + meta) (N, H*W)  ← learnable
        ↓
    gumbel_topk (N, 1, H, W)  ← differentiable mask
        ↓
    masked_feature (N, C, H, W), core_mass scalar

Where N = total number of agents across the batch (sum of record_len).
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


def _build_positional_grid(h, w, device):
    """Normalized (h, w) coordinates in [0, 1]."""
    ys = torch.linspace(0.0, 1.0, h, device=device)
    xs = torch.linspace(0.0, 1.0, w, device=device)
    yy, xx = torch.meshgrid(ys, xs, indexing="ij")  # (H, W) each
    return yy, xx


class CoreSelectionModule(nn.Module):
    """
    Per-agent learned spatial gate approximating the irredundant core.

    Args:
        in_dim: input feature channels (default 256, matches v2x-vit shrink_conv output)
        metadata_dim: number of metadata channels used for scoring
            (we use 5 channels: y, x, log_var, intensity_peak, dist_to_center)
        hidden: hidden width of the score MLP
        target_mass: P_A — target fraction of positions selected as core
        gumbel_tau: Gumbel-Softmax temperature; will be annealed externally via set_temperature()
    """

    def __init__(self,
                 in_dim: int = 256,
                 metadata_dim: int = 5,
                 hidden: int = 128,
                 target_mass: float = 0.5,
                 gumbel_tau: float = 5.0):
        super().__init__()
        self.in_dim = in_dim
        self.metadata_dim = metadata_dim
        self.target_mass = float(target_mass)
        self.gumbel_tau = float(gumbel_tau)

        self.score_mlp = nn.Sequential(
            nn.Linear(in_dim + metadata_dim, hidden),
            nn.ReLU(inplace=True),
            nn.Linear(hidden, 1),
        )

        # Cache the last computed score_logits so the trainer can read it back
        # for the rate regularizer (RR) without re-running the network.
        self._last_score_logits = None

    # ------------------------------------------------------------------ utils

    def set_target_mass(self, mass: float):
        self.target_mass = float(mass)

    def set_temperature(self, tau: float):
        self.gumbel_tau = float(tau)

    @torch.no_grad()
    def _local_variance(self, x: torch.Tensor, ksize: int = 3) -> torch.Tensor:
        """Local spatial variance via unfold — used as one of the metadata."""
        N, C, H, W = x.shape
        pad = ksize // 2
        x_pad = F.pad(x, (pad, pad, pad, pad), mode="reflect")
        patches = x_pad.unfold(2, ksize, 1).unfold(3, ksize, 1)
        # patches: (N, C, H, W, k, k)
        var = patches.var(dim=(4, 5)).mean(dim=1, keepdim=True)  # (N, 1, H, W)
        var = torch.log1p(var)  # compress range
        return var

    def build_metadata(self, feature_map: torch.Tensor) -> torch.Tensor:
        """Compute per-position metadata (5 channels).

        Channels (in order):
            0: normalized y
            1: normalized x
            2: log local feature variance
            3: max-pooled feature magnitude (proxy for "interestingness")
            4: distance to BEV center (0 = center, 1 = corner)
        """
        N, C, H, W = feature_map.shape
        device = feature_map.device

        yy, xx = _build_positional_grid(H, W, device)  # each (H, W)
        yy = yy.unsqueeze(0).unsqueeze(0).expand(N, 1, H, W)
        xx = xx.unsqueeze(0).unsqueeze(0).expand(N, 1, H, W)

        # local variance
        var = self._local_variance(feature_map, ksize=3)  # (N, 1, H, W)

        # magnitude proxy: max over channels (sparse — highlights "active" positions)
        mag = feature_map.abs().max(dim=1, keepdim=True).values  # (N, 1, H, W)
        mag = mag / (mag.amax(dim=(2, 3), keepdim=True) + 1e-6)

        # distance to BEV center
        cy, cx = 0.5, 0.5
        d = torch.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)  # (N, 1, H, W)
        d = d / (d.amax(dim=(2, 3), keepdim=True) + 1e-6)

        return torch.cat([yy, xx, var, mag, d], dim=1)  # (N, 5, H, W)

    # ----------------------------------------------------------------- forward

    def forward(self, feature_map: torch.Tensor, hard: bool = False):
        """
        Args:
            feature_map: (N, C, H, W) where N = total agents in batch
            hard: if True, use hard top-k (eval mode). If False, use Gumbel-Softmax (train mode).

        Returns:
            masked_feature: (N, C, H, W) — redundant positions zeroed
            mask: (N, 1, H, W) — 1=core, 0=redundant (hard) or soft probabilities
            core_mass: scalar — measured P_A
            score_logits: (N, H*W) — cached for RR
        """
        N, C, H, W = feature_map.shape
        device = feature_map.device

        # 1. build metadata
        metadata = self.build_metadata(feature_map)  # (N, M, H, W)

        # 2. score each position
        feat_flat = feature_map.permute(0, 2, 3, 1).reshape(N, H * W, C)
        meta_flat = metadata.permute(0, 2, 3, 1).reshape(N, H * W, self.metadata_dim)
        cat = torch.cat([feat_flat, meta_flat], dim=-1)  # (N, H*W, C+M)
        score_logits = self.score_mlp(cat).squeeze(-1)  # (N, H*W)
        self._last_score_logits = score_logits.detach()

        # 3. top-k (or gumbel top-k)
        k = max(1, int(self.target_mass * H * W))

        if self.training and not hard:
            # Differentiable top-k via Gumbel noise + soft selection
            # Reference: "Categorical Reparameterization with Gumbel-Softmax"
            # and the sparse top-k trick from "Differentiable Top-k Operator".
            #
            # Approach: add Gumbel noise to scores, take k-th largest as threshold,
            # then use sigmoid((score - threshold) / tau) for soft selection.
            gumbel = -torch.log(-torch.log(torch.rand_like(score_logits) + 1e-20) + 1e-20)
            noisy = score_logits + gumbel
            # k-th largest value per row
            topk_vals, _ = noisy.topk(k, dim=-1)
            threshold = topk_vals[:, -1:].expand_as(noisy)
            soft_mask_flat = torch.sigmoid((noisy - threshold) / max(self.gumbel_tau, 1e-3))
            mask = soft_mask_flat.view(N, 1, H, W)
        else:
            # Hard selection (eval or hard=True)
            _, idx = score_logits.topk(k, dim=-1)
            hard_mask = torch.zeros_like(score_logits)
            hard_mask.scatter_(-1, idx, 1.0)
            mask = hard_mask.view(N, 1, H, W)

        # 4. apply mask
        masked_feature = feature_map * mask

        # 5. measure effective core mass (use binary for hard, mean for soft)
        if self.training and not hard:
            core_mass = mask.mean()
        else:
            core_mass = mask.sum() / mask.numel()

        return masked_feature, mask, core_mass, score_logits