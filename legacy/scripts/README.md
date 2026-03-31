# Shell 脚本使用指南

本文档说明项目中所有 Shell 脚本的用途和使用方法。

## 📁 目录结构

```
scripts/
├── launch/          # 应用启动脚本
├── evolution/       # 自动进化训练脚本
├── git/             # Git 操作脚本
├── utils/           # 工具和检查脚本
└── README.md        # 本文档
```

## 🚀 应用启动脚本 (scripts/launch/)

### start.sh
**WSL 稳定启动脚本** - 推荐在 WSL 环境下使用
- 解决视频处理导致的频繁重载问题
- 使用 poll 模式文件监控
- 自动清理旧进程
- 显示 WSL IP 地址

```bash
bash scripts/launch/start.sh
```

### run_bazi_stable.sh
**稳定模式启动** - 进程分离模式
- 将 UI 和 Worker 分离为独立进程
- 解决 "Reload Window" OOM 崩溃问题
- 后台运行 Worker 服务

```bash
bash scripts/launch/run_bazi_stable.sh
```

### run_bazi_wsl.sh
**WSL2 专用启动脚本** - 最大化稳定性
- 针对 WSL2 文件系统优化
- 完全禁用文件监控（生产模式）
- 支持外部数据目录迁移

```bash
bash scripts/launch/run_bazi_wsl.sh
```

### run_bazi_optimized.sh
**优化模式启动** - 平衡性能和稳定性
- 使用 poll 模式文件监控
- 启用热重载（仅代码文件）
- 忽略数据目录变化

```bash
bash scripts/launch/run_bazi_optimized.sh
```

### run_bazi.sh
**基础启动脚本** - 简单快速启动
- 自动安装依赖
- 清理旧进程
- 基础配置

```bash
bash scripts/launch/run_bazi.sh
```

### run_bazi_stable_fixed.sh
**稳定修复版启动** - 与 run_bazi_stable.sh 类似
- 进程分离模式
- 改进的错误处理

```bash
bash scripts/launch/run_bazi_stable_fixed.sh
```

## 🔬 自动进化训练脚本 (scripts/evolution/)

### start_evolution.sh
**启动自动进化训练**
- 检查是否已在运行
- 后台运行 auto_evolve.py
- 输出日志到 evolution.log

```bash
bash scripts/evolution/start_evolution.sh
```

### restart_evolution.sh
**重启自动进化训练**
- 停止旧进程
- 检查参数范围更新
- 启动新进程

```bash
bash scripts/evolution/restart_evolution.sh
```

### stop_evolution.sh
**停止自动进化训练**
- 查找所有 auto_evolve.py 进程
- 优雅停止，必要时强制停止

```bash
bash scripts/evolution/stop_evolution.sh
```

### check_evolution_status.sh
**检查进化训练状态**
- 显示进程信息（PID、运行时间、CPU、内存）
- 显示日志文件信息
- 提取关键指标（准确率、迭代次数）

```bash
bash scripts/evolution/check_evolution_status.sh
```

### monitor_evolution.sh
**监控进化训练**
- 实时显示关键指标
- 显示最新日志
- 参数文件修改时间

```bash
bash scripts/evolution/monitor_evolution.sh
```

### view_evolution.sh
**查看实时日志**
- 使用 tail -f 实时显示日志
- 按 Ctrl+C 退出

```bash
bash scripts/evolution/view_evolution.sh
```

### preflight_check.sh
**发射前检查**
- 检查备份文件
- 检查必要文件
- 检查 Git 状态
- 检查 Python 环境
- 显示配置摘要

```bash
bash scripts/evolution/preflight_check.sh
```

### restart_v51.sh
**重启 V51.0 版本**
- 停止旧进程
- 启动 V52.0 Fine-Tuning Mode
- 锁定核心参数，只调整边缘参数

```bash
bash scripts/evolution/restart_v51.sh
```

### restart_v53_step1.sh
**重启 V53.0 Step 1**
- 停止旧进程
- 启动 Foundation Locking Tuning
- 仅优化基础物理层

```bash
bash scripts/evolution/restart_v53_step1.sh
```

## 🔧 Git 操作脚本 (scripts/git/)

### git_push_safe.sh
**安全 Git 推送**
- 检查未提交的更改
- 检查本地和远程差异
- 显示将要推送的提交
- 交互式确认
- 30秒超时保护

```bash
bash scripts/git/git_push_safe.sh
```

### resolve_git_all.sh
**解决所有 Git 问题**
- 检查并拉取远程最新状态
- 合并远程更改
- 添加所有修改的文件
- 提交并推送

```bash
bash scripts/git/resolve_git_all.sh
```

### fix_git_refs.sh
**修复 Git 引用**
- 清理并重新获取远程引用
- 自动设置 origin/HEAD
- 检查本地分支跟踪

```bash
bash scripts/git/fix_git_refs.sh
```

