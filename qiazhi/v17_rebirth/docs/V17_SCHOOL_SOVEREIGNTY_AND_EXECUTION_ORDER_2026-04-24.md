# V17 门派主权与执行顺序说明

日期：2026-04-24

## 1. 目的

这份文档回答两个核心问题：

1. 当前 V17 面对子平、盲派、调候、象法、格局、风险等专题时，究竟如何选择、如何分权、如何解决冲突。
2. 当前 V17 的模型算法为什么对执行顺序敏感，以及系统现在是如何控制“先算什么、后算什么”的。

这不是新的理论提案，而是对**当前已落地实现**的工程化说明。

---

## 2. 总结结论

### 2.1 当前不是“门派投票制”，而是“主权分层制”

V17 现在不是：

- 先挑一个门派
- 再让整盘都听这个门派

而是：

- 先共享底层物理层
- 再让不同门派按权限进入
- 最后通过 authority 协议收束

一句话：

> 门派不是平票竞争，而是按主权层级参与最终裁决。

### 2.2 当前不是“纯黑盒智能算法”，而是“分层确定性主链 + 局部智能加权”

V17 现在的算法不是完全自适应乱序推理，而是：

- 主链顺序固定
- 局部评分智能化
- 偏置进入时受权限和限幅约束

一句话：

> 当前 V17 是“有智能评分的分层流水线”，不是“任意顺序的自由博弈器”。

---

## 3. 当前门派/专题如何分层

### 3.1 底层共享物理层

所有门派先共享同一套底层状态：

- L0：十神静态基础、根气、透干、基础来源分解
- L1：关系家族、几何命中、关系运行态
- Core：做功图、运流场、冲突、裁决、authority

也就是说：

- 子平看到的是这套底层物理
- 盲派看到的也是这套底层物理
- 调候、格局、象法、风险也都建立在同一份 physics tensor 上

因此系统不会出现“每个门派各算各的世界”。

### 3.2 当前专题层

当前 L2 以上的专题大致分成：

- `ziping umbrella`
- `pattern_specializations`
- `climate family`
- `blind family`
- `xiangfa family`
- `risk_matrix`
- `shensha`

但它们不是同权的。

---

## 4. 当前谁主导，谁辅助

### 4.1 Level 1：硬主裁决

当前真正拥有硬主权的是：

- `ziping umbrella`

它承担：

- 月令轴
- 旺衰/扶抑轴
- 用神/忌神硬裁决
- 调候桥接
- 格局桥接
- 最终 `god_ring_authority`

这条线的特点是：

- 可以进入 authority 主排序
- 可以决定 hard top
- 其它软专题不能直接把它顶掉

### 4.2 Level 2：结构增强层

当前这一层主要包括：

- `pattern_specializations`
- `climate modifier layer`
- `risk_matrix`

它们可以：

- 增强结构解释
- 调整效率/稳定性/优先级
- 提供结构增强或风险放大

但它们不应该替代 ziping 的硬主裁决。

### 4.3 Level 3：软偏置/语义层

当前这一层主要包括：

- `blind`
- `xiangfa`
- `shensha`
- 少量 narrative / strategy

其中：

- `blind`：可以进入 soft bias，但有限幅
- `xiangfa`：当前只做 semantic mapping，不进入 bias
- `shensha`：辅助标签，不覆盖主结构

这意味着：

- 盲派有发言权
- 但不能篡位

---

## 5. 当前门派冲突如何解决

### 5.1 不是靠“谁更像对的”，而是靠 authority 协议

当前系统解决冲突的关键协议包括：

- `authority_level`
- `override_forbidden`
- `max_bias_ratio`
- `hard_constraint_source`
- `structure_enhancement_source`
- `soft_bias_source`

它们共同定义：

- 谁是硬约束
- 谁只能增强
- 谁只能偏置
- 谁不能越权

### 5.2 当前的真实处理方式

