#!/usr/bin/env bash
# Run ALL 11 experiments for the SemRD-V2X paper on a 3x A800 server.
#
# Assumes:
#   - v2x-vit + SemRD-V2X modules are installed
#   - 100% V2XSet data in v2x-vit/v2xset/{train,validate,test}
#   - /dev/shm >= 4GB (so num_workers=8 is OK)
#   - conda env v2x-vit activated
#
# Usage:
#   bash v2xvit/tools/run_all_experiments.sh
#
# Each run will be in its own logs/ subdirectory named with the run_id.
# Logs: logs/<run_id>/training_log.csv + metrics.json (after inference).

set -e

PROJ=/home/xuhu/project/distortion_SemRD_V2X
V2X=$PROJ/project/v2x-vit
YAML=$V2X/v2xvit/hypes_yaml/point_pillar_v2xvit_semrd.yaml
LOGS=$V2X/logs

# Number of epochs (matching V2X-ViTv1's standard)
EPOCHS=${EPOCHS:-30}

# Default num_workers (overridable). New server: 8, Docker: 0
export NUM_WORKERS=${NUM_WORKERS:-8}

# SemRD training config (CSM + IM + RR)
SEMRD_OPTS="--hypes_yaml $YAML"

# Helper to set yaml field
set_yaml() {
    local key="$1" val="$2"
    sed -i "s|^${key}:.*|${key}: ${val}|" $YAML
}

# Helper to run one training job on a given GPU
run_train() {
    local run_id=$1
    local gpu=$2
    local logfile=$LOGS/${run_id}.log
    mkdir -p $LOGS/${run_id}
    echo "[$(date +%H:%M:%S)] Training $run_id on GPU $gpu"
    CUDA_VISIBLE_DEVICES=$gpu nohup python $V2X/v2xvit/tools/train_semrd.py \
        $SEMRD_OPTS > $logfile 2>&1
    echo "[$(date +%H:%M:%S)] Done $run_id"
}

# Helper to run inference
run_inference() {
    local run_id=$1
    local gpu=$2
    local model_dir=$LOGS/${run_id}
    echo "[$(date +%H:%M:%S)] Inference $run_id on GPU $gpu"
    CUDA_VISIBLE_DEVICES=$gpu python $V2X/v2xvit/tools/inference_semrd.py \
        --model_dir $model_dir --fusion_method intermediate \
        > $LOGS/${run_id}_inference.log 2>&1
    echo "[$(date +%H:%M:%S)] Done inference $run_id"
}

# Helper to run a full experiment (configure + train + inference)
run_full() {
    local run_id=$1      # e.g. "P10D00_S00.2"
    local gpu=$2
    local pa=$3        # 1.0, 0.5, 0.3, ...
    local depth=$4     # 0, 1, 3, 5
    local rr=$5        # true / false
    local sigma=$6     # noise std (0, 0.2, 0.5)

    # configure yaml
    set_yaml target_core_mass $pa
    set_yaml inference_depth $depth
    set_yaml use_rate_reg $rr
    set_yaml epoches $EPOCHS
    set_yaml xyz_std $sigma

    # train
    run_train $run_id $gpu
    # inference
    run_inference $run_id $gpu
}

cd $V2X

# ============================================================
# BATCH 1 (3 runs in parallel on 3 GPUs)
# ============================================================
echo "=== Batch 1: 3 critical runs (P_A = 1.0, 0.5, 0.3) ==="
(run_full "P10D00_S00.2" 0 1.0 0 false 0.2) &
P1=$!
(run_full "P05D03_S00.2" 1 0.5 3 true  0.2) &
P2=$!
(run_full "P03D03_S00.2" 2 0.3 3 true  0.2) &
P3=$!
wait $P1 $P2 $P3

# ============================================================
# BATCH 2 (3 runs in parallel)
# ============================================================
echo "=== Batch 2: P_A = 0.1, 0.5 d=5, 0.5 d=0 ==="
(run_full "P01D03_S00.2" 0 0.1 3 true  0.2) &
(run_full "P05D05_S00.2" 1 0.5 5 true  0.2) &
(run_full "P05D00_S00.2" 2 0.5 0 true  0.2) &
wait

# ============================================================
# BATCH 3 (2 runs in parallel)
# ============================================================
echo "=== Batch 3: P_A = 0.75, 0.2 ==="
(run_full "P075D03_S00.2" 0 0.75 3 true  0.2) &
(run_full "P02D03_S00.2" 1 0.2 3 true  0.2) &
wait

# ============================================================
# BATCH 4 (3 runs in parallel)
# ============================================================
echo "=== Batch 4: noise test + 2 heterogeneous ==="
(run_full "P05D03_S00.5" 0 0.5 3 true  0.5) &
(run_full "P05D03_VEHICLE" 1 0.5 3 true  0.2) &
(run_full "P05D03_INFRA" 2 0.5 3 true  0.2) &
wait

echo
echo "=== ALL EXPERIMENTS COMPLETED ==="
echo "Collecting metrics..."
python $V2X/v2xvit/tools/generate_section7.py
