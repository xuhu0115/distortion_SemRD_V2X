#!/usr/bin/env bash
# Quick Comparison Experiment: V2X-ViT v1 baseline vs SemRD-V2X
# Designed for POC: 2 methods x 2 settings x N epochs = fast validation
#
# Usage (from v2x-vit root):
#   bash $SEMRD_ROOT/tools/run_quick_comparison.sh
# or with custom epochs:
#   EPOCHS=3 bash $SEMRD_ROOT/tools/run_quick_comparison.sh
#
# Runs 4 experiments in parallel on 2 GPUs (about EPOCHS * 4.2h total):
#   - Run A: baseline (P_A=1.0, delta=0), Noisy   on GPU 0
#   - Run B: SemRD   (P_A=0.5, delta=3), Noisy   on GPU 1
#   - Run C: baseline (P_A=1.0, delta=0), Perfect on GPU 0  (after A)
#   - Run D: SemRD   (P_A=0.5, delta=3), Perfect on GPU 1  (after B)
#
# After all 4 done, run summarize_quick_comparison.py for the comparison table.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SEMRD_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
V2XVIT_ROOT="$(cd "$SEMRD_ROOT/../v2x-vit" && pwd)"

if [ ! -d "$V2XVIT_ROOT" ]; then
    echo "Error: v2x-vit not found at $V2XVIT_ROOT"
    echo "Adjust by setting V2XVIT_ROOT env var"
    exit 1
fi

# Number of epochs (override with EPOCHS=N bash run_quick_comparison.sh)
EPOCHS=${EPOCHS:-2}

# 4 experiment configs (as bash arrays; older bash < 4.0 needs different syntax)
EXP_A_PA="1.0";  EXP_A_DELTA="0"; EXP_A_RR="false"; EXP_A_SETTING="noisy"
EXP_B_PA="0.5";  EXP_B_DELTA="3"; EXP_B_RR="true";  EXP_B_SETTING="noisy"
EXP_C_PA="1.0";  EXP_C_DELTA="0"; EXP_C_RR="false"; EXP_C_SETTING="perfect"
EXP_D_PA="0.5";  EXP_D_DELTA="3"; EXP_D_RR="true";  EXP_D_SETTING="perfect"

# Make per-experiment yaml files in v2x-vit/hypes_yaml/quick_compare/
mkdir -p "$V2XVIT_ROOT/v2xvit/hypes_yaml/quick_compare"

for exp in A B C D; do
    pa_var="EXP_${exp}_PA";       pa="${!pa_var}"
    delta_var="EXP_${exp}_DELTA"; delta="${!delta_var}"
    rr_var="EXP_${exp}_RR";      rr="${!rr_var}"
    setting_var="EXP_${exp}_SETTING"; setting="${!setting_var}"
    yaml="$V2XVIT_ROOT/v2xvit/hypes_yaml/quick_compare/exp_${exp}_pa${pa}_d${delta}_${setting}.yaml"
    cp "$V2XVIT_ROOT/v2xvit/hypes_yaml/point_pillar_v2xvit_semrd.yaml" "$yaml"
    sed -i "s/target_core_mass: .*/target_core_mass: ${pa}/" "$yaml"
    sed -i "s/inference_depth: .*/inference_depth: ${delta}/" "$yaml"
    sed -i "s/use_rate_reg: .*/use_rate_reg: ${rr}/" "$yaml"
    sed -i "s/epoches: .*/epoches: ${EPOCHS}/" "$yaml"
    if [ "$setting" = "perfect" ]; then
        sed -i "s/async: .*/async: false/" "$yaml"
        sed -i "s/xyz_std: .*/xyz_std: 0.0/" "$yaml"
        sed -i "s/ryp_std: .*/ryp_std: 0.0/" "$yaml"
    else
        sed -i "s/async: .*/async: true/" "$yaml"
        sed -i "s/xyz_std: .*/xyz_std: 0.2/" "$yaml"
        sed -i "s/ryp_std: .*/ryp_std: 0.2/" "$yaml"
    fi
    echo "Created $yaml"
done

# Launch A and B in parallel
echo
echo "=== Launching Run A (baseline noisy) on GPU 0 ==="
CUDA_VISIBLE_DEVICES=0 nohup python "$V2XVIT_ROOT/v2xvit/tools/train_semrd.py" \
    --hypes_yaml "$V2XVIT_ROOT/v2xvit/hypes_yaml/quick_compare/exp_A_pa1.0_d0_noisy.yaml" \
    > /tmp/run_A.log 2>&1 &
PID_A=$!
echo "  PID: $PID_A"

echo "=== Launching Run B (SemRD noisy) on GPU 1 ==="
CUDA_VISIBLE_DEVICES=1 nohup python "$V2XVIT_ROOT/v2xvit/tools/train_semrd.py" \
    --hypes_yaml "$V2XVIT_ROOT/v2xvit/hypes_yaml/quick_compare/exp_B_pa0.5_d3_noisy.yaml" \
    > /tmp/run_B.log 2>&1 &
PID_B=$!
echo "  PID: $PID_B"

echo
echo "Waiting for A and B to complete (will take ~${EPOCHS}*4.2h)..."
wait $PID_A
echo "Run A done."
wait $PID_B
echo "Run B done."

# Launch C and D
echo
echo "=== Launching Run C (baseline perfect) on GPU 0 ==="
CUDA_VISIBLE_DEVICES=0 nohup python "$V2XVIT_ROOT/v2xvit/tools/train_semrd.py" \
    --hypes_yaml "$V2XVIT_ROOT/v2xvit/hypes_yaml/quick_compare/exp_C_pa1.0_d0_perfect.yaml" \
    > /tmp/run_C.log 2>&1 &
PID_C=$!
echo "  PID: $PID_C"

echo "=== Launching Run D (SemRD perfect) on GPU 1 ==="
CUDA_VISIBLE_DEVICES=1 nohup python "$V2XVIT_ROOT/v2xvit/tools/train_semrd.py" \
    --hypes_yaml "$V2XVIT_ROOT/v2xvit/hypes_yaml/quick_compare/exp_D_pa0.5_d3_perfect.yaml" \
    > /tmp/run_D.log 2>&1 &
PID_D=$!
echo "  PID: $PID_D"

wait $PID_C
echo "Run C done."
wait $PID_D
echo "Run D done."

echo
echo "=== All 4 runs done. Run summary script: ==="
echo "  python $SEMRD_ROOT/tools/summarize_quick_comparison.py"
