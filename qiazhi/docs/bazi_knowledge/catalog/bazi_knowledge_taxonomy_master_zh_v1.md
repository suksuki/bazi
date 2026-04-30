# 八字知识总目录 v1

状态：总目录先行版

日期：2026-04-30

## 目标

先建立一个相对全面的八字知识地图，再一类一类补内容、转规则、做回归。

原则：

- 目录先行，内容后填。
- 每个知识点先归类，再决定是否规则化。
- 低风险结构知识优先，高风险断语先归档。
- 真实命盘不作为当前训练基础，先用合成盘验证。

## 状态标记

| 标记 | 含义 |
|---|---|
| 已有 | 已有知识文档和结构化草案 |
| 部分 | 有一些 seed 或文档，但不完整 |
| 缺失 | 目录还没建或没有结构化知识 |
| 归档 | 可记录，但暂不进入规则 |
| 后置 | 等主干知识完成后再做 |

## L0：基础排盘与符号

| 类别 | 目录 | 状态 | 优先级 | 说明 |
|---|---|---|---:|---|
| 天干 | core/ | 已有 | P0 | 十天干、五行、阴阳 |
| 地支 | core/ | 已有 | P0 | 十二地支、五行、藏干 |
| 五行 | core/ | 已有 | P0 | 生克、同类、泄耗 |
| 阴阳 | core/ | 部分 | P0 | 当前有基础属性，还可扩 |
| 藏干 | core/ | 已有 | P0 | 主气、中气、余气还需细化 |
| 四柱结构 | core/ | 部分 | P0 | 年月日时已有入口，但宫位未完整 |
| 节气 / 月令 | strength/ core/ | 部分 | P0 | 月令作为结构入口已有，节气边界不足 |
| 出生地 / 时区 | geo_context/ | 部分 | P1 | P31A 已补排盘校验元数据边界 |
| 经度 / 真太阳时 | geo_context/ | 部分 | P1 | P31A 已补时柱边界校验，是否启用仍需审阅 |
| 夏令时 / 历史时区 | geo_context/ | 部分 | P2 | P31A 已补历史时间校验边界 |
| 历法换算 | calendar/ | 部分 | P2 | P31B 已补排盘元数据边界，当前不作为命理规则主线 |

## L1：干支关系

| 类别 | 目录 | 状态 | 优先级 | 说明 |
|---|---|---|---:|---|
| 天干五合 | core/ | 部分 | P1 | 已有边界，缺条件细化 |
| 天干冲克 | core/ | 部分 | P1 | P31A 已补方向关系边界，仍需条件细化 |
| 地支六合 | core/ | 已有 | P0 | 已有结构边界 |
| 地支六冲 | core/ | 已有 | P0 | 已有结构边界 |
| 地支三合 | core/ | 部分 | P0 | 缺半合、拱合、成局条件 |
| 地支三会 | core/ | 部分 | P0 | 缺季节成势条件 |
| 地支刑 | core/ | 部分 | P1 | 当前只做关系索引 |
| 地支害 | core/ | 部分 | P1 | 当前只做关系索引 |
| 地支破 | core/ | 部分 | P1 | 当前只做关系索引 |
| 穿 / 绝 / 暗合 | branch_advanced/ | 部分 | P2 | P31B 已补高级关系归档边界 |
| 墓库 | core/ wealth/ | 部分 | P0 | 位置、藏干已有；开闭库条件不足 |

### L1A：地支关系与时间引动细化第一批

