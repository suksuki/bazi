# Qiazhi-Bazi 文档目录

本目录用于维护会随产品演进的设计、架构、测试和引擎规范，避免把长说明散落在代码和提交记录里。

## 目录结构

```text
docs/
├── architecture/
│   ├── OVERVIEW.md
│   ├── FRONTEND_MVC.md
│   └── BACKEND_SERVICE_ARCH.md
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

## 维护约定

- 架构变化后，先更新文档，再做下一轮拆分。
- 新增主链路测试时，同时更新测试策略和用例矩阵。
- 命理引擎规则仍以 [engine/ARCH_STANDARDS.md](/home/hlsystem/bazi/qiazhi_bazi/docs/engine/ARCH_STANDARDS.md) 为强制基线。
