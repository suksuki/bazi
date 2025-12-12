# WSL 环境下服务器稳定性问题及解决方案

## 🔍 根本原因分析

### 1. **YouTube视频大量处理 - 主要原因** ⚠️

你的怀疑是对的！视频处理会导致频繁重载：

#### 文件写入热点：
```
data/video_history.txt  # 每完成一个视频就写入一次（第209行）
data/books/[Video]*.txt # 每个视频转录后保存
data/logs/task_errors.log # 任务错误日志
learning.db             # SQLite数据库频繁更新
```

#### 具体影响：
- **每处理一个视频**都会：
  1. 写入 `video_history.txt`（1次）
  2. 保存转录文本到 `data/books/`（1次）
  3. 更新数据库状态（多次）
  4. 如果有进度更新，每个chunk写入数据库（N次）

- **当你批量读取YouTube频道时**：
  - 10个视频 = 至少30-50次文件写入操作
  - 100个视频 = 300-500次文件写入！

### 2. **WSL2 文件系统问题 - 放大因素** 🔥

WSL2的文件监控特别敏感：

#### WSL2 特有问题：
1. **跨文件系统监控延迟**：如果项目在 `/mnt/c/` (Windows) 下
   - 文件监控延迟高
   - 更容易触发误报
   
2. **inotify事件放大**：
   - WSL2的文件系统层会放大文件变化事件
   - 一次写入可能触发多个inotify事件

3. **IDE文件监控冲突**：
   - VSCode在Windows和WSL两边都监控文件
   - 双重监控导致事件风暴

### 3. **IDE稳定性问题** 💥

你提到的IDE crash也很有可能：
- VSCode Remote-WSL扩展可能不稳定
- 文件监控占用过多资源导致IDE卡死
- 当有太多文件变化时，IDE可能崩溃

---

## 🛠️ 针对性解决方案

### 方案A：分离数据目录（推荐）⭐

**将频繁写入的data目录移到WSL文件系统外**：

```bash
# 1. 在WSL home目录创建数据目录（不被文件监控监控）
mkdir -p ~/bazi_data_external

# 2. 移动现有数据
cp -r data/* ~/bazi_data_external/

# 3. 创建符号链接（可选，或者修改代码路径）
rm -rf data
ln -s ~/bazi_data_external data
```

**优势**：
- ✅ data目录的变化不会触发Streamlit监控
- ✅ 视频处理再多也不会导致重载
- ✅ 性能提升（WSL本地文件系统更快）

### 方案B：优化video_history写入策略 🔧

修改 `video_miner.py` 减少写入频率：