| 类别 | 目录 | 状态 | 优先级 | 说明 |
|---|---|---|---:|---|
| 六合细化 | core/ | 部分 | P0 | P35 已补合住、合动、合化边界 |
| 六冲细化 | core/ | 部分 | P0 | P35 已补目标对象、藏干、宫位和时间层边界 |
| 三合局细化 | core/ | 部分 | P0 | P35 已补全局、半合、拱合与成势边界 |
| 三会局细化 | core/ | 部分 | P0 | P35 已补会方、月令和季节成势边界 |
| 地支刑细化 | core/ | 部分 | P1 | P35 已补刑类型、目标对象与高风险边界 |
| 地支害细化 | core/ | 部分 | P1 | P35 已补隐性牵制与路径影响边界 |
| 地支破细化 | core/ | 部分 | P1 | P35 已补破的对象、合局、墓库和宫位边界 |
| 天干五合细化 | core/ | 部分 | P1 | P35 已补合绊、合动、合化和化气边界 |
| 天干冲克细化 | core/ | 部分 | P1 | P35 已补透出、同层、有根和通关边界 |
| 墓库开闭细化 | core/ wealth/ | 部分 | P0 | P35 已补库位、藏物、冲合与开闭条件 |

## L2：十神

| 类别 | 目录 | 状态 | 优先级 | 说明 |
|---|---|---|---:|---|
| 十神映射 | ten_god/ core/ | 已有 | P0 | 关系元数据已建立 |
| 正官 | ten_god/ | 已有 | P0 | P27 已有 |
| 七杀 | ten_god/ | 已有 | P0 | P27 已有 |
| 正印 | ten_god/ | 已有 | P0 | P27 已有 |
| 偏印 / 枭神 | ten_god/ | 已有 | P0 | P27 已有 |
| 食神 | ten_god/ | 已有 | P0 | P27 已有 |
| 伤官 | ten_god/ | 已有 | P0 | P27 已有 |
| 正财 | ten_god/ wealth/ | 已有 | P0 | P27 已有 |
| 偏财 | ten_god/ wealth/ | 已有 | P0 | P27 已有 |
| 比肩 | ten_god/ | 已有 | P0 | P27 已有 |
| 劫财 | ten_god/ wealth/ | 已有 | P0 | P27 已有 |
| 透干 / 藏干十神 | ten_god/ | 部分 | P0 | 还需来源层细化 |

## L3：十神组合类知识

| 类别 | 目录 | 状态 | 优先级 | 说明 |
|---|---|---|---:|---|
| 伤官见官 | interaction/ | 部分 | P0 | P28E 已有组合存在与机制边界，待专题审阅 |
| 枭神夺食 | interaction/ | 部分 | P0 | P28E 已有组合存在与机制边界，待专题审阅 |
| 食神制杀 | interaction/ | 部分 | P1 | P28E 已有组合存在与机制边界，待专题审阅 |
| 伤官制杀 | interaction/ | 部分 | P1 | P28F 已入冲突/制化专题，待专题审阅 |
| 杀印相生 | interaction/ | 部分 | P1 | P28E 已有组合存在与机制边界，待专题审阅 |
| 印化杀 | interaction/ | 部分 | P1 | P31B 已补制化路径存在与机制边界 |
| 官印相生 | interaction/ | 部分 | P1 | P28E 已有组合存在与机制边界，待专题审阅 |
| 伤官配印 | interaction/ | 部分 | P1 | P28E 已有组合存在与机制边界，待专题审阅 |
| 财生官 | interaction/ | 部分 | P1 | P28E 已有组合存在与机制边界，待专题审阅 |
| 财官相生 | interaction/ | 部分 | P1 | P31B 已补生助连续路径边界 |
| 食伤生财 | wealth/ interaction/ | 部分 | P0 | P28E 已有组合存在与机制边界，wealth 仍需联动细化 |
| 比劫夺财 | wealth/ interaction/ | 部分 | P1 | P28E 已有组合存在与机制边界，wealth 仍需联动细化 |
| 财破印 / 贪财坏印 | interaction/ | 部分 | P1 | P28E 已有组合存在与机制边界，待专题审阅 |
| 官杀混杂 | interaction/ pattern/ | 部分 | P1 | P28E 已有组合存在与机制边界，格局交叉待补 |
| 食伤混杂 | interaction/ | 部分 | P2 | P28F 已入冲突/混杂专题 |
| 印枭混杂 | interaction/ | 部分 | P2 | P28F 已入冲突/混杂专题 |
| 印制食伤 | interaction/ | 部分 | P1 | P28F 已入牵制专题 |
| 比劫分财 | wealth/ interaction/ | 部分 | P1 | P28F 已入财富牵制专题 |
| 财多坏印 | interaction/ | 部分 | P1 | P28F 已入夺破牵制专题 |
| 财滋杀 | interaction/ wealth/ | 部分 | P1 | P28F 已入压力来源专题 |
| 官杀攻身 | interaction/ strength/ | 部分 | P1 | P28F 已入控制压力专题 |
| 合杀留官 | interaction/ pattern/ | 部分 | P1 | P28F 已入官杀去留专题 |
| 合官留杀 | interaction/ pattern/ | 部分 | P1 | P28F 已入官杀去留专题 |
| 羊刃驾杀 | interaction/ pattern/ | 部分 | P1 | P28E 已有组合存在与机制边界，禄刃模型待补 |

