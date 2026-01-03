# FDS-V3.0 标准注入提示词 (Standard Injection Prompt)

**版本**: V3.0  
**对齐文档**: FDS_ARCHITECTURE_v3.0.md 第六章  
**状态**: ✅ 标准化

---

## 📋 标准Prompt模板

### 完整Prompt（复制使用）

```markdown
# Role
You are the **FDS-V3.0 Lead Architect**. Your task is to generate a `pattern_manifest.json` for a specific Bazi pattern based on the strict FDS-V3.0 Schema defined in `FDS_ARCHITECTURE_v3.0.md` Chapter 6.

# Target Pattern
**Pattern Name**: [在此填入格局名，例如: 食神格 / Eating God]
**Source Reference**: Based on 《子平真诠》(Zi Ping Zhen Quan) and 《三命通会》(San Ming Tong Hui) logic.

# Schema Constraints (Strict Enforcement)

You must output a single valid JSON block following `FDS_ARCHITECTURE_v3.0.md` Chapter 6 (Pattern Manifest Schema).

## 1. Ten Gods Standard Codes (MUST USE THESE - NO EXCEPTIONS)

**CRITICAL**: Use ONLY these standard codes defined in FDS_ARCHITECTURE_v3.0.md:

- **ZG** (Direct Officer/正官), **PG** (Seven Killings/七杀)
- **ZC** (Direct Seal/正印), **PC** (Indirect Seal/Owl/枭神)
- **ZS** (Eating God/食神), **PS** (Hurting Officer/伤官)
- **ZR** (Direct Wealth/正财), **PR** (Indirect Wealth/偏财)
- **ZB** (Friend/比肩), **PB** (Rob Wealth/劫财)

**FORBIDDEN**: Do NOT use old codes like EG, IR, DO, etc. Only use ZG, PG, ZC, PC, ZS, PS, ZR, PR, ZB, PB.

## 2. Dimensions Definition

- **E** (Energy/能量), **O** (Order/有序度), **M** (Material/物质), **S** (Stress/应力), **R** (Relation/关系)
- Weight range: **[-1.0, 1.0]** (strictly enforced)

## 3. JSON Structure Requirements

### 3.1 meta_info (Required)
```json
{
  "pattern_id": "B-01",  // Format: [Category]-[Number]
  "version": "3.0",
  "display_name": "Eating God Pattern",
  "chinese_name": "食神格",
  "category": "TALENT",  // Must be: WEALTH, POWER, TALENT, or SELF
  "source_ref": ["ZPZQ-09-02", "SMTH-06-15"]  // Optional: source references
}
```

### 3.2 classical_logic_rules (Required)
```json
{
  "format": "jsonlogic",  // Must be "jsonlogic"
  "description": "Brief description of the logic",
  "expression": {
    // JSONLogic tree - must have root node (and/or)
    "and": [
      { ">": [{ "var": "ten_gods.ZS" }, 0] },
      // ... more conditions
    ]
  }
}
```

**Variable Format**:
- `{ "var": "ten_gods.ZS" }` - Ten God variable
- `{ "var": "self_energy" }` - Self energy
- `{ "var": "@config.gating.weak_self_limit" }` - System config

**Logic Operators**: and, or, not, >, <, >=, <=, ==, !=

### 3.3 tensor_mapping_matrix (Required)
```json
{
  "ten_gods": ["ZG", "PG", "ZC", "PC", "ZS", "PS", "ZR", "PR", "ZB", "PB"],
  "dimensions": ["E", "O", "M", "S", "R"],
  "weights": {
    "ZG": [0.1, 0.8, 0.2, 0.1, 0.3],  // 5 floats for E, O, M, S, R
    // ... all 10 ten gods
  },
  "strong_correlation": [
    {
      "ten_god": "ZS",
      "dimension": "O",
      "value": 0.9,  // Optional: explicit value
      "reason": "食神泄秀，才华核心"
    }
  ]
}
```

**Physics Rules**:
- ZS (Eating God): Increases O(Talent) and M(Wealth), reduces S(Stress)
- PC (Owl): Increases S(Stress), reduces O(Talent)
- ZR (Direct Wealth): Increases M(Wealth)
- PG (Seven Killings): Increases S(Stress)

# Output Requirements

1. Output **ONLY** valid JSON (no markdown code blocks, no explanations)
2. Ensure all weights are in range [-1.0, 1.0]
3. Ensure all ten_god codes use standard format (ZG, PG, etc.)
4. Ensure expression_tree has root node (and/or)
5. Include strong_correlation for physics axioms that must be LOCKED

# Task
Generate the pattern_manifest.json for: [格局名称]
```

---

## 🎯 使用指南

### 步骤1: 准备Prompt

1. 复制上面的完整Prompt模板
2. 替换 `[在此填入格局名]` 为实际格局名称
3. 替换 `[格局名称]` 为实际格局名称

### 步骤2: 发送给AI

将准备好的Prompt发送给：
- Claude (Anthropic)
- Gemini (Google)
- GPT-4 (OpenAI)
- 或其他高质量LLM

### 步骤3: 验证输出

1. **JSON格式验证**: 确保是有效的JSON
2. **Schema验证**: 检查是否符合FDS_ARCHITECTURE_v3.0.md第六章
3. **十神代码验证**: 确保使用标准代码（ZG, PG等）
4. **权重范围验证**: 确保所有权重在[-1.0, 1.0]

### 步骤4: 保存和使用

1. 保存为 `pattern_manifest_[pattern_id].json`
2. 运行SOP模拟器验证
3. 集成到系统使用

---

## 📝 示例：食神格

**Prompt中的替换**:
- `[在此填入格局名]`: 食神格 / Eating God
- `[格局名称]`: 食神格

**预期输出**: 符合FDS-V3.0规范的完整pattern_manifest.json

---

## ✅ 验证清单

生成后，检查以下项目：

- [ ] JSON格式有效（可通过json.tool验证）
- [ ] pattern_id格式正确（如"B-01"）
- [ ] version为"3.0"
- [ ] category为WEALTH/POWER/TALENT/SELF之一
- [ ] 所有十神代码使用标准格式（ZG, PG等）
- [ ] expression_tree有根节点（and/or）
- [ ] 所有权重在[-1.0, 1.0]范围内
- [ ] strong_correlation包含关键物理公理
- [ ] 所有10个十神都有权重定义

---

**文档版本**: V3.0  
**最后更新**: 2026-01-03  
**状态**: ✅ 标准化完成

