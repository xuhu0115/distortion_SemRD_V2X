#!/usr/bin/env bash
# Shared helpers for all run_*.sh scripts.
# Source this from the run scripts:
#   source "$(dirname "$0")/_run_helpers.sh"

set -e

# Locate the v2x-vit install. Priority:
#   1. $PROJ env var
#   2. $V2XVIT_ROOT env var
#   3. Auto-detect: look up for v2x-vit/ or v2xvit/ from cwd
#   4. Fallback: hardcoded /home/xuhu/project/...
if [[ -n "$PROJ" ]]; then
    : # use PROJ as is
elif [[ -n "$V2XVIT_ROOT" ]]; then
    PROJ="$(dirname "$(dirname "$V2XVIT_ROOT")")"
elif [[ -d "$(pwd)/../v2x-vit" ]]; then
    PROJ="$(cd .. && pwd)"
elif [[ -d "$(pwd)/v2x-vit" ]]; then
    PROJ="$(pwd)"
else
    PROJ="/home/xuhu/project/distortion_SemRD_V2X"
fi

V2X=$PROJ/project/v2x-vit
YAML=$V2X/v2xvit/hypes_yaml/point_pillar_v2xvit_semrd.yaml
LOGS=$V2X/logs

echo "[run_helpers] PROJ=$PROJ"
echo "[run_helpers] YAML=$YAML"

mkdir -p "$LOGS"

# num_workers: 8 for new server, 0 for Docker (override with env)
export NUM_WORKERS=${NUM_WORKERS:-8}

# Set a yaml field (idempotent, preserves leading whitespace).
# Uses python (not sed) to avoid quoting/escaping issues that bit us before.
set_yaml() {
    local key="$1" val="$2"
    python3 -c "
import sys, re
path = '$YAML'
key = sys.argv[1]
val = sys.argv[2]
with open(path, 'r') as f:
    lines = f.readlines()
new_lines = []
pat = re.compile(r'^(\s*)' + re.escape(key) + r'\s*:')
replaced = False
for line in lines:
    m = pat.match(line)
    if m and not replaced:
        indent = m.group(1)
        new_lines.append(indent + key + ': ' + val + '\n')
        replaced = True
    else:
        new_lines.append(line)
with open(path, 'w') as f:
    f.writelines(new_lines)
" "$key" "$val"
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

# ----- Filter functions (selective run) -----
# These functions let you select a subset of runs to execute, instead of running all.
# Usage examples (in your run_table*.sh):
#   ONLY_PA="0.5 0.3" bash run_table1.sh 0
#   ONLY_INDICES="0 2 4" bash run_table1.sh 0 1
#   ONLY_RUN_IDS="T1_P05_D03_S00.2" bash run_table1.sh 0
# Each returns 0 (skip) or 1 (run).

should_skip_by_value() {
    # Args: $1 = value to test, $2 = env var name (e.g. ONLY_PA, ONLY_DEPTHS)
    local value="$1"
    local var_name="$2"
    local allow_list="${!var_name:-}"
    if [[ -z "$allow_list" ]]; then
        return 1  # no filter, don't skip
    fi
    # allow_list is space-separated; check if value is in it
    if [[ " $allow_list " =~ " $value " ]]; then
        return 1  # value is in list, don't skip
    fi
    return 0  # value not in list, skip
}

should_skip_by_index() {
    local index="$1"
    local allow_list="${ONLY_INDICES:-}"
    if [[ -z "$allow_list" ]]; then
        return 1  # no filter, don't skip
    fi
    if [[ " $allow_list " =~ " $index " ]]; then
        return 1  # index in list, don't skip
    fi
    return 0  # skip
}

should_skip_by_run_id() {
    local run_id="$1"
    local allow_list="${ONLY_RUN_IDS:-}"
    if [[ -z "$allow_list" ]]; then
        return 1  # no filter, don't skip
    fi
    if [[ " $allow_list " =~ " $run_id " ]]; then
        return 1  # run_id in list, don't skip
    fi
    return 0  # skip
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