### L3A：十神路径第二批

| 类别 | 目录 | 状态 | 优先级 | 说明 |
|---|---|---|---:|---|
| 伤官生财 | interaction/ wealth/ | 部分 | P1 | P32 已补输出转资源路径 |
| 食神泄秀 | interaction/ | 部分 | P1 | P32 已补温和输出泄秀路径 |
| 伤官泄秀 | interaction/ | 部分 | P1 | P32 已补强输出泄秀路径 |
| 比劫帮身 | interaction/ strength/ | 部分 | P1 | P32 已补同类支持日主路径 |
| 印比扶身 | interaction/ strength/ | 部分 | P1 | P32 已补印星与比劫连续支持路径 |
| 比劫抗杀 | interaction/ strength/ | 部分 | P1 | P32 已补同类承压与抗杀候选 |
| 官杀制比劫 | interaction/ wealth/ | 部分 | P1 | P32 已补控制比劫与护财前置路径 |
| 官星护财 | interaction/ wealth/ | 部分 | P1 | P32 已补官星约束比劫保护财星候选 |
| 财制枭护食 | interaction/ | 部分 | P1 | P32 已补枭神夺食的救应路径 |
| 财星制印 | interaction/ | 部分 | P1 | P32 已补财印关系的中性反制路径 |
| 食神生财制杀 | interaction/ pattern/ | 部分 | P1 | P32 已补食神、财星、七杀多段链 |
| 财印交战 | interaction/ | 部分 | P1 | P32 已补财印互相牵制候选 |

## L4：强弱与承载

| 类别 | 目录 | 状态 | 优先级 | 说明 |
|---|---|---|---:|---|
| 月令关系 | strength/ | 已有 | P0 | 已有证据边界 |
| 根气 / 通根 | strength/ | 部分 | P0 | 缺主气中气余气细分 |
| 透藏支持 | strength/ | 已有 | P0 | P27 已有 |
| 印星生扶 | strength/ | 已有 | P0 | P27 已有 |
| 食伤泄耗 | strength/ | 已有 | P1 | P27 已有，需测试 |
| 官杀压力 | strength/ | 已有 | P1 | P27 已有，需测试 |
| 财星耗身 | strength/ wealth/ | 部分 | P1 | P31A 已补承载力上下文边界 |
| 中和平衡 | strength/ | 部分 | P1 | 有中性边界 |
| 调候 | strength/ | 部分 | P2 | 高风险修正，先归档 |
| 地域气候背景 | geo_context/ strength/ | 部分 | P2 | P31A 已补调候背景候选 |
| 南北寒暖燥湿 | geo_context/ strength/ | 部分 | P2 | P31A 已补地域气候边界，不直接参与强弱裁决 |
| 用神 / 忌神 | useful_god/ | 部分 | P3 | 当前不作为主线启用 |

## L5：格局

