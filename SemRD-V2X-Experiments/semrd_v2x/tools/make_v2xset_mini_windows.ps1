# make_v2xset_mini_windows.ps1
# Create a mini V2XSet for fast pipeline testing, on Windows local machine.
# Reads from:
#   - v2xset/train_chunks.zip (65GB, nested zips that need merging)
#   - v2xset/validate.zip (6.8GB, single zip)
#   - v2xset/test.zip (28.7GB, single zip)
# Outputs to:
#   - v2xset_mini/ (~50MB total)
#
# Usage (from project/v2x-vit/ directory in PowerShell):
#   powershell -ExecutionPolicy Bypass -File ..\SemRD-V2X-Experiments\semrd_v2x\tools\make_v2xset_mini_windows.ps1
#
# Optional args:
#   -NFrames 30      frames per scenario to keep
#   -NTrain 2        train scenarios
#   -NVal 1          val scenarios
#   -NTest 1         test scenarios

param(
    [int]$NFrames = 30,
    [int]$NTrain = 2,
    [int]$NVal = 1,
    [int]$NTest = 1
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression.FileSystem

# Locate paths. The structure is:
#   project/
#   ├── v2x-vit/                <-- contains v2xset/ (data)
#   │   └── v2xset/
#   └── SemRD-V2X-Experiments/  <-- contains this script
#       └── semrd_v2x/tools/
#           └── make_v2xset_mini_windows.ps1   <-- we are here
#
# So we need to go up 3 levels from this script to reach project/, then down to v2x-vit/v2xset.
# But that depends on where SemRD-V2X-Experiments is. Use a smarter search:
# 1. Look at current working directory
# 2. If cwd is v2x-vit, use ../v2xset (already exists)
# 3. If cwd is project/, use v2x-vit/v2xset
# 4. Otherwise, search for v2xset directory

# Try to find v2xset directory by walking up
$searchDir = (Get-Location).Path
$found = $false
for ($i = 0; $i -lt 5; $i++) {
    $candidate = Join-Path $searchDir "v2xset"
    if (Test-Path $candidate) {
        $V2XSet = (Resolve-Path $candidate).Path
        $found = $true
        Write-Host "Found v2xset at: $V2XSet"
        break
    }
    # Try v2x-vit/v2xset
    $candidate = Join-Path $searchDir "v2x-vit\v2xset"
    if (Test-Path $candidate) {
        $V2XSet = (Resolve-Path $candidate).Path
        $found = $true
        Write-Host "Found v2xset at: $V2XSet"
        break
    }
    $parent = Split-Path $searchDir -Parent
    if ($parent -eq $searchDir) { break }
    $searchDir = $parent
}

if (-not $found) {
    Write-Host "ERROR: v2xset directory not found."
    Write-Host "Please set the v2xset path manually by editing this script."
    Write-Host "Or set environment variable V2XSET_ROOT before running:"
    Write-Host "  `$env:V2XSET_ROOT = 'D:\path\to\v2xset'"
    Write-Host "  powershell -File make_v2xset_mini_windows.ps1"
    exit 1
}

# Allow env var override
if ($env:V2XSET_ROOT -and (Test-Path $env:V2XSET_ROOT)) {
    $V2XSet = (Resolve-Path $env:V2XSET_ROOT).Path
    Write-Host "Using V2XSET_ROOT env var: $V2XSet"
}

# Output paths (sibling of v2xset)
$parent = Split-Path $V2XSet -Parent
$OUT = Join-Path $parent "v2xset_mini"
$TEMP = Join-Path $parent "v2xset_temp"

Write-Host "============================================================"
Write-Host "  V2XSet Mini Extractor (Windows)"
Write-Host "============================================================"
Write-Host "Source:  $V2XSet"
Write-Host "Output: $OUT"
Write-Host "Temp:   $TEMP"
Write-Host "Scenarios per split: train=$NTrain, val=$NVal, test=$NTest"
Write-Host "Frames each:        $NFrames"
Write-Host "============================================================"

# Clean previous
if (Test-Path $OUT) {
    Write-Host "Removing existing $OUT"
    Remove-Item -Recurse -Force $OUT
}
if (Test-Path $TEMP) {
    Write-Host "Removing existing $TEMP"
    Remove-Item -Recurse -Force $TEMP
}
New-Item -ItemType Directory -Path $OUT | Out-Null
New-Item -ItemType Directory -Path $TEMP | Out-Null

# === Helper: extract first N entries of type X from a single-file zip ===
function Extract-Selected-FromZip {
    param(
        [string]$ZipPath,
        [string]$DestDir,         # output directory
        [string]$Prefix,         # only entries starting with this
        [int]$NFrames,
        [int]$NSce,
        [string]$FileExt         # e.g. ".pcd" or ".yaml"
    )
    $archive = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
    try {
        # Get all entries that match prefix + ext, sorted naturally
        $matching = $archive.Entries |
            Where-Object { $_.FullName.StartsWith($Prefix) -and $_.FullName.EndsWith($FileExt) } |
            Sort-Object FullName

        # Group by scenario
        $byScenario = $matching | Group-Object {
            $parts = $_.FullName -split "/"
            # For entries like "train/2021_xx_yy/scenario_agent/00000.pcd"
            if ($parts.Count -ge 3) { $parts[1] } else { "unknown" }
        }

        $selected = $byScenario | Select-Object -First $NSce
        Write-Host "  Selected scenarios from $ZipPath : $($selected.Name -join ', ')"

        # For each selected scenario, take first N frames of each agent
        $allByScenario = $matching | Group-Object { ($_.FullName -split "/")[1] }
        foreach ($grp in $selected) {
            $scenario = $grp.Name
            $allInScenario = $matching | Where-Object { ($_.FullName -split "/")[1] -eq $scenario }
            $agentGroups = $allInScenario | Group-Object { ($_.FullName -split "/")[2] }
            foreach ($ag in $agentGroups) {
                $agentName = $ag.Name
                $dest = Join-Path $DestDir $scenario
                $dest = Join-Path $dest $agentName
                New-Item -ItemType Directory -Path $dest -Force | Out-Null
                $count = 0
                foreach ($entry in ($ag.Group | Sort-Object FullName)) {
                    if ($count -ge $NFrames) { break }
                    $rel = "$scenario/$agentName/" + ($entry.FullName -split "/")[-1]
                    $outFile = Join-Path $DestDir $rel
                    [System.IO.Compression.ZipFileExtensions]::ExtractToFile(
                        $entry, $outFile, $true)
                    $count++
                }
                # Also copy data_protocol.yaml if exists
                $dpEntry = $archive.Entries |
                    Where-Object { $_.FullName -eq "$Prefix$scenario/$agentName/data_protocol.yaml" }
                if ($dpEntry) {
                    $dpDest = Join-Path $DestDir $scenario
                    $dpDest = Join-Path $dpDest $agentName
                    $dpDest = Join-Path $dpDest "data_protocol.yaml"
                    [System.IO.Compression.ZipFileExtensions]::ExtractToFile(
                        $dpEntry, $dpDest, $true)
                }
            }
        }
    } finally {
        $archive.Dispose()
    }
}

# === Step 1: Extract from validate.zip ===
Write-Host ""
Write-Host "=== Step 1: Extract from validate.zip ==="
$valOut = Join-Path $OUT "validate"
New-Item -ItemType Directory -Path $valOut -Force | Out-Null
Extract-Selected-FromZip -ZipPath "$V2XSet\validate.zip" `
    -DestDir $valOut -Prefix "validate/" -NFrames $NFrames -NSce $NVal -FileExt ".pcd"
Extract-Selected-FromZip -ZipPath "$V2XSet\validate.zip" `
    -DestDir $valOut -Prefix "validate/" -NFrames $NFrames -NSce $NVal -FileExt ".yaml"

# === Step 2: Extract from test.zip ===
Write-Host ""
Write-Host "=== Step 2: Extract from test.zip ==="
$testOut = Join-Path $OUT "test"
New-Item -ItemType Directory -Path $testOut -Force | Out-Null
Extract-Selected-FromZip -ZipPath "$V2XSet\test.zip" `
    -DestDir $testOut -Prefix "test/" -NFrames $NFrames -NSce $NTest -FileExt ".pcd"
Extract-Selected-FromZip -ZipPath "$V2XSet\test.zip" `
    -DestDir $testOut -Prefix "test/" -NFrames $NFrames -NSce $NTest -FileExt ".yaml"

# === Step 3: Handle train_chunks.zip ===
Write-Host ""
Write-Host "=== Step 3: Extract from train_chunks.zip ==="
Write-Host "  (Step 3a) Extracting parts from train_chunks.zip..."
$trainPartDir = Join-Path $TEMP "train_parts"
New-Item -ItemType Directory -Path $trainPartDir -Force | Out-Null
$archive = [System.IO.Compression.ZipFile]::OpenRead("$V2XSet\train_chunks.zip")
try {
    foreach ($entry in $archive.Entries) {
        if ($entry.FullName -like "train_chunks/train.zip.part*") {
            $outFile = Join-Path $trainPartDir (Split-Path $entry.FullName -Leaf)
            Write-Host "    Extracting $($entry.FullName)"
            [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $outFile, $true)
        }
    }
} finally {
    $archive.Dispose()
}

Write-Host "  (Step 3b) Merging parts into train.zip..."
$trainZipPath = Join-Path $TEMP "train.zip"
$parts = Get-ChildItem $trainPartDir -Filter "train.zip.part*" | Sort-Object Name
Write-Host "    Found $($parts.Count) parts, total size $([math]::Round(($parts | Measure-Object -Property Length -Sum).Sum / 1GB, 2)) GB"
$fs = [System.IO.File]::Create($trainZipPath)
try {
    $buffer = New-Object byte[] 10485760  # 10MB buffer
    foreach ($p in $parts) {
        Write-Host "    Appending $($p.Name) ($([math]::Round($p.Length / 1GB, 2)) GB)"
        $rs = [System.IO.File]::OpenRead($p.FullName)
        try {
            while ($true) {
                $n = $rs.Read($buffer, 0, $buffer.Length)
                if ($n -eq 0) { break }
                $fs.Write($buffer, 0, $n)
            }
        } finally {
            $rs.Dispose()
        }
    }
} finally {
    $fs.Dispose()
}
Write-Host "    Merged into $trainZipPath ($([math]::Round((Get-Item $trainZipPath).Length / 1GB, 2)) GB)"

Write-Host "  (Step 3c) Extracting first $NTrain scenarios from train.zip..."
$trainOut = Join-Path $OUT "train"
New-Item -ItemType Directory -Path $trainOut -Force | Out-Null
Extract-Selected-FromZip -ZipPath $trainZipPath `
    -DestDir $trainOut -Prefix "train/" -NFrames $NFrames -NSce $NTrain -FileExt ".pcd"
Extract-Selected-FromZip -ZipPath $trainZipPath `
    -DestDir $trainOut -Prefix "train/" -NFrames $NFrames -NSce $NTrain -FileExt ".yaml"

# === Step 4: Clean up temp ===
Write-Host ""
Write-Host "=== Step 4: Cleaning up temp files ==="
Write-Host "  Removing $TEMP..."
Remove-Item -Recurse -Force $TEMP

# === Step 5: Report ===
Write-Host ""
Write-Host "============================================================"
Write-Host "  Mini V2XSet Created"
Write-Host "============================================================"
$totalSize = (Get-ChildItem $OUT -Recurse | Measure-Object -Property Length -Sum).Sum
Write-Host "  Output: $OUT"
Write-Host "  Total: $([math]::Round($totalSize / 1MB, 1)) MB"
Write-Host ""
Write-Host "  Structure:"
foreach ($split in @("train", "validate", "test")) {
    $sdir = Join-Path $OUT $split
    if (Test-Path $sdir) {
        $n = (Get-ChildItem $sdir | Measure-Object).Count
        Write-Host "    $sdir/ ($n scenarios)"
    }
}
Write-Host ""
Write-Host "  Next: zip the mini dataset and upload to new server:"
Write-Host "    Compress-Archive -Path '$OUT' -DestinationPath 'v2xset_mini.zip'"
Write-Host "    scp v2xset_mini.zip user@newserver:/path/to/v2x-vit/"
Write-Host ""
Write-Host "  On new server, use the mini yaml:"
Write-Host "    python v2xvit/tools/train_semrd.py \"
Write-Host "        --hypes_yaml v2xvit/hypes_yaml/point_pillar_v2xvit_semrd_mini.yaml"
