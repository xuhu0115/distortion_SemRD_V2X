#!/usr/bin/env bash
# Run inference on ALL completed training runs.
# Detects which runs have checkpoints but no metrics.json, and runs them.
# Usage: bash run_inference_all.sh 0
#   Args: GPU ID to use for inference (default: 0)

source "$(dirname "$0")/_run_helpers.sh"

GPUS=("$@")
GPU=${GPUS:-0}

# Find all run directories that have checkpoints but no metrics.json
RUNS_TO_INFER=()
for run_dir in $(ls -d $LOGS/*/ 2>/dev/null); do
    run_id=$(basename $run_dir)
    if [[ -f $run_dir/net_epoch*.pth ]] && [[ ! -f $run_dir/metrics.json ]]; then
        RUNS_TO_INFER+=($run_id)
    fi
done

if [[ ${#RUNS_TO_INFER[@]} -eq 0 ]]; then
    echo "No runs need inference (all done or none trained)."
    exit 0
fi

echo "=== Inference for ${#RUNS_TO_INFER[@]} runs on GPU $GPU ==="
for run_id in "${RUNS_TO_INFER[@]}"; do
    start_inference $run_id $GPU
done

echo "Done! Now run 'python v2xvit/tools/generate_section7.py' to assemble the tables."
