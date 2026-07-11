# Section 7 TODO 清单

所有 TODO 标记位于 `SemRD_V2X/main.tex` Section 7 内(行号通过 `grep -n "TODO\[EXP" SemRD_V2X/main.tex` 查看)。

## 标记体系

- `TODO[EXP-RUN-X]` — 第 X 个实验的 run,数据来自 `logs/<exp>/metrics.json`
- `TODO[EXP-ABL-X]` — 第 X 个消融实验
- `TODO[OBS-Ti]` — 第 i 个 Observations 段落,改写文字
- `TODO[FIG-RD-CURVE]` — Figure 1 RD 曲线,需 Python 画图
- `[TBD]` — 表格单元占位符

## 各 Section 的 TODO 数量

| Section | 标记 | 实验 |
|---|---|---|
| 7.2 Table 1 + Fig 1 | 6 rows × `[TBD]` + 8 obs TBDs | 6 个 P_A 值的训练 |
| 7.3 Table 2 | 5 rows × `[TBD]` | δ ∈ {0,1,2,3,4} 扫描 |
| 7.4 Table 3 | 5 rows × `[TBD]` | σ_xyz + t_d 扫描 (含 4 个基线) |
| 7.5 Table 4 | 3 rows × `[TBD]` | DAIR-V2X (Vehicle/Infra) |
| 7.6 Table 5 | 6 rows × `[TBD]` | H(π_A) + 实测带宽 |
| 7.7 Table 6 | 5 rows × `[TBD]` | 5 个消融变体 |

## 替换工作流(实验完成后)

1. 跑完实验,获得 `logs/<exp_name>/metrics.json`
2. 把 metrics.json 内容发给我
3. 我帮你:
   - 计算 Table 数字
   - 给出 sed/Edit 命令
   - 改写 Observations 段落

或自行替换:
```bash
grep -n "TODO\[EXP" SemRD_V2X/main.tex
sed -i 's/\[TBD-AP0.5\]/0.848/g' SemRD_V2X/main.tex
```

## 工作量估算

| 优先级 | 内容 | 数量 | 时间 |
|---|---|---|---|
| 必做 | 7.2 + 7.3 + 7.6 | 12 个 run | 5-6 天 (A800) |
| 加分 | 7.4 Robustness | 36 个 run | 14 天 |
| 加分 | 7.5 DAIR-V2X | 3 个 run | 2-3 天 |
| 加分 | 7.7 Ablation | 5 个 run | 3-4 天 |

**POC 最低**:12 个 run 即可填 Table 1+2+5 + Figure 1。
