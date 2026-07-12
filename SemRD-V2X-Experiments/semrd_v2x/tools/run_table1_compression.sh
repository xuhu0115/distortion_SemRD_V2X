#!/usr/bin/env bash
# Table 1: P_A sweep (Core Compression Analysis)
# 6 runs total, each on one GPU
# Usage: bash run_table1_compression.sh 0 1 2 3 4 5
#   Args: GPU IDs to use (provide 1-6)
#   If you have 4 GPUs, only 4 runs start in parallel; remaining wait.
#   Idempotent: re-running skips runs that have metrics.json.

source "$(dirname "$0")/_run_helpers.sh"

# Auto-detect PROJ if not set (catches user running from /root/project/...)
if [[ -z "$PROJ" ]] || [[ ! -d "$V2X" ]]; then
    for candidate in /root/project/distortion_SemRD_V2X \
                    /home/xuhu/project/distortion_SemRD_V2X \
                    $HOME/project/distortion_SemRD_V2X; do
        if [[ -d "$candidate/project/v2x-vit" ]]; then
            export PROJ=$candidate
            V2X=$PROJ/project/v2x-vit
            YAML=$V2X/v2xvit/hypes_yaml/point_pillar_v2xvit_semrd.yaml
            LOGS=$V2X/logs
            echo "[run_table1] Auto-detected PROJ=$PROJ"
            break
        fi
    done
fi

# P_A values to sweep (matching V2X-ViTv2 paper's compression comparison)
PA_VALUES=(1.0 0.75 0.5 0.3 0.2 0.1)
EPOCHS=${EPOCHS:-30}

# Collect GPU IDs
GPUS=("$@")
if [[ ${#GPUS[@]} -eq 0 ]]; then
    echo "Usage: $0 <gpu1> [gpu2] [gpu3] ..."
    echo "Example: $0 0 1 2 3 4 5"
    exit 1
fi

# Configure yaml defaults
set_yaml inference_depth 3
set_yaml use_rate_reg true
set_yaml xyz_std 0.2
set_yaml async false
set_yaml epoches $EPOCHS

echo "=== Table 1: P_A sweep (${#PA_VALUES[@]} runs) ==="
echo "  P_A values: ${PA_VALUES[@]}"
echo "  GPUs: ${GPUS[@]}"
echo "  Epochs: $EPOCHS"
echo

PIDS=()
RUN_IDS=()

for i in "${!PA_VALUES[@]}"; do
    pa=${PA_VALUES[$i]}
    # Filter by env var
    if should_skip_by_index $i; then
        echo "[$(date +%H:%M:%S)] SKIP index $i (filtered by ONLY_INDICES)"
        continue
    fi
    if should_skip_by_value "$pa" "ONLY_PA"; then
        echo "[$(date +%H:%M:%S)] SKIP P_A=$pa (filtered by ONLY_PA)"
        continue
    fi

    # Assign GPU round-robin
    gpu=${GPUS[$((i % ${#GPUS[@]}))]}
    # Format P_A as 2-digit integer (1.0 -> 10, 0.5 -> 05, 0.1 -> 01).
    # Uses python3 to avoid depending on bc.
    pa_x10=$(python3 -c "print(int($pa * 10))")
    run_id="T1_P$(printf '%02d' $pa_x10)_D03_S00.2"

    # Skip if run_id filtered out
    if should_skip_by_run_id "$run_id"; then
        echo "[$(date +%H:%M:%S)] SKIP $run_id (filtered by ONLY_RUN_IDS)"
        continue
    fi

    # Skip if already done (has metrics.json)
    if [[ -f $LOGS/${run_id}/metrics.json ]]; then
        echo "[$(date +%H:%M:%S)] SKIP $run_id (already done)"
        continue
    fi

    # Configure this run's yaml
    set_yaml target_core_mass $pa
    sleep 2  # let yaml write settle

    start_training $run_id $gpu
    PIDS+=($(get_pids $run_id))
    RUN_IDS+=($run_id)
done

# Wait for all
echo "Waiting for ${#PIDS[@]} runs to complete..."
wait_for_pids "${PIDS[@]}"

summarize
echo "Done! Run 'bash run_inference_all.sh <gpu>' to evaluate."
