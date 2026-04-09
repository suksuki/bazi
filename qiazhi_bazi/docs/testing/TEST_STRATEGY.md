# Test Strategy

更新时间：`2026-04-09`

## 1. 目标

测试的目标不是“堆数量”，而是保护这次重构后的三个核心承诺：

1. 不改变原有业务逻辑
2. 长模块拆分后行为保持稳定
3. 前后端主链路可回归、可持续演进

## 2. 测试分层

### 后端单元测试

覆盖：

- service
- helper
- physics rules / calculations
- runtime config

当前重点：

- `consultation_service`
- `admin_service`
- `analysis_service`
- `audit_service`
- `llm_service`
- `physics_rules`
- `physics_calculations`

### 后端集成测试

覆盖：

- `router` 主链路
- fake session 下的 consultation / rollback / analyze-seed
- admin runtime config roundtrip

### 前端单元测试

覆盖：

- feature utils
- component helper
- prompt/state formatting helpers

### 前端集成测试

覆盖：

- controller hooks
- view wiring
- fetch/localStorage/timer 副作用

### 回归测试

覆盖：

- StreamBoard analyze-seed 主链路
- physics/service fallback 行为
- admin settings runtime-config 流程

## 3. 当前执行命令

### 后端

```bash
cd qiazhi_bazi/backend
pytest tests/unit tests/integration -q
```

### 前端

```bash
cd qiazhi_bazi/frontend
pnpm test
pnpm run build
```

## 4. 执行清单

### 后端改动后

1. 跑 `pytest tests/unit tests/integration -q`
2. 如果改到 `skills/physics_*`，补跑相关 physics 单测
3. 如果改到输出契约，确认 integration case 仍覆盖该字段

### 前端改动后

1. 跑 `pnpm test`
2. 跑 `pnpm run build`
3. 如果改到 controller，确认有 `fetch/localStorage/timer` 覆盖
4. 如果改到纯 helper，确认有单测

### 文档/skills 改动后

1. 检查 `README` 与 `docs/` 索引是否一致
2. 检查 `SKILL.md` 与 `agents/openai.yaml` 是否一致
3. 如果测试范围变化，更新 `TEST_CASES.md`

## 5. 通过标准

- 新增 service/helper 必须至少有单测
- 新增 controller hook 必须至少有一条集成测试
- 主链路重构必须至少保留一条 regression test
- 前端构建和后端核心测试要同时通过

## 6. 测试设计原则

- mock 外部依赖，不 mock 自己的纯逻辑
- controller 测试优先 mock `fetch`
- 只对不稳定边界 mock：网络、存储、定时器、数据库连接
- 断言契约与行为，不断言实现细节

## 7. 提交前检查

- 代码拆分是否保持原有业务逻辑
- 文档是否同步
- skill 元信息是否同步
- 前后端主验证命令是否全绿
