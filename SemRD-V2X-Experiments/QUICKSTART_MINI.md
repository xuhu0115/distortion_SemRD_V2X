# Quick Reference: Create Mini V2XSet on Windows

## One-time: create mini dataset locally

```powershell
# 1. Open PowerShell, cd to v2x-vit dir
cd D:\common_file\SJU\Obsidian_vault\10_Research\project\oit\distortion_SemRD_V2X\project\v2x-vit

# 2. Run the extraction script
powershell -ExecutionPolicy Bypass -File "SemRD-V2X-Experiments\semrd_v2x\tools\make_v2xset_mini_windows.ps1"
# 默认: 2 train / 1 val / 1 test scenarios, 每个 scenario 30 frames
# 自定义: -NTrain 3 -NVal 2 -NTest 2 -NFrames 50

# 3. 等待(大约 15-30 分钟,主要是 train_chunks.zip 解压合并)

# 4. 验证
ls v2xset_mini/
ls v2xset_mini/train/  # 应该有 2 个 scenario
ls v2xset_mini/train/<scenario_name>/  # 应该有 1-2 个 agent dir
ls v2xset_mini/train/<scenario_name>/<agent_name>/  # 应该有 30 个 pcd + 30 个 yaml

# 5. 打包
Compress-Archive -Path v2xset_mini -DestinationPath v2xset_mini.zip
# 或者只打包必需文件
```

## 上传到新服务器

```powershell
# 用 scp(假设有 SSH key)
scp v2xset_mini.zip user@newserver:/path/to/project/v2x-vit/

# 或用 rsync over SSH
rsync -avz --progress v2xset_mini.zip user@newserver:/path/to/project/v2x-vit/
```

## 在新服务器上跑

```bash
cd /path/to/project/v2x-vit

# 1. 解压
unzip v2xset_mini.zip

# 2. 验证结构
ls v2xset_mini/train/   # 应该有 2 个 scenario
ls v2xset_mini/validate/  # 1 个 scenario
ls v2xset_mini/test/      # 1 个 scenario

# 3. 跑训练(用 mini yaml,2 epoch 应该 10-15 分钟)
python v2xvit/tools/train_semrd.py \
    --hypes_yaml v2xvit/hypes_yaml/point_pillar_v2xvit_semrd_mini.yaml

# 4. 跑推理
python v2xvit/tools/inference_semrd.py \
    --model_dir logs/point_pillar_v2xvit_semrd_*/ \
    --fusion_method intermediate

# 5. 验证生成的 metrics.json
cat logs/point_pillar_v2xvit_semrd_*/metrics.json
```

## 预期

- **训练**: 2 epoch,约 10-15 分钟
- **train_loss**: 1.0-1.5(快速下降)
- **val_loss**: 0.5-1.0(可能)
- **AP**: 几乎 0(数据量不够,这是预期的)
- **带宽**: 1-2 MB(只有 1-2 agents)
- **目的**: 验证 pipeline 跑通,不验证精度

## 故障排查

| 错误 | 原因 | 解决 |
|---|---|---|
| `No space left on device` | 临时目录空间不足 | 删掉 `v2xset_temp/` |
| `DataLoader worker killed by signal: Bus error` | /dev/shm 不够 | `NUM_WORKERS=0` |
| `No module named 'v2xvit'` | 没 `pip install -e .` | 跑 install.sh |
| `Cython extension not found` | 没 `python v2xvit/utils/setup.py build_ext --inplace` | install.sh 自动做 |
| `RuntimeError: No module named 'cumm'` | spconv/cumm 缺失 | `pip install spconv-cu<对应 CUDA 版本>` |
| `RuntimeError: libQt5Core` | opencv-python 需要 Qt5 | `pip install opencv-python-headless` |
