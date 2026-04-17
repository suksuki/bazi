# Qiazhi-Bazi 文档目录

本目录用于维护会随产品演进的设计、架构、测试和引擎规范，避免把长说明散落在代码和提交记录里。

## 目录结构

```text
docs/
├── architecture/
│   ├── OVERVIEW.md
│   ├── FRONTEND_MVC.md
│   ├── BACKEND_SERVICE_ARCH.md
│   └── PIPELINE_INBOX_LLM_WHITEPAPER.md
├── testing/
│   ├── TEST_STRATEGY.md
│   └── TEST_CASES.md
├── engine/
│   └── ARCH_STANDARDS.md
└── api/
    └── examples.json
```

## 推荐阅读顺序

1. [architecture/OVERVIEW.md](/home/hlsystem/bazi/qiazhi_bazi/docs/architecture/OVERVIEW.md)
2. [architecture/FRONTEND_MVC.md](/home/hlsystem/bazi/qiazhi_bazi/docs/architecture/FRONTEND_MVC.md)
3. [architecture/BACKEND_SERVICE_ARCH.md](/home/hlsystem/bazi/qiazhi_bazi/docs/architecture/BACKEND_SERVICE_ARCH.md)
4. [testing/TEST_STRATEGY.md](/home/hlsystem/bazi/qiazhi_bazi/docs/testing/TEST_STRATEGY.md)
5. [testing/TEST_CASES.md](/home/hlsystem/bazi/qiazhi_bazi/docs/testing/TEST_CASES.md)
6. [architecture/PIPELINE_INBOX_LLM_WHITEPAPER.md](./architecture/PIPELINE_INBOX_LLM_WHITEPAPER.md) — 测算 → Inbox → 终判全链路审计白皮书（随架构迭代更新）

### V12.0 智能大脑（草案）

- **[architecture/V12_DOCUMENTATION_STEWARDSHIP.md](./architecture/V12_DOCUMENTATION_STEWARDSHIP.md)** — **文档索引与重构期维护约定（请先读）**  
- **[architecture/V12_IMPLEMENTATION_ROADMAP.md](./architecture/V12_IMPLEMENTATION_ROADMAP.md)** — **V11→V12 落地路线图**：三阶段、双轨、`repair_mode` 灰度、回滚、Phase 1 首改路径  
- [architecture/V12_INFERENCE_PULSE_WHITEPAPER.md](./architecture/V12_INFERENCE_PULSE_WHITEPAPER.md) — Inference-Pulse：从管道到中枢、三权分立、核心算子与进化回路  
- [V12_BRAIN_FRAMEWORK.md](./V12_BRAIN_FRAMEWORK.md) — **M1–M4**：三色/中断、监军、主动交互、**断言树（FACT/LAW/WILL/SYNTHESIS）、缝合接口、剪枝路由**

## 维护约定

- 架构变化后，先更新文档，再做下一轮拆分。
- 新增主链路测试时，同时更新测试策略和用例矩阵。
- 命理引擎规则仍以 [engine/ARCH_STANDARDS.md](/home/hlsystem/bazi/qiazhi_bazi/docs/engine/ARCH_STANDARDS.md) 为强制基线。
