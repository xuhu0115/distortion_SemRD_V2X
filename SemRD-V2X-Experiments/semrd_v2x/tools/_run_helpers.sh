#!/usr/bin/env bash
# Shared helpers for all run_*.sh scripts.
# Source this from the run scripts:
#   source "$(dirname "$0")/_run_helpers.sh"

set -e

# Locate the v2x-vit install
PROJ=${PROJ:-/home/xuhu/project/distortion_SemRD_V2X}
V2X=$PROJ/project/v2x-vit
YAML=$V2X/v2xvit/hypes_yaml/point_pillar_v2xvit_semrd.yaml
LOGS=$V2X/logs

mkdir -p "$LOGS"

# num_workers: 8 for new server, 0 for Docker (override with env)
export NUM_WORKERS=${NUM_WORKERS:-8}

# Set a yaml field (idempotent, replaces value after colon)
set_yaml() {
    local key="$1" val="$2"
    sed -i "s|^[[:space:]]*${key}:.*|${key}: ${val}|" "$YAML"
}

# Set yaml with structured fields like 'cav_att_config' nested
# (not used currently but kept for future)
set_yaml_nested() {
    local block="$1" key="$2" val="$3"
    sed -i "/^${block}:/,/^[^[:space:]]/ s|^[[:space:]]*${key}:.*|  ${key}: ${val}|" "$YAML"
}

# Configure yaml with multiple fields at once
configure_yaml() {
    # Args: key1 val1 key2 val2 ...
    while [[ $# -gt 0 ]]; do
        set_yaml "$1" "$2"
        shift 2
    done
}

# Start a training job on a given GPU
# Args: run_id gpu_id
start_training() {
    local run_id=$1
    local gpu=$2
    local logfile=$LOGS/${run_id}.log
    mkdir -p $LOGS/${run_id}
    echo "[$(date +%H:%M:%S)] Training $run_id on GPU $gpu"
    CUDA_VISIBLE_DEVICES=$gpu nohup python $V2X/v2xvit/tools/train_semrd.py \
        --hypes_yaml $YAML > $logfile 2>&1 &
    echo $! > $LOGS/${run_id}.pid
}

# Start inference
# Args: run_id gpu_id
start_inference() {
    local run_id=$1
    local gpu=$2
    local model_dir=$LOGS/${run_id}
    if [[ ! -f $model_dir/net_epoch*.pth ]]; then
        echo "[$(date +%H:%M:%S)] WARN: no checkpoint in $model_dir, skip inference"
        return 1
    fi
    echo "[$(date +%H:%M:%S)] Inference $run_id on GPU $gpu"
    CUDA_VISIBLE_DEVICES=$gpu python $V2X/v2xvit/tools/inference_semrd.py \
        --model_dir $model_dir --fusion_method intermediate \
        > $LOGS/${run_id}_inference.log 2>&1
}

# Wait for a set of training PIDs
# Args: pid1 pid2 ...
wait_for_pids() {
    local failed=0
    for pid in "$@"; do
        if ! wait $pid; then
            failed=1
            echo "[$(date +%H:%M:%S)] PID $pid failed"
        fi
    done
    return $failed
}

# Get list of PIDs from saved .pid files
# Args: run_id1 run_id2 ...
get_pids() {
    for run_id in "$@"; do
        if [[ -f $LOGS/${run_id}.pid ]]; then
            cat $LOGS/${run_id}.pid
        fi
    done
}

# Print summary of all runs
summarize() {
    echo
    echo "=== Summary of training ==="
    for run_dir in $(ls -dt $LOGS/*/); do
        run_id=$(basename $run_dir)
        if [[ -f $run_dir/training_log.csv ]]; then
            echo "  $run_id:"
            tail -n 1 $run_dir/training_log.csv
        fi
    done
}