### fix_git_history.sh
**修复 Git 历史**
- 检查当前 Git 状态
- 获取远程最新状态
- 检查合并冲突
- 显示差异统计

```bash
bash scripts/git/fix_git_history.sh
```

### force_push.sh
**强制推送工具**
- 提供多种强制推送选项
- 从最安全到最暴力
- 交互式选择

```bash
bash scripts/git/force_push.sh
```

## 🛠️ 工具和检查脚本 (scripts/utils/)

### check_startup.sh
**启动前诊断**
- 检查虚拟环境
- 检查 Python 路径
- 检查关键依赖
- 检查端口占用
- 测试导入 main.py

```bash
bash scripts/utils/check_startup.sh
```

### check_evolution.sh
**检查进化脚本状态**
- 检查进程状态
- 检查日志文件
- 显示最新日志

```bash
bash scripts/utils/check_evolution.sh
```

### check_params_status.sh
**检查参数调整状态**
- 检查进程状态
- 显示当前参数值
- 检查参数范围
- 参数使用情况分析

```bash
bash scripts/utils/check_params_status.sh
```

### check_step_status.sh
**检查训练阶段状态**
- 检查运行中的进程
- 检查命令行参数
- 显示日志中的阶段信息

```bash
bash scripts/utils/check_step_status.sh
```

### run_in_wsl.sh
**WSL 执行包装脚本**
- 切换到正确目录
- 激活虚拟环境
- 执行传入的命令

```bash
wsl -e bash scripts/utils/run_in_wsl.sh <command>
```

### run_without_warning.sh
**无警告运行脚本**
- 过滤 WSL 路径警告
- 激活虚拟环境
- 执行命令

```bash
bash scripts/utils/run_without_warning.sh <script> [args...]
```

### train_wrapper.sh
**训练脚本包装器**
- 切换到项目目录
- 激活虚拟环境
- 执行训练脚本

```bash
bash scripts/utils/train_wrapper.sh [args...]
```

### start_miner.sh
**启动挖矿服务**
- 启动 Antigravity Miner Service
- 处理后台任务（视频下载、理论挖掘、模型训练）

```bash
bash scripts/utils/start_miner.sh
```

## 📋 快捷启动脚本（根目录）

为了便于使用，在根目录创建了快捷启动脚本：

- `start.sh` → `scripts/launch/start.sh`
- `run_bazi.sh` → `scripts/launch/run_bazi.sh`
- `check_startup.sh` → `scripts/utils/check_startup.sh`
- `start_evolution.sh` → `scripts/evolution/start_evolution.sh`
- `check_evolution.sh` → `scripts/utils/check_evolution.sh`

## 🔍 脚本选择指南

### 日常开发
- **WSL 环境**: `scripts/launch/start.sh` 或 `scripts/launch/run_bazi_wsl.sh`
- **Linux 环境**: `scripts/launch/run_bazi_stable.sh`
- **需要热重载**: `scripts/launch/run_bazi_optimized.sh`

### 生产环境
- **WSL**: `scripts/launch/run_bazi_wsl.sh` (完全禁用文件监控)
- **Linux**: `scripts/launch/run_bazi_stable.sh` (进程分离模式)

### 自动进化训练
1. **首次运行**: `bash scripts/evolution/preflight_check.sh` (检查环境)
2. **启动训练**: `bash scripts/evolution/start_evolution.sh`
3. **监控训练**: `bash scripts/evolution/monitor_evolution.sh`
4. **查看日志**: `bash scripts/evolution/view_evolution.sh`
5. **停止训练**: `bash scripts/evolution/stop_evolution.sh`

### Git 操作
- **安全推送**: `bash scripts/git/git_push_safe.sh`
- **解决冲突**: `bash scripts/git/resolve_git_all.sh`
- **修复引用**: `bash scripts/git/fix_git_refs.sh`
- **强制推送**: `bash scripts/git/force_push.sh`

## ⚠️ 注意事项

1. **路径问题**: 所有脚本假设在项目根目录执行，或使用绝对路径 `/home/jin/bazi_predict`
2. **虚拟环境**: 大部分脚本会自动激活虚拟环境，确保 `venv/` 目录存在
3. **权限问题**: 确保脚本有执行权限: `chmod +x scripts/**/*.sh`
4. **WSL 环境**: WSL 相关脚本会检测环境，在其他环境可能不是最优

## 🔄 脚本维护

- 所有脚本应包含 `#!/bin/bash` shebang
- 使用 `set -e` 在遇到错误时退出（可选）
- 使用 `cd "$(dirname "$0")/.."` 或绝对路径确保目录正确
- 添加适当的错误处理和用户提示
- 使用有意义的变量名和注释

## 📝 更新日志

- **2025-01-XX**: 初始整理，按功能分类组织脚本
- 创建快捷启动脚本在根目录
- 统一脚本格式和注释

