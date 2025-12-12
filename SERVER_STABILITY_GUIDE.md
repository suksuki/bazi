# 服务器稳定性优化指南

## 📋 问题诊断

你的 Bazi 预测系统服务器频繁断线和重载的主要原因：

### 1. **文件监控过于敏感**
- Streamlit 默认监控所有 Python 文件的变化
- 你的应用有后台任务不断写入数据文件和日志
- `data/` 目录、日志文件、缓存文件的变化都可能触发重载

### 2. **后台任务的影响**
- `BackgroundWorker` 每 2 秒检查一次任务队列
- 频繁的数据库读写（SQLite）
- 日志文件的持续写入
- 下载的媒体文件和转录文本的保存

### 3. **配置缺失**
- 没有 `.streamlit/config.toml` 配置文件
- 缺少文件监控的排除规则

---

## 🛠️ 已实施的优化方案

### 1. **Streamlit 配置优化** ✅

创建了 `.streamlit/config.toml` 文件：

```toml
[server]
fileWatcherType = "poll"      # 使用更稳定的轮询模式
runOnSave = true              # 启用热重载（仅代码文件）
scriptTimeout = 600           # 增加脚本超时时间

[runner]
fastReruns = true             # 减少不必要的重载
postScriptGC = true           # 后台任务处理优化
```

**关键改进：**
- `poll` 模式比 `watchdog` 更稳定，减少误触发
- 优化后台任务处理，防止因任务导致的重载

### 2. **文件监控排除规则** ✅

创建了 `.streamlit/.gitignore` 来排除数据文件：

```
data/          # 数据目录
*.db           # 数据库文件
*.log          # 日志文件
venv/          # 虚拟环境
__pycache__/   # 缓存文件
*.mp3, *.mp4   # 媒体文件
```

**注意：** Streamlit 的文件监控主要关注 `.py` 文件，但排除这些目录可以减少系统负载。

### 3. **优化的启动脚本** ✅

创建了 `run_bazi_optimized.sh`：

```bash
# 环境变量优化
export STREAMLIT_SERVER_FILE_WATCHER_TYPE=poll
export STREAMLIT_SERVER_RUN_ON_SAVE=true

# 预创建目录，避免运行时创建触发变化
mkdir -p data/books data/logs data/profiles
```

### 4. **诊断工具** ✅

创建了 `diagnose_stability.py` 用于监控和诊断：

```bash
# 快速诊断
./venv/bin/python diagnose_stability.py

# 持续监控文件变化
./venv/bin/python diagnose_stability.py --monitor
```

---

## 🚀 使用方法

### 方法 1: 使用优化的启动脚本（推荐）

```bash
./run_bazi_optimized.sh
```

### 方法 2: 手动启动（开发模式）

```bash
./venv/bin/streamlit run main.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.fileWatcherType poll
```

### 方法 3: 生产模式（最稳定）

如果你不需要热重载，可以禁用它以获得最大稳定性：

1. 编辑 `.streamlit/config.toml`：
```toml
[server]
runOnSave = false  # 禁用热重载
```

2. 启动服务器：
```bash
./venv/bin/streamlit run main.py \
    --server.headless=true \
    --server.fileWatcherType none
```

---

## 🔍 进一步优化建议

### 1. **如果仍然频繁重载**

运行诊断工具找出具体原因：

```bash
# 在一个终端运行服务器
./run_bazi_optimized.sh

# 在另一个终端运行监控
./venv/bin/python diagnose_stability.py --monitor
```

观察哪些文件变化导致重载，然后针对性优化。

### 2. **优化后台任务检查间隔**

如果发现重载仍然频繁，可以增加 `scheduler.py` 中的检查间隔：

```python
# core/scheduler.py, line 9
def __init__(self, check_interval=2):  # 改为 5 或 10
```

### 3. **使用进程分离**

将后台任务移到单独的进程中运行：

```bash
# 终端 1: 运行 Streamlit UI
./venv/bin/streamlit run main.py

# 终端 2: 运行后台任务
./venv/bin/python -c "from core.scheduler import BackgroundWorker; w=BackgroundWorker(); w.start(); import time; time.sleep(99999)"
```

然后在 `main.py` 中注释掉后台任务启动代码（第 95-103 行）。

### 4. **数据库优化**

考虑使用 SQLite 的 WAL 模式减少文件锁定：

```python
# learning/db.py
conn = sqlite3.connect('data/learning.db')
conn.execute('PRAGMA journal_mode=WAL')  # 添加这行
```

### 5. **日志优化**

减少日志写入频率：

- 使用内存缓冲，定期批量写入
- 或者使用系统日志（syslog）而非文件日志

---

## 📊 性能监控

### 检查服务器状态

```bash
# 查看 Streamlit 进程
ps aux | grep streamlit

# 查看最近的日志
tail -f server.log

# 检查文件变化
./venv/bin/python diagnose_stability.py
```

### 常见问题排查

| 症状 | 可能原因 | 解决方案 |
|------|---------|---------|
| 每 2 秒重载一次 | 后台任务写入文件 | 增加 check_interval |
| 点击按钮后重载 | 配置文件被修改 | 检查 ConfigManager 调用 |
| 不规则重载 | 用户上传/下载文件 | 确保临时文件在 data/ 目录 |
| 启动时多次重载 | 导入时的副作用 | 使用 @st.cache_resource |

---

## 🎯 推荐配置

根据你的使用场景选择：

### 开发环境（需要热重载）
```toml
[server]
runOnSave = true
fileWatcherType = "poll"
```

### 演示环境（稳定性优先）
```toml
[server]
runOnSave = false
fileWatcherType = "none"
```

### 生产环境（最高稳定性）
```bash
# 使用 Docker 或 systemd 服务
# 禁用所有文件监控
streamlit run main.py --server.headless=true --server.fileWatcherType none
```

---

## 📝 总结

已为你实现的优化：

1. ✅ 创建了优化的 Streamlit 配置文件
2. ✅ 设置了文件监控排除规则
3. ✅ 提供了优化的启动脚本
4. ✅ 创建了诊断工具

**下一步行动：**

1. 使用 `./run_bazi_optimized.sh` 启动服务器
2. 观察是否仍有频繁重载
3. 如果有问题，运行 `./venv/bin/python diagnose_stability.py --monitor` 诊断
4. 根据诊断结果进一步调整配置

---

## 🆘 如果问题仍未解决

1. 收集诊断信息：
   ```bash
   ./venv/bin/python diagnose_stability.py > diagnosis.txt
   ```

2. 查看详细日志，找出重载前的最后操作

3. 考虑临时禁用热重载（`runOnSave = false`）确认是否是文件监控问题

4. 检查是否有其他进程在修改项目文件（如 IDE 的自动保存、Git 操作等）

祝服务器稳定运行！🎉
