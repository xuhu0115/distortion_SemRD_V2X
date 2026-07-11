# Delivery Summary

This document summarizes what was built and how to use it. For detailed
instructions see [README.md](README.md).

## What was built

### Three new modules (POC implementation of the paper's theoretical framework)

| Module | File | Lines | Purpose |
|---|---|---|---|
| Core Selection Module (CSM) | `semrd_v2x/models/sub_modules/core_selection.py` | 175 | Per-agent learned spatial gate via MLP + Gumbel-Top-k |
| Differentiable Inference Module (IM) | `semrd_v2x/models/sub_modules/inference_module.py` | 75 | δ-layer spatial Conv2d stack with mask anchoring (corresponds to paper's rule R1) |
| Rate Regularizer (RR) | `semrd_v2x/models/sub_modules/rate_regularizer.py` | 35 | L_rate = λ · P_A · H(π_A), soft-entropy differentiable proxy |

### Integrated main model

| File | Lines | Purpose |
|---|---|---|
| `semrd_v2x/models/point_pillar_v2xvit_semrd.py` | 250 | Subclass of V2X-ViT's `PointPillarTransformer`. Wires CSM between shrink_conv and regroup, wires IM between regroup and fusion_net, wires RR into the output dict. |

### Training / evaluation infrastructure

| File | Lines | Purpose |
|---|---|---|
| `semrd_v2x/hypes_yaml/point_pillar_v2xvit_semrd.yaml` | 165 | V2X-ViT v1 yaml + new `semrd:` block. P_A, δ, λ, Gumbel schedule all configurable. |
| `semrd_v2x/tools/train_semrd.py` | 160 | Training loop, identical to v2x-vit/train.py except: adds rate_loss to det_loss, anneals Gumbel τ, logs core_mass / bandwidth to tensorboard. |
| `semrd_v2x/tools/inference_semrd.py` | 135 | Eval loop, identical to v2x-vit/inference.py except: times each forward, accumulates core_mass and bandwidth, saves JSON metrics. |
| `semrd_v2x/tools/measure_bandwidth.py` | 80 | Standalone bandwidth estimator. Useful for sanity-checking the RD curve. |
| `semrd_v2x/tests/test_modules.py` | 130 | 5 unit tests using synthetic data, no v2x-vit / GPU required. |

### Deployment helpers

| File | Purpose |
|---|---|
| `install.sh` | Copies the 8 new files into a v2x-vit checkout, without modifying any existing file. |
| `download_v2xset.sh` | Helper for downloading V2XSet (instructions for Box.com manual step + aria2c fast path). |
| `README.md` | Full instructions: install, run, results interpretation. |
| `Section7_Template.tex` | LaTeX section template with [TODO] placeholders. Paste into main.tex once results are in. |

## What I CANNOT do

1. **Run experiments**: I do not have access to your A800 server. You need to
   run training/eval there and report back the metrics.json files.

2. **Verify the code is bug-free end-to-end**: I wrote and reviewed the code
   carefully, but the unit tests only cover the 3 new modules in isolation.
   The full forward pass through V2X-ViT is not unit-tested.

3. **Implement the v2 of V2X-ViTv2 (MSPA, multi-stage backbone)**: This is
   not publicly available. The paper draft's claim of using V2X-ViTv2 needs
   to be downgraded to "V2X-ViT v1" (see Section 7 template's first note).

## Quick start (on your server)

```bash
# The project lives at $PROJ (rename to your actual path)
PROJ=~/projects/distortion_SemRD_V2X
cd $PROJ

# v2x-vit is already cloned at $PROJ/project/v2x-vit/ — no need to re-clone
ls project/v2x-vit/    # confirm it's there

# 1. One-time setup (Python env + pip install)
cd project/v2x-vit
conda create -n v2x-vit python=3.8 -y && conda activate v2x-vit
pip install torch==1.10.0+cu113 spconv-cu113 -f https://download.pytorch.org/whl/cu113
pip install -r requirements.txt && pip install -e .
cd ../..

# 2. Install our new code (default V2XVIT_ROOT auto-resolves to ../v2x-vit)
bash project/SemRD-V2X-Experiments/install.sh

# 3. Sanity check (no data needed)
cd project/v2x-vit
python v2xvit/tests/test_modules.py    # 5/5 should pass

# 4. Download data
bash ../SemRD-V2X-Experiments/download_v2xset.sh

# 5. Train (baseline P_A=1.0, δ=0, no rate reg)
python v2xvit/tools/train_semrd.py --hypes_yaml v2xvit/hypes_yaml/point_pillar_v2xvit_semrd.yaml

# 6. Edit yaml to change P_A / δ / use_rate_reg, repeat for other runs.

# 7. Evaluate
python v2xvit/tools/inference_semrd.py --model_dir logs/<exp_name>/ --fusion_method intermediate
```

### Alternative path setup (if v2x-vit is not in the default location)

```bash
# If v2x-vit is at /some/other/path/v2x-vit
V2XVIT_ROOT=/some/other/path/v2x-vit bash project/SemRD-V2X-Experiments/install.sh
```

## What to report back

For each of the 5 runs in the experimental matrix, send me the contents of
`logs/<exp_name>/metrics.json` — I'll then fill in Section 7.

If something fails, please include the full error trace and the yaml file
you used. I can then debug from the symptoms.
