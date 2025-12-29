# 📊 QGA 格局审计监控指南

## 监控工具

### 1. 详细进度监控（推荐）

**前台运行（实时显示，可随时Ctrl+C停止）**：
```bash
python3 scripts/detailed_progress_monitor.py
```

**后台运行**：
```bash
nohup python3 scripts/detailed_progress_monitor.py > /tmp/detailed_monitor.log 2>&1 &
tail -f /tmp/detailed_monitor.log
```

**功能**：
- ✅ 实时显示 Step A/B/C/D 的详细进度
- ✅ 显示已处理/剩余样本数
- ✅ 计算处理速度和预计剩余时间
- ✅ 显示统计结果（均值、标准差、离群样本数）
- ✅ 不影响审计进程（只读取日志文件）

### 2. 快速状态查看

```bash
./scripts/auto_monitor_audit.sh MOD_101_SGJG_FAILURE
```

### 3. 实时日志监控

```bash
tail -f /tmp/audit_mod101_fixed.log | grep -E "进度|Step|完成|ERROR"
```

## 当前审计状态

### Step A: ✅ 已完成
- 总样本: 518,400
- 命中: 108,678 (20.96%)

### Step B: 🔄 进行中
- 候选样本: 108,678
- 需要仿真: 326,034 次（每个样本3个场景）
- 预计时间: 15-30 分钟

### Step C: ⏳ 等待中
- 等待 Step B 完成

### Step D: ⏳ 等待中
- 等待 Step C 完成

## 注意事项

1. **监控不影响审计**：所有监控工具都只读取日志文件，不会干扰审计进程
2. **可以随时停止监控**：按 Ctrl+C 停止监控，审计进程继续运行
3. **审计进程独立运行**：即使关闭终端，审计也会在后台继续

## 查看审计进程

```bash
ps aux | grep pattern_audit_rss_v14.py
```

## 查看报告

审计完成后，报告保存在：
```
reports/pattern_audit/audit_report_MOD_101_SGJG_FAILURE_*.json
reports/pattern_audit/audit_report_MOD_101_SGJG_FAILURE_*.md
```

