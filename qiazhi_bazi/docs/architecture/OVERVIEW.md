# Qiazhi-Bazi Architecture Overview

更新时间：`2026-04-08`

## 1. 总览

Qiazhi-Bazi 当前采用单仓单体结构：

- 前端：`Next.js 14 App Router`
- 后端：`FastAPI`
- 引擎：`physics_engine + final_verdict + LLM audit`
- 数据：`PostgreSQL + SQLModel`

目标不是一次性重写业务，而是在不改变原有逻辑的前提下，把高耦合长文件拆成可维护、可测试、可审计的结构。

## 2. 分层原则

### 前端

- `page`：路由入口，只做装配
- `controller hook`：状态、异步请求、副作用
- `view`：渲染布局和交互绑定
- `pure helpers`：纯计算、格式化、状态派生

### 后端

- `router`：HTTP 入口、参数接收、异常映射
- `service`：业务编排、跨模块协调
- `service helpers`：纯拼装、纯归一化、无 HTTP 语义
- `skills`：命理/物理/判词核心能力
- `db/models`：持久化与数据模型

## 3. 当前重点链路

### 用户推演链路

1. 前端 `StreamBoard` 提交生辰
2. 后端 `analyze-seed`
3. 后端 `analyze-clash`
4. 后端 `audit-physics-with-llm`
5. 用户/系统产生 decision cards
6. 后端 `final-verdict`

### 管理端链路

1. 前端 `admin/settings`
2. 后端 `db-status / db-init`
3. 后端 `llm-models / llm-test`
4. 后端 `runtime-config`

## 4. 已完成的主要拆分

### 前端

- `StreamBoard.tsx` 已拆为 `controller + view + helpers`
- `admin/settings/page.tsx` 已拆为 `page + controller + view + utils`
- `DecisionInbox / BaziCard / TenGodNumericList / AuditorBriefing` 已抽出 helper

### 后端

- `router.py` 主链路已 service 化
- `admin.py` 核心逻辑已 service 化
- `physics_engine.py` 的纯计算已抽出
- `analysis_service / audit_service / llm_service / consultation_service / admin_service` 已建立

## 5. 设计边界

- 不改变现有业务逻辑与输出契约
- 不隐式更改 API 字段名
- 不把规则说明硬编码回组件/路由
- 所有主链路重构都要配套测试

## 6. 当前目录建议

### 前端

- 新页面优先放 `src/features/<feature>`
- `src/components` 保留通用展示组件
- 一旦组件超过约 150-200 行，优先检查是否应抽 helper

### 后端

- 路由文件保持薄
- service 超过约 180-220 行时优先抽 helper
- helper 只做纯逻辑，不承载 HTTP 语义
