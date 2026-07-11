#!/usr/bin/env bash
# Table 4: heterogeneous receivers (DAIR-V2X-style vocab split)
# 3 runs: homogeneous / vehicle-only / infra-only
# Usage: bash run_table4_heterogeneous.sh 0 1 2

source "$(dirname "$0")/_run_helpers.sh"

# Vocab configurations (need dataset with vehicle/infra vocab split, DAIR-V2X)
# For now, we run on V2XSet with feature masking as a proxy
VOCABS=(homogeneous vehicle_only infra_only)
EPOCHS=${EPOCHS:-30}

GPUS=("$@")
if [[ ${#GPUS[@]} -eq 0 ]]; then
    echo "Usage: $0 <gpu1> [gpu2] [gpu3] ..."
    echo "Example: $0 0 1 2"
    exit 1
fi

# Configure yaml defaults
set_yaml target_core_mass 0.5
set_yaml inference_depth 3
set_yaml use_rate_reg true
set_yaml epoches $EPOCHS

echo "=== Table 4: heterogeneous receivers (${#VOCABS[@]} runs) ==="
echo "  vocab: ${VOCABS[@]}"
echo "  GPUs: ${GPUS[@]}"
echo
echo "WARNING: heterogeneous experiment requires vocab split in the dataset."
echo "Current v2x-vit does not have this built-in. The runs will use the"
echo "default vocab (homogeneous). To enable proper hetero evaluation,"
echo "modify intermediate_fusion_dataset.py to accept vocab mask."
echo

PIDS=()

for i in "${!VOCABS[@]}"; do
    vocab=${VOCABS[$i]}
    gpu=${GPUS[$((i % ${#GPUS[@]}))]}
    run_id="T4_P05_D03_${vocab}"

    if [[ -f $LOGS/${run_id}/metrics.json ]]; then
        echo "[$(date +%H:%M:%S)] SKIP $run_id (already done)"
        continue
    fi

    # TODO: add vocab-specific yaml config
    set_yaml epoches $EPOCHS
    sleep 2
    start_training $run_id $gpu
    PIDS+=($(get_pids $run_id))
done

echo "Waiting for ${#PIDS[@]} runs..."
wait_for_pids "${PIDS[@]}"

summarize
