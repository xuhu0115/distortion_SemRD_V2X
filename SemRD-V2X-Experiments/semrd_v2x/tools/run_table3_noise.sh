#!/usr/bin/env bash
# Table 3: noise robustness
# 3 runs at P_A=0.5, varying sigma_xyz
# Usage: bash run_table3_noise.sh 0 1 2

source "$(dirname "$0")/_run_helpers.sh"

SIGMAS=(0.0 0.2 0.5)
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
set_yaml async true
set_yaml epoches $EPOCHS

echo "=== Table 3: noise robustness (${#SIGMAS[@]} runs at P_A=0.5) ==="
echo "  noise levels: ${SIGMAS[@]}"
echo "  GPUs: ${GPUS[@]}"
echo

PIDS=()

for i in "${!SIGMAS[@]}"; do
    sigma=${SIGMAS[$i]}
    gpu=${GPUS[$((i % ${#GPUS[@]}))]}
    sigma_str=$(printf 'S%0.1f' $sigma)
    run_id="T3_P05_D03_${sigma_str}"

    if [[ -f $LOGS/${run_id}/metrics.json ]]; then
        echo "[$(date +%H:%M:%S)] SKIP $run_id (already done)"
        continue
    fi

    set_yaml xyz_std $sigma
    set_yaml loc_err $([ "$sigma" = "0" ] && echo "false" || echo "true")
    sleep 2
    start_training $run_id $gpu
    PIDS+=($(get_pids $run_id))
done

echo "Waiting for ${#PIDS[@]} runs..."
wait_for_pids "${PIDS[@]}"

summarize
