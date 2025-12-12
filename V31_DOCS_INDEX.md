# V31.0 财富模块文档索引

## 📚 文档导航

### 🚀 快速开始
1. **[快速参考卡](WEALTH_V31_QUICKREF.md)** ⭐ 推荐首读
   - 核心公式
   - 杠杆模式表
   - 评级标准
   - 故障排查

2. **[演示脚本](demo_wealth_v31.py)**
   - 三个实际案例
   - 完整输出示例
   - 使用方法演示

### 📖 深入学习
3. **[完整协议](docs/WEALTH_V31_PROTOCOL.md)**
   - 理论基础
   - 算法详解
   - 案例分析
   - 技术实现

4. **[更新日志](CHANGELOG_V31.md)**
   - 版本信息
   - 核心变更
   - 技术细节
   - 未来计划

5. **[实现总结](V31_IMPLEMENTATION_SUMMARY.md)**
   - 项目概述
   - 成果展示
   - 质量保证
   - 使用指南

## 🎯 按需求查找

### 我想快速了解 V31.0
→ 阅读 [快速参考卡](WEALTH_V31_QUICKREF.md)

### 我想看实际效果
→ 运行 `python demo_wealth_v31.py`

### 我想深入理解算法
→ 阅读 [完整协议](docs/WEALTH_V31_PROTOCOL.md)

### 我想知道改了什么
→ 阅读 [更新日志](CHANGELOG_V31.md)

### 我想了解整体实现
→ 阅读 [实现总结](V31_IMPLEMENTATION_SUMMARY.md)

## 📂 文件结构

```
bazi_predict/
├── core/
│   └── meaning.py              # 核心实现 (V31.0)
├── ui/pages/
│   └── prediction_dashboard.py # UI 集成
├── docs/
│   └── WEALTH_V31_PROTOCOL.md  # 完整协议文档
├── demo_wealth_v31.py          # 演示脚本
├── WEALTH_V31_QUICKREF.md      # 快速参考卡 ⭐
├── CHANGELOG_V31.md            # 更新日志
├── V31_IMPLEMENTATION_SUMMARY.md # 实现总结
└── V31_DOCS_INDEX.md           # 本文件
```

## 🔍 关键概念速查

| 概念 | 定义 | 文档位置 |
|------|------|----------|
| 高能粒子 | Energy > 40 | 快速参考卡 |
| 杠杆率 | 0.8x - 3.0x | 快速参考卡 |
| 固化率 | Storage / 100 | 完整协议 |
| 获利模式 | 4种类型 | 完整协议 |
| 过路财 | 固化率 = 0 | 快速参考卡 |

## 🎓 学习路径

### 初学者路径
1. 快速参考卡 (5分钟)
2. 演示脚本 (10分钟)
3. 实现总结 (15分钟)

### 进阶路径
1. 完整协议 (30分钟)
2. 更新日志 (15分钟)
3. 源代码阅读 (60分钟)

### 开发者路径
1. 更新日志 (技术细节)
2. 源代码 (core/meaning.py)
3. 测试代码 (tests/test_meaning.py)

## 🛠️ 常见任务

### 运行演示
```bash
python demo_wealth_v31.py
```

### 查看快速参考
```bash
cat WEALTH_V31_QUICKREF.md
```

### 阅读完整协议
```bash
cat docs/WEALTH_V31_PROTOCOL.md
```

### 查看源代码
```bash
# 核心实现
cat core/meaning.py | grep -A 200 "_calculate_wealth"

# UI 集成
cat ui/pages/prediction_dashboard.py | grep -A 100 "财富统一场"
```

## 📊 文档统计

| 文档 | 字数 | 阅读时间 |
|------|------|----------|
| 快速参考卡 | ~1,200 | 5分钟 |
| 演示脚本 | ~1,800 | 10分钟 |
| 完整协议 | ~3,800 | 30分钟 |
| 更新日志 | ~2,500 | 15分钟 |
| 实现总结 | ~2,900 | 20分钟 |

**总计**: ~12,200 字，约 80 分钟阅读时间

## 🔗 相关链接

### 内部文档
- [项目 README](README.md)
- [核心公理](docs/KERNEL_AXIOMS.md) (如果存在)
- [能量流引擎](core/flux.py)

### 外部资源
- 传统子平八字理论
- 量子力学基础
- 系统工程原理

## 📝 更新记录

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2025-12-12 | V31.0 | 初始发布 |

## 🎯 下一步

### 建议行动
1. ✅ 阅读快速参考卡
2. ✅ 运行演示脚本
3. ✅ 在实际应用中测试
4. ✅ 提供反馈和建议

### 反馈渠道
- GitHub Issues
- 项目文档
- 开发团队

---

**版本**: V31.0  
**更新**: 2025-12-12  
**维护**: Antigravity Team

**提示**: 按 Ctrl+F 可快速搜索本文档
