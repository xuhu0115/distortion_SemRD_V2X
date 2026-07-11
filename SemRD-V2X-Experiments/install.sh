#!/usr/bin/env bash
# Install SemRD-V2X modules into the v2x-vit codebase.
#
# Usage (from the project root):
#   bash SemRD-V2X-Experiments/install.sh
#
# This script:
#   1. Locates the v2x-vit checkout (default: ./v2x-vit/ relative to project root).
#      Override with V2XVIT_ROOT env var, e.g.:
#          V2XVIT_ROOT=/some/other/path bash install.sh
#   2. Copies our 3 new sub_modules (CSM, IM, RR) into v2xvit/models/sub_modules/
#   3. Copies the integrated model (point_pillar_v2xvit_semrd.py) into v2xvit/models/
#   4. Copies train_semrd.py / inference_semrd.py / measure_bandwidth.py into v2xvit/tools/
#   5. Copies the new yaml config into v2xvit/hypes_yaml/
#   6. Copies the test module to v2xvit/tests/ for sanity checking
# It does NOT modify any existing file.

set -e

# --- locate v2x-vit ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SEMRD_ROOT="$SCRIPT_DIR/semrd_v2x"

# default: v2x-vit is a sibling of SemRD-V2X-Experiments inside the project root
V2XVIT_ROOT="${V2XVIT_ROOT:-$PROJECT_ROOT/v2x-vit}"

if [ ! -d "$V2XVIT_ROOT" ]; then
    echo "Error: v2x-vit repo not found at $V2XVIT_ROOT"
    echo
    echo "Options:"
    echo "  1. Clone it:  git clone https://github.com/DerrickXuNu/v2x-vit.git $V2XVIT_ROOT"
    echo "  2. Use a different path:"
    echo "       V2XVIT_ROOT=/your/path/to/v2x-vit bash $0"
    exit 1
fi

echo "Project root:  $PROJECT_ROOT"
echo "SemRD-V2X:     $SEMRD_ROOT"
echo "v2x-vit root:  $V2XVIT_ROOT"
echo

# --- copy files ---
echo "=== Installing SemRD-V2X modules into v2x-vit ==="
echo

# 1. sub_modules (3 new files)
cp -v "$SEMRD_ROOT/models/sub_modules/core_selection.py" \
      "$V2XVIT_ROOT/v2xvit/models/sub_modules/core_selection.py"
cp -v "$SEMRD_ROOT/models/sub_modules/inference_module.py" \
      "$V2XVIT_ROOT/v2xvit/models/sub_modules/inference_module.py"
cp -v "$SEMRD_ROOT/models/sub_modules/rate_regularizer.py" \
      "$V2XVIT_ROOT/v2xvit/models/sub_modules/rate_regularizer.py"

# 2. main model
cp -v "$SEMRD_ROOT/models/point_pillar_v2xvit_semrd.py" \
      "$V2XVIT_ROOT/v2xvit/models/point_pillar_v2xvit_semrd.py"

# 3. tools
cp -v "$SEMRD_ROOT/tools/train_semrd.py" \
      "$V2XVIT_ROOT/v2xvit/tools/train_semrd.py"
cp -v "$SEMRD_ROOT/tools/inference_semrd.py" \
      "$V2XVIT_ROOT/v2xvit/tools/inference_semrd.py"
cp -v "$SEMRD_ROOT/tools/measure_bandwidth.py" \
      "$V2XVIT_ROOT/v2xvit/tools/measure_bandwidth.py"
# Shared helper
cp -v "$SEMRD_ROOT/tools/_run_helpers.sh" \
      "$V2XVIT_ROOT/v2xvit/tools/_run_helpers.sh"
# Per-table run scripts
cp -v "$SEMRD_ROOT/tools/run_table1_compression.sh" \
      "$V2XVIT_ROOT/v2xvit/tools/run_table1_compression.sh"
cp -v "$SEMRD_ROOT/tools/run_table2_depth.sh" \
      "$V2XVIT_ROOT/v2xvit/tools/run_table2_depth.sh"
cp -v "$SEMRD_ROOT/tools/run_table3_noise.sh" \
      "$V2XVIT_ROOT/v2xvit/tools/run_table3_noise.sh"
cp -v "$SEMRD_ROOT/tools/run_table4_heterogeneous.sh" \
      "$V2XVIT_ROOT/v2xvit/tools/run_table4_heterogeneous.sh"
cp -v "$SEMRD_ROOT/tools/run_table6_ablation.sh" \
      "$V2XVIT_ROOT/v2xvit/tools/run_table6_ablation.sh"
cp -v "$SEMRD_ROOT/tools/run_inference_all.sh" \
      "$V2XVIT_ROOT/v2xvit/tools/run_inference_all.sh"
