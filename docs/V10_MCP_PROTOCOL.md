# V10.0 Model Context Protocol (MCP) 完整协议文档

**版本**: V10.0  
**发布日期**: 2025-12-17  
**状态**: ✅ 正式发布

---

## 📋 目录

1. [MCP 概述](#mcp-概述)
2. [核心组件](#核心组件)
3. [工作流程](#工作流程)
4. [数据结构](#数据结构)
5. [API 接口](#api-接口)
6. [实现示例](#实现示例)

---

## MCP 概述

**Model Context Protocol (MCP)** 是 V10.0 引入的上下文管理协议，用于在推演过程中注入"地面真值"上下文，实现更精准的预测。

### 设计目标

1. **上下文注入**: 在推演开始前注入案例的真实背景信息
2. **时空感知**: 捕捉时间序列中的长程依赖
3. **不确定性量化**: 提供概率分布信息
4. **反馈循环**: 存储真实事件反馈，用于持续优化

### 核心价值

- ✅ **提升预测精度**: 通过注入真实上下文，提高预测准确性
- ✅ **量化不确定性**: 提供置信区间和概率分布
- ✅ **持续学习**: 通过反馈循环实现参数自动调优
- ✅ **可解释性**: 清晰的上下文结构，便于理解和调试

---

## 核心组件

### 1. Context Injection (上下文注入)

**目的**: 在推演开始前注入案例的真实背景信息。

**触发时机**: 推演开始前

**数据来源**:
- 案例基本信息（八字、日主、性别）
- 历史事件时间线
- 地理环境信息
- 时代背景信息

**处理流程**:
```
1. 加载案例数据
2. 提取关键特征（财库、身强等）
3. GAT 网络识别节点特征
4. 构建上下文对象
```

### 2. Temporal Context (时空上下文)

**目的**: 捕捉时间序列中的长程依赖。

**触发时机**: 时序推演过程中

**数据来源**:
- 历史年份的能量状态
- 时间序列特征
- 能量积累模式

**处理流程**:
```
1. Transformer 编码时间序列
2. 提取长程依赖特征
3. 识别能量积累模式
4. 预测临界点
```

### 3. Probabilistic Context (概率上下文)

**目的**: 提供不确定性量化信息。

**触发时机**: 预测计算完成后

**数据来源**:
- 贝叶斯推理结果
- 蒙特卡洛模拟
- 不确定性因子

**处理流程**:
```
1. 执行蒙特卡洛模拟
2. 计算概率分布
3. 生成置信区间
4. 评估风险等级
```

### 4. Feedback Context (反馈上下文)

**目的**: 存储真实事件反馈，用于 RLHF 调优。

**触发时机**: 推演完成后

**数据来源**:
- 真实事件值
- 预测误差
- 用户反馈

**处理流程**:
```
1. 比对预测值与真实值
2. 计算误差和命中率
3. 生成调优建议
4. 更新参数配置
```

---

## 工作流程

### 完整推演流程

```
┌─────────────────────────────────────────────────────────┐
│ 步骤1: Context Injection (上下文注入)                   │
│  - 加载案例数据                                          │
│  - GAT 网络识别节点特征                                  │
│  - 构建上下文对象                                        │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 步骤2: Nonlinear Simulation (非线性仿真)                 │
│  - Transformer 编码时间序列                              │
│  - 非线性激活计算                                        │
│  - 能量传播                                              │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 步骤3: Probabilistic Output (概率分布生成)              │
│  - 贝叶斯推理                                            │
│  - 蒙特卡洛模拟                                          │
│  - 生成置信区间                                          │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 步骤4: RLHF Feedback (反馈循环)                         │
│  - 比对预测值与真实值                                    │
│  - 计算误差和命中率                                      │
│  - 生成调优建议                                          │
│  - 更新参数配置                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 数据结构

### Context Injection 数据结构

```json
{
  "case_id": "JASON_D_T1961_1010",
  "case_name": "Jason D (财库连冲)",
  "bazi": ["辛丑", "丁酉", "庚辰", "丙戌"],
  "day_master": "庚",
  "gender": "男",
  "ground_truth": {
    "strength": "Special_Strong",
    "strength_score": 106.44,
    "wealth_vaults": ["丑", "辰", "戌"],
    "vault_count": 3,
    "vault_density": 0.75
  },
  "context_features": {
    "node_features": {
      "node_1": {"energy": 85.2, "vault_mark": 1.0},
      "node_5": {"energy": 72.8, "vault_mark": 1.0},
      "node_7": {"energy": 78.5, "vault_mark": 1.0}
    },
    "attention_weights": {
      "vault_nodes": 1.5,
      "normal_nodes": 1.0
    }
  }
}
```

### Temporal Context 数据结构

```json
{
  "timeline": [
    {"year": 1961, "energy": 50, "state": "accumulation"},
    {"year": 1971, "energy": 55, "state": "accumulation"},
    {"year": 1981, "energy": 60, "state": "accumulation"},
    {"year": 1991, "energy": 65, "state": "accumulation"},
    {"year": 2001, "energy": 70, "state": "accumulation"},
    {"year": 2011, "energy": 85, "state": "accumulation"},
    {"year": 2015, "energy": 130, "state": "critical"}
  ],
  "temporal_features": {
    "accumulation_period": 54,
    "pressure_gradient": 0.8,
    "critical_point": 2015,
    "transformer_encoding": [0.12, 0.34, 0.56, ...]
  }
}
```

### Probabilistic Context 数据结构

```json
{
  "distribution": {
    "mean": 100.0,
    "std": 10.2,
    "percentiles": {
      "p5": 83.25,
      "p25": 92.68,
      "p50": 99.74,
      "p75": 106.89,
      "p95": 116.83
    },
    "samples_count": 1000
  },
  "uncertainty_factors": {
    "strength_uncertainty": 5.0,
    "clash_uncertainty": 0.0,
    "trine_uncertainty": 0.0,
    "mediation_uncertainty": 2.0,
    "help_uncertainty": 1.0,
    "base_uncertainty": 5.0
  },
  "risk_level": "medium",
  "confidence_interval": {
    "p25": 92.68,
    "p50": 99.74,
    "p75": 106.89
  }
}
```

### Feedback Context 数据结构

```json
{
  "feedback_events": [
    {
      "year": 2015,
      "real_value": 100.0,
      "predicted_value": 100.0,
      "predicted_mean": 99.71,
      "predicted_std": 10.39,
      "error": 0.0,
      "z_score": 0.03,
      "in_confidence_interval": true,
      "is_correct": true
    }
  ],
  "statistics": {
    "total_events": 1,
    "correct_predictions": 1,
    "hit_rate": 100.0,
    "avg_error": 0.0,
    "confidence_interval_hit_rate": 100.0,
    "avg_z_score": 0.03
  },
  "recommendations": []
}
```

---

## API 接口

### Context Injection API

```python
def inject_context(case_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    注入上下文信息
    
    Args:
        case_data: 案例数据字典
        
    Returns:
        上下文对象
    """
    # 1. 提取基本信息
    bazi = case_data.get('bazi', [])
    day_master = case_data.get('day_master', '')
    
    # 2. GAT 网络识别节点特征
    analyze_result = engine.analyze(bazi, day_master)
    
    # 3. 构建上下文对象
    context = {
        'bazi': bazi,
        'day_master': day_master,
        'strength_score': analyze_result.get('strength_score', 0.0),
        'strength_label': analyze_result.get('strength_label', 'Unknown'),
        'wealth_vaults': detect_vaults(bazi),
        'attention_weights': analyze_result.get('attention_weights', {})
    }
    
    return context
```

### Temporal Context API

```python
def encode_temporal_context(timeline: List[Dict], max_length: int = 100) -> Dict[str, Any]:
    """
    编码时空上下文
    
    Args:
        timeline: 时间线数据
        max_length: 最大长度
        
    Returns:
        时空上下文对象
    """
    # 1. Transformer 编码
    transformer_output = transformer.encode(timeline, max_length)
    
    # 2. 提取特征
    temporal_features = {
        'accumulation_period': calculate_accumulation_period(timeline),
        'pressure_gradient': calculate_pressure_gradient(timeline),
        'critical_point': detect_critical_point(timeline),
        'transformer_encoding': transformer_output
    }
    
    return {
        'timeline': timeline,
        'temporal_features': temporal_features
    }
```

### Probabilistic Context API

```python
def generate_probabilistic_context(base_estimate: float, 
                                   parameter_ranges: Dict[str, Tuple[float, float]],
                                   n_samples: int = 1000) -> Dict[str, Any]:
    """
    生成概率上下文
    
    Args:
        base_estimate: 基础估计值
        parameter_ranges: 参数范围
        n_samples: 采样数量
        
    Returns:
        概率上下文对象
    """
    # 1. 蒙特卡洛模拟
    distribution = BayesianInference.monte_carlo_simulation(
        base_estimate, parameter_ranges, n_samples
    )
    
    # 2. 计算不确定性因子
    uncertainty_factors = BayesianInference.estimate_uncertainty_factors(...)
    
    # 3. 评估风险等级
    risk_level = 'high' if distribution['std'] > 20 else \
                 'medium' if distribution['std'] > 10 else 'low'
    
    return {
        'distribution': distribution,
        'uncertainty_factors': uncertainty_factors,
        'risk_level': risk_level
    }
```

### Feedback Context API

```python
def collect_feedback_context(predictions: List[Dict], 
                            ground_truth: List[Dict]) -> Dict[str, Any]:
    """
    收集反馈上下文
    
    Args:
        predictions: 预测结果列表
        ground_truth: 真实值列表
        
    Returns:
        反馈上下文对象
    """
    # 1. 比对预测值与真实值
    feedback_events = []
    for pred, truth in zip(predictions, ground_truth):
        error = abs(pred['value'] - truth['value'])
        z_score = (truth['value'] - pred['mean']) / pred['std'] if pred.get('std', 0) > 0 else 0
        in_ci = pred['p25'] <= truth['value'] <= pred['p75']
        
        feedback_events.append({
            'year': truth['year'],
            'real_value': truth['value'],
            'predicted_value': pred['value'],
            'error': error,
            'z_score': z_score,
            'in_confidence_interval': in_ci,
            'is_correct': error <= 20.0 or abs(z_score) <= 2.0
        })
    
    # 2. 计算统计信息
    statistics = calculate_statistics(feedback_events)
    
    # 3. 生成调优建议
    recommendations = generate_recommendations(statistics)
    
    return {
        'feedback_events': feedback_events,
        'statistics': statistics,
        'recommendations': recommendations
    }
```

---

## 实现示例

### 完整推演示例

```python
from scripts.v10_full_inference_jason_d import V10FullInferenceEngine

# 初始化引擎
engine = V10FullInferenceEngine()

# 执行完整推演
result = engine.run_full_inference('JASON_D_T1961_1010', target_years=[2015])

# 访问上下文信息
context = result['context']
print(f"身强分数: {context['strength_score']}")
print(f"财库数量: {context['vault_count']}")

# 访问概率分布
prob_result = result['probability_results'][0]
print(f"均值: {prob_result['mean']}")
print(f"标准差: {prob_result['std']}")
print(f"置信区间: [{prob_result['confidence_interval']['p25']}, {prob_result['confidence_interval']['p75']}]")

# 访问反馈信息
rlhf = result['rlhf_feedback']
print(f"命中率: {rlhf['hit_rate']}%")
print(f"平均误差: {rlhf['avg_error']}")
```

### 单独使用 MCP 组件

```python
# 1. 上下文注入
from controllers.wealth_verification_controller import WealthVerificationController

controller = WealthVerificationController()
case = controller.get_case_by_id('JASON_D_T1961_1010')
context = controller.inject_context(case)

# 2. 时空上下文编码
from core.transformer_temporal import TransformerTemporal

transformer = TransformerTemporal()
temporal_context = transformer.encode_timeline(case.timeline)

# 3. 概率分布生成
from core.bayesian_inference import BayesianInference

distribution = BayesianInference.monte_carlo_simulation(
    base_estimate=100.0,
    parameter_ranges={'base_value': (90.0, 110.0)},
    n_samples=1000
)

# 4. 反馈收集
feedback = controller.collect_feedback(predictions, ground_truth)
```

---

## 配置参数

### MCP 相关配置

```json
{
  "mcp": {
    "enable_context_injection": true,
    "enable_temporal_context": true,
    "enable_probabilistic_context": true,
    "enable_feedback_context": true,
    "context_cache_ttl": 3600,
    "feedback_update_frequency": 10
  }
}
```

---

## 最佳实践

### 1. 上下文注入时机

- ✅ **推演开始前**: 注入案例基本信息
- ✅ **时序推演中**: 注入历史事件信息
- ❌ **推演完成后**: 不应再修改上下文

### 2. 概率分布使用

- ✅ **置信区间**: 用于判断预测可靠性
- ✅ **Z-score**: 用于评估预测准确性
- ✅ **风险等级**: 用于提示用户不确定性

### 3. 反馈循环优化

- ✅ **定期更新**: 每 10 个案例更新一次参数
- ✅ **增量学习**: 保留历史反馈数据
- ✅ **参数验证**: 更新后验证预测准确性

---

## 版本历史

### V10.0 (2025-12-17)

- ✅ 引入 MCP 协议
- ✅ 实现四大核心组件
- ✅ 提供完整 API 接口
- ✅ 支持概率分布验证

### V9.3 (之前版本)

- 基础上下文管理
- 地理修正模块
- 流时修正模块

---

## 参考文档

- [V10.0 算法总纲](./V10_ALGORITHM_CONSTITUTION.md)
- [V10.0 Jason D 推演报告](./V10_JASON_D_2015_ENERGY_BURST_ANALYSIS.md)
- [MCP 实施状态](./MCP_IMPLEMENTATION_STATUS.md)

---

**文档维护**: Bazi Predict Team  
**最后更新**: 2025-12-17  
**状态**: ✅ 正式发布

