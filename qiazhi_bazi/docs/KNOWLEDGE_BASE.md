# Qiazhi 0.13 Knowledge Base

## 1. 盲派核心技能逻辑（Skill-Logic）

- 宾主准则：
  - 年/月 -> 宾（外部、他者、环境）
  - 日/时 -> 主（自我、家内、内核）
- 体用定义：
  - `BODY`：比肩、劫财、正印、偏印
  - `USE`：食神、伤官、正财、偏财、正官、七杀
- 做功定义：
  - 能量从宾位向主位迁移并造成可观测 `Abs` 变化
  - 主判据：`expected_work = unlock_gain - backfire_risk`
- 禄命关系：
  - 禄神可视为日主延伸
  - 禄受穿/冲导致日主承载能力下降，表现为 `BODY` 轴风险上升

## 2. 古典旺衰对齐（Classical-Logic）

- 虚浮阈值：
  - 当 `Self_Abs < 1.0` 且无根（`Root_Score` 低）时，判为“虚浮”
  - 虚浮状态下不可担高压财官结构
- 通根判定：
  - 根源与根分高于阈值时，提升结构稳定性标签
- 终审切换临界点（V0）：
  - `Self_Abs < 0.5` 且做功净值为正：可进入从势/从财官候选
  - `Self_Abs > 1.2`：从格终审触发回滚压力（需复审）
  - `Self_Abs > 4.0` 且 `Root_Score > 1.5`：身强结构候选优先

## 3. 盲派六法的物理化（V1）

- 冲：显式触发墓库解锁（`clash_only_v1`）
- 穿/刑/害/破/合：参与 `eta` 与风险扰动，不作为 V1 的墓库显式解锁因子
- 审计关键词：
  - `[DANGEROUS_TURBULENCE]`
  - `[BROKEN_LINK]`
  - `[POTENTIAL_FOLLOWER_STRUCTURE]`
