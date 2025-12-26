---
description: 新增物理模型同步清单 (New Pattern Sync Checklist)
---
# 新增物理模型同步清单

当新增一个物理模型/专题时，必须同步更新以下文件：

## 必须更新的文件

### 1. 算法实现
// turbo
- [ ] `core/trinity/core/engines/pattern_scout.py`
  - 在 `_deep_audit()` 方法中添加 `if pattern_id == "PATTERN_NAME":` 分支
  - 返回包含 `chart`, `category`, `stress`/`sai`, `label` 等标准字段

### 2. 注册模块
// turbo
- [ ] `core/logic_manifest.json`
  - 在 `modules` 下添加 `MOD_XXX_PATTERN_NAME` 条目
  - 包含: id, name, icon, theme, type, version, description, goal, outcome, linked_rules, linked_metrics, formula, parameters, data_evidence, class, status

### 3. UI 轨道配置
// turbo
- [ ] `ui/pages/quantum_simulation.py`
  - 在 `track_labels` 字典中添加条目: `"PATTERN_ID": "🔥 中文名 (CODE)"`
  - 在 `track_names` 字典中添加条目 (full_pipeline_scan 部分)
  - 在 Phase 1 海选逻辑中添加 `elif track_id == "PATTERN_ID":` 分支

### 4. 技术文档
// turbo
- [ ] `docs/PATTERN_PHASE1_REPORT.md`
  - 包含: 判据、能量公式、扫描结果、发现

## 标准字段

### pattern_scout.py 返回字典必须包含:
```python
{
    "chart": chart,
    "category": str,          # 分类判定
    "stress": str or "sai": str,  # SAI 应力值
    "label": str,             # 八字标签
    "audit_mode": str,        # 审计模式名称
    # ... 其他专题特定字段
}
```

### logic_manifest.json 必须包含:
```json
{
    "id": "MOD_XXX_NAME",
    "name": "🔥 中文名 (CODE)",
    "version": "X.0",
    "description": "[VX.0] 简述",
    "status": "CALIBRATED"
}
```

## 当前已注册模型

| ID | 名称 | 版本 | pattern_scout | logic_manifest | UI |
|----|------|------|---------------|----------------|-----|
| SHANG_GUAN_JIAN_GUAN | 伤官见官 | V3.0 | ✅ | ✅ MOD_101 | ✅ |
| SHANG_GUAN_SHANG_JIN | 伤官伤尽 | V2.0 | ✅ | ✅ MOD_104 | ✅ |
| YANG_REN_JIA_SHA | 羊刃架杀 | V1.0 | ✅ | ✅ MOD_105 | ✅ |
| XIAO_SHEN_DUO_SHI | 枭神夺食 | V1.0 | ✅ | ✅ MOD_106 | ✅ |
| PGB_SUPER_FLUID_LOCK | 超流锁定 | V1.0 | ✅ | ✅ MOD_102 | ✅ |
| PGB_BRITTLE_TITAN | 脆性巨人 | V1.0 | ✅ | ✅ MOD_103 | ✅ |


// turbo-all
