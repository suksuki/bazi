# Shell 脚本整理总结

## 📋 整理完成时间
2025-01-XX

## 🎯 整理目标
1. 按功能分类组织脚本
2. 统一脚本格式和风格
3. 创建使用文档
4. 提供快捷启动方式

## 📁 新的目录结构

```
scripts/
├── launch/              # 应用启动脚本 (6个)
│   ├── start.sh                    # WSL稳定启动（推荐）
│   ├── run_bazi.sh                 # 基础启动
│   ├── run_bazi_stable.sh          # 稳定模式（进程分离）
│   ├── run_bazi_wsl.sh             # WSL2专用
│   ├── run_bazi_optimized.sh       # 优化模式
│   └── run_bazi_stable_fixed.sh    # 稳定修复版
│
├── evolution/           # 自动进化训练脚本 (9个)
│   ├── start_evolution.sh          # 启动训练
│   ├── restart_evolution.sh         # 重启训练
│   ├── stop_evolution.sh            # 停止训练
│   ├── check_evolution_status.sh    # 检查状态
│   ├── monitor_evolution.sh         # 监控训练
│   ├── view_evolution.sh             # 查看日志
│   ├── preflight_check.sh            # 发射前检查
│   ├── restart_v51.sh                # 重启V51版本
│   └── restart_v53_step1.sh          # 重启V53 Step1
│
├── git/                 # Git操作脚本 (5个)
│   ├── git_push_safe.sh             # 安全推送
│   ├── resolve_git_all.sh           # 解决所有Git问题
│   ├── fix_git_refs.sh              # 修复Git引用
│   ├── fix_git_history.sh           # 修复Git历史
│   └── force_push.sh                # 强制推送工具
│
├── utils/               # 工具和检查脚本 (8个)
│   ├── check_startup.sh             # 启动前诊断
│   ├── check_evolution.sh            # 检查进化状态
│   ├── check_params_status.sh        # 检查参数状态
│   ├── check_step_status.sh          # 检查训练阶段
│   ├── run_in_wsl.sh                # WSL执行包装
│   ├── run_without_warning.sh        # 无警告运行
│   ├── train_wrapper.sh             # 训练包装器
│   └── start_miner.sh               # 启动挖矿服务
│
├── README.md            # 使用指南
└── ORGANIZATION.md      # 本文档
```

## 🔗 根目录快捷脚本

为了便于使用，在根目录保留了以下快捷脚本：

- `start.sh` → `scripts/launch/start.sh`
- `run_bazi.sh` → `scripts/launch/run_bazi.sh`
- `check_startup.sh` → `scripts/utils/check_startup.sh`
- `start_evolution.sh` → `scripts/evolution/start_evolution.sh`
- `check_evolution.sh` → `scripts/utils/check_evolution.sh`

## ✅ 完成的整理工作

### 1. 目录分类
- ✅ 创建了 4 个功能目录：launch, evolution, git, utils
- ✅ 将所有脚本移动到对应目录
- ✅ 保持了脚本的原有功能

### 2. 格式统一
- ✅ 为所有脚本添加了 `#!/bin/bash` shebang（修复了 run_bazi.sh）
- ✅ 统一了注释风格
- ✅ 添加了执行权限

### 3. 文档创建
- ✅ 创建了 `scripts/README.md` 详细使用指南
- ✅ 创建了 `scripts/ORGANIZATION.md` 整理总结
- ✅ 每个脚本都有功能说明和使用示例

### 4. 快捷方式
- ✅ 在根目录创建了常用脚本的快捷方式
- ✅ 使用 `exec` 确保正确传递参数

## 📊 脚本统计

- **总脚本数**: 28 个
- **启动脚本**: 6 个
- **进化训练脚本**: 9 个
- **Git 脚本**: 5 个
- **工具脚本**: 8 个

## 🔍 脚本功能分类

### 启动类脚本
用于启动 Bazi 应用系统，支持多种模式：
- WSL 环境优化
- 进程分离模式
- 文件监控配置
- 热重载控制

### 进化训练类脚本
用于自动进化训练系统：
- 启动/停止/重启训练
- 状态监控和日志查看
- 参数检查和验证
- 版本特定启动

### Git 操作类脚本
用于 Git 版本控制操作：
- 安全推送（带检查）
- 冲突解决
- 引用修复
- 强制推送工具

### 工具类脚本
各种实用工具：
- 环境检查
- 状态诊断
- WSL 包装器
- 服务启动

## 🚀 使用建议

### 日常开发
```bash
# WSL 环境（推荐）
bash scripts/launch/start.sh

# 或使用快捷方式
bash start.sh
```

### 自动进化训练
```bash
# 1. 检查环境
bash scripts/evolution/preflight_check.sh

# 2. 启动训练
bash scripts/evolution/start_evolution.sh

# 3. 监控训练
bash scripts/evolution/monitor_evolution.sh
```

### Git 操作
```bash
# 安全推送
bash scripts/git/git_push_safe.sh

# 解决所有问题
bash scripts/git/resolve_git_all.sh
```

## 📝 后续改进建议

1. **脚本标准化**
   - 统一错误处理模式
   - 添加日志记录功能
   - 统一配置管理

2. **功能增强**
   - 添加脚本参数验证
   - 支持配置文件
   - 添加单元测试

3. **文档完善**
   - 添加更多使用示例
   - 创建故障排除指南
   - 添加最佳实践

## ⚠️ 注意事项

1. **路径依赖**: 所有脚本假设在项目根目录执行
2. **虚拟环境**: 确保 `venv/` 目录存在
3. **权限**: 所有脚本已添加执行权限
4. **兼容性**: WSL 相关脚本会检测环境

## 🔄 维护指南

### 添加新脚本
1. 确定脚本功能分类
2. 放入对应的目录（launch/evolution/git/utils）
3. 添加 `#!/bin/bash` shebang
4. 添加功能注释
5. 更新 `scripts/README.md`

### 修改现有脚本
1. 保持向后兼容
2. 更新相关文档
3. 测试脚本功能

### 删除脚本
1. 确认脚本不再使用
2. 从文档中移除
3. 删除文件

## 📚 相关文档

- `scripts/README.md` - 详细使用指南
- 项目根目录 `README.md` - 项目总体说明

---

**整理完成**: 所有脚本已按功能分类组织，格式统一，文档完善。