| 类别 | 目录 | 状态 | 优先级 | 说明 |
|---|---|---|---:|---|
| 正官格 | pattern/regular/ | 部分 | P0 | P31A 已补候选边界 |
| 七杀格 | pattern/regular/ | 部分 | P0 | P31A 已补候选边界 |
| 正财格 | pattern/regular/ | 部分 | P0 | P31A 已补财格候选边界 |
| 偏财格 | pattern/regular/ | 部分 | P0 | P31A 已补财格候选边界 |
| 食神格 | pattern/regular/ | 部分 | P0 | P31A 已补食伤格候选边界 |
| 伤官格 | pattern/regular/ | 部分 | P0 | P31A 已补食伤格候选边界 |
| 正印格 | pattern/regular/ | 部分 | P0 | P31A 已补印格候选边界 |
| 偏印格 | pattern/regular/ | 部分 | P0 | P31A 已补印格候选边界 |
| 建禄格 | pattern/regular/ | 部分 | P0 | P31A 已补禄位候选边界 |
| 羊刃格 | pattern/regular/ | 部分 | P0 | P31A 已补禄刃候选边界 |
| 成格 / 破格 | pattern/quality/ | 部分 | P1 | P31A 已补条件模型边界 |
| 救应 | pattern/quality/ | 部分 | P1 | P31A 已纳入格局质量目录 |
| 相神 | pattern/quality/ | 部分 | P1 | P31A 已补辅助条件边界 |
| 清浊 / 混杂 | pattern/quality/ | 部分 | P1 | P31A 已补质量标签边界 |
| 从财 | pattern/special/ | 部分 | P2 | P31A 已补特殊格局归档边界 |
| 从杀 | pattern/special/ | 部分 | P2 | P31A 已补特殊格局归档边界 |
| 从儿 | pattern/special/ | 部分 | P2 | P31A 已补特殊格局归档边界 |
| 从旺 / 从强 | pattern/special/ | 部分 | P2 | P31A 已补特殊格局归档边界 |
| 专旺五格 | pattern/special/ | 部分 | P2 | P31A 已补特殊格局归档边界 |
| 化气五格 | pattern/special/ | 部分 | P2 | P31A 已补特殊格局归档边界 |
| 真从 / 假从 | pattern/special/ | 部分 | P2 | P31A 已补反例审查边界 |

### L5A：格局细化第一批

| 类别 | 目录 | 状态 | 优先级 | 说明 |
|---|---|---|---:|---|
| 月令取格 | pattern/ core/ | 部分 | P0 | P33 已补格局来源边界 |
| 透干成格 | pattern/ core/ | 部分 | P0 | P33 已补可见性与根气边界 |
| 杂气取格 | pattern/ core/ | 部分 | P1 | P33 已补藏干层级与杂气边界 |
| 正官格细化 | pattern/regular/ | 部分 | P0 | P33 已补官星清浊与救应边界 |
| 七杀格细化 | pattern/regular/ | 部分 | P0 | P33 已补制杀、化杀与混杂边界 |
| 财格细化 | pattern/regular/ wealth/ | 部分 | P0 | P33 已补身财承载与护财边界 |
| 食神格细化 | pattern/regular/ interaction/ | 部分 | P0 | P33 已补泄秀、生财、制杀与枭夺边界 |
| 伤官格细化 | pattern/regular/ interaction/ | 部分 | P0 | P33 已补见官、配印、生财边界 |
| 印格细化 | pattern/regular/ interaction/ | 部分 | P0 | P33 已补财破印、官印、印制食伤边界 |
| 建禄格细化 | pattern/regular/ strength/ | 部分 | P1 | P33 已补同类根气与取用边界 |
| 羊刃格细化 | pattern/regular/ interaction/ | 部分 | P1 | P33 已补制刃、泄刃和高风险边界 |
| 从财格细化 | pattern/special/ wealth/ | 部分 | P2 | P33 已补真从假从边界 |
| 从杀格细化 | pattern/special/ interaction/ | 部分 | P2 | P33 已补破从与制化边界 |
| 从儿格细化 | pattern/special/ interaction/ | 部分 | P2 | P33 已补食伤从势与反例边界 |
| 专旺格细化 | pattern/special/ core/ | 部分 | P2 | P33 已补一气成势与破局边界 |
| 化气格细化 | pattern/special/ core/ | 部分 | P2 | P33 已补合化与合而不化边界 |

## L6：宫位与象法

