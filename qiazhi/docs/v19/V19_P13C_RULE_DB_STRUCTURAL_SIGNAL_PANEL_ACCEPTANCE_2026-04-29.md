# V19 P13-C：Rule DB Structural Signal Panel 验收记录

日期：2026-04-29

## 结论

P13-C 已接入用户端 `/oracle`。

系统现在可以在 Guided Question Builder 中展示：

- 当前推荐问题由哪些 Rule DB 结构信号触发
- 触发来源属于墓库结构、地支关系、十神元数据、时间结构边界等哪一类
- 观察到的结构值
- 明确的边界说明：只用于提问，不改变结果

## 当前链路

```text
Bazi Rule DB
→ Structural Rule Signals
→ Guided Question Context
→ Dynamic Guided Questions
→ Oracle Question Builder
→ Structural Signal Panel
```

## UI 变化

### 1. Question Builder 增加结构信号面板

新增 `structuralSignalPanel`：

- 展示 Rule DB 触发信号列表
- 当前选中的动态问题会高亮对应信号
- 面板显示 `Questions only` / `只用于提问`

### 2. 动态问题 chip 显示推荐来源

动态问题现在显示类似：

```text
知识库触发：墓库结构
知识库触发：地支关系
知识库触发：十神关系元数据
```

### 3. 用户端不暴露内部规则编号

`/oracle` 不显示：

- `rule_id`
- `knowledge_id`
- developer trace
- validation 信息

这些仍属于 Lab/Admin 层。

## 边界

P13-C 只做可视化说明。

没有修改：

- `income_stability`
- `ResultCard`
- runtime inference
- LLM prompt 主结论
- 推荐排序学习机制

## Guardrails

```text
RULE_DB_GUIDES_QUESTIONS_ONLY
NO_RESULT_MUTATION
NO_FORTUNE
NO_TIME_AWARE_INFERENCE
NO_RULE_ID_EXPOSURE_ON_USER_SURFACE
```

## 文件变更

- `v19/frontend/oracle.html`
- `v19/frontend/assets/oracle.js`
- `v19/frontend/assets/styles.css`
- `v19/lab_interfaces.py`

## 验收状态

```text
accepted_for_local_agent_lab: true
public_prediction_product_ready: false
```