当多个专题给出不同方向时，系统大致按下面方式处理：

1. 先拿到 ziping 的 hard scores
2. 再拿 structure enhancement 的修正
3. 最后吸收 soft bias
4. soft bias 先经过限幅
5. 最终排序后，再保住 hard top

所以当前不是：

- 盲派说这个盘伤官为用，就直接把子平推翻

而是：

- 盲派可以把伤官往上推一点
- 但如果 ziping 的硬主轴仍然是正官，系统会保住正官的硬第一位

### 5.3 一个简单例子

如果当前：

- ziping 认为：`正官` 是硬主用神
- blind 认为：`伤官` 才是当前主线

系统不会二选一，而是：

- 让 blind 提供 `use_bias / taboo_bias`
- 再对 bias 做限幅
- 再把 hard top 保下来

结果通常是：

- `正官` 仍然排第一
- `伤官` 会被抬高，但不会直接越权顶掉正官

这就是当前的门派冲突裁决方式。

---

## 6. 当前模型算法是怎么“选顺序”的

这部分很关键，因为八字系统里：

> 算法顺序错了，结果会比参数误差更离谱。

### 6.1 当前不是自由乱序，而是固定主链

当前大致顺序是：

1. 计算 L0 静态基线
2. 初始化 runtime 与 analysis input
3. 扫描插件，收集 facts / proposals / authority fragments / topic meta
4. 统一整理 claims / conflicts / knowledge snapshot
5. 统一结算 modifier proposals
6. 形成 runtime 分数
7. 再进入 authority、调候修正、体用裁决
8. 最后进入 prompt / narrative / LLM

换句话说：

- 先有物理
- 再有关系
- 再有结构
- 再有体用
- 再有叙事

这条顺序是当前系统稳定的核心。

### 6.1.1 现在已经不是“只靠人工记顺序”，而是带依赖图的执行协议

当前 hydration 主链已经具备：

- 阶段声明：`phase / category / critical / requires / sovereignty_sensitive`
- 关键路径：`claims -> conflicts -> settlement -> flow -> runtime_sync -> meta_contract`
- authority gate 关键阶段：`runtime_synced`

因此系统后续不是只检查“有没有按线性顺序跑完”，而是会额外检查：

- 是否缺失关键阶段
- 是否跳过依赖阶段
- authority gate 是否在正确阶段可见

### 6.2 为什么顺序很重要

因为以下几类事情如果顺序错了，会立刻失真：

#### 情况 1：先做盲派，再做物理

如果先让盲派决定体用，再回头做物理层，就会出现：

- 盲派主题污染底层
- 体用成为先验答案
- 失去“共享物理层”

这正是我们现在避免的。

#### 情况 2：先叠加 bias，再决定 hard top

如果 soft bias 在 hard constraint 之前进入，就会出现：

- 盲派/风险/叙事把主裁决顶掉
- authority 失去主权边界

所以现在必须：

- 先 hard
- 后 soft

#### 情况 3：先叙事，再结算

如果 LLM 或 narrative 太早进入，就会出现：

- 观测污染世界
- 文案倒逼物理
- 结构性回授失控

所以 prompt/LLM 必须是最后阶段消费结果，不应倒推底层。

---

## 7. 当前系统里的“智能算法”到底是什么

### 7.1 现在已经有的智能部分

当前 V17 已经不是纯规则堆叠，主要智能性体现在：

1. **结构候选识别**
- 格局候选
- 盲派体用候选
- climate favored/strained gods

2. **双轴与多轴评分**
- 能量
- 稳定性
- 波动
- authority_use / authority_taboo
- climate efficiency / stability / priority delta

3. **冲突与裁决路由**
- claim detection
- conflict detection
- arbiter routing

4. **学习治理层**
- synthetic lab
- practitioner benchmark
- learning campaign
- parameter optimization map

### 7.2 现在还没有完全做到的智能部分

当前还没有做到的是：

