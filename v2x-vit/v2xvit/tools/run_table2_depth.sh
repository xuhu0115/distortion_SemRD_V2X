#!/usr/bin/env bash
# Table 2: depth sweep (Inference Depth Analysis)
# 6 runs total at P_A=0.5
# Usage: bash run_table2_depth.sh 0 1 2 3 4 5
#   Args: GPU IDs to use (provide 1-6)
#   If you have 4 GPUs, only 4 runs start in parallel; remaining wait.
#   Idempotent: re-running skips runs that have metrics.json.
#
# Selective run (env vars):
#   ONLY_DEPTHS="0 3 5"     - run only depths 0, 3, 5
#   ONLY_INDICES="0 2 4"    - run only array indices 0, 2, 4
#   ONLY_RUN_IDS="T2_P05_D03_S00.2" - run a specific run
#
# Reuses results: if logs/<run_id>/metrics.json exists, skip that run.

source "$(dirname "$0")/_run_helpers.sh"

DEPTHS=(0 1 2 3 4 5)
EPOCHS=${EPOCHS:-30}

GPUS=("$@")
if [[ ${#GPUS[@]} -eq 0 ]]; then
    echo "Usage: $0 <gpu1> [gpu2> [gpu3> ..."
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
RUN_IDS=()

for i in "${!DEPTHS[@]}"; do
    d=${DEPTHS[$i]}
    # Filter by env var
    if should_skip_by_index $i; then
        echo "[$(date +%H:%M:%S)] SKIP index $i (filtered by ONLY_INDICES)"
        continue
    fi
    if should_skip_by_value "$d" "ONLY_DEPTHS"; then
        echo "[$(date +%H:%M:%S)] SKIP δ=$d (filtered by ONLY_DEPTHS)"
        continue
    fi

    d_x=$(printf '%02d' $d)
    run_id="T2_P05_D${d_x}_S00.2"

    # Skip if run_id filtered out
    if should_skip_by_run_id "$run_id"; then
        echo "[$(date +%H:%M:%S)] SKIP $run_id (filtered by ONLY_RUN_IDS)"
        continue
    fi

    if [[ -f $LOGS/${run_id}/metrics.json ]]; then
        echo "[$(date +%H:%M:%S)] SKIP $run_id (already done)"
        continue
    fi

    set_yaml inference_depth $d
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
