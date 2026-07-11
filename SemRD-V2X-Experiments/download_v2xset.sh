#!/usr/bin/env bash
# Download V2XSet dataset (and optionally V2X-ViT pretrained weights).
#
# V2XSet is hosted on UCLA Box. The download is large (~80GB compressed for
# train, ~20GB for validate, ~25GB for test). Use aria2c for fast parallel
# downloads if available; otherwise wget/curl.
#
# Usage:
#   bash download_v2xset.sh                  # download all
#   bash download_v2xset.sh train validate   # only train + validate
#   bash download_v2xset.sh pretrained       # only the V2X-ViT pretrained weights

set -e

# config
V2XVIT_ROOT="${V2XVIT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/v2x-vit}"
DATA_ROOT="$V2XVIT_ROOT/v2xset"

# Box.com folder ID for V2XSet
BOX_FOLDER="https://ucla.app.box.com/v/UCLA-MobilityLab-V2XVIT"

# Pretrained V2X-ViT model (point_pillar_v2xvit) on Google Drive
GDRIVE_FOLDER="1h2UOPP2tNRkV_s6cbKcSfMvTgb8_ZFj9"

mkdir -p "$DATA_ROOT"

# -------- helpers --------
have() { command -v "$1" >/dev/null 2>&1; }

# aria2 is 10x faster for big files
if have aria2c; then
    echo "[info] Using aria2c for fast parallel download"
    DOWNLOAD_CMD="aria2c -x 8 -s 8 -c --console-log-level=warn"
elif have curl; then
    echo "[info] Using curl (consider installing aria2 for faster downloads)"
    DOWNLOAD_CMD="curl -L -C - -o"
else
    echo "Error: neither aria2c nor curl is available"
    exit 1
fi

# gdown for Google Drive
if ! have gdown; then
    echo "[info] Installing gdown for Google Drive downloads..."
    pip install gdown
fi

download_pretrained() {
    echo
    echo "=== Downloading V2X-ViT pretrained weights from Google Drive ==="
    mkdir -p "$V2XVIT_ROOT/weights"
    cd "$V2XVIT_ROOT/weights"
    gdown --folder "https://drive.google.com/drive/folders/$GDRIVE_FOLDER"
    echo "Pretrained weights saved to $V2XVIT_ROOT/weights"
}

download_v2xset() {
    local SPLIT=$1
    echo
    echo "=== Downloading V2XSet [$SPLIT] ==="
    echo "Source: $BOX_FOLDER"
    echo
    echo "MANUAL STEPS REQUIRED (Box.com does not allow direct download from CLI):"
    echo
    echo "1. Open this URL in a browser:"
    echo "       $BOX_FOLDER"
    echo
    echo "2. Find the file $SPLIT.zip (or $SPLIT.zip.part*) and download it"
    echo "   to:  $DATA_ROOT/"
    echo
    echo "3. If it is in parts, concatenate and unzip:"
    echo "       cd $DATA_ROOT"
    echo "       cat $SPLIT.zip.part* > $SPLIT.zip"
    echo "       unzip $SPLIT.zip"
    echo "       rm $SPLIT.zip $SPLIT.zip.part*"
    echo
    echo "Expected final structure:"
    echo "  $DATA_ROOT/$SPLIT/"
    echo "    ├── 2021_08_22_21_41_24/"
    echo "    │   ├── data_protocol.yaml"
    echo "    │   ├── -1/         # infrastructure agent"
    echo "    │   └── 112/        # connected vehicle"
    echo "    └── ...             # more scenarios"
    echo
}

# -------- main --------
case "${1:-all}" in
    pretrained)
        download_pretrained
        ;;
    train|validate|test)
        download_v2xset "$1"
        ;;
    all)
        download_v2xset train
        download_v2xset validate
        download_v2xset test
        ;;
    *)
        echo "Usage: $0 [train|validate|test|pretrained|all]"
        exit 1
        ;;
esac