- 全局自由图调度
- 动态自动重排所有插件的执行顺序
- 根据每张命盘实时生成最优计算拓扑

所以当前 V17 不是：

- 全图自适应调度器

而更像：

- 固定主干流水线
- 局部有评分和门禁的智能裁决系统

### 7.3 这意味着什么

这意味着当前算法是“可解释、可控、可审计”的。

代价是：

- 灵活性比完全图优化低一点

但收益是：

- 不容易数值爆炸
- 不容易主题越权
- 更容易用 synthetic lab 做回归

这其实更适合当前阶段。

---

## 8. 当前系统应如何理解“先算哪个、后算哪个”

建议把当前 V17 的顺序理解为四段：

### 第一段：世界建立

建立底层 physics tensor：

- 十神静态基础
- 根透桥
- 关系 formation / dynamics
- climate field

这是“物理真相层”。

### 第二段：专题观察

不同专题在同一个物理世界上做观察：

- ziping
- pattern
- blind
- climate theme
- xiangfa
- risk

这是“专题解释层”。

### 第三段：主权裁决

authority 按层级收束：

- hard constraint
- structure enhancement
- soft bias

这是“体用与用忌裁决层”。

### 第四段：叙事输出

把已经裁决好的结果给：

- prompt
- narrative
- LLM
- UI

这是“表达层”。

### 关键原则

> 表达层不能回写物理层。  
> 软偏置不能覆盖硬裁决。  
> 专题不能绕过 shared physics。

---

## 9. 当前还存在的真实问题

虽然这套顺序已经比以前稳定很多，但还没到完美：

### 9.1 `l1_meta_hydration.py` 仍然过重

现在很多主流程仍集中在 hydration 中央核里：

- 插件扫描
- facts 收集
- authority 合并
- blind/climate/xiangfa 主题提升
- claim/conflict
- settlement
- meta contract

这意味着：

- 主顺序虽然对
- 但中央神经核仍偏大

后面如果继续智能化，最好进一步模块化。

### 9.2 `work_path` 和 `flux` 还可以更智能

当前做功图和 flux 已经相当强，但还没有完全成为：

- 可重排执行图
- 动态优先级调度器

后续如果要更高阶智能，就会落在这里。

### 9.3 门派冲突解决是“协议化”的，但还不够“案例自适应”

现在系统可以：

- 正确限幅
- 正确保 hard top

但对于一些复杂命盘里的：

- 双体竞争
- 体转移
- 结构抢权

仍然需要 benchmark 和 synthetic 的持续校盘。

---

## 10. 当前结论

### 10.1 门派如何选择

当前 V17 不是“选门派”，而是：

- 共享底层物理
- 按主权层级接入各专题
- 用 authority 协议收束

所以：

- 子平负责硬主裁决
- 格局/调候/风险负责增强
- 盲派负责受限偏置
- 象法负责语义解释

### 10.2 冲突如何解决

当前冲突不是靠拍脑袋，而是靠：

- `authority_level`
- `override_forbidden`
- `max_bias_ratio`
- `preserve_hard_top`
- `clamp_soft_bias_map`

来解决。

### 10.3 算法是否有智能性

有，但不是全自由黑盒：

- 当前是“固定主链 + 局部智能评分 + 主权门禁”
- 这比完全自由图调度保守
- 但更适合现在这套可验证、可调优、可学习的系统

---

## 11. 下一步建议

如果要在这个主题上继续推进，最值得做的不是“再加新门派”，而是：

1. 把当前执行顺序画成一张正式流程图
2. 进一步拆轻 `l1_meta_hydration.py`
3. 把“体转移 / 双体竞争 / 抢权”做成 benchmark 样盘矩阵
4. 让 learning campaign 也能审计：
   - 哪些偏差来自物理顺序
   - 哪些偏差来自门派分权

一句话：

> 现在系统最大的进步，不是门派变多，而是终于开始知道“谁先说话，谁最后拍板”。  
