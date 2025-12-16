# GitLens 使用指南

## 什么是 GitLens？

GitLens 是 VS Code 的 Git 增强插件，提供：
- ✅ 图形化 Git 操作界面
- ✅ 代码历史查看和对比
- ✅ 提交作者信息显示
- ✅ 分支管理可视化
- ✅ 推送/拉取操作

## 是否需要 GitLens？

### 推荐使用 ✅

**优点**：
1. **图形化界面**：比命令行更直观
2. **自动处理认证**：可以弹出浏览器进行 OAuth 认证
3. **实时状态显示**：在编辑器中直接看到代码作者和修改历史
4. **错误提示更友好**：图形化错误信息更容易理解

**缺点**：
- 需要安装插件（但这是小事）
- 某些高级操作仍需命令行

## 当前问题解决

### 问题 1: `data` 目录不存在

**已解决**：已创建 `data` 目录和 `.gitkeep` 文件

### 问题 2: 推送认证失败

**解决方案**：
1. **使用 SSH（推荐）**：已配置，推送成功 ✅
2. **使用 GitLens OAuth**：在 VS Code 中点击推送时，GitLens 会弹出浏览器进行认证

## 使用 GitLens 推送的步骤

### 方法 1: 使用 Source Control 面板

1. 打开 VS Code 的 **Source Control** 面板（Ctrl+Shift+G）
2. 查看待提交的文件
3. 点击 **"+"** 暂存文件，或点击 **"..."** → **"Stage All Changes"**
4. 输入提交信息
5. 点击 **"✓ Commit"**
6. 点击 **"..."** → **"Push"** 或使用 GitLens 的推送按钮

### 方法 2: 使用 GitLens 侧边栏

1. 打开 GitLens 侧边栏（点击左侧 GitLens 图标）
2. 查看 **Repositories** → **Your Repository**
3. 查看 **Commits** 和 **Branches**
4. 右键点击分支 → **Push**

## 认证配置

### SSH（已配置 ✅）

当前远程 URL：`git@github.com:suksuki/bazi.git`

**优点**：
- 无需每次输入密码
- 更安全
- 推送速度快

### HTTPS + Personal Access Token

如果需要切换到 HTTPS：

1. 在 GitHub 创建 Personal Access Token
   - Settings → Developer settings → Personal access tokens → Tokens (classic)
   - 权限：至少需要 `repo` 权限

2. 更改远程 URL：
   ```bash
   git remote set-url origin https://<YOUR_TOKEN>@github.com/suksuki/bazi.git
   ```

3. 或使用 GitLens 的认证流程（会自动处理）

## 常见问题

### Q: GitLens 推送卡住怎么办？

**A**: 
1. 检查网络连接
2. 检查 SSH 密钥配置（如果使用 SSH）
3. 尝试在终端手动推送：
   ```bash
   git push origin main
   ```

### Q: 推送时提示 "Host key verification failed"

**A**: 
1. 运行：`ssh -T git@github.com`
2. 输入 `yes` 接受 GitHub 的 SSH 密钥
3. 重新尝试推送

### Q: 推送时提示 "Missing or invalid credentials"

**A**:
1. 如果使用 HTTPS，需要配置 Personal Access Token
2. 如果使用 SSH，检查 SSH 密钥是否添加到 GitHub
3. 使用 GitLens 的 OAuth 认证流程

## 推荐工作流程

### 日常开发

1. **使用 GitLens** 查看代码历史和作者信息
2. **使用 Source Control 面板** 进行提交和推送
3. **使用命令行** 进行复杂操作（如 rebase、cherry-pick）

### 推送操作

- **简单推送**：使用 GitLens 或 Source Control 面板
- **批量操作**：使用命令行脚本（如 `scripts/git_push_safe.sh`）

## 总结

✅ **推荐使用 GitLens**，它让 Git 操作更简单直观
✅ **推送已成功**，使用 SSH 方式
✅ **data 目录问题已修复**

现在可以在 VS Code 中正常使用 GitLens 进行所有 Git 操作了！

