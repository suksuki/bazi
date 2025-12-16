# Git 推送问题解决指南

## 问题：Push 卡住无反应

### 原因分析
1. **身份验证问题**：GitHub 不再支持密码认证，需要使用 Personal Access Token (PAT) 或 SSH
2. **网络问题**：连接 GitHub 可能较慢
3. **推送进程卡住**：等待用户输入但无法交互

## 解决方案

### 方案 1：使用 GitLens 插件（推荐）⭐

**GitLens** 是 VS Code 的 Git 增强插件，提供图形化界面，可以：
- 自动处理身份验证
- 显示推送进度
- 提供更好的错误提示

**步骤**：
1. 在 VS Code 中安装 **GitLens** 插件
2. 打开 Source Control 面板（Ctrl+Shift+G）
3. 点击 "..." 菜单 → "Push" 或使用 GitLens 的推送按钮
4. 如果需要认证，GitLens 会弹出浏览器窗口进行 OAuth 认证

### 方案 2：使用 VS Code 内置 Git 功能

VS Code 内置的 Git 功能也可以处理推送：

1. 打开 Source Control 面板（Ctrl+Shift+G）
2. 点击 "..." 菜单 → "Push"
3. 如果需要认证，VS Code 会提示输入用户名和 Personal Access Token

### 方案 3：配置 Personal Access Token

如果要在命令行推送，需要配置 PAT：

```bash
# 1. 在 GitHub 创建 Personal Access Token
# Settings → Developer settings → Personal access tokens → Tokens (classic)
# 权限：至少需要 repo 权限

# 2. 配置 Git 使用 token
git remote set-url origin https://<YOUR_TOKEN>@github.com/suksuki/bazi.git

# 或使用 Git Credential Manager
git config --global credential.helper store
# 然后推送时会提示输入用户名和 token
```

### 方案 4：使用 SSH（最安全）

```bash
# 1. 生成 SSH 密钥（如果还没有）
ssh-keygen -t ed25519 -C "your_email@example.com"

# 2. 添加 SSH 密钥到 ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# 3. 将公钥添加到 GitHub
cat ~/.ssh/id_ed25519.pub
# 复制输出，添加到 GitHub: Settings → SSH and GPG keys

# 4. 更改远程 URL 为 SSH
git remote set-url origin git@github.com:suksuki/bazi.git

# 5. 测试连接
ssh -T git@github.com

# 6. 推送
git push origin main
```

### 方案 5：使用 GitHub CLI

```bash
# 1. 安装 GitHub CLI
# WSL: sudo apt install gh

# 2. 登录
gh auth login

# 3. 推送
git push origin main
```

## 当前状态

- ✅ 本地已有 1 个提交待推送（965a922）
- ⚠️  还有未暂存的更改（config/parameters.json）
- ⚠️  推送进程可能卡在身份验证

## 推荐操作流程

### 使用 GitLens（最简单）

1. **在 VS Code 中**：
   - 打开 Source Control 面板（Ctrl+Shift+G）
   - 查看待推送的提交
   - 点击 "..." → "Push"
   - GitLens 会处理身份验证

2. **如果需要先提交剩余更改**：
   - 在 Source Control 面板中
   - 暂存 `config/parameters.json`
   - 提交更改
   - 然后推送

### 使用命令行（需要配置认证）

```bash
# 1. 先提交剩余更改
git add config/parameters.json
git commit -m "chore: update parameters from auto-evolution"

# 2. 配置认证（选择一种方式）
# 方式 A: 使用 GitHub CLI
gh auth login

# 方式 B: 使用 Personal Access Token
git remote set-url origin https://<TOKEN>@github.com/suksuki/bazi.git

# 方式 C: 使用 SSH
git remote set-url origin git@github.com:suksuki/bazi.git

# 3. 推送
git push origin main
```

## 快速检查

```bash
# 检查远程 URL
git remote -v

# 检查认证状态（如果使用 GitHub CLI）
gh auth status

# 检查 SSH 连接（如果使用 SSH）
ssh -T git@github.com
```

## 总结

**推荐使用 GitLens 插件**，因为：
- ✅ 图形化界面，操作简单
- ✅ 自动处理身份验证
- ✅ 显示详细的推送状态
- ✅ 无需配置命令行认证

如果 GitLens 不可用，建议使用 **GitHub CLI** (`gh auth login`)，这是最简单可靠的命令行认证方式。

