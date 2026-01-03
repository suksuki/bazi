# FDS-V3.0 云端注入协议 (Cloud Injection Protocol)

**版本**: V3.0  
**对齐文档**: FDS_ARCHITECTURE_v3.0.md, FDS_SOP_v3.0.md  
**状态**: ✅ 标准化

---

## 📋 协议概述

本协议定义了"Step 0: 注入协议"，作为SOP执行的前置检查。虽然不写入SOP正文（保持SOP通用性），但作为SOP的执行前置条件。

---

## 🔄 完整流程

### 协议 0.1: 云端立法 (Cloud Generation)

**执行者**: 架构师 + 云端LLM (Claude/Gemini/GPT-4)

**动作**:
1. 使用 `CLOUD_KMS_STANDARD_PROMPT.md` 中的标准Prompt
2. 替换格局名称和相关信息
3. 发送给云端LLM生成JSON

**校验清单**:
- [ ] `meta_info.category` 是否为 `WEALTH`, `POWER`, `TALENT`, `SELF` 之一
- [ ] `tensor_mapping_matrix.ten_gods` 是否使用标准代码（ZG, PG, ZC, PC, ZS, PS, ZR, PR, ZB, PB）
- [ ] 禁止使用旧代码（EG, IR, DO等）
- [ ] 所有权重在 [-1.0, 1.0] 范围内
- [ ] `expression_tree` 有根节点（and/or）
- [ ] JSON格式有效

**输出**: 符合FDS-V3.0规范的 `pattern_manifest.json`

---

### 协议 0.2: 物理隔离 (Physical Isolation)

**执行者**: 系统管理员

**动作**:
1. 将生成的JSON保存至项目目录：
   ```
   ./config/patterns/manifest_[pattern_id].json
   ```
   例如: `./config/patterns/manifest_B-01.json`

2. **原则**: 
   - 此文件一旦保存，即视为"只读"的法律文件
   - SOP运行时的代码**严禁**修改此文件内容
   - 如需修改，必须重新生成并替换文件

**文件命名规范**:
- 格式: `manifest_[pattern_id].json`
- 示例: `manifest_B-01.json`, `manifest_A-03.json`

---

### 协议 0.3: SOP 启动 (SOP Initiation)

**执行者**: SOP执行引擎

**动作**:
1. 调用SOP主程序时，必须通过参数传入配置文件路径：
   ```bash
   python fds_sop_runner.py --manifest ./config/patterns/manifest_B-01.json
   ```

2. **对齐**: 这完全满足 `FDS_SOP_v3.0.md` 中"核心依赖声明"的要求

**SOP验证**:
- Step 0: 检查配置文件是否存在
- Step 0: 验证配置文件格式
- Step 0: 加载 `classical_logic_rules` 和 `tensor_mapping_matrix`
- 如果验证失败，SOP流程终止并报错

---

## 📊 协议对齐检查

### 与FDS_ARCHITECTURE_v3.0.md对齐

- ✅ Schema定义完全匹配
- ✅ 十神代码使用标准格式
- ✅ 维度定义一致（E, O, M, S, R）
- ✅ 权重范围一致（[-1.0, 1.0]）

### 与FDS_SOP_v3.0.md对齐

- ✅ 满足"核心依赖声明"要求
- ✅ 配置文件作为外部输入
- ✅ SOP代码不包含硬编码逻辑

### 与FDS_KMS_SPEC_v1.0-BETA.md对齐

- ✅ 生成符合规范的manifest
- ✅ 包含完整的逻辑规则和物理映射
- ✅ 格式符合JSONLogic标准

---

## 🎯 执行示例

### 完整流程示例

```bash
# Step 0.1: 云端生成（使用Claude/Gemini）
# 发送标准Prompt，获得JSON输出

# Step 0.2: 保存配置文件
mkdir -p config/patterns
cp generated_manifest.json config/patterns/manifest_B-01.json

# Step 0.3: 运行SOP
python fds_sop_runner.py --manifest config/patterns/manifest_B-01.json
```

---

## ✅ 验收标准

### 配置文件验收

- [ ] JSON格式有效
- [ ] 符合FDS_ARCHITECTURE_v3.0.md第六章Schema
- [ ] 十神代码使用标准格式
- [ ] 逻辑规则格式正确（JSONLogic）
- [ ] 权重矩阵完整（10神×5维）
- [ ] 强相关标记正确

### SOP集成验收

- [ ] SOP能够正确加载配置文件
- [ ] 逻辑规则能够正确执行
- [ ] 权重矩阵能够正确初始化
- [ ] 强相关权重能够正确锁定

---

## 📝 注意事项

1. **版本控制**: 配置文件应纳入版本控制，但标记为"只读"
2. **备份**: 生成新配置前，备份旧配置
3. **验证**: 每次生成后，必须运行SOP模拟器验证
4. **文档**: 记录每个配置文件的生成来源和日期

---

## 🔗 相关文档

- `CLOUD_KMS_STANDARD_PROMPT.md` - 标准Prompt模板
- `FDS_ARCHITECTURE_v3.0.md` - Schema定义
- `FDS_SOP_v3.0.md` - SOP执行规范
- `FDS_KMS_SPEC_v1.0-BETA.md` - KMS生成规范

---

**协议版本**: V3.0  
**最后更新**: 2026-01-03  
**状态**: ✅ 标准化完成

