# V20 八字特征、智能问题与交互系统模型

FeatureState 表达当前八字特征的可见性、强度、反证和主题归属。

QuestionIntent 表达用户当前想问的方向，例如事业、财运、关系、健康、用神或岁运。

InteractionSignal 记录用户、命理师和系统运行中的反馈信号，只用于调优排序和参数。

Utility-based Question Ranking 根据特征命中、当前角色、问题意图和中枢大脑策略排序问题。

交互层不能直接改 RuleSpec；它只能产生训练信号，由中枢大脑统一写入可生效参数。