| 类别 | 目录 | 状态 | 优先级 | 说明 |
|---|---|---|---:|---|
| 年柱宫位 | palace/ | 部分 | P0 | P31A 已补远外层标签 |
| 月柱宫位 | palace/ | 部分 | P0 | P31A 已补结构环境标签 |
| 日支宫位 | palace/ | 部分 | P0 | P31A 已补贴身承载位置 |
| 时柱宫位 | palace/ | 部分 | P0 | P31A 已补结果端与后段标签 |
| 天干外显 | palace/ core/ | 部分 | P0 | 已有显隐层，但未宫位化 |
| 地支内在 | palace/ core/ | 部分 | P0 | 已有显隐层，但未宫位化 |
| 远近 | palace/ | 部分 | P1 | P31A 已补距离标签 |
| 内外 | palace/ | 部分 | P1 | P31A 已补内外标签 |
| 宫位与十神组合 | palace/ interaction/ | 部分 | P1 | P31A 已补双重来源层边界 |

## L7：盲派

| 类别 | 目录 | 状态 | 优先级 | 说明 |
|---|---|---|---:|---|
| 理法 | blind/lifa/ | 部分 | P0 | P31A 已补宾主、体用、做功目录 |
| 象法 | blind/xiangfa/ | 部分 | P1 | P31A 已补归档优先目录 |
| 技法 | blind/jifa/ | 部分 | P3 | P31A 已补技法归档目录 |
| 宾主 | blind/lifa/ | 部分 | P0 | P31A 已补作用方向框架 |
| 体用 | blind/lifa/ | 部分 | P0 | P31A 已补主体对象分层 |
| 做功 | blind/lifa/ | 部分 | P0 | P31A 已补作用路径候选 |
| 做功效率 | blind/lifa/ | 部分 | P1 | P31A 已补强弱路径审核边界 |
| 原神 / 目标神 | blind/lifa/ | 部分 | P1 | P31A 已补路径端点边界 |
| 换象 / 带象 | blind/xiangfa/ | 部分 | P2 | P31A 已补象法归档目录 |

### L7A：盲派理法细化第一批

| 类别 | 目录 | 状态 | 优先级 | 说明 |
|---|---|---|---:|---|
| 宾主定位细化 | blind/lifa/ | 部分 | P0 | P34 已补角色归因和作用方向边界 |
| 体用定位细化 | blind/lifa/ | 部分 | P0 | P34 已补体用分层与用神边界 |
| 原神目标神细化 | blind/lifa/ | 部分 | P1 | P34 已补路径端点与可达性边界 |
| 做功路径细化 | blind/lifa/ | 部分 | P0 | P34 已补 actor、receiver、action_path |
| 做功效率细化 | blind/lifa/ strength/ | 部分 | P1 | P34 已补强弱、距离、通关和阻隔边界 |
| 合冲做功 | blind/lifa/ core/ | 部分 | P1 | P34 已补合冲关系进入做功的边界 |
| 制化做功 | blind/lifa/ interaction/ | 部分 | P1 | P34 已补制化、通关、转化路径边界 |
| 墓库做功 | blind/lifa/ core/ | 部分 | P1 | P34 已补入库、出库、开闭库边界 |
| 宫位做功 | blind/lifa/ palace/ | 部分 | P1 | P34 已补宫位承载和位置边界 |
| 十神做功 | blind/lifa/ interaction/ | 部分 | P1 | P34 已补十神作用路径边界 |
| 时间引动作功 | blind/lifa/ time_context/ | 部分 | P1 | P34 已补时间层引动不改写本命边界 |
| 换象带象细化 | blind/xiangfa/ | 部分 | P2 | P34 已补象法归档和中性标签边界 |

## L8：领域应用

