"""
SemRD-V2X main model: PointPillarTransformer with three new modules.

This is the integrated model for the POC. It inherits PointPillarTransformer
from v2x-vit v1 (which is the public codebase for V2X-ViT; the official
V2X-ViTv2 v2 has not been released). The three additions are:

  1. CoreSelectionModule (CSM) — placed after shrink_conv, before regroup.
     Operates on (N, C, H, W) where N is total agents in batch.
  2. DifferentiableInferenceModule (IM) — placed after regroup, before fusion_net.
     Operates on (B, L, C, H, W) padded per-agent features.
  3. RateRegularizer (RR) — applied during training, no extra forward.

The output dict now contains additional keys for the trainer:
    'rate_loss': scalar — added to detection loss
    'core_mass': scalar — measured P_A (for logging)
    'core_mask': (N, 1, H, W) — for visualization / debugging

This file is meant to be placed at:
    v2xvit/models/point_pillar_v2xvit_semrd.py

so that train_utils.create_model() can find it via core_method='point_pillar_v2xvit_semrd'.
"""

import torch
import torch.nn.functional as F

from v2xvit.models.point_pillar_transformer import PointPillarTransformer
from v2xvit.models.sub_modules.fuse_utils import regroup

# These three are the new modules; they live in the same sub_modules package
# alongside the rest of v2x-vit.
from v2xvit.models.sub_modules.core_selection import CoreSelectionModule
from v2xvit.models.sub_modules.inference_module import DifferentiableInferenceModule
from v2xvit.models.sub_modules.rate_regularizer import rate_regularization


def _regroup_mask(per_agent_mask: torch.Tensor, record_len, max_cav: int):
    """
    Regroup a per-agent (N, 1, H, W) mask into (B, L, 1, H, W), padding with zeros
    for missing agents. Mirrors the logic in v2xvit.models.sub_modules.fuse_utils.regroup.

    Args:
        per_agent_mask: (N, 1, H, W) — from CoreSelectionModule
        record_len: (B,) tensor — number of valid agents per sample
        max_cav: maximum number of CAVs (L)

    Returns:
        regrouped_mask: (B, L, 1, H, W) — padded with zeros
    """
    import numpy as np
    from v2xvit.utils.common_utils import torch_tensor_to_numpy

    _, _, H, W = per_agent_mask.shape
    device = per_agent_mask.device
    cum_sum_len = list(np.cumsum(torch_tensor_to_numpy(record_len)))
    split_masks = torch.tensor_split(per_agent_mask, cum_sum_len[:-1])

    regrouped = []
    for split_mask in split_masks:
        M = split_mask.shape[0]
        pad_len = max_cav - M
        # padding with zeros
        pad = torch.zeros(pad_len, 1, H, W, device=device, dtype=split_mask.dtype)
        padded = torch.cat([split_mask, pad], dim=0)  # (L, 1, H, W)
        # view as (1, L, H, W) since C=1
        padded = padded.view(-1, H, W).unsqueeze(0)  # (1, L, H, W)
        regrouped.append(padded)

    out = torch.cat(regrouped, dim=0)  # (B, L, H, W)
    out = out.unsqueeze(2)  # (B, L, 1, H, W)
    return out


