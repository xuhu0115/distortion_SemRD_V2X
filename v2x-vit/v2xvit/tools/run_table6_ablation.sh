#!/usr/bin/env bash
# Table 6: ablation studies
# 4 runs comparing: random core / no IM / no RR / full method
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
# Each entry: "run_id P_A inference_depth use_rate_reg core_selection_mode"
# core_selection_mode: 'random' (no learning) or 'learned' (default)
ABLATIONS=(
    "T6_RANDOM_P05_D03_RRon 0.5 3 true random"      # random core, IM, RR
    "T6_LEARNED_P05_D00_RRon 0.5 0 true learned"    # learned core, no IM, RR
    "T6_LEARNED_P05_D03_RRoff 0.5 3 false learned"  # learned + IM, no RR
    "T6_LEARNED_P05_D03_RRon 0.5 3 true learned"    # full method
)

echo "=== Table 6: ablation (${#ABLATIONS[@]} runs) ==="
echo "  GPUs: ${GPUS[@]}"
echo "  EPOCHS: $EPOCHS"
echo
echo "  Ablations:"
for cfg in "${ABLATIONS[@]}"; do
    run_id=$(echo $cfg | awk '{print $1}')
    pa=$(echo $cfg | awk '{print $2}')
    d=$(echo $cfg | awk '{print $3}')
    rr=$(echo $cfg | awk '{print $4}')
    mode=$(echo $cfg | awk '{print $5}')
    rr_str=$([ "$rr" = "true" ] && echo "RR=on" || echo "RR=off")
    im_str=$([ "$d" = "0" ] && echo "no-IM" || echo "IM=${d}")
    echo "    $run_id: P_A=$pa, $im_str, $rr_str, mode=$mode"
done
echo

PIDS=()
RUN_IDS=()

for i in "${!ABLATIONS[@]}"; do
    cfg_line=${ABLATIONS[$i]}
    run_id=$(echo $cfg_line | awk '{print $1}')

    # Filter by env var
    if should_skip_by_index $i; then
        echo "[$(date +%H:%M:%S)] SKIP index $i (filtered by ONLY_INDICES)"
        continue
    fi
    if should_skip_by_run_id "$run_id"; then
        echo "[$(date +%H:%M:%S)] SKIP $run_id (filtered by ONLY_RUN_IDS)"
        continue
    fi

    pa=$(echo $cfg_line | awk '{print $2}')
    d=$(echo $cfg_line | awk '{print $3}')
    rr=$(echo $cfg_line | awk '{print $4}')
    mode=$(echo $cfg_line | awk '{print $5}')

    if [[ -f $LOGS/${run_id}/metrics.json ]]; then
        echo "[$(date +%H:%M:%S)] SKIP $run_id (already done)"
        continue
    fi

    set_yaml target_core_mass $pa
    set_yaml inference_depth $d
    set_yaml use_rate_reg $rr
    set_yaml core_selection_mode $mode
    set_yaml epoches $EPOCHS
    sleep 2

    # Assign GPU by filtered index (avoids the wrap-around bug where
    # multiple runs were assigned to the same GPU because of skipped
    # indices in between).
    local_idx=${#PIDS[@]}  # 0, 1, 2, ... for non-skipped runs
    gpu=${GPUS[$((local_idx % ${#GPUS[@]}))]}

    start_training $run_id $gpu
    PIDS+=($(get_pids $run_id))
    RUN_IDS+=($run_id)
done

echo "Waiting for ${#PIDS[@]} runs..."
wait_for_pids "${PIDS[@]}"

summarize
