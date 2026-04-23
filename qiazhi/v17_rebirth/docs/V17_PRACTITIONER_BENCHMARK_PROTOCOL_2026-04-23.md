# V17 命理师校盘基准集协议

日期：2026-04-23  
状态：首批基准盘已落地  
定位：真实命盘校盘基线，用于在 Synthetic Lab 之后做“命理师视角”的长期回归

## 1. 为什么需要这层

Synthetic Lab 负责把系统放在可控世界里训稳，但它天然偏“干净”和“单变量”。

真实校盘还需要另一层：

- 允许多路关系并存
- 允许争议与张力共存
- 保留命理师的审盘轨迹
- 验证系统是否会在复杂盘里误判家族、误读主轴，或把一条副路抹掉

所以 V17 现在把“真实命盘校盘”正式单列为一套基准集，而不是继续夹在聊天记录里零散讨论。

## 2. 基本原则

命理师校盘基准集不追求“一步到位地给出真理分数”，它的职责是：

1. 固定一批具有代表性的真实样盘。
2. 为每张样盘写清楚当前最值得审的点。
3. 先固化“系统当前必须不能犯的错”。
4. 再逐步增加“更细的命理期望断言”。

换句话说，这套基准首先是 **防回退宪法**，然后才是 **精度进化跑道**。

## 3. 协议结构

代码位置：

- `v17_rebirth/testing/practitioner_benchmarks.py`

每张基准盘当前遵循下面这份协议：

```python
PractitionerBenchmarkCase(
    case_id="real.audit.metal_mix_gengzi_bingwu",
    description="丁巳/乙巳/乙丑/乙酉，庚子大运、丙午流年。",
    four_pillars={"year": "...", "month": "...", "day": "...", "hour": "..."},
    luck_pillar="庚子",
    flow_pillar="丙午",
    audit_focus=("巳酉丑三合金", "子丑六合", "不得误判巳午未三会"),
    expected_relation_families=("sanhe", "liuhe", "anhe"),
    expected_dynamic_families=("sanhe", "chong", "stem_fusion_transform"),
    forbidden_relation_families=("sanhui",),
    expected_top_contains=("正官", "七杀", "伤官"),
    expected_leader="正官",
    reviewer_note="用于压住三会误判与官杀轴回归。",
)
```

字段含义：

- `audit_focus`：这张盘当前到底想审什么。
- `expected_relation_families`：关系成局层必须保留的家族。
- `expected_dynamic_families`：动力学层必须可见的家族。
- `forbidden_relation_families`：系统绝对不应误判出来的家族。
- `expected_top_contains`：当前主轴里必须看得到的十神。
- `expected_leader`：只有在命理共识足够强时才设置。
- `reviewer_note`：命理师/系统后续继续讨论时的锚点。

## 4. 首批基准盘

### 4.1 metal_mix_gengzi_bingwu

- 六柱：`丁巳 / 乙巳 / 乙丑 / 乙酉`
- 运流：`庚子 / 丙午`
- 目标：
  - `巳酉丑三合金` 必须存在
  - `子丑六合`、`子巳暗合` 必须可见
  - 不得误判 `巳午未三会火`
  - 官杀轴必须已经被拉起

### 4.2 metal_mix_xinchou_yiwei

- 六柱：`丁巳 / 乙巳 / 乙丑 / 乙酉`
- 运流：`辛丑 / 乙未`
- 目标：
  - `三合金` 进入满配态
  - `辛金透干 + 丑支重叠` 需要把 `七杀` 推成绝对主轴
  - 用于长期回归“强七杀纯盘”

### 4.3 fire_water_gengxu_bingwu

- 六柱：`壬寅 / 甲辰 / 丙子 / 甲午`
- 运流：`庚戌 / 丙午`
- 目标：
  - `寅午戌三合火` 必须保留
  - `子辰半合水` 必须保留
  - 火局主势与水路侧势要并存，不能抹掉其中一路
  - 不得误判三会

## 5. 当前测试入口

```bash
# 只跑真实命盘校盘基准
bash qiazhi/v17_rebirth/scripts/run_practitioner_benchmarks.sh

# 等价命令
pytest qiazhi/v17_rebirth/tests/test_practitioner_benchmark_cases.py -q
```

## 6. 与 Synthetic Lab 的关系

顺序必须是：

1. 先过 Synthetic Lab  
2. 再过 Practitioner Benchmark  
3. 最后才去做实时 UI 校盘和长对话精修

理由很简单：

- Synthetic Lab 保证规则在干净世界里不崩
- Practitioner Benchmark 保证规则进复杂盘后不跑偏

## 7. 后续扩展方向

下一批建议补入：

- 强格 / 弱格 / 从格 / 混格
- 高动态冲突盘
- 用神 / 忌神 / 通关神争议盘
- 天干五合与地支合化并存盘
- 典型“误判风险盘”

原则：

- 每新增一张真实基准盘，都要先写 `audit_focus`
- 先固化“不能犯的错”
- 再逐步增加“应该更精确的地方”