class PointPillarV2XViTSemRD(PointPillarTransformer):
    """
    V2X-ViT v1 backbone + CSM + IM + (optional) RR.

    The model name is intentionally `point_pillar_v2xvit_semrd` so the
    trainer's `train_utils.create_model()` can find it via the
    `core_method` field in the yaml.

    Important: for `target_core_mass=1.0`, the model should behave identically
    to the baseline V2X-ViT. For `inference_depth=0`, the IM is a no-op.
    """

    def __init__(self, args):
        super().__init__(args)

        # ---- read SemRD config ----
        semrd_cfg = args.get('semrd', {})
        self.semrd_enabled = semrd_cfg.get('enabled', True)
        self.target_core_mass = float(semrd_cfg.get('target_core_mass', 0.5))
        self.inference_depth = int(semrd_cfg.get('inference_depth', 3))
        self.lambda_rate = float(semrd_cfg.get('lambda_rate', 0.05))
        self.use_rate_reg = bool(semrd_cfg.get('use_rate_reg', False))
        self.gumbel_tau_init = float(semrd_cfg.get('gumbel_temperature_init', 5.0))
        self.gumbel_tau_end = float(semrd_cfg.get('gumbel_temperature_end', 0.5))
        self.metadata_dim = int(semrd_cfg.get('metadata_dim', 5))
        self.score_mlp_hidden = int(semrd_cfg.get('score_mlp_hidden', 128))

        # ---- new modules ----
        if self.semrd_enabled:
            self.core_selector = CoreSelectionModule(
                in_dim=256,  # matches shrink_conv output channels
                metadata_dim=self.metadata_dim,
                hidden=self.score_mlp_hidden,
                target_mass=self.target_core_mass,
                gumbel_tau=self.gumbel_tau_init,
            )
            self.inference_module = DifferentiableInferenceModule(
                dim=256,  # matches core_selector input
                depth=self.inference_depth,
            )
        else:
            self.core_selector = None
            self.inference_module = None

        # ---- state for logging ----
        self._last_core_mass = None
        self._last_score_logits = None
        self._last_bandwidth_bytes = None

    # ----------------------------------------------------------------- helpers

    def set_gumbel_temperature(self, tau: float):
        if self.core_selector is not None:
            self.core_selector.set_temperature(tau)

    def set_target_core_mass(self, mass: float):
        if self.core_selector is not None:
            self.core_selector.set_target_mass(mass)
        self.target_core_mass = float(mass)

    @torch.no_grad()
    def measure_bandwidth_bytes(self, mask: torch.Tensor, channels: int = 256) -> float:
        """Measure the per-frame transmission bandwidth given a binary core mask.

        mask: (N, 1, H, W) — 1=core (transmitted), 0=redundant (NOT transmitted)
        Returns: total bytes per frame, assuming float32 (4 bytes per element).
        """
        if mask is None:
            return 0.0
        nonzero = (mask > 0.5).sum().item()
        return float(nonzero) * float(channels) * 4.0  # float32

    # ----------------------------------------------------------------- forward

    def forward(self, data_dict):
        """
        Standard v2x-vit forward, with two new stages injected.

        data_dict (the 'ego' sub-dict passed in):
            - processed_lidar: voxelized point cloud
            - record_len: (B,) number of CAVs per sample
            - spatial_correction_matrix: (B, L, 4, 4)
            - prior_encoding: (B, L, 3)  [velocity, dt, infra]
        """
        voxel_features = data_dict['processed_lidar']['voxel_features']
        voxel_coords = data_dict['processed_lidar']['voxel_coords']
        voxel_num_points = data_dict['processed_lidar']['voxel_num_points']
        record_len = data_dict['record_len']
        spatial_correction_matrix = data_dict['spatial_correction_matrix']
        prior_encoding = data_dict['prior_encoding'].unsqueeze(-1).unsqueeze(-1)

        # ---- Standard v2x-vit stage 1: PillarVFE ----
        batch_dict = {
            'voxel_features': voxel_features,
            'voxel_coords': voxel_coords,
            'voxel_num_points': voxel_num_points,
            'record_len': record_len,
        }
        batch_dict = self.pillar_vfe(batch_dict)
        batch_dict = self.scatter(batch_dict)
        batch_dict = self.backbone(batch_dict)

        spatial_features_2d = batch_dict['spatial_features_2d']
        # (N, 384, 96, 352) — N = total agents in batch

        # ---- Standard v2x-vit stage 2: ShrinkConv ----
        if self.shrink_flag:
            spatial_features_2d = self.shrink_conv(spatial_features_2d)
        # now (N, 256, 48, 176)

        # ===== NEW Stage A: Core Selection =====
        if self.semrd_enabled and self.core_selector is not None:
            masked_features, core_mask, core_mass, score_logits = \
                self.core_selector(spatial_features_2d)
            spatial_features_2d = masked_features

            # measure bandwidth (for logging)
            self._last_core_mass = core_mass
            self._last_score_logits = score_logits
            self._last_bandwidth_bytes = self.measure_bandwidth_bytes(core_mask.detach())
        else:
            core_mask = None
            core_mass = torch.tensor(1.0, device=spatial_features_2d.device)
            score_logits = None
            self._last_core_mass = core_mass
            # full feature transmission (no compression)
            N, C, H, W = spatial_features_2d.shape
            self._last_bandwidth_bytes = float(N) * float(C) * float(H) * float(W) * 4.0

        # ---- Standard v2x-vit stage 3: optional NaiveCompressor ----
        if self.compression:
            spatial_features_2d = self.naive_compressor(spatial_features_2d)

        # ---- Standard v2x-vit stage 4: regroup ----
        regroup_feature, mask = regroup(spatial_features_2d,
                                        record_len,
                                        self.max_cav)
        # (B, L, 256, 48, 176)
        B, L, C, H, W = regroup_feature.shape

        # ===== NEW Stage B: regroup the core mask too =====
        if core_mask is not None:
            regrouped_mask = _regroup_mask(core_mask, record_len, self.max_cav)
        else:
            regrouped_mask = torch.ones(B, L, 1, H, W, device=regroup_feature.device)

        # ===== NEW Stage C: Differentiable Inference Module =====
        if self.semrd_enabled and self.inference_module is not None and self.inference_depth > 0:
            regroup_feature = self.inference_module(regroup_feature, regrouped_mask)
            # missing-agent positions (mask[i]=0 in v2x-vit's regroup mask) should
            # stay at 0 to avoid contaminating the fusion with fake data
            # regroup_feature = regroup_feature * mask.unsqueeze(2).unsqueeze(-1).unsqueeze(-1)

        # ---- Standard v2x-vit stage 5: prior encoding concat ----
        prior_encoding = prior_encoding.repeat(1, 1, 1,
                                               regroup_feature.shape[3],
                                               regroup_feature.shape[4])
        regroup_feature = torch.cat([regroup_feature, prior_encoding], dim=2)

        # ---- Standard v2x-vit stage 6: V2XTransformer fusion ----
        regroup_feature = regroup_feature.permute(0, 1, 3, 4, 2)
        fused_feature = self.fusion_net(regroup_feature, mask, spatial_correction_matrix)
        fused_feature = fused_feature.permute(0, 3, 1, 2)

        # ---- Standard v2x-vit stage 7: detection heads ----
        psm = self.cls_head(fused_feature)
        rm = self.reg_head(fused_feature)

        output_dict = {
            'psm': psm,
            'rm': rm,
            'core_mass': self._last_core_mass,
            'bandwidth_bytes': self._last_bandwidth_bytes,
        }

        # ===== NEW Stage D: Rate Regularizer (only if training + enabled) =====
        if self.training and self.use_rate_reg and score_logits is not None:
            # use soft probabilities from Gumbel-Softmax as the "score_probs"
            # to compute entropy. To avoid re-running the network, we
            # approximate by re-softmaxing the cached score_logits.
            with torch.no_grad():
                probs_for_entropy = F.softmax(score_logits, dim=-1)
            output_dict['rate_loss'] = rate_regularization(
                core_mass=core_mass,
                score_probs=probs_for_entropy,
                lambda_rate=self.lambda_rate,
            )
        else:
            output_dict['rate_loss'] = torch.tensor(0.0, device=psm.device)

        return output_dict