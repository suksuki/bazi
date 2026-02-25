# FDS V5.5 审计脚本库 — DuckDB 一键点将

第 045 号 / SOP V5.5：常用 DuckDB 审计 SQL 与跑数脚本，供「物理穿透」「判词回测」「流形健康度」使用。

## 目录说明

| 文件 | 用途 | 产出/用法 |
|------|------|-----------|
| `extreme_cases_top100.sql` | Step 6.1 极端异类点：按到质心欧氏距离取 Top100 | 可导出为 extreme_cases_audit.json |
| `extreme_cases_audit.py` | 执行极值扫描并写 JSON，支持指定 pattern_id | `audit_logs/extreme_cases_audit.json` |
| `physics_baseline.sql` | 全格局 COUNT/AVG/STDDEV（与 audit_v2_physics_baseline 一致） | 基线统计 |
| `iou_dilution_check.sql` | 新格局接入后 IoU/丰度对比（示例） | 稀释坍缩检查 |
| `a04_wealth_weak.sql` | A-04 身强财弱坍缩样本 | 分层审计 |
| `audit_a11_e_collapse.py` | A-11 从财格 日主坍缩度（E/O 联合，弃命极值点） | Step 6 专项 |
| `audit_a13_purity.py` | A-13 专旺格 流形纯度（E>2.0 时 M/S 受排斥） | Step 6 专项 |
| `v5_5_extreme_patterns_alignment.py` | 法理一致性：DuckDB 实测 vs 审计师 TMM 主向量 | 终审报告 |

## 使用方式

- **直接 SQL**：`duckdb core/database/fds_physics.duckdb < scripts/audit/extreme_cases_top100.sql`
- **Python 跑数**：`python3 scripts/audit/extreme_cases_audit.py --pattern A-07`

数据库路径默认：`core/database/fds_physics.duckdb`（项目根下执行）。