# Aggregator + published baselines
cp -v "$SEMRD_ROOT/tools/generate_section7.py" \
      "$V2XVIT_ROOT/v2xvit/tools/generate_section7.py"
cp -v "$SEMRD_ROOT/tools/compare_methods_data.json" \
      "$V2XVIT_ROOT/v2xvit/tools/compare_methods_data.json"
cp -v "$SEMRD_ROOT/tools/make_v2xset_mini.sh" \
      "$V2XVIT_ROOT/v2xvit/tools/make_v2xset_mini.sh"
chmod +x $V2XVIT_ROOT/v2xvit/tools/run_table*.sh \
          $V2XVIT_ROOT/v2xvit/tools/run_inference_all.sh \
          $V2XVIT_ROOT/v2xvit/tools/make_v2xset_mini.sh

# 4. yaml config
cp -v "$SEMRD_ROOT/hypes_yaml/point_pillar_v2xvit_semrd.yaml" \
      "$V2XVIT_ROOT/v2xvit/hypes_yaml/point_pillar_v2xvit_semrd.yaml"
cp -v "$SEMRD_ROOT/hypes_yaml/point_pillar_v2xvit_semrd_mini.yaml" \
      "$V2XVIT_ROOT/v2xvit/hypes_yaml/point_pillar_v2xvit_semrd_mini.yaml"

# 5. tests
mkdir -p "$V2XVIT_ROOT/v2xvit/tests"
cp -v "$SEMRD_ROOT/tests/test_modules.py" \
      "$V2XVIT_ROOT/v2xvit/tests/test_modules.py"

# 6. compile Cython extension (REQUIRED; v2x-vit's setup.py does NOT auto-compile)
#    Note: the .pyx path in setup.py is RELATIVE to v2x-vit root, not v2xvit/utils/.
#    So we must run from $V2XVIT_ROOT, not from v2xvit/utils.
echo
echo "=== Compiling Cython extension (box_overlaps) ==="
echo "(running from $V2XVIT_ROOT so the .pyx relative path resolves)"
cd "$V2XVIT_ROOT"
python v2xvit/utils/setup.py build_ext --inplace 2>&1 | tail -10
echo "Cython extension compiled (or already present)"
ls "$V2XVIT_ROOT/v2xvit/utils/" | grep "box_overlaps.*\.so" && echo "✓ .so file generated" || echo "✗ .so file NOT generated — check error above"

# 7. Replace opencv-python with opencv-python-headless to avoid Qt5 dependency
#    (v2x-vit's vis_utils imports cv2 at top level, which breaks on headless servers
#     where libQt5Core is not installed.)
echo
echo "=== Replacing opencv-python with opencv-python-headless ==="
pip uninstall -y opencv-python 2>&1 | tail -3
pip install opencv-python-headless 2>&1 | tail -3
echo "opencv-python-headless installed"

echo
echo "=== Done ==="
echo
echo "Next steps:"
echo "  1. Install Python dependencies (PyTorch + spconv + open3d):"
echo "       pip install -r $V2XVIT_ROOT/requirements.txt"
echo "       pip install -e $V2XVIT_ROOT"
echo
echo "  2. Compile the Cython extension (box_overlaps):"
echo "       cd $V2XVIT_ROOT && python v2xvit/utils/setup.py build_ext --inplace"
echo "     (This is REQUIRED; v2x-vit's setup.py does NOT compile Cython automatically."
echo "      Without this step, training will fail with: 'No module named v2xvit.utils.box_overlaps')"
echo
echo "  3. Install opencv-python-headless (avoids Qt5 lib dependency):"
echo "       pip install opencv-python-headless"
echo
echo "  4. Run sanity tests (no data needed):"
echo "       python $V2XVIT_ROOT/v2xvit/tests/test_modules.py"
echo
echo "  5. Download V2XSet (see SemRD-V2X-Experiments/download_v2xset.sh)"
echo
echo "  5. Train (baseline P_A=1.0):"
echo "       python $V2XVIT_ROOT/v2xvit/tools/train_semrd.py \\"
echo "           --hypes_yaml $V2XVIT_ROOT/v2xvit/hypes_yaml/point_pillar_v2xvit_semrd.yaml"
echo
echo "  6. Edit the yaml to set semrd.target_core_mass to 0.5 / 0.2 for the other runs."
echo
echo "  7. Evaluate:"
echo "       python $V2XVIT_ROOT/v2xvit/tools/inference_semrd.py \\"
echo "           --model_dir $V2XVIT_ROOT/logs/<exp_name>/ \\"
echo "           --fusion_method intermediate"
