# V17 Master Reasoning Protocol

## 目标

把命理师对八字的判定轨迹，从“聊天式纠偏”升级成系统可读、可回放、可学习的结构化协议。

这层 **不直接修改物理十神值**。它负责把“命理师是怎么走到结论的”显影出来，供：

- 后端规则继续吸收
- UI 调试与审计
- LLM 叙事调用
- 未来的人类反馈学习

## 基本原则

### 1. 判断顺序比单点结论更重要

系统需要优先学习：

1. 先看体
2. 再看势
3. 再看成局
4. 再看透干
5. 再看运引
6. 最后看冲破

而不是把所有规则平铺成一堆加权分。

### 2. 高层推理不应直接改物理

`MasterReasoningLayer` 只输出：

- `reasoning_steps`
- `dominant_evidence`
- `suppressed_evidence`
- `learning_hooks`

真正能改十神的，仍然主要保留在 `L0/L1` 原子物理插件。

### 3. 角色区分重于元素泛化

例如：

- `辛透` 是纯七杀直透
- `庚透` 是正官主透，对七杀是同元素旁助

系统以后要区分：

- 纯透
- 旁助
- 借局得势
- 虚浮无根

而不能仅按五行元素簇一锅端。

### 4. 成局内部要分角色

以三合为例，不能平均处理：

- 中神：主旺点，最高权重
- 墓库：承载与收束，次权重
- 生地/起势支：最低权重

重复支也不能简单累计为一个 `duplicate_count`，而应进一步区分：

- 重复库支：增强稳定度与收束
- 重复起势支：增强引动与发动

## 当前最小实现

后端新增：

- `backend/services/master_reasoning.py`

并在 hydration 阶段注入：

- `meta.master_reasoning`
- `pt.master_reasoning`

当前版本号：

- `v17.master_reasoning.v1`

## 数据结构

```json
{
  "version": "v17.master_reasoning.v1",
  "day_master": "乙",
  "summary": {
    "dominant_ten_gods": [
      {"god": "伤官", "score": 42.0}
    ],
    "visible_elements": {
      "wood": 3,
      "metal": 1
    },
    "top_sanhe_group": ["丑", "巳", "酉"],
    "top_sanhe_strength": 1.32
  },
  "reasoning_steps": [
    {
      "stage": "body",
      "title": "先看体",
      "summary": "先看原局与基线十神主轴。",
      "evidence": {}
    }
  ],
  "dominant_evidence": [],
  "suppressed_evidence": [],
  "learning_hooks": {
    "requires_human_review": true,
    "review_axes": [],
    "feedback_slots": {
      "structure_judgement": "",
      "support_order": "",
      "suppression_order": "",
      "final_strength_verdict": ""
    }
  }
}
```

## 当前 reasoning steps 语义

### `body`
先看原局体用、十神主轴。

### `visible_stems`
看透干，区分纯透、旁助、虚浮。

### `formation`
看成局，尤其三合/半合的：

- 中神
- 重复支
- 柱位旺点

### `runtime`
看大运与流年：

- 大运偏背景延续
- 流年偏引动触发

### `suppression`
看冲、害、破、刑是否压制成局，但默认它们是后置抑制层，而不是先验灭局。

## 学习入口

`learning_hooks` 是这层最重要的输出。未来每次命理师纠偏，都可以落进这四个槽位：

- `structure_judgement`
- `support_order`
- `suppression_order`
- `final_strength_verdict`

也就是说，系统不只学习“结果对不对”，还学习：

- 结构是否判断对
- 支撑顺序是否对
- 抑制顺序是否对
- 最终强弱结论是否对

## 下一阶段演进

### v2

- 将 `辛透/庚透` 等纯十神透干类型正式编码
- 将三合内部角色权重拆成 `mid_branch / tomb_branch / starter_branch`
- 将重复支从总数改成按角色分类累积

### v3

- 将命理师人工纠偏写入长期反馈表
- 用于对 `MasterReasoningLayer` 的顺序、权重与裁决做持续更新

## 定位总结

`MasterReasoningLayer` 不是新的物理引擎。

它是系统开始“像命理师一样思考”的第一层骨架：

- 记录判定轨迹
- 保留证据顺序
- 显示主导与被压制证据
- 为未来学习与适应能力提供结构入口
