# First Run, Streaming and Actions v1

## 首轮认知预算

生产入口只允许一次阻塞式核心 LLM 调用。该调用读取最小充分命理世界，输出完整整盘基线对象；事业、财富、关系、健康等专题只在用户主动进入后调用。

旧多阶段认知链保留为离线研究协议，不再作为公开首轮体验。

## 等待状态

```text
chart_ready
→ baseline_generating
→ baseline_draft_ready
→ baseline_validating
→ baseline_committed
```

`baseline_draft_ready` 只存在于任务事件流；服务器不得在这一阶段保存 Life Case。校验失败时回到确定性命盘状态并明确弃权。

## 首屏三层

```text
1. 看见命局：整盘重心、主要路径、关键条件、最大不确定性
2. 现在处于哪里：确定性阶段信息；未形成 Temporal Prior 时不制造建议
3. 继续探索：用户主动选择领域，或向 Abu 提出具体问题
```

三层采用单开式折叠阅读：默认展开“看见命局”；打开另一层时，其余层收起为编号、标题和一行命盘摘要。用户也可以把当前层再次收起。手机端折叠内容必须退出可访问焦点顺序，不能只做视觉隐藏。

色阶固定为浅色命局首段、深绿阶段段和墨绿探索段。每个色阶独立定义前景色；深色段正文、摘要、按钮与边界说明不得继承浅色页面的灰色文字。

## Abu Action Registry

Abu 不直接修改数据库或 DOM。页面按钮与 Abu 都提交同一受控动作：

```text
CREATE_PROFILE
SELECT_PROFILE
START_BASELINE
OPEN_DOMAIN
OPEN_TEMPORAL_STATE
RECORD_REALITY_EVIDENCE
CONTINUE_LAST_EXPLORATION
```

应用操作不调用强命理模型；只有整盘综合、领域推演、阶段解释和案例修正使用核心 Reasoner。
