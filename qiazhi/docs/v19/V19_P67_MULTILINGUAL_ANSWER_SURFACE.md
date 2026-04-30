# V19 P67 Multilingual Answer Surface

P67 解决当前多语言版本里最明显的断点：界面和问题标签已经有多语言，但对话回答仍容易只输出中文。

## 完成内容

- `/api/agent/turn` 接收并标准化 `locale`，支持 `zh`、`en`、`ko`。
- Oracle UI 在调用 `/api/agent/turn` 时带上当前语言。
- 旧版测试页带上本地保存的 `v19_oracle_locale`，没有设置时默认中文。
- guided answer 的 `agent_reply`、`deterministic_outputs` 和 session turn 都记录 locale。
- deterministic guided answer 会保留 `text/content.zh`、`text/content.en`、`text/content.ko` 三份文本。
- LLM rewrite 只做当前语言的表达改写，不能改变结构事实、结论或边界。
- 收入稳定性 deterministic renderer 增加英文和韩文输出。

## 边界

- 多语言回答是 answer surface 升级，不改变八字结构计算、规则命中、Rule Graph 路由或知识检索。
- 非中文回答仍使用同一份结构事实，只切换表达语言。
- 用户反馈不因语言切换进入规则学习。

## 验收

- English / Korean agent turn 不再返回中文主回答。
- `guided_question_answer.text/content` 至少保留 `zh/en/ko`。
- 前端请求包含 locale。
- 禁止输出内部字段、预测词和审计口吻的约束继续有效。
