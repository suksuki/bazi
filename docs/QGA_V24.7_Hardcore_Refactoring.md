# QGA V24.7 硬核重构方案实施文档

## 文档信息
- **版本**: V24.7
- **创建日期**: 2024
- **状态**: 实施中

---

## 一、重构目标

### 核心目标
从"黑盒计算"转变为"确定性逻辑链路"

### 解决的核心问题
1. **逻辑脱节**：LLM输出不规范，解析不稳定
2. **数值乱跳**：五行修正值不合理，缺乏约束
3. **逻辑颠倒**：物理因果关系理解错误

---

## 二、重构架构

### 1. LLM逻辑网关中间件

**文件**: `utils/llm_parser.py`

**类**: `LLMParser`

**核心功能**:
- **正则强制提取JSON**：无论LLM输出多少废话，只抓取 `{...}` 中的JSON
- **脏数据清洗**：处理算式（`14.3 + 5` → `19.3`）、移除代码逻辑（`Math.max()`等）
- **非负约束**：确保所有五行值 >= 0
- **能量守恒**：归一化到原始总和（保持100%）
- **修正幅度限制**：限制LLM校准幅度（最大±30%）

**使用示例**:
```python
from utils.llm_parser import LLMParser

parser = LLMParser()
persona, calibration, debug_info = parser.parse_llm_response(
    response_text=llm_response,
    original_elements={"金": 5.2, "木": 74.8, "水": 0, "火": 19.9, "土": 0}
)
```

### 2. 格局引擎注册机制

**文件**: `core/models/pattern_engine.py`

**核心类**:
- `PatternEngine`（抽象基类）
- `PatternEngineRegistry`（注册表）
- `PatternMatchResult`（匹配结果）
- `VectorBias`（五行矢量偏移）

**每个格局引擎必须实现**:
1. `matching_logic()`: 判定规则
2. `semantic_definition()`: 给LLM看的硬核物理判词
3. `vector_bias()`: 预设的五行受力偏移方向

**示例实现**:
```python
class CongErGeEngine(PatternEngine):
    """从儿格引擎"""
    
    def matching_logic(self, chart, day_master, ...) -> PatternMatchResult:
        # 判定逻辑
        pass
    
    def semantic_definition(self, match_result, geo_context) -> str:
        if geo_context in ["北方/北京", "近水环境"]:
            return "等离子喷泉遭遇极寒冷却，才华产出虽高但无法变现/受阻"
        # ...
    
    def vector_bias(self, match_result, geo_context) -> VectorBias:
        if geo_context in ["北方/北京", "近水环境"]:
            return VectorBias(fire=-15.0, water=+10.0)
        # ...
```

### 3. P.F.A权重坍缩算法

**文件**: `core/models/weight_collapse.py`

**类**: `WeightCollapseAlgorithm`

**核心公式**:
- **主格局权重** = 0.7
- **次格局总权重** = 0.3（按Strength比例分配）

**算法流程**:
1. 按PriorityRank和Strength排序
2. 识别主格局（PriorityRank=1或Strength最高）
3. 主格局获得0.7权重
4. 次格局按Strength比例瓜分剩余0.3权重
5. 验证权重总和（归一化到1.0）

**使用示例**:
```python
from core.models.weight_collapse import WeightCollapseAlgorithm

patterns = [
    {"name": "从儿格", "PriorityRank": 1, "Strength": 0.85},
    {"name": "食神制杀", "PriorityRank": 2, "Strength": 0.6},
]

weighted = WeightCollapseAlgorithm.collapse_pattern_weights(patterns)
# 结果: [({"name": "从儿格", ...}, 0.7), ({"name": "食神制杀", ...}, 0.3)]
```

### 4. 五行矢量反向校准 (V.F.I)

**文件**: `core/models/weight_collapse.py`

**类**: `VectorFieldCalibration`

**核心功能**:
1. 根据格局引擎的`vector_bias`计算总偏移
2. 应用权重坍缩后的格局权重
3. 限制LLM修正幅度（最大±30%）
4. 确保能量守恒（总和保持100%）

**使用示例**:
```python
from core.models.weight_collapse import VectorFieldCalibration

# 计算加权偏移
base_bias = VectorFieldCalibration.calculate_weighted_bias(
    patterns_with_weights=weighted_patterns,
    pattern_engines=engine_dict,
    geo_context="北方/北京"
)

# 应用LLM校准
final_elements = VectorFieldCalibration.apply_llm_calibration(
    base_bias=base_bias,
    llm_calibration=llm_calibration,
    original_elements=original_elements
)
```

---

## 三、集成方案

### 步骤1: 更新LLM语义合成器

**文件**: `core/models/llm_semantic_synthesizer.py`

**修改点**:
1. 使用`LLMParser.parse_llm_response()`替代原有的`_parse_structured_response()`
2. 集成权重坍缩算法
3. 应用V.F.I矢量校准

