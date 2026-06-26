# V20 裁决链路与画像层模型

V20 Bazi Defeasible Decision Model 以 RuleSpec Runtime 为主规则运行层。

核心链路：

- RuleSpec Runtime 读取八字事实、特征和知识规则。
- Defeasible ArgumentNode 表达支持、反证、弱候选和阻断。
- PortraitProjection 只从当前命局裁决结果生成画像轴。
- LLM 负责解释和表达，不允许 LLM 直接裁决格局、用神或人生事件。

本模型服务中枢大脑调度：规则、画像、问题和回答上下文都从同一份裁决证据产生。
