# Git 引用修复总结

## 问题诊断

从 GitLens 日志中发现两个核心问题：

### 问题 1: origin/HEAD 不是符号引用 ✅ 已修复

**症状**：
```
fatal: ref refs/remotes/origin/HEAD is not a symbolic ref
ENOENT ... .git\refs\remotes\origin\main
```

**原因**：
- 远程仓库的默认分支信息（origin/HEAD）没有在本地正确记录
- VS Code 假设存在 `origin/main`，但本地引用文件缺失

**修复命令**：
```bash
git fetch --all --prune
git remote set-head origin -a
```

**验证**：
```bash
git symbolic-ref refs/remotes/origin/HEAD
# 应返回: refs/remotes/origin/main
```

### 问题 2: 未跟踪文件的 git show 错误 ⚠️ 需处理

**症状**：
```
git show --textconv :scripts/auto_evolve.py
File not found - git:/.../scripts/auto_evolve.py.git?...
```

**原因**：
- 这些文件是未跟踪的新文件
- VS Code 的 diff/历史视图使用 `git show :路径` 读取暂存区版本
- 未暂存的文件会导致 "File not found"

**解决方案**：

#### 选项 A: 添加到版本控制（推荐）
```bash
git add scripts/auto_evolve.py scripts/auto_tune_val005.py scripts/debug_outliers.py scripts/train_wrapper.sh
git commit -m "chore: add new scripts"
```

#### 选项 B: 添加到 .gitignore
如果这些是临时文件或不想提交：
```bash
echo "scripts/auto_evolve.py" >> .gitignore
echo "scripts/auto_tune_val005.py" >> .gitignore
# ... 等等
```

## 修复结果

### ✅ 已修复

1. **origin/HEAD 符号引用**：
   - ✅ `origin/HEAD set to main`
   - ✅ `git symbolic-ref` 返回正确值

2. **远程分支跟踪**：
   - ✅ `main` 分支正确跟踪 `origin/main`
   - ✅ 远程引用文件已创建

3. **远程配置**：
   - ✅ HEAD branch: main
   - ✅ Remote branch: main tracked

### ⚠️ 待处理

1. **未跟踪文件**：
   - 需要决定是提交还是忽略这些文件
   - 建议：提交重要的脚本，忽略临时文件

## 预防措施

### 1. 使用 WSL 路径（推荐）

如果使用 WSL，建议：
- 在 VS Code 中使用 **Remote - WSL** 扩展
- 直接打开 WSL 路径：`\\wsl$\Ubuntu\home\jin\bazi_predict`
- 避免使用 Windows 映射路径：`Z:\home\jin\bazi_predict`

### 2. 关闭自动 Fetch（可选）

如果频繁的自动 fetch 造成问题：
- VS Code 设置 → 搜索 "Git: Auto Fetch"
- 设置为 `false` 或 `off`

### 3. 定期清理引用

定期运行：
```bash
git fetch --all --prune
git remote set-head origin -a
```

或使用我们创建的脚本：
```bash
bash scripts/fix_git_refs.sh
```

## 快速修复脚本

已创建 `scripts/fix_git_refs.sh`，可以一键修复所有引用问题：

```bash
bash scripts/fix_git_refs.sh
```

## 总结

✅ **问题 1 已完全修复**：origin/HEAD 和远程分支引用现在都正常
⚠️ **问题 2 需要您决定**：是否提交那些未跟踪的脚本文件

现在 VS Code 和 GitLens 应该不会再报那些引用错误了！

