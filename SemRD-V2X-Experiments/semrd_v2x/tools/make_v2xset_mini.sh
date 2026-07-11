#!/usr/bin/env bash
# Create a mini V2XSet for fast pipeline testing on a new server.
#
# Source: full v2xset at /home/xuhu/project/distortion_SemRD_V2X/project/v2x-vit/v2xset
# Dest:   mini v2xset at v2x-vit/v2xset_mini
#
# Selects first N scenarios of each split, keeps only first K frames
# of each scenario-agent pair. Total size: ~30-80MB.
#
# Usage:
#   bash v2xvit/tools/make_v2xset_mini.sh
#   bash v2xvit/tools/make_v2xset_mini.sh [SRC] [DST]
#   bash v2xvit/tools/make_v2xset_mini.sh [SRC] [DST] --n-train 3 --n-frames 30

set -e

SRC=${1:-/home/xuhu/project/distortion_SemRD_V2X/project/v2x-vit/v2xset}
DST=${2:-/home/xuhu/project/distortion_SemRD_V2X/project/v2x-vit/v2xset_mini}

# Defaults
N_TRAIN=3
N_VAL=1
N_TEST=1
N_FRAMES=30
# Skip args if they're options
[[ "${3:-}" == --* ]] && shift 2 2>/dev/null || true

# Parse named args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --n-train) N_TRAIN=$2; shift 2;;
        --n-val)   N_VAL=$2;   shift 2;;
        --n-test)  N_TEST=$2;  shift 2;;
        --n-frames) N_FRAMES=$2; shift 2;;
        *) echo "Unknown arg: $1"; exit 1;;
    esac
done

# Format frame number as 5-digit string (00000, 00001, ...)
format_frame() {
    printf '%05d' "$1"
}

# Verify source exists
if [[ ! -d "$SRC" ]]; then
    echo "ERROR: source not found: $SRC"
    exit 1
fi

echo "============================================================"
echo "  V2XSet mini extractor"
echo "============================================================"
echo "Source:       $SRC"
echo "Destination:  $DST"
echo "Scenarios:    train=$N_TRAIN, val=$N_VAL, test=$N_TEST"
echo "Frames each:  $N_FRAMES"
echo "============================================================"

# Wipe destination if exists
rm -rf "$DST"
mkdir -p "$DST"

# For each split
for split_idx in 0 1 2; do
    split_name=(train validate test)
    split=${split_name[$split_idx]}
    case $split_idx in
        0) n_scenarios=$N_TRAIN ;;
        1) n_scenarios=$N_VAL ;;
        2) n_scenarios=$N_TEST ;;
    esac

    if [[ ! -d "$SRC/$split" ]]; then
        echo "WARN: $SRC/$split does not exist, skipping"
        continue
    fi

    echo
    echo "=== Processing $split (keeping $n_scenarios scenarios) ==="
    mkdir -p "$DST/$split"

    cnt=0
    for scenario in $(ls -1 "$SRC/$split" | sort); do
        if (( cnt >= n_scenarios )); then
            break
        fi
        echo "  [$((cnt+1))/$n_scenarios] Copying $scenario..."

        # Check scenario dir structure
        if [[ ! -d "$SRC/$split/$scenario" ]]; then
            continue
        fi

        # Create scenario dest dir
        mkdir -p "$DST/$split/$scenario"

        # Copy data_protocol.yaml (always keep)
        if [[ -f "$SRC/$split/$scenario/data_protocol.yaml" ]]; then
            cp "$SRC/$split/$scenario/data_protocol.yaml" \
               "$DST/$split/$scenario/" 2>/dev/null || true
        fi

        # For each agent dir
        n_agents=0
        for agent_dir in "$SRC/$split/$scenario"/*/; do
            if [[ ! -d "$agent_dir" ]]; then continue; fi
            agent_name=$(basename "$agent_dir")
            mkdir -p "$DST/$split/$scenario/$agent_name"

            # Copy data_protocol.yaml for agent
            if [[ -f "$agent_dir/data_protocol.yaml" ]]; then
                cp "$agent_dir/data_protocol.yaml" \
                   "$DST/$split/$scenario/$agent_name/" 2>/dev/null || true
            fi

            # Copy first N_FRAMES files for each file type
            for ext in pcd yaml; do
                count=0
                for f in $(ls -1 "$agent_dir"/*.$ext 2>/dev/null | sort); do
                    if (( count >= N_FRAMES )); then
                        break
                    fi
                    cp "$f" "$DST/$split/$scenario/$agent_name/"
                    count=$((count + 1))
                done
            done
            n_agents=$((n_agents + 1))
        done

        # Sanity check: must have at least 1 agent
        if (( n_agents == 0 )); then
            echo "    WARN: no agent dirs in $scenario, removing"
            rm -rf "$DST/$split/$scenario"
        else
            echo "    -> $n_agents agents, $N_FRAMES frames each"
        fi

        cnt=$((cnt + 1))
    done

    echo "  $split: copied $cnt scenarios"
done

# Report
echo
echo "============================================================"
echo "  Mini dataset created"
echo "============================================================"
du -sh "$DST"
echo
echo "Directory structure:"
for split in train validate test; do
    if [[ -d "$DST/$split" ]]; then
        n=$(ls -1 "$DST/$split" 2>/dev/null | wc -l)
        echo "  $DST/$split/  ($n scenarios)"
    fi
done
echo
echo "To use: edit the yaml's root_dir / validate_dir to point to:"
echo "  root_dir: '$(realpath --relative-to=$PWD $DST 2>/dev/null || echo $DST)/train'"
echo "  validate_dir: '$(realpath --relative-to=$PWD $DST 2>/dev/null || echo $DST)/validate'"
echo "  test_dir:     '$(realpath --relative-to=$PWD $DST 2>/dev/null || echo $DST)/test'"
