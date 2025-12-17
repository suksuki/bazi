#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行 APP 的脚本
==============

快速启动八字预测系统的 Streamlit 应用

使用方法:
    python run_app.py

或者:
    chmod +x run_app.py
    ./run_app.py
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """主函数：启动 Streamlit 应用"""
    
    # 获取项目根目录
    project_root = Path(__file__).parent.absolute()
    os.chdir(project_root)
    
    print("=" * 60)
    print("🚀 启动八字预测系统 (Bazi Prediction System)")
    print("=" * 60)
    print()
    
    # 检查虚拟环境
    venv_path = project_root / "venv"
    if not venv_path.exists():
        print("⚠️  警告: 未找到虚拟环境 (venv/)")
        print("   请先创建虚拟环境: python3 -m venv venv")
        print()
        use_venv = False
    else:
        use_venv = True
        print("✅ 找到虚拟环境")
    
    # 检查 main.py
    main_py = project_root / "main.py"
    if not main_py.exists():
        print("❌ 错误: 未找到 main.py")
        sys.exit(1)
    
    print("✅ 找到主程序: main.py")
    print()
    
    # 设置环境变量
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'
    env['STREAMLIT_SERVER_FILE_WATCHER_TYPE'] = 'poll'
    env['STREAMLIT_SERVER_RUN_ON_SAVE'] = 'true'
    env['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    
    # 获取 WSL IP（如果在 WSL 中）
    try:
        import socket
        hostname = socket.gethostname()
        wsl_ip = socket.gethostbyname(hostname)
    except:
        wsl_ip = "localhost"
    
    print("🌐 访问地址:")
    print(f"   - 本地: http://localhost:8501")
    if wsl_ip != "localhost":
        print(f"   - 网络: http://{wsl_ip}:8501")
    print()
    print("💡 提示: 按 Ctrl+C 停止服务器")
    print("=" * 60)
    print()
    
    # 构建启动命令
    if use_venv:
        streamlit_cmd = str(venv_path / "bin" / "streamlit")
    else:
        streamlit_cmd = "streamlit"
    
    cmd = [
        streamlit_cmd,
        "run",
        "main.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0",
        "--server.fileWatcherType", "poll"
    ]
    
    # 启动 Streamlit
    try:
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\n\n✅ 服务器已停止")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 启动失败: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n❌ 错误: 未找到 streamlit 命令")
        print("   请先安装依赖: pip install streamlit")
        sys.exit(1)

if __name__ == '__main__':
    main()

