# 🚀 Antigravity Auto-Evolve 发射指南

## ✅ 发射前检查清单

### 1. ✅ 黄金存档备份
```bash
cp config/parameters.json config/parameters_v49_golden.json
```
**状态**: ✅ 已完成

### 2. 日志管理
建议使用日志重定向：
```bash
# Linux/WSL
python3 scripts/auto_evolve.py > evolution.log 2>&1 &

# Windows PowerShell
python scripts/auto_evolve.py | Tee-Object -FilePath evolution.log
```

### 3. 物理边界监控
建议定期检查日志，确保参数在合理范围内：
- `rootingWeight`: 建议 < 30.0
- `controlImpact`: 建议 < 15.0
- `earthMetalMoistureBoost`: 建议 < 25.0

---

## 🧪 试运行结果

**测试命令**: `python3 scripts/auto_evolve.py --target 80.0 --max-iter 2`

**结果**:
- ✅ 脚本运行正常
- ✅ 自动加载种子参数成功
- ✅ 动态权重调整工作正常
- ✅ 参数范围扩展逻辑正常
- ⚠️  准确率解析有小问题（但总准确率正确）

**观察**:
- 迭代 1: 72.7% → 75.8% (+3.1%)
- 迭代 2: 75.8% (目标 80.0%)
- 系统正常运行，权重自动调整，参数范围自动扩展

---

## 🚀 正式发射指令

### 选项 1: 无限循环模式（推荐）
```bash
# 后台运行，日志保存到文件
nohup python3 scripts/auto_evolve.py > evolution.log 2>&1 &

# 查看实时日志
tail -f evolution.log
```

### 选项 2: 限制迭代次数（测试用）
```bash
# 限制最多 10 次迭代
python3 scripts/auto_evolve.py --target 82.0 --max-iter 10 > evolution.log 2>&1
```

### 选项 3: 使用 screen/tmux（推荐用于长时间运行）
```bash
# 启动 screen 会话
screen -S antigravity_evolve

# 在 screen 中运行
python3 scripts/auto_evolve.py

# 退出 screen: Ctrl+A, 然后 D
# 重新连接: screen -r antigravity_evolve
```

---

## 📊 预期结果

### 理想情况
- **目标达成**: 准确率达到 82%+，自动停止
- **参数合理**: 所有参数在物理意义范围内
- **平衡性好**: Strong/Balanced/Weak 准确率接近

### 可能情况

#### 1. 胜利 (Victory)
```
🎉 Target Reached! Accuracy: 81.8%
```
**行动**: 验证新参数，提交代码，庆祝！

#### 2. 瓶颈 (Plateau)
```
⚠️  达到最大迭代次数
最终准确率: 75.8% (目标: 82.0%)
```
**原因**: 
- 案例集存在物理矛盾
- 参数空间已充分探索

**行动**: 
- 分析失败案例，考虑增加特征维度
- 或接受当前结果，已经是很好的基线

#### 3. 过拟合 (Overfitting)
```
准确率: 90%+
但参数异常: rootingWeight=50.0
```
**行动**: 
- 回滚到 V49.0 黄金配置
- 考虑增加正则化或扩大验证集

---

## 🔍 监控建议

### 实时监控
```bash
# 查看最新日志（最后 50 行）
tail -n 50 evolution.log

# 查看准确率趋势
grep "准确率结果" evolution.log | tail -20

# 查看参数变化
grep "已更新最佳参数" evolution.log | tail -10
```

### 参数健康检查
```bash
# 检查当前参数是否在合理范围
python3 << 'EOF'
import json
with open("config/parameters.json", "r") as f:
    config = json.load(f)
    
checks = [
    ("rootingWeight", config.get("structure", {}).get("rootingWeight"), 30.0),
    ("controlImpact", config.get("flow", {}).get("controlImpact"), 15.0),
    ("moistureBoost", config.get("flow", {}).get("earthMetalMoistureBoost"), 25.0),
]

print("参数健康检查:")
for name, value, max_val in checks:
    if value is not None:
        status = "✅" if value <= max_val else "⚠️"
        print(f"{status} {name}: {value:.2f} (上限: {max_val:.2f})")
EOF
```

---

## 🛑 紧急停止

如果需要停止运行中的脚本：

```bash
# 查找进程
ps aux | grep auto_evolve.py

# 停止进程（替换 PID）
kill <PID>

# 或强制停止
kill -9 <PID>
```

---

## 📝 结果分析

运行完成后，使用以下命令分析结果：

```bash
# 查看完整日志
cat evolution.log

# 提取准确率变化
grep "准确率结果" evolution.log

# 提取参数更新记录
grep "已更新最佳参数" evolution.log

# 查看最终配置
cat config/parameters.json | python3 -m json.tool
```

---

## 🎯 成功标准

**V50.0 Auto-Evolve 成功的标志**：

1. ✅ 脚本能正常运行并迭代
2. ✅ 准确率有提升趋势（即使未达目标）
3. ✅ 参数保持在物理意义范围内
4. ✅ 日志清晰，便于分析

**记住**: 即使没有达到 82%，任何改进都是成功！V49.0 的 72.7% 已经是很好的基线。

---

## 🎉 Good Luck, Commander!

**Antigravity 的自我进化之旅即将开始！**