| 类别 | 目录 | 状态 | 优先级 | 说明 |
|---|---|---|---:|---|
| 财富 / 收入结构 | wealth/ | 部分 | P0 | 当前有 20 条 |
| 事业 / 职业结构 | career/ | 部分 | P2 | P31B 已补领域承接边界，等格局、宫位、十神组合后专题化 |
| 感情 / 婚姻结构 | relationship/ | 部分 | P3 | P31B 已补归档与安全边界，高风险后置 |
| 健康结构 | health/ | 部分 | P4 | P31B 已补健康安全归档边界，不进入规则 |
| 六亲结构 | family/ | 部分 | P3 | P31B 已补宫位来源层边界，需宫位基础 |
| 子女结构 | children/ | 部分 | P3 | P31B 已补时柱来源层边界，需时柱宫位基础 |
| 性格象意 | personality/ | 归档 | P3 | 当前 R4 占位 |

### L8A：领域应用承接第一批

| 类别 | 目录 | 状态 | 优先级 | 说明 |
|---|---|---|---:|---|
| 财富收入结构承接 | wealth/ | 部分 | P0 | P36 已补财富只承接上游结构信号 |
| 财星显隐可达 | wealth/ | 部分 | P0 | P36 已补财星可见不等于可用 |
| 财富稳定波动 | wealth/ | 部分 | P0 | P36 已补财库、合冲、比劫、时间层归因 |
| 食伤变现路径 | wealth/ interaction/ | 部分 | P0 | P36 已补输出到资源路径边界 |
| 比劫资源分配 | wealth/ interaction/ | 部分 | P1 | P36 已补竞争、合作和分配语境 |
| 事业官杀语境 | career/ interaction/ | 部分 | P2 | P36 已补官杀只作规则压力和组织结构候选 |
| 事业产出资源路径 | career/ wealth/ | 部分 | P2 | P36 已补食伤、财、印的事业承接边界 |
| 格局事业承接 | career/ pattern/ | 部分 | P2 | P36 已补格局进入事业前的质量边界 |
| 关系日支语境 | relationship/ palace/ | 部分 | P3 | P36 已补日支只作贴身位置 |
| 关系十神语境 | relationship/ interaction/ | 部分 | P3 | P36 已补关系十神来源层边界 |
| 健康安全归档 | health/ | 部分 | P4 | P36 已补健康安全降级和禁用边界 |
| 六亲来源层 | family/ palace/ | 部分 | P3 | P36 已补柱位、宫位、十神来源层 |
| 子女来源层 | children/ palace/ | 部分 | P3 | P36 已补时柱与食伤来源层 |
| 性格象意归档细化 | personality/ | 归档 | P3 | P36 已补中性象意标签和表达安全边界 |

## L9：时间系统

| 类别 | 目录 | 状态 | 优先级 | 说明 |
|---|---|---|---:|---|
| 大运 | time_context/ | 部分 | P0 | 背景层已建 |
| 流年 | time_context/ | 部分 | P0 | 触发层已建 |
| 小运 | time_context/ | 部分 | P3 | P31B 已补后置时间层归档边界 |
| 流月 | time_context/ | 部分 | P3 | P31B 已补后置时间层归档边界 |
| 运命关系 | time_context/ | 部分 | P1 | 需更多规则 |
| 岁命关系 | time_context/ | 部分 | P1 | 需更多规则 |
| 岁运关系 | time_context/ | 部分 | P1 | 需更多规则 |
| 大运引动本命 | time_context/ | 部分 | P0 | P31A 已补背景触发边界 |
| 流年引动本命 | time_context/ | 部分 | P0 | P31A 已补短期触发边界 |
| 流年引动大运 | time_context/ | 部分 | P1 | P31A 已补岁运层级归因 |
| 天干引动 | time_context/ | 部分 | P1 | P31A 已补来源层边界 |
| 地支引动 | time_context/ | 部分 | P1 | P31A 已补来源层边界 |
| 藏干引动 | time_context/ | 部分 | P2 | P31A 已补藏干引动边界 |
| 墓库引动 | time_context/ wealth/ | 部分 | P1 | 已有墓库边界，缺时间引动细化 |
| 宫位引动 | time_context/ palace/ | 部分 | P2 | P31B 已补位置触发边界，需宫位基础 |
| 十神引动 | time_context/ interaction/ | 部分 | P1 | P31B 已补时间层十神触发边界，与十神组合类知识相连 |
| 应期 | timing/ | 归档 | P4 | 暂不进入规则 |

