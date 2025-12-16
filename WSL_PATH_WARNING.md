# WSL 路径转换警告说明

## 警告信息

```
<3>WSL (xxxxx) ERROR: CreateProcessParseCommon:711: Failed to translate Z:\home\jin\bazi_predict
```

## 原因

这个警告是 WSL 在尝试转换 Windows 路径 `Z:\home\jin\bazi_predict` 为 Linux 路径时产生的。

**重要**: 这个警告**不影响功能**，脚本仍然正常运行。

## 为什么会发生？

1. Cursor 的工作区路径是 Windows 格式: `Z:\home\jin\bazi_predict`
2. 当 Cursor 调用 WSL 命令时，会传递这个 Windows 路径作为工作目录
3. WSL 尝试转换这个路径，但由于 `Z:` 驱动器可能未正确映射，转换失败
4. WSL 发出警告，但仍然继续执行命令（使用脚本内部的 Linux 路径）

## 解决方案

### 方案 1: 忽略警告（推荐）
这个警告不影响功能，可以安全忽略。所有脚本都使用相对路径 `Path(__file__).parent.parent`，会自动解析为正确的 Linux 路径。

### 方案 2: 使用包装脚本
可以使用 `scripts/train_wrapper.sh` 来运行训练脚本：

```bash
wsl bash scripts/train_wrapper.sh
```

### 方案 3: 在 WSL 内部直接运行
在 WSL 终端中直接运行，不会看到这个警告：

```bash
cd /home/jin/bazi_predict
source venv/bin/activate
python3 scripts/train_model_optuna.py
```

## 技术细节

- 脚本内部使用: `/home/jin/bazi_predict` (Linux 路径) ✅
- Cursor 传递: `Z:\home\jin\bazi_predict` (Windows 路径) ⚠️
- WSL 转换失败: 发出警告但继续执行 ✅

## 结论

这个警告是 WSL 的内部行为，无法通过代码层面完全消除。但可以安全忽略，因为：
1. 所有脚本使用相对路径，不依赖工作目录
2. 脚本在 WSL 内部使用正确的 Linux 路径
3. 功能完全正常

