# Backend Service Architecture

更新时间：`2026-04-08`

## 1. 目标

后端重构的核心目标是让 `router` 退出“大而全”状态，转为：

- `router` 只处理 HTTP 层
- `service` 负责业务编排
- `helper` 负责纯拼装与纯归一化
- `skill` 负责核心命理/物理能力

## 2. 当前服务层

### Consultation Service

- 文件：[backend/app/services/consultation_service.py](/home/hlsystem/bazi/qiazhi_bazi/backend/app/services/consultation_service.py:1)
- 负责：
  - consultation 创建
  - structure 确认
  - decision step 写入
  - rollback 事件
  - history 列表

### Admin Service

- 文件：[backend/app/services/admin_service.py](/home/hlsystem/bazi/qiazhi_bazi/backend/app/services/admin_service.py:1)
- 负责：
  - db status
  - db init
  - llm test

### Analysis Service

- 文件：[backend/app/services/analysis_service.py](/home/hlsystem/bazi/qiazhi_bazi/backend/app/services/analysis_service.py:1)
- 负责：
  - translate
  - analyze-clash
  - analyze-seed
  - final verdict orchestration

### Audit Service

- 文件：[backend/app/services/audit_service.py](/home/hlsystem/bazi/qiazhi_bazi/backend/app/services/audit_service.py:1)
- 负责：
  - physics tensor fallback
  - audit prompt building
  - LLM structured parse / retry / fallback

### LLM Service

- 文件：[backend/app/services/llm_service.py](/home/hlsystem/bazi/qiazhi_bazi/backend/app/services/llm_service.py:1)
- 负责：
  - llm chat
  - llm stream
  - shared prompt construction

## 3. Helper 层

### Analysis Helpers

- 文件：[backend/app/services/helpers/analysis_helpers.py](/home/hlsystem/bazi/qiazhi_bazi/backend/app/services/helpers/analysis_helpers.py:1)
- 负责：
  - 翻译消息构造
  - 翻译结果解析
  - 冲合 fallback 文案
  - analyze-seed 审计摘要拼装

### Audit Helpers

- 文件：[backend/app/services/helpers/audit_helpers.py](/home/hlsystem/bazi/qiazhi_bazi/backend/app/services/helpers/audit_helpers.py:1)
- 负责：
  - fallback structured response
  - 审计结果标准化

## 4. 设计约束

- service 不直接输出 HTTPException，除非确实属于 HTTP 边界
- helper 不读取 request/session/global mutable state
- skill 只关注领域逻辑，不承载路由和页面耦合
- service/helper 重构必须保持返回契约稳定

## 5. 测试分层

- router：当前主要通过 integration tests 间接覆盖
- service：unit tests 为主
- helper：unit tests 为主
- physics skill：unit + regression
