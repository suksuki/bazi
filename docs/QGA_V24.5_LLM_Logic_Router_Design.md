# QGA V24.5 智能路由审计系统设计方案

## 文档信息
- **版本**: V24.5 / V24.6 (增强版)
- **创建日期**: 2024
- **最后更新**: 2024
- **状态**: 已实现（部分功能持续优化中）

---

## 一、核心思路：逻辑路由与语义合成

### 设计理念

放弃传统的"静态数值统计"，构建以"格局为中心"的智能推理架构。系统不再简单数干支个数，而是通过以下路径实现精准的命运张力捕捉：

```
格局识别 -> 逻辑过滤 -> 语义合成 -> 反向五行校准
```

### 核心优势

1. **动态推理**：基于实时时空耦合状态（原局+大运+流年+地理）进行格局识别
2. **权重优先**：通过PriorityRank和Strength建立格局优先级体系
3. **语义化输出**：将物理计算结果转换为人类可理解的"临床报告"
4. **自校准机制**：通过LLM推导的五行偏移，反向修正矢量场展示

---

## 二、核心组件设计

### 1. 格局注册库 (Pattern Registry)

**位置**: `core/logic_registry.py`, `core/logic_manifest.json`

**功能**: 将所有物理模型（伤官见官、从儿格、建禄月劫等）标准化为逻辑微服务

**实现方式**:
- 通过LogicRegistry统一管理
- 按主题分类：`PATTERN_PHYSICS`（物理模型仿真）
- 每个格局包含：逻辑ID、名称、物理特性、能量流、命运特征

**相关文件**:
- `core/models/pattern_semantic_pool.py`: 格局语义池，存储格局的物理逻辑判断

### 2. 智能路由引擎 (LLM Logic Router)

**位置**: `core/models/llm_semantic_synthesizer.py`

**核心类**: `LLMSemanticSynthesizer`

**功能**: 
- 担任"主诊医生"，在多个激活格局中识别"主病"与"权重"
- 执行权重坍缩：识别第一核心矛盾（PriorityRank=1或Strength最高）
- 语义编织：合成因果画像，拒绝碎片描述
- 矢量校准：输出五行修正百分比

**关键技术**:
- 结构化Prompt（Few-shot示例引导）
- 脏数据清洗（正则表达式提取JSON，处理算式）
- 非负约束验证（确保五行值 >= 0）
- 因果映射表（硬编码的物理逻辑规则）

### 3. 动态矢量场 (V.F.I - Vector Field Indicator)

**位置**: `controllers/profile_audit_controller.py`, `ui/pages/profile_audit.py`

**功能**: 
- 根据格局碰撞结果，反向修正五行十神场强
- 确保视觉展示（Radar Chart）与逻辑自洽
- 应用LLM推导的element_calibration进行矢量偏移

**实现方式**:
- 使用Plotly Polar Chart展示五行能量分布
- 支持"振动效果"（高冲突时显示震荡动画）
- 实时应用LLM校准值更新矢量场

---

## 三、执行流程

### 步骤1: [数据注入层]

**位置**: `controllers/profile_audit_controller.py::_build_structured_data`

**功能**: 自动合成原局、大运、流年、地理、微环境的JSON数据包

**数据结构**:
```json
{
  "Context": {
    "Name": "档案名称",
    "TimeSpace": "2025年 | 大运丁酉 | 流年乙巳 | 城市北京",
    "DayMaster": "丙火"
  },
  "ActivePatterns": [
    {
      "Name": "从儿格等离子喷泉",
      "Type": "Special",
      "PriorityRank": 1,
      "Logic": "击中逻辑描述",
      "Strength": 60.37
    }
  ],
  "RawElements": {
    "金": 5.2,
    "木": 74.8,
    "水": 0,
    "火": 19.9,
    "土": 0
  }
}
```

**关键特性**:
- 按Strength降序排列格局
- 自动添加PriorityRank字段（1=最高优先级）
- 包含完整的时空耦合信息

### 步骤2: [格局扫描层]

**位置**: `controllers/profile_audit_controller.py::_analyze_year_patterns`

**功能**: 基于注册规则，列出所有"实时激活"的格局及其物理特性

**流程**:
1. 合成场强：将原局+大运+流年+地理合并为单一矢量场
2. 检测格局状态变化（如：从"伤官伤尽"退化为"内耗受阻"）
3. 识别最终激活格局（基于合成场强）
4. 解析格局详情：击中逻辑、特性、干预策略

**输出**: `pattern_audit`字典，包含patterns列表

### 步骤3: [LLM推理层]

**位置**: `core/models/llm_semantic_synthesizer.py::synthesize_persona`

**核心方法**:
- `_construct_structured_prompt`: 构造严格的结构化Prompt
- `_llm_synthesize_structured`: 调用LLM进行推理
- `_parse_structured_response`: 解析和清洗LLM响应

**3.1 权重坍缩（识别第一核心矛盾）**

**实现逻辑**:
```python
# 优先使用PriorityRank=1的格局
top_pattern = patterns[0] if patterns[0].get('PriorityRank') == 1 else max(patterns, key=lambda x: x.get('Strength', 0))
```