### 步骤2: 更新审计控制器

**文件**: `controllers/profile_audit_controller.py`

**修改点**:
1. 使用`PatternEngineRegistry`检测格局
2. 应用权重坍缩算法
3. 计算格局引擎的`vector_bias`
4. 应用V.F.I校准

### 步骤3: 实现格局引擎

**需要实现的格局引擎**（示例）:
1. `CongErGeEngine`（从儿格）- 已实现
2. `ShangGuanJianGuanEngine`（伤官见官）
3. `HuaHuoGeEngine`（化火格）
4. `JianLuYueJieEngine`（建禄月劫）
5. ...（共10+个）

---

## 四、数据流架构

```
[数据注入层]
  ↓
[格局扫描层] → PatternEngineRegistry.detect_patterns()
  ↓
[权重坍缩层] → WeightCollapseAlgorithm.collapse_pattern_weights()
  ↓
[格局引擎层] → PatternEngine.semantic_definition() + PatternEngine.vector_bias()
  ↓
[LLM推理层] → LLMSemanticSynthesizer.synthesize_persona()
  ↓
[逻辑网关层] → LLMParser.parse_llm_response()（清洗和验证）
  ↓
[矢量校准层] → VectorFieldCalibration.apply_llm_calibration()
  ↓
[前端渲染层] → UI更新受力图和审计报告
```

---

## 五、关键技术细节

### 1. LLM输出清洗流程

```
LLM原始输出
  ↓ [移除markdown标记]
  ↓ [提取第一个{到最后一个}]
  ↓ [处理算式: "14.3 + 5" → "19.3"]
  ↓ [移除代码逻辑: Math.max()等]
  ↓ [JSON解析]
  ↓ [非负约束: max(0.0, value)]
  ↓ [能量守恒: 归一化到原始总和]
  ↓ [限制修正幅度: ±30%]
最终校准值
```

### 2. 权重坍缩公式

```
主格局权重 = 0.7（固定）

次格局i权重 = (Strength_i / ΣStrength_次格局) × 0.3

验证: Σ权重 = 1.0（归一化）
```

### 3. 矢量校准公式

```
最终值 = 原始值 + 格局引擎偏移 + LLM校准偏移

约束:
- 非负: 最终值 >= 0
- LLM修正幅度: |LLM校准偏移| <= 原始值 × 30%
- 能量守恒: Σ最终值 = Σ原始值（归一化）
```

---

## 六、测试用例

### 测试1: LLM输出清洗

```python
# 输入: LLM返回带算式的JSON
response = '{"persona": "...", "corrected_elements": {"火": 14.3 + 5}}'

# 期望输出: 清洗后的JSON，火=19.3
persona, calibration, _ = LLMParser.parse_llm_response(response, original_elements)
assert calibration['fire'] == 19.3 - 14.3  # 偏移量 = 5.0
```

### 测试2: 权重坍缩

```python
patterns = [
    {"name": "从儿格", "PriorityRank": 1, "Strength": 0.85},
    {"name": "食神制杀", "PriorityRank": 2, "Strength": 0.6},
]

weighted = WeightCollapseAlgorithm.collapse_pattern_weights(patterns)
assert weighted[0][1] == 0.7  # 主格局权重
assert abs(sum(w for _, w in weighted) - 1.0) < 0.01  # 权重总和=1.0
```

### 测试3: 矢量校准

```python
# 测试能量守恒
original = {"金": 20, "木": 20, "水": 20, "火": 20, "土": 20}
final = VectorFieldCalibration.apply_llm_calibration(
    base_bias={"fire": 10.0},  # 火+10
    llm_calibration={"fire": 5.0},  # LLM再+5
    original_elements=original
)
assert abs(sum(final.values()) - 100.0) < 0.01  # 总和保持100
```

---

## 七、实施进度

- [x] **第一步**: LLM逻辑网关中间件（`utils/llm_parser.py`）
- [x] **第二步**: 格局引擎基类和注册机制（`core/models/pattern_engine.py`）
- [x] **第三步**: P.F.A权重坍缩算法（`core/models/weight_collapse.py`）
- [x] **第四步**: 五行矢量反向校准（`VectorFieldCalibration`）
- [ ] **第五步**: 集成到`llm_semantic_synthesizer.py`
- [ ] **第六步**: 集成到`profile_audit_controller.py`
- [ ] **第七步**: 实现具体格局引擎（10+个）
- [ ] **第八步**: UI交互优化（实时动效、审计路径溯源）

---

## 八、未来扩展

### 1. 格局引擎自动化注册

从`logic_registry.py`自动加载格局，动态创建`PatternEngine`实例

### 2. 缓存机制

缓存格局匹配结果和LLM推理结果，提升性能

### 3. 异步处理

支持批量审计和异步LLM调用

---

**文档结束**

