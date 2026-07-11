#!/usr/bin/env bash
# Table 2: depth sweep (Inference Depth Analysis)
# 5 runs total at P_A=0.5
# Usage: bash run_table2_depth.sh 0 1 2 3 4

source "$(dirname "$0")/_run_helpers.sh"

DEPTHS=(0 1 2 3 4 5)
EPOCHS=${EPOCHS:-30}

GPUS=("$@")
if [[ ${#GPUS[@]} -eq 0 ]]; then
    echo "Usage: $0 <gpu1> [gpu2] [gpu3] ..."
    echo "Example: $0 0 1 2 3 4"
    exit 1
fi

# Configure yaml defaults
set_yaml target_core_mass 0.5
set_yaml use_rate_reg true
set_yaml xyz_std 0.2
set_yaml epoches $EPOCHS

echo "=== Table 2: depth sweep (${#DEPTHS[@]} runs at P_A=0.5) ==="
echo "  depths: ${DEPTHS[@]}"
echo "  GPUs: ${GPUS[@]}"
echo "  Epochs: $EPOCHS"
echo

PIDS=()

for i in "${!DEPTHS[@]}"; do
    d=${DEPTHS[$i]}
    gpu=${GPUS[$((i % ${#GPUS[@]}))]}
    d_x=$(printf '%02d' $d)
    run_id="T2_P05_D${d_x}_S00.2"

    if [[ -f $LOGS/${run_id}/metrics.json ]]; then
        echo "[$(date +%H:%M:%S)] SKIP $run_id (already done)"
        continue
    fi

    set_yaml inference_depth $d
    sleep 2
    start_training $run_id $gpu
    PIDS+=($(get_pids $run_id))
done

echo "Waiting for ${#PIDS[@]} runs..."
wait_for_pids "${PIDS[@]}"

summarize
