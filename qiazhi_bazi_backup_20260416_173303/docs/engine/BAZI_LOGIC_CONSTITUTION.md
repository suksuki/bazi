# BAZI Logic Constitution (0.13)

## 1) 主权分层（Sovereignty Stack）

### L1：基础物理层（Standard Physics）
- 职责：计算能量（Abs）与基础交互，不直接判定吉凶。
- 范围：刑、冲、克、害、合、破、穿、墓库。
- 墓库定性：高密度压缩态（Cranking），可锁定为势能。

### L2-A：旺衰派系统（Balance Engine）
- 职责：审计日主生存压力与平衡度。
- 核心：中和为贵。Self_Abs 过高为过载，过低为贫血。
- 用忌：按“抑强扶弱”给出调节策略。

### L2-B：盲派系统（Efficiency Engine）
- 职责：审计社会资源获取效率（体用做功）。
- 核心：不以强弱为第一判据，以“能否做成功”为第一判据。
- 做功：使用 L1 交互作为抓取工具，计算 gain/risk/net。

## 2) 基础规则的双流派映射

| 基础交互 (L1) | 旺衰派解读 (L2-A) | 盲派解读 (L2-B) |
| --- | --- | --- |
| 冲 (Clash) | 动荡、损耗、两强并损 | 主要做功手段；冲开库门/冲动目标 |
| 穿/害 (Pierce) | 慢性损伤、关系破裂 | 高级捕获，精准截获或毁伤占有 |
| 墓库 (Grave) | 收敛、沉寂、入墓偏弱 | 能量保险柜；闭库为潜能，开库为爆发 |
| 合 (Combine) | 羁绊、稳定、情义 | 合住“用”为得，合住“体”为绊 |

## 3) 终极合拢协议（Physics First）

1. 先读 L1：所有结论先对齐 Abs 与交互事实。
2. 双轨并行：
   - L2-A 输出 `balance_verdict`
   - L2-B 输出 `work_verdict`
3. 若两轨冲突：
   - 必须保留两条结论，不允许互相覆盖。
   - 触发 `LOGIC_CONFLICT_WARNING`，要求折中策略（先止损，再调平衡）。

## 4) 阈值治理（Risk Bands）

- 不采用“单点硬阈值”作为唯一裁决线，采用风险带治理。
- 建议带宽：
  - `Self_Abs >= 20`：高风险过载带
  - `Self_Abs >= 24`：极端过载带（接近物理坍缩）
- 说明：调候、岁运、参数注入会改变承载上限，阈值应与上下文联审。

## 5) 214.55 案例合拢示例

- 旺衰派：极旺/过载，平衡度崩塌，忌继续加压。
- 盲派：身强无依，若做功路径断裂则高能空转。
- 合拢陈述模板：
  - “高能级已形成，但因关键路径断裂（如子午冲切断泄秀链），出现内耗黑洞。”

## 6) 实施契约（Implementation Contract）

- `structure_final_decision_v0` 必须输出：
  - `balance_verdict`
  - `work_verdict`
- `final_verdict` 必须输出：
  - `[BALANCE_SCHOOL] ...`
  - `[WORK_SCHOOL] ...`
  - 冲突时追加 `[LOGIC_CONFLICT_WARNING] ...`

## 7) 治理规则（Governance）

- 任何跨 L1/L2 边界的算法变更，先改本文件再改代码。
- 如触及命名阈值或冲突策略，需同步更新 `AUDIT_FIELD_MAP.md`。