**Prompt约束**:
- 明确要求仅根据主导格局生成persona
- 忽略其他格局（Top 2-3仅作为扰动因素）

**3.2 语义编织（合成因果画像）**

**因果映射表（硬编码规则）**:
- `[从儿格（火土）] + [北方/北京/近水]` → "等离子喷泉遭遇极寒冷却，才华产出虽高但无法变现/受阻"
- `[从儿格（火土）] + [南方/火地]` → "才华在火环境中得到充分激活，但需注意过度消耗"
- `[食神制杀] + [近水环境]` → "过度的理智(水)淹没了表现力(火)，导致才华无法释放"
- `[建禄月劫] + [近水]` → "水克火，导致热失控格局被抑制，但可能产生内部压力"

**输出格式**: 
- 严禁带标题、任务A/B、解释性文字
- 仅输出纯JSON：`{"persona": "...", "corrected_elements": {...}}`

**3.3 矢量校准（输出五行修正百分比）**

**规则**:
- 所有五行值必须 >= 0（非负约束）
- 五行总和应接近原始总和（允许小幅波动）
- 仅在JSON中输出纯数字，不要写算式或代码

**脏数据清洗**:
```python
# 1. 移除markdown代码块标记
# 2. 提取第一个{到最后一个}之间的内容
# 3. 处理算式（如 "14.3 + 5" -> "19.3"）
# 4. 移除Math.max()等函数调用
# 5. 应用非负约束
```

### 步骤4: [前端渲染层]

**位置**: `ui/pages/profile_audit.py::render_audit_report`

**功能**: 
- 更新受力图（应用LLM校准值）
- 输出临床审计报告（人话翻译）

**报告内容**:
1. **核心矛盾**：一句话直击要害
2. **深度画像**：300字左右的性格与宿命逻辑（由LLM生成）
3. **财富相预测**：判定财富等级与性质
4. **干预药方**：用、喜、忌、调候及具体的改运建议
5. **实时激活格局清单**：显示所有激活格局的详细信息

**调试功能**:
- LLM调试控制台：显示输入JSON、Prompt、原始响应
- 完整审计报告：包含完整的LLM交互信息，可复制发送给AI分析师

---

## 四、调优策略

### 1. 小模型适配（Qwen2.5:2.5b / 3b）

**挑战**: 
- 逻辑理解能力有限
- 输出规范性差（容易添加多余文字、算式、代码）
- 物理常识匮乏（容易混淆因果关系）

**解决方案**:

**A. 结构化Prompt + Few-shot示例**
```python
# 提供2个完整的正确示例
example1 = {"persona": "...", "corrected_elements": {...}}
example2 = {"persona": "...", "corrected_elements": {...}}
```

**B. 严格输出约束**
- 明确要求"严禁输出任何分析过程、标题或解释性文字"
- 仅允许输出纯JSON格式
- 不要带markdown代码块标记

**C. 脏数据清洗拦截器**
- 正则表达式提取JSON
- 自动处理算式（eval简单数学表达式）
- 移除代码逻辑（Math.max等函数调用）
- 应用非负约束

**D. 因果映射表（硬编码）**
- 针对常见格局+地理组合，硬编码物理逻辑
- 避免LLM自由发挥导致的逻辑错误

### 2. 异步处理（待实现）

**需求**: 解决LLM推理延迟问题

**建议方案**:
- 引入批量审计机制
- 使用后台任务队列（如Celery）
- 支持进度显示和结果回调

### 3. 未来升级（70B模型接口）

**预留接口**: 
- `LLMSemanticSynthesizer`类设计支持模型切换
- 通过`ConfigManager`读取模型配置
- 支持动态切换模型名称和API地址

**升级路径**:
- 从"逻辑通顺"（3b）到"命运穿透"（70b）
- 减少硬编码的因果映射表依赖
- 提升物理逻辑理解的准确性

---

## 五、关键技术细节

### 1. PriorityRank机制

**目的**: 明确标识格局优先级，避免LLM混淆

**实现**:
```python
# 在_build_structured_data中
active_patterns_list.sort(key=lambda x: x.get('Strength', 0.0), reverse=True)
for idx, pattern in enumerate(active_patterns_list, start=1):
    pattern['PriorityRank'] = idx  # 1=最高优先级
```

### 2. 非负约束验证

**问题**: LLM可能输出负数（违反物理约束）

**解决方案**:
```python
# 在解析时应用
val = max(0.0, float(raw_val))  # 非负约束
```

### 3. 算式处理

**问题**: LLM可能在JSON中写入算式（如 `"火": 14.3 + 5`）

**解决方案**:
```python
# 正则表达式提取并计算
if isinstance(raw_val, str) and ('+' in raw_val or '-' in raw_val):
    raw_val = eval(raw_val)  # 安全计算简单算式
```

### 4. 地理环境识别

**实现**:
```python
geo_info = structured_data.get('Context', {}).get('TimeSpace', '')
if '近水' in geo_info or 'water' in geo_info.lower():
    geo_context = "近水环境"
elif '北京' in geo_info or '北方' in geo_info:
    geo_context = "北方/北京"
elif '南方' in geo_info or 'fire' in geo_info.lower():
    geo_context = "南方/火地"
```

