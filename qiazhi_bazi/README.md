# Qiazhi-Bazi

`qiazhi_bazi/` 是当前默认开发入口，采用 `FastAPI + Next.js 14` 单体仓结构，按「独立开发、按需引用 legacy」原则演进。

## 当前架构

```text
qiazhi_bazi/
├── backend/                     # FastAPI API / service / skills / tests
├── frontend/                    # Next.js App Router / feature controllers / views / tests
├── docs/                        # 设计、架构、测试、命理引擎规范
└── .codex/skills/               # 仓库级协作 skills（本轮新增）
```

## 开发原则

- 不改变既有业务逻辑，优先做职责拆分和可测试性增强。
- 前端遵循 `page -> controller hook -> view -> pure helpers`。
- 后端遵循 `router -> service -> helper/model/skill`。
- 所有主链路变更必须补单元、集成或回归测试。

## 文档导航

- 总索引：[docs/README.md](/home/hlsystem/bazi/qiazhi_bazi/docs/README.md)
- 总体架构：[docs/architecture/OVERVIEW.md](/home/hlsystem/bazi/qiazhi_bazi/docs/architecture/OVERVIEW.md)
- 前端 MVC 设计：[docs/architecture/FRONTEND_MVC.md](/home/hlsystem/bazi/qiazhi_bazi/docs/architecture/FRONTEND_MVC.md)
- 后端 service 架构：[docs/architecture/BACKEND_SERVICE_ARCH.md](/home/hlsystem/bazi/qiazhi_bazi/docs/architecture/BACKEND_SERVICE_ARCH.md)
- 测试策略：[docs/testing/TEST_STRATEGY.md](/home/hlsystem/bazi/qiazhi_bazi/docs/testing/TEST_STRATEGY.md)
- 测试用例矩阵：[docs/testing/TEST_CASES.md](/home/hlsystem/bazi/qiazhi_bazi/docs/testing/TEST_CASES.md)

## 快速开始

- 后端见：[backend/README.md](/home/hlsystem/bazi/qiazhi_bazi/backend/README.md)
- 前端见：[frontend/README.md](/home/hlsystem/bazi/qiazhi_bazi/frontend/README.md)

## 当前验证基线

- 后端：`pytest tests/unit tests/integration -q`
- 前端：`npm test`
- 前端构建：`npm run build`
