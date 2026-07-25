# Monthly Prior and Review Protocol

## 目的

月度机制验证的是阶段趋势与观察价值，不是制造每日吉凶内容。当前文件冻结数据与认识论边界；公开月度功能尚未在本阶段上线。

## 月初先验

```text
Committed Baseline
+ Deterministic Timing State
+ 当前案例中当时已知的现实条件
→ Temporal Prior (committed before observation window)
```

先验必须保存生成时间、适用窗口、命理解释链、观察主题、反证信号和不确定性。生成后不可被月末结果覆盖或改写。

## 月末复盘

```text
Original Temporal Prior
+ Reality Evidence observed during the window
→ Case Revision
```

复盘分别记录命中、部分命中、未命中、无法判断和新异常。事后解释不得冒充事前预测，用户未反馈也不得自动视为命中或未命中。

## 红线

- 不从个体事件直接提升全局理论；
- 不把药物、疾病、婚姻或财富具体事件写成必然预测；
- 不使用现实结果反向重写原先先验；
- 不把一般生活建议包装成命理洞察；
- 没有足够命理依据时允许弃权。

## 后续实现门禁

只有在 `Temporal Prior` 和 `Case Revision` 都能独立保存、盲测和审计后，才允许进入公开月度提醒。
