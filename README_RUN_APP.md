# 运行 APP 的脚本

## 📋 快速启动

### 方法 1: Python 脚本（推荐）

```bash
python run_app.py
```

或者：

```bash
chmod +x run_app.py
./run_app.py
```

### 方法 2: Shell 脚本

```bash
chmod +x run_app.sh
./run_app.sh
```

### 方法 3: 使用现有的启动脚本

```bash
# 使用 start.sh（推荐，已优化）
./start.sh

# 或使用 run_bazi.sh
./run_bazi.sh
```

## 🌐 访问地址

启动后，在浏览器中访问：

- **本地访问**: http://localhost:8501
- **网络访问**: http://<WSL_IP>:8501（如果在 WSL 中）

## ⚙️ 配置说明

脚本会自动设置以下环境变量：

- `PYTHONUNBUFFERED=1`: 实时输出日志
- `STREAMLIT_SERVER_FILE_WATCHER_TYPE=poll`: 使用 poll 模式（更稳定）
- `STREAMLIT_SERVER_RUN_ON_SAVE=true`: 启用热重载
- `STREAMLIT_BROWSER_GATHER_USAGE_STATS=false`: 禁用使用统计

## 🛠️ 故障排除

### 1. 虚拟环境不存在

如果提示"未找到虚拟环境"，请先创建：

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Streamlit 未安装

如果提示"未找到 streamlit 命令"，请安装：

```bash
pip install streamlit
```

### 3. 端口被占用

如果 8501 端口被占用，可以修改脚本中的端口号：

```python
# 在 run_app.py 中修改
"--server.port", "8502",  # 改为其他端口
```

### 4. 权限问题

如果脚本无法执行，请添加执行权限：

```bash
chmod +x run_app.py
chmod +x run_app.sh
```

## 📝 注意事项

1. **首次运行**: 可能需要安装依赖，请运行 `pip install -r requirements.txt`
2. **WSL 环境**: 如果在 WSL 中运行，可以使用网络 IP 从 Windows 浏览器访问
3. **停止服务器**: 按 `Ctrl+C` 停止服务器

## 🔗 相关文件

- `main.py`: Streamlit 主程序入口
- `start.sh`: 优化的启动脚本（推荐）
- `run_bazi.sh`: 基础启动脚本
- `scripts/launch/`: 更多启动脚本选项