### L9B：时间引动细化第一批

| 类别 | 目录 | 状态 | 优先级 | 说明 |
|---|---|---|---:|---|
| 藏干引动细化 | time_context/ core/ | 部分 | P1 | P35 已补藏干层级、可达性和主机制边界 |
| 大运引动本命细化 | time_context/ | 部分 | P0 | P35 已补本命锚点和不改写本命边界 |
| 流年引动本命细化 | time_context/ | 部分 | P0 | P35 已补短期触发与本命对象边界 |
| 流年引动大运细化 | time_context/ | 部分 | P1 | P35 已补岁运层级归因与本命锚点边界 |
| 干支同动 | time_context/ core/ | 部分 | P1 | P35 已补天干证据、地支证据拆分边界 |
| 十神引动细化 | time_context/ interaction/ | 部分 | P1 | P35 已补时间层十神不直接转领域结论边界 |
| 宫位引动细化 | time_context/ palace/ | 部分 | P1 | P35 已补宫位、十神对象和关系类型边界 |
| 墓库引动细化 | time_context/ core/ | 部分 | P1 | P35 已补时间触发、藏物和开闭条件边界 |

## L9A：地理信息与环境背景

| 类别 | 目录 | 状态 | 优先级 | 说明 |
|---|---|---|---:|---|
| 出生地 | geo_context/ | 部分 | P1 | P31A 已补排盘元数据 |
| 时区 | geo_context/ | 部分 | P1 | P31A 已补排盘校验 |
| 经纬度 | geo_context/ | 部分 | P1 | P31A 已补真太阳时边界 |
| 真太阳时 | geo_context/ | 部分 | P1 | P31A 已补启用边界，仍需审阅 |
| 夏令时 | geo_context/ | 部分 | P2 | P31A 已补历史时间校验 |
| 地域气候 | geo_context/ | 部分 | P2 | P31A 已补调候背景候选 |
| 出生地与居住地差异 | geo_context/ | 归档 | P3 | 后置 |
| 迁移地影响 | geo_context/ | 归档 | P4 | 不作为当前规则 |

### L9C：地理与排盘元数据细化第一批

| 类别 | 目录 | 状态 | 优先级 | 说明 |
|---|---|---|---:|---|
| 出生地时区细化 | geo_context/ | 部分 | P1 | P37 已补排盘元数据与不确定性边界 |
| 经纬度真太阳时细化 | geo_context/ | 部分 | P1 | P37 已补算法版本、用户确认和时柱边界 |
| 夏令时历史时区细化 | geo_context/ | 部分 | P2 | P37 已补历史时间制度校验边界 |
| 地域气候背景细化 | geo_context/ | 部分 | P2 | P37 已补调候背景不得覆盖主结构 |
| 出生地居住地差异细化 | geo_context/ | 归档 | P3 | P37 已补居住地不参与本命计算 |
| 迁移地影响归档细化 | geo_context/ | 归档 | P4 | P37 已补迁移地建议禁用边界 |

## L10：辅助体系

| 类别 | 目录 | 状态 | 优先级 | 说明 |
|---|---|---|---:|---|
| 神煞 | shensha/ | 部分 | P3 | 只有占位，先象意归档 |
| 纳音 | nayin/ | 部分 | P3 | P31B 已补传统符号归档边界 |
| 十二长生 | growth_phase/ | 部分 | P2 | 有 1 条，占比低 |
| 胎元 | auxiliary_pillars/ | 部分 | P3 | P31B 已补辅助柱归档边界 |
| 命宫 | auxiliary_pillars/ | 部分 | P3 | P31B 已补辅助柱归档边界 |
| 身宫 | auxiliary_pillars/ | 部分 | P3 | P31B 已补辅助柱归档边界 |
| 空亡 | auxiliary_symbols/ | 部分 | P3 | P31B 已补辅助符号归档边界 |

### L10A：辅助体系细化第一批

