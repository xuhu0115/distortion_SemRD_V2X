#!/usr/bin/env bash
# Table 0: TRUE V2X-ViTv1 baseline (no SemRD modules)
#
# This is a CRITICAL addition: T1_P10_D03_S00.2 is NOT equivalent to V2X-ViTv1
# because even with P_A=1.0, the CSM/IM/RR modules are still active and add:
#   - CSM: score_mlp forward pass (no-op for selection but consumes FLOPs)
#   - IM: 3 extra Conv2d layers (adds capacity)
#   - RR: extra loss term (changes training dynamics)
#
# The TRUE baseline uses semrd.enabled: false to completely disable all SemRD modules.
# This gives us the fair "V2X-ViTv1 baseline" number for the paper.
#
# Usage: bash run_table0_v2xvit_baseline.sh 0

source "$(dirname "$0")/_run_helpers.sh"

EPOCHS=${EPOCHS:-30}
SIGMA=${SIGMA:-0.2}

GPUS=("$@")
GPU=${GPUS:-0}

echo "=== Table 0: TRUE V2X-ViTv1 baseline (semrd.enabled: false) ==="
echo "  GPU: $GPU"
echo "  EPOCHS: $EPOCHS"
echo "  sigma: $SIGMA"
echo

# Configure yaml to be exactly V2X-ViTv1
# The model is PointPillarV2XViTSemRD (inherits from V2X-ViTv1),
# but when semrd.enabled: false, all SemRD modules are bypassed.
set_yaml semrd_enabled false
set_yaml target_core_mass 1.0       # irrelevant but set
set_yaml inference_depth 0          # NO IM
set_yaml use_rate_reg false         # NO RR
set_yaml epoches $EPOCHS
set_yaml xyz_std $SIGMA
set_yaml async false
set_yaml core_selection_mode learned  # irrelevant (CSM is off)
set_yaml vocab homogeneous           # irrelevant (vocab is off)
sleep 2

# Run with same hyperparams as the rest (Adam, lr=0.001, etc.)
# The only difference is semrd.enabled: false
run_id="T0_V2XVITv1_sigma${SIGMA}"

if [[ -f $LOGS/${run_id}/metrics.json ]]; then
    echo "[$(date +%H:%M:%S)] SKIP $run_id (already done)"
else
    start_training $run_id $GPU
    wait
fi

# Inference
start_inference $run_id $GPU

echo
echo "Done! Compare T0 (true baseline) vs T1_P10 (SemRD with P_A=1.0, IM, RR)."
echo "If T0 AP >> T1_P10 AP, then IM and RR add value even at no compression."
echo "If T0 AP == T1_P10 AP, then SemRD overhead is negligible."
