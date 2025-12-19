# V10.2 自动调优系统安装指南

**版本**: V10.2  
**状态**: ✅ 安装说明已更新

---

## 📦 依赖安装

### 1. 激活虚拟环境

项目已经配置了虚拟环境（`venv/`），请先激活：

```bash
source venv/bin/activate
```

### 2. 安装依赖

V10.2自动调优系统需要以下依赖：

```bash
# 安装所有依赖（包括optuna）
pip install -r requirements.txt

# 或者只安装optuna
pip install optuna
```

### 3. 验证安装

```bash
# 检查optuna是否安装成功
python3 -c "import optuna; print('✅ Optuna版本:', optuna.__version__)"
```

---

## 🧪 运行测试

### 运行完整测试套件

```bash
# 在虚拟环境中
source venv/bin/activate
python3 tests/test_v10_2_auto_tuning.py
```

### 运行特定测试

```bash
# 使用pytest（如果已安装）
pytest tests/test_v10_2_auto_tuning.py -v

# 运行特定测试类
pytest tests/test_v10_2_auto_tuning.py::TestMCPTuningServer -v
```

---

## 🚀 运行自动调优

### 快速测试（Phase 1）

```bash
source venv/bin/activate
python3 scripts/v10_2_auto_driver.py --mode phase1 --phase1-trials 20
```

### 完整自动调优

```bash
source venv/bin/activate
python3 scripts/v10_2_auto_driver.py --mode auto \
    --phase1-trials 50 \
    --phase2-trials 50 \
    --phase3-trials 50
```

---

## ⚠️ 常见问题

### 问题1: "externally-managed-environment" 错误

**原因**: Python 3.12+的系统保护机制，不允许直接在系统Python中安装包。

**解决**: 使用虚拟环境（项目已有`venv/`目录）：

```bash
# 激活虚拟环境
source venv/bin/activate

# 然后再安装
pip install optuna
```

### 问题2: 虚拟环境不存在

**解决**: 创建虚拟环境：

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 问题3: 测试失败 - "Optuna未安装"

**说明**: 这是正常的。如果未安装optuna，相关测试会被自动跳过。

**解决**: 按照上述步骤安装optuna。

---

## 📚 相关文档

- **架构文档**: `docs/V10_2_AUTO_TUNING_ARCHITECTURE.md`
- **测试文档**: `docs/V10_2_AUTO_TUNING_TESTING.md`
- **调优结果**: `docs/V10_STRENGTH_TUNING_RESULTS_NEW_DATASET.md`

---

**维护者**: Bazi Predict Team  
**最后更新**: 2025-01-XX