| 类别 | 目录 | 状态 | 优先级 | 说明 |
|---|---|---|---:|---|
| 十二长生细化 | growth_phase/ | 部分 | P2 | P37 已补阶段标签与禁断边界 |
| 神煞索引归档细化 | shensha/ | 部分 | P3 | P37 已补传统符号参考与默认折叠边界 |
| 纳音归档细化 | nayin/ | 部分 | P3 | P37 已补文化解释与不覆盖主结构边界 |
| 胎元归档细化 | auxiliary_pillars/ | 部分 | P3 | P37 已补算法版本和归档边界 |
| 命宫归档细化 | auxiliary_pillars/ | 部分 | P3 | P37 已补四柱优先和禁用边界 |
| 身宫归档细化 | auxiliary_pillars/ | 部分 | P3 | P37 已补后续接入所需验证边界 |
| 空亡归档细化 | auxiliary_symbols/ | 部分 | P3 | P37 已补算法版本、作用范围与禁断边界 |
| 用神候选禁用边界 | useful_god/ | 归档 | P3 | P37 已补不启用用神裁决和多模型仲裁要求 |
| 忌神补救建议禁用 | useful_god/ answer_expression/ | 归档 | P3 | P37 已补补五行、改运建议禁用边界 |

## L11：回答表达与治理

| 类别 | 目录 | 状态 | 优先级 | 说明 |
|---|---|---|---:|---|
| 回答说人话 | answer_expression/ | 已有 | P0 | 已有 |
| 不支持问题降级 | answer_expression/ | 已有 | P0 | 已有 |
| 内部术语清理 | answer_expression/ | 已有 | P0 | 已有 |
| 预测断语过滤 | answer_expression/ | 部分 | P0 | 还要继续 |
| Review UI | lab/ | 部分 | P1 | 现有基础 |
| Rule DB 门禁 | rule_db/ | 部分 | P1 | P27 已有智能门禁 |

### L11A：回答表达与治理细化第一批

| 类别 | 目录 | 状态 | 优先级 | 说明 |
|---|---|---|---:|---|
| 结构说人话细化 | answer_expression/ | 已有 | P0 | P38 已补普通中文表达和候选不等于结论 |
| 不支持问题降级细化 | answer_expression/ | 已有 | P0 | P38 已补不硬答和安全结构范围 |
| 内部术语过滤细化 | answer_expression/ | 已有 | P0 | P38 已补内部字段只进审计不进回答 |
| 预测断语过滤细化 | answer_expression/ | 已有 | P0 | P38 已补断语替换和禁词边界 |
| 证据边界表达 | answer_expression/ | 已有 | P0 | P38 已补证据来源和不足表达 |
| 时间层表达 | answer_expression/ time_context/ | 已有 | P0 | P38 已补时间层触发不改写本命 |
| 领域安全降级表达 | answer_expression/ | 已有 | P0 | P38 已补财富事业结构承接和高风险降级 |
| 用户反馈表达优化 | answer_expression/ | 部分 | P1 | P38 已补反馈只优化表达和推荐 |
| 失败归因展示 | lab/ | 部分 | P1 | P38 已补推荐、知识、规则、表达归因展示 |
| draft 提案展示 | lab/ | 部分 | P1 | P38 已补 seed、rule draft、answer expression 展示边界 |
| 合成评估报告展示 | lab/ | 部分 | P1 | P38 已补正反样本、干扰样本和误触发展示 |
| 智能门禁报告 | rule_db/ | 部分 | P1 | P38 已补选中、阻断、原因和回滚路径 |
| 回滚谱系记录 | rule_db/ | 部分 | P1 | P38 已补版本、来源、评估批次和回滚 |
| 自动审批边界 | rule_db/ | 部分 | P1 | P38 已补高风险阻断和禁止自动上线 |

## 第一轮只做这些

```text
P28E 十神组合类知识
P29 盲派理法
P30 宫位象法
P31 格局正格
P32 大运流年引动
P33 地理信息与排盘边界
```

其他目录先占位，不急着填。
