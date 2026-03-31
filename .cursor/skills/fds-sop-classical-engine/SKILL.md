---
name: fds-sop-classical-engine
description: Encodes the FDS SOPs (V7.x) for classical pattern matching and ranking in this repo. Use when editing legacy/core/classical_matcher.py, classical_registry.json, holographic_pattern UI around classical patterns, or any logic about tiers, integrity, structural rescue, geographic adjustment or dynamic state (岁运成格/破格).
---

# FDS Classical Engine SOP Skill

## Scope

- This skill applies when the agent:
  - Edits `legacy/core/classical_matcher.py`, `legacy/config/classical_registry.json`, or related helpers.
  - Touches UI sections that display classical格局 (especially在 `legacy/ui/pages/holographic_pattern.py`).
  - Implements or refactors logic for:
    - 动态格局状态机（原局 vs 合成场、岁运成格/岁运破格）—— SOP V7.5
    - 神煞格加严（将星格/驿马格/天乙格）—— SOP V7.6
    - 弹性定性判格（逻辑结构优先，能量作为成色）—— SOP V7.7

## Core Principles (from SOP + .cursorrules)

1. **零硬编码 / 物理纯洁性**
   - 不在代码或文档中写死物理参数（阈值、系数、权重等）。
   - 一切参数必须出自 `config/`（如 `classical_registry.json`、`tuning_params.json` 等）或 AlgoParams/ConfigManager。
   - 修改算法行为优先改配置而不是改 if 阈值。

2. **结构优先，能量为成色**
   - 判定“格成”以**拓扑结构/法理链路**为准（如杀印相生、从格结构等），而非单一能量阈值。
   - `affinity` / 匹配度：对结构成立的格局统一视为 100% 逻辑命中（除非有明显破格）。
   - `integrity`：仅表示“成色/贵贱/纯度”，不再决定是否命中。
   - 引入 `energy_tier`（high/mid/low）和 `structural_rescue`（成败救应）参与排序与 LLM 提示。

3. **动态状态机 & 岁运因子**
   - 使用合成能量场（原局 + 大运 + 流年）判断：
     - `formed_by_transport`：岁运补齐/合化使格局成立 → 标成 “岁运成格”。
     - `broken_year`：岁运引入比劫夺财等破坏链路 → 降低 `integrity` 并标红 “岁运破格”。
   - UI 必须展示这些状态标签，而不是只给静态“格成 100%”。

4. **Tier 层级与神煞加严（V7.6）**
   - Tier1/2 主格：在 UI 中作为「命定格局」，排在高光位置。
   - Tier3 神煞：单独区域「命带神煞」，不能与主格平起平坐。
   - 神煞格（A-54/A-55/A-57 等）必须满足 SOP 约束：
     - 将星：对应支五行能量占比达到配置下限，且不被冲刑。
     - 驿马：马头天干为日主的财/官/印（马头带箭/带财），否则不命格。
     - 天乙：贵人支不入空亡、不被冲。

5. **地理得失地与完整性修正**
   - 匹配地域五行（得地）：`integrity` 加上配置的 bonus（有上限 cap）。
   - 被地域克制（失地）：`integrity` 扣减 penalty。
   - 具体数值从 `classical_registry.json.integrity_geo` 读取。

6. **排序与 Final Score**
   - 排序综合考虑：
     - pattern tier（主权优先）
     - active/ephemeral（岁运成格标记但不盖过原局主权）
     - energy_tier（high/mid/low）
     - structural_rescue（符合“正官见财”、“七杀见印”等成败救应时给予乘数加成）。

## Implementation Checklist

当你修改 classical 引擎时，按以下顺序检查：

1. **是否触及参数？**
   - 若只是调权重/阈值 → 优先修改 `config/classical_registry.json` 或相关 config。
   - 避免在 `.py` 文件里直接写数字常量作为业务阈值。

2. **是否破坏逻辑优先原则？**
   - 不要新增简单的 “E > x 才算格成”；判断应该尽量写成**结构关系**（月令、透干、刑冲合害链路）。

3. **是否尊重 Tier 与神煞位置？**
   - UI 里主格列表只能出 Tier1/2；Tier3 必须在「命带神煞」区。
   - 新增的神煞类逻辑一律加严，不允许“见字即成格”。

4. **是否更新了衍生字段？**
   - 所有输出的格局项应携带：`qualitative_match=True`、`ephemeral`、`energy_tier`、`structural_rescue`、`tier` 等字段，以便 UI 与 LLM 使用。

5. **测试与审计思路**
   - 至少准备一例：
     - 原局成格 + 岁运破格
     - 原局不中 + 岁运成格
     - 神煞“看上去很多”但经加严后明显减少的命例
   - 确认 UI 中标签、列表层级与预期一致。

## Examples

- **好修改**：在 `classical_registry.json` 中新增 `tier3_hardening` 或 `integrity_geo` 参数，然后在 `classical_matcher` 中以配置驱动逻辑。
- **需避免**：在 `classical_matcher.py` 里直接写 `if value > 0.6:` 之类的硬阈值判断，而不经过配置。