---

## 六、文件结构

```
core/
├── models/
│   ├── llm_semantic_synthesizer.py    # LLM语义合成器（核心）
│   ├── pattern_semantic_pool.py       # 格局语义池
│   ├── profile_audit_engines.py       # PFA/SOA/MCA引擎
│   └── profile_audit_model.py         # 数据模型
├── logic_registry.py                  # 逻辑注册表
└── logic_manifest.json                # 格局注册清单

controllers/
└── profile_audit_controller.py        # 审计控制器（编排逻辑）

ui/pages/
└── profile_audit.py                   # UI渲染层

docs/
└── QGA_V24.5_LLM_Logic_Router_Design.md  # 本文档
```

---

## 七、使用示例

### 基本调用流程

```python
from controllers.profile_audit_controller import ProfileAuditController

controller = ProfileAuditController()

# 执行深度审计（启用LLM）
result = controller.perform_deep_audit(
    profile_id="profile_001",
    year=2025,
    city="北京",
    micro_env=["近水", "低层"],
    use_llm=True
)

# 获取LLM生成的画像
persona = result['semantic_report']['persona']
calibration = result['llm_calibration']
```

### LLM语义合成器直接调用

```python
from core.models.llm_semantic_synthesizer import LLMSemanticSynthesizer

synthesizer = LLMSemanticSynthesizer(use_llm=True)

result = synthesizer.synthesize_persona(
    active_patterns=[...],
    synthesized_field={...},
    profile_name="蒋柯栋",
    day_master="丙火",
    force_vectors={...},
    year=2025,
    luck_pillar="丁酉",
    year_pillar="乙巳",
    geo_info="城市北京 | 近水"
)

persona = result['persona']
element_calibration = result['element_calibration']
```

---

## 八、已知问题与限制

### 1. 小模型局限性

- **输出规范性**: 即使有Few-shot示例，3b模型仍可能添加多余文字
- **物理逻辑**: 对复杂因果关系理解不准确（需依赖硬编码映射表）
- **计算能力**: 可能在JSON中写入算式而非数字

**缓解措施**: 
- 脏数据清洗拦截器（正则表达式）
- 硬编码因果映射表
- 严格的Prompt约束

### 2. 性能问题

- **延迟**: LLM推理需要3-10秒（取决于模型大小和硬件）
- **并发**: 当前为同步调用，高并发时可能阻塞

**未来改进**: 
- 异步处理机制
- 批量审计优化
- 缓存机制（相同输入复用结果）

### 3. 错误处理

- **LLM调用失败**: 自动回退到规则生成
- **JSON解析失败**: 尝试多种格式解析，最终回退到旧格式
- **网络问题**: 通过connection_status检测，提示用户检查连接

---

## 九、未来规划

### 短期（1-2周）

1. **优化Prompt**: 进一步精简，减少LLM"废话"
2. **增强清洗**: 处理更多边缘情况（嵌套JSON、多个JSON对象等）
3. **错误处理**: 更详细的错误日志和用户提示

### 中期（1-2月）

1. **异步处理**: 实现后台任务队列
2. **批量审计**: 支持批量处理多个档案
3. **缓存机制**: 相同输入的LLM结果缓存

### 长期（3-6月）

1. **70B模型**: 集成更大的模型，减少硬编码依赖
2. **自学习机制**: 基于用户反馈优化因果映射表
3. **多模态**: 支持图像、图表等更多输入格式

---

## 十、参考资料

- **QGA架构文档**: `docs/Antigravity_Constitution.md`
- **格局注册机制**: `core/logic_registry.py`
- **代码实现**: `core/models/llm_semantic_synthesizer.py`
- **UI实现**: `ui/pages/profile_audit.py`

---

## 附录：关键代码片段

### A. 结构化Prompt构造

```python
prompt = f"""你是一个逻辑转换器。严禁输出任何分析过程、标题或解释性文字。仅允许输出纯JSON格式。

【严格响应模版 (Template)】
仅允许输出符合以下格式的JSON，不要带markdown代码块标记，不要带任何其他文字：
{{"persona": "...", "corrected_elements": {{"金": XX, "木": XX, "水": XX, "火": XX, "土": XX}}}}

【Few-Shot示例1】
输入：{example_input}
输出：{example_output}

【Few-Shot示例2】
输入：{example2_input}
输出：{example2_output}
...
"""
```

### B. 脏数据清洗

```python
# 1. 移除markdown代码块
cleaned_text = re.sub(r'```json\s*', '', cleaned_text, flags=re.IGNORECASE)
cleaned_text = re.sub(r'```\s*', '', cleaned_text)

# 2. 提取JSON
json_start = cleaned_text.find('{')
json_end = cleaned_text.rfind('}')
cleaned_text = cleaned_text[json_start:json_end + 1]

# 3. 处理算式
if isinstance(raw_val, str) and ('+' in raw_val or '-' in raw_val):
    raw_val = eval(raw_val)  # 安全计算

# 4. 非负约束
val = max(0.0, float(raw_val))
```

---

**文档结束**

