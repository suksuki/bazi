# 张量全息格局注册表

## 目录结构

```
core/subjects/holographic_pattern/
├── registry.json          # 格局注册表（QGA-HR V1.0格式）
└── README.md              # 本文件
```

## 注册表规范

本注册表严格遵循 **QGA-HR V1.0 注册表规范**。

### 层级命名规范

- **L1 (Category)**: 大类（如：[A] 杀刃类、[B] 食财类）
- **L2 (Subject ID)**: 专题唯一编号（如：[A-03] 羊刃架杀）
- **L3 (Variants)**: 子结构变体（如：[A-03-V1] 刃重杀轻）

### 核心注册模块

每个格局必须包含以下四个模块：

#### 模块 I：语义意象层 (Semantic Seed)
- **内容**：由 AI 分析师执行的格局物理意象解构
- **定义**：将古典判词转化为物理态描述（如：能量流向、约束场强度、振幅频率）

#### 模块 II：张量投影算子 (Tensor Operator)
- **核心参数**：定义 SAI (总能级) 向五维轴分配的初始权重系数 $\mathbf{W}$
  - $w_E$ (能级轴)：生命总量与抗压底气
  - $w_O$ (秩序轴)：权力、名誉、社会地位
  - $w_M$ (物质轴)：财富、资产、执行转化
  - $w_S$ (应力轴)：健康损耗、结构扭曲、意外
  - $w_R$ (关联轴)：六亲交互、情感、人际网络
- **激活函数**：注册非线性转换算法（如 Sigmoid），定义能量爆发或坍缩的阈值

#### 模块 III：动力学演化注册 (Kinetic Evolution)
- **触发算子 (Trigger)**：定义引起张量突变的因子（如：冲、穿、刑的相位变化）
- **增益算子 (Gain)**：定义引起能级跃迁的因子（如：格局清纯度的提升点）
- **地理阻尼 ($\delta$)**：注册环境对张量传导的修正系数

#### 模块 IV：审计对撞历史 (Audit Trail)
- **统计底色**：51.84 万全量样本中的覆盖率
- **命中指标**：记录历史回测（Ground Truth）的命中率
- **参数记录**：保留每一次调优的版本历史（Version Control）

## 注册表格式示例

```json
{
  "patterns": {
    "A-03": {
      "id": "A-03",
      "name": "羊刃架杀",
      "name_cn": "羊刃架杀",
      "category": "A",
      "subject_id": "A-03",
      "icon": "⚔️",
      "version": "1.0",
      "active": true,
      "semantic_seed": {
        "description": "AI分析师解构的物理意象",
        "physical_image": "...",
        "source": "ai_analyst",
        "updated_at": "2025-12-29"
      },
      "tensor_operator": {
        "weights": {
          "E": 0.3,
          "O": 0.5,
          "M": 0.1,
          "S": 0.05,
          "R": 0.05
        },
        "activation_function": {
          "type": "sigmoid",
          "parameters": {
            "k": 1.0,
            "x0": 0.8
          }
        },
        "normalized": true
      },
      "kinetic_evolution": {
        "trigger_operators": [],
        "gain_operators": [],
        "geo_damping": 1.0
      },
      "audit_trail": {
        "coverage_rate": 0.0,
        "hit_rate": 0.0,
        "version_history": []
      }
    }
  }
}
```

## 参考规范

- **QGA-HR V1.0 注册表规范**: `docs/QGA_HR_V1.0_Registry_Specification.md`
- **FDS-V1.1 正向拟合与建模规范**: `docs/QGA_FDS_V1.1_Specification.md`
