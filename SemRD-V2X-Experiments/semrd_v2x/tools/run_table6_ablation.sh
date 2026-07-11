#!/usr/bin/env bash
# Table 6: ablation studies
# 4 runs comparing: fixed core / no IM / no RR / full method
# Usage: bash run_table6_ablation.sh 0 1 2 3

source "$(dirname "$0")/_run_helpers.sh"

EPOCHS=${EPOCHS:-30}

GPUS=("$@")
if [[ ${#GPUS[@]} -eq 0 ]]; then
    echo "Usage: $0 <gpu1> [gpu2] [gpu3] [gpu4]"
    echo "Example: $0 0 1 2 3"
    exit 1
fi

# Ablation configurations
# Each entry: "run_id P_A inference_depth use_rate_reg"
ABLATIONS=(
    "T6_FIXED_P05_D00_RRoff 0.5 0 false"      # fixed core (random), no IM, no RR
    "T6_LEARNED_P05_D00_RRoff 0.5 0 false"    # learned core, no IM, no RR
    "T6_LEARNED_P05_D03_RRoff 0.5 3 false"    # learned + IM, no RR
    "T6_LEARNED_P05_D03_RRon  0.5 3 true"      # full method
)

echo "=== Table 6: ablation (${#ABLATIONS[@]} runs) ==="
echo "  GPUs: ${GPUS[@]}"
echo

PIDS=()

for i in "${!ABLATIONS[@]}"; do
    cfg_line=${ABLATIONS[$i]}
    run_id=$(echo $cfg_line | awk '{print $1}')
    pa=$(echo $cfg_line | awk '{print $2}')
    d=$(echo $cfg_line | awk '{print $3}')
    rr=$(echo $cfg_line | awk '{print $4}')

    gpu=${GPUS[$((i % ${#GPUS[@]}))]}

    if [[ -f $LOGS/${run_id}/metrics.json ]]; then
        echo "[$(date +%H:%M:%S)] SKIP $run_id (already done)"
        continue
    fi

    set_yaml target_core_mass $pa
    set_yaml inference_depth $d
    set_yaml use_rate_reg $rr
    set_yaml epoches $EPOCHS
    sleep 2
    start_training $run_id $gpu
    PIDS+=($(get_pids $run_id))
done

echo "Waiting for ${#PIDS[@]} runs..."
wait_for_pids "${PIDS[@]}"

summarize
