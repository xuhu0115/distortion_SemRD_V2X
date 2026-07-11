# SemRD-V2X: Empirical Validation of Deductive Source Coding for V2X Cooperative Perception

This package contains the code to reproduce the experiments in:

> **"Rate-Distortion Theory Meets V2X Cooperative Perception: A Deductive Source Coding Framework for Vision Transformers"** (target: AAAI 2027)

The project applies a recently proposed information-theoretic framework
([Rate-Distortion Theory for Deductive Sources under Closure Fidelity](https://arxiv.org/abs/2604.15698v4),
Xu 2026) to V2X cooperative perception, building on the V2X-ViT v1
backbone (Xu et al., ECCV 2022).

## What is new in this paper

Three new modules on top of the V2X-ViT v1 architecture:

| Module | File | Purpose | Paper Reference |
|---|---|---|---|
| **Core Selection Module (CSM)** | `models/sub_modules/core_selection.py` | Per-agent learned spatial gate that selects the irredundant perceptual core A ⊆ S | Def. 4.2, Sec. 4.3 |
| **Differentiable Inference Module (IM)** | `models/sub_modules/inference_module.py` | δ-layer spatial diffusion approximating the closure operator | Def. 4.4, Sec. 4.4 |
| **Rate Regularizer (RR)** | `models/sub_modules/rate_regularizer.py` | Approximation of the zero-distortion rate bound R(0) = P_A · H(π_A) | Sec. 4.5 |

These are integrated into `models/point_pillar_v2xvit_semrd.py`, a
subclass of V2X-ViT's `PointPillarTransformer`.

## Repository structure

The project lives at `D:\common_file\SJU\Obsidian_vault\10_Research\project\oit\distortion_SemRD_V2X\`:

```
distortion_SemRD_V2X/                  # project root
├── DeepSeek-Chat-Exporter.html        # your advisor's original chat
├── reference/                         # the two reference papers
├── SemRD_V2X/                         # the LaTeX source of your paper
├── SemRD_V2X.tex.zip
└── project/                           # all experimental code
    ├── v2x-vit/                       # cloned v2x-vit (baseline)
    │   ├── v2xvit/                   # main package (unchanged)
    │   └── ...
    └── SemRD-V2X-Experiments/         # this package (new code)
        ├── README.md                  # this file
        ├── install.sh                 # auto-install into v2x-vit/
        ├── download_v2xset.sh         # V2XSet download helper
        ├── Section7_Template.tex      # LaTeX template for paper Section 7
        ├── DELIVERY_SUMMARY.md        # what was built and how to use it
        └── semrd_v2x/                 # the new code
            ├── models/
            │   ├── sub_modules/
            │   │   ├── core_selection.py
            │   │   ├── inference_module.py
            │   │   └── rate_regularizer.py
            │   └── point_pillar_v2xvit_semrd.py
            ├── hypes_yaml/
            │   └── point_pillar_v2xvit_semrd.yaml
            ├── tools/
            │   ├── train_semrd.py
            │   ├── inference_semrd.py
            │   └── measure_bandwidth.py
            └── tests/
                └── test_modules.py
```

## Installation

### Prerequisites
- Linux (Ubuntu 20.04+ recommended) — note: Windows is not directly supported
- Python 3.7+ (3.8 preferred, matches v2x-vit v1)
- CUDA 11.x + cuDNN
- ≥1 GPU with ≥24GB VRAM (A800 recommended)
- ~500 GB free disk space for V2XSet

### Step 1: Verify v2x-vit is in place

The v2x-vit baseline is already cloned to `./project/v2x-vit/`:

```bash
cd /path/to/distortion_SemRD_V2X    # e.g. ~/projects/distortion_SemRD_V2X
ls project/v2x-vit/                  # should show docs/ images/ LICENSE/ README.md ...
```

If you move the project to a different location, you can either:
- Keep the relative layout: `./project/SemRD-V2X-Experiments/` next to `./project/v2x-vit/`, OR
- Override the path with `V2XVIT_ROOT=/path/to/v2x-vit bash project/SemRD-V2X-Experiments/install.sh`

### Step 2: Install Python dependencies (on GPU server)

```bash
# create conda env
conda create -n v2x-vit python=3.8 -y
conda activate v2x-vit

# install PyTorch (adjust cuda version to match your server)
pip install torch==1.10.0+cu113 torchvision==0.11.0+cu113 \
    --extra-index-url https://download.pytorch.org/whl/cu113

# install spconv (use the cuda version matching your torch)
pip install spconv-cu113

# install v2x-vit as a package (and its other deps)
cd project/v2x-vit
pip install -r requirements.txt
pip install -e .
cd ../..
```

### Step 3: Install SemRD-V2X modules

```bash
bash project/SemRD-V2X-Experiments/install.sh
```

This copies our new files (CSM, IM, RR, integrated model, training/eval
scripts, yaml) into the v2x-vit tree without modifying any existing file.

### Step 4: Download V2XSet

V2XSet is ~200-300 GB. The primary source is at UCLA Box:
<https://ucla.app.box.com/v/UCLA-MobilityLab-V2XVIT>

After downloading, place the data as:
```
distortion_SemRD_V2X/
└── project/
    ├── v2x-vit/
    │   ├── v2xset/
    │   │   ├── train/
    │   │   ├── validate/
    │   │   └── test/
    │   └── v2xvit/
    └── SemRD-V2X-Experiments/
```

The `download_v2xset.sh` helper provides instructions:
```bash
bash project/SemRD-V2X-Experiments/download_v2xset.sh
```

## Running experiments

### Sanity check (no data, no GPU)

Verify the new modules can be instantiated and forward correctly:
```bash
cd v2x-vit
python v2xvit/tests/test_modules.py
```
Expected output: 5/5 tests pass.

### Estimate bandwidth (no GPU, no data)

```bash
cd v2x-vit
python v2xvit/tools/measure_bandwidth.py --sweep
```

### Train (single P_A value)

```bash
cd v2x-vit
python v2xvit/tools/train_semrd.py \
    --hypes_yaml v2xvit/hypes_yaml/point_pillar_v2xvit_semrd.yaml
```

To change P_A, edit the yaml:
```yaml
semrd:
  target_core_mass: 0.5   # change to 0.2 / 0.3 / 0.75 / 1.0
  inference_depth: 3       # change to 0 / 1 / 2 / 4
  use_rate_reg: true       # false to disable
```

### Evaluate

```bash
cd v2x-vit
python v2xvit/tools/inference_semrd.py \
    --model_dir logs/point_pillar_v2xvit_semrd_YYYY_MM_DD_HH_MM_SS/ \
    --fusion_method intermediate
```

Saves `metrics.json` with AP@0.5, AP@0.7, bandwidth, core mass, latency.

## Full experiment matrix (paper Section 7)

The experiments are split into 5 **independent** shell scripts, each producing
the runs needed for one table. This lets you parallelize across many GPUs
(4-8) and run them whenever machines are available.

### Scripts overview

| Script | Purpose | # runs | Run IDs |
|---|---|---|---|
| `run_table1_compression.sh` | Table 1: P_A sweep | 6 | `T1_P*_D03_S00.2` |
| `run_table2_depth.sh` | Table 2: δ sweep | 6 | `T2_P05_D*_S00.2` |
| `run_table3_noise.sh` | Table 3: noise robustness | 3 | `T3_P05_D03_S*` |
| `run_table4_heterogeneous.sh` | Table 4: vocab split | 3 | `T4_P05_D03_*` |
| `run_table6_ablation.sh` | Table 6: ablation | 4 | `T6_*` |
| `run_inference_all.sh` | Run inference on completed runs | (auto) | - |
| `generate_section7.py` | Aggregate all results into LaTeX | (1) | - |

All scripts accept GPU IDs as positional args and run in parallel:
```bash
# Use 4 GPUs for Table 1
bash v2xvit/tools/run_table1_compression.sh 0 1 2 3

# Use 2 GPUs for Table 2 (runs will wait for free GPUs)
bash v2xvit/tools/run_table2_depth.sh 0 1

# Use 1 GPU for Table 3 (sequential)
bash v2xvit/tools/run_table3_noise.sh 0
```

### Idempotent design

Each script checks for `metrics.json` and **skips runs that are already done**.
You can re-run any script at any time to retry failed runs.

### After all training is done

```bash
# 1. Run inference on all completed runs (uses GPU 0)
bash v2xvit/tools/run_inference_all.sh 0

# 2. Aggregate all results into LaTeX tables
python v2xvit/tools/generate_section7.py

# Output: v2x-vit/logs/section7_output.tex + rd_curve.csv
# These can be \input{}'d into the main paper.
```

### Example: full 11-run schedule on 4 GPUs

Day 1 (parallel):
- Terminal 1: `bash v2xvit/tools/run_table1_compression.sh 0 1 2`  (3 runs)
- Terminal 2: `bash v2xvit/tools/run_table2_depth.sh 3`             (1 run, takes 6 sequential)

Day 2 (parallel):
- Continue Table 1 (P_A=0.3, 0.2, 0.1)
- Start Table 6 ablation

Day 3:
- Table 3 noise
- Table 4 heterogeneous

Day 4:
- Run inference: `bash v2xvit/tools/run_inference_all.sh 0`
- Generate tables: `python v2xvit/tools/generate_section7.py`

## Experimental matrix for the POC

| Run | P_A | δ | Rate Reg | Approx. time on A800 | Purpose |
|---|---|---|---|---|---|
| 1 | 1.0 | 0 | off | 18-24h | Baseline (V2X-ViT v1) |
| 2 | 0.5 | 0 | off | 18-24h | CSM only, no IM |
| 3 | 0.5 | 3 | off | 18-24h | CSM + IM, no RR |
| 4 | 0.2 | 3 | off | 18-24h | Aggressive compression |
| 5 | 0.2 | 3 | on  | 18-24h | Full SemRD-V2X |

(For a faster POC: 30 epochs and 3 runs → 5-6 days wall clock.)

## Quick Comparison (recommended for fast validation)

For a quick check, run 4 experiments in parallel on 2 GPUs:

```bash
# Default: 2 epochs (~8.4h total wall clock on 2 A800s)
bash v2xvit/tools/run_quick_comparison.sh

# Or 3 epochs (~12.6h)
EPOCHS=3 bash v2xvit/tools/run_quick_comparison.sh
```

### Even faster: use only 10% of data

For an even quicker first sanity check, use only 1/10 of the training data:

```bash
# In yaml, add to train_params:
#   train_subset: 0.1
#   val_subset: 0.1
# Or via env vars (no yaml edit needed):
TRAIN_SUBSET=0.1 VAL_SUBSET=0.1 python v2xvit/tools/train_semrd.py \
    --hypes_yaml v2xvit/hypes_yaml/point_pillar_v2xvit_semrd.yaml
```

With 10% data, each epoch is ~10x faster, so 1 epoch takes ~25 minutes.
Use this to validate the pipeline end-to-end before committing to full runs.

The script runs:
- **Run A**: baseline (P_A=1.0, δ=0), Noisy setting on GPU 0
- **Run B**: SemRD (P_A=0.5, δ=3, rate reg on), Noisy on GPU 1
- **Run C**: baseline, Perfect setting on GPU 0
- **Run D**: SemRD, Perfect setting on GPU 1

After all 4 complete, run inference + summary:

```bash
# Per-run AP / bandwidth
for d in logs/point_pillar_v2xvit_semrd_*; do
    python v2xvit/tools/inference_semrd.py \
        --model_dir "$d" --fusion_method intermediate
done

# Aggregate table (epoch time, GPU memory, bandwidth from training_log.csv)
python v2xvit/tools/summarize_quick_comparison.py
```

Output is a table comparing:
- Final training loss
- Epoch time, total time
- Peak GPU memory
- Average core mass (P_A)
- Average bandwidth during training
- AP@0.5, AP@0.7 (after inference)
- Per-frame bandwidth (after inference)

## Results to report back

After running the above, please report the contents of each
`logs/.../metrics.json`, specifically:

```json
{
    "ap_at_0.5": {...},
    "ap_at_0.7": {...},
    "avg_bandwidth_MB_per_frame": ...,
    "avg_core_mass": ...,
    "avg_latency_ms_per_frame": ...
}
```

I will then update Section 7 (Experiments) of the main.tex paper with
the real numbers.

## Notes on differences from the paper's Section 7

The original paper draft used V2X-ViTv2 (TPAMI 2025) as the backbone.
V2X-ViTv2 v2 is not publicly released, so this implementation uses
V2X-ViT v1 (ECCV 2022) which is the publicly available codebase from
the same lab. The two architectures share the same HMSA core, and our
contribution (CSM + IM + RR) is **architecturally orthogonal** to the
MSPA / multi-stage backbone improvements in v2. The numbers reported
in Section 7 will note this and discuss expected deltas to v2.

## Citation

If you use this code, please cite:
- (Original paper TBD)
- V2X-ViT: Xu et al., "V2X-ViT: Vehicle-to-Everything Cooperative Perception
  with Vision Transformer", ECCV 2022
- The deductive source coding theory: Xu, "Rate-Distortion Theory for
  Deductive Sources under Closure Fidelity", arXiv 2026
