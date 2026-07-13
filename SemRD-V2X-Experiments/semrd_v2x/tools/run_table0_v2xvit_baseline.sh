#!/usr/bin/env bash
# Table 0: TRUE V2X-ViTv1 baseline (no SemRD modules)
#
# This is a CRITICAL addition: T1_P10_D03_S00.2 is NOT equivalent to V2X-ViTv1
# because even with P_A=1.0, the CSM/IM/RR modules are still active.
#
# To get a TRULY clean baseline, we use the original V2X-ViT yaml (point_pillar_v2xvit.yaml)
# and the original PointPillarTransformer model class. This is byte-equivalent to
# running V2X-ViTv1 with no SemRD modifications whatsoever.
#
# Usage: bash run_table0_v2xvit_baseline.sh 0

source "$(dirname "$0")/_run_helpers.sh"

# Use the ORIGINAL V2X-ViT yaml, NOT the SemRD yaml.
# The model core_method 'point_pillar_v2xvit' maps to PointPillarTransformer
# (the original V2X-ViT model class with no SemRD code).
V2XVIT_YAML=$V2X/v2xvit/hypes_yaml/point_pillar_v2xvit.yaml

EPOCHS=${EPOCHS:-60}  # default to V2X-ViT paper's 60 epochs
SIGMA=${SIGMA:-0.2}

# Override the original V2X-ViT yaml's epoches field with our EPOCHS.
# This is needed because the V2X-ViT yaml has epoches: 60 hardcoded
# but we may want to run fewer epochs for time budget reasons.
update_v2xvit_yaml() {
    local key="$1" val="$2"
    python3 -c "
import sys
path = '$V2XVIT_YAML'
key = sys.argv[1]
val = sys.argv[2()
import re
with open(path) as f:
    lines = f.readlines()
new_lines = []
pat = re.compile(r'^(\s*)' + re.escape(key) + r'\s*:')
for line in lines:
    m = pat.match(line)
    if m:
        indent = m.group(1)
        new_lines.append(indent + key + ': ' + val + '\n')
    else:
        new_lines.append(line)
with open(path, 'w') as f:
    f.writelines(new_lines)
" "$key" "$val"
}

GPUS=("$@")
GPU=${GPUS:-0}

echo "=== Table 0: TRUE V2X-ViTv1 baseline (using ORIGINAL V2X-ViT yaml) ==="
echo "  GPU: $GPU"
echo "  EPOCHS: $EPOCHS"
echo "  sigma: $SIGMA"
echo "  yaml: $V2XVIT_YAML"
echo
echo "NOTE: This uses the original PointPillarTransformer (no SemRD wrapper)."
echo "It should be byte-equivalent to V2X-ViTv1 reproduction."
echo

# We need to temporarily change the yaml the script uses.
# Save current SEMRD yaml path, point to original V2X-ViT yaml.
run_id="T0_V2XVITv1_sigma${SIGMA}"

if [[ -f $LOGS/${run_id}/metrics.json ]]; then
    echo "[$(date +%H:%M:%S)] SKIP $run_id (already done)"
else
    # Override the original V2X-ViT yaml's epoches field with our EPOCHS env var
    update_v2xvit_yaml epoches $EPOCHS
    sleep 2

    mkdir -p $LOGS/${run_id}
    echo "[$(date +%H:%M:%S)] Training $run_id on GPU $GPU (using V2X-ViT yaml, $EPOCHS epochs)"
    CUDA_VISIBLE_DEVICES=$GPU nohup python $V2X/v2xvit/tools/train_semrd.py \
        --hypes_yaml $V2XVIT_YAML > $LOGS/${run_id}.log 2>&1 &
    TRAIN_PID=$!

    # Wait for it
    wait $TRAIN_PID
fi

# Inference
start_inference $run_id $GPU

echo
echo "Done! Compare T0 (true V2X-ViT baseline) vs T1_P10 (SemRD P_A=1.0, IM, RR)."
echo "If T0 AP >> T1_P10 AP, then IM and RR add value even at no compression."
echo "If T0 AP == T1_P10 AP, then SemRD overhead is negligible."
