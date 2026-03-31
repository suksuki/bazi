# FDS-KMS 安装指南

## 虚拟环境使用

项目已包含虚拟环境 `venv`，请按以下步骤操作：

### 激活虚拟环境

**Linux/Mac**:
```bash
source venv/bin/activate
```

**Windows**:
```bash
venv\Scripts\activate
```

激活后，命令行提示符前会显示 `(venv)`。

### 安装依赖

在激活虚拟环境后，执行：

```bash
pip install chromadb sentence-transformers
```

### 验证安装

```bash
python -c "import chromadb; from sentence_transformers import SentenceTransformer; print('✅ 依赖安装成功')"
```

### 运行测试

激活虚拟环境后，运行：

```bash
# 1. 索引黄金数据
python kms/scripts/vector_indexer_setup.py

# 2. 测试记忆检索
python kms/scripts/test_memory.py
```

### 退出虚拟环境

```bash
deactivate
```

---

## 完整执行流程

```bash
# 1. 激活虚拟环境
source venv/bin/activate

# 2. 安装依赖（如果未安装）
pip install chromadb sentence-transformers

# 3. 运行第一阶段测试
python kms/scripts/vector_indexer_setup.py
python kms/scripts/test_memory.py

# 4. 运行第二阶段测试（验证Prompt优化）
python kms/scripts/llm_distill_example.py
python kms/scripts/batch_processor.py kms/data/raw_texts/zpzq_shishen.txt --topic "食神格"
```

---

## 常见问题

### Q: 如何确认虚拟环境已激活？

A: 命令行提示符前应该显示 `(venv)`，例如：
```
(venv) jin@JinLaptop:~/bazi_predict$
```

### Q: 如果虚拟环境中没有pip怎么办？

A: 确保使用python3-full：
```bash
sudo apt install python3-full python3-venv
python3 -m venv venv
source venv/bin/activate
```

### Q: 依赖安装失败怎么办？

A: 可以尝试：
1. 升级pip: `pip install --upgrade pip`
2. 使用国内镜像: `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple chromadb sentence-transformers`
3. 检查Python版本: `python --version` (需要3.8+)

