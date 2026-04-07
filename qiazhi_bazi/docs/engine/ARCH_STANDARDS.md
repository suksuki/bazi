# Qiazhi-Bazi 0.13 插件宪法（ARCH Standards）

版本：`v1.0`  
适用范围：`qiazhi_bazi/backend/app/skills`、`api`、`db`、`frontend` 联动链路

## 1. 目标与原则

- 单一真值源：所有能量相关计算以 `physics_tensor` 为唯一真值源（SSOT）。
- 数据即逻辑：业务阈值、系数、规则必须在 PostgreSQL 中管理，不得硬编码。
- 可追溯：每次推演都能追溯到参数版本、规则版本和插件版本。
- 可回退：参数异常时可降级、可回滚、可审计。

## 2. 三位一体溯源

- 动态基因（DB）：`physics_*` 参数表与规则表，必须包含 `updated_at`。
- 静态文档（Docs）：本目录维护公式、字段、判定门槛定义。
- 计算快照（API）：`analyze-seed` 返回 `physics_tensor.meta`，记录参数与插件版本。

## 3. 命名标准（强制）

- 十神命名（全系统统一中文）：
  - `比肩` `劫财` `食神` `伤官` `正财` `偏财` `正官` `七杀` `正印` `偏印`
- 系数字段命名：
  - 交互系数统一前缀：`EFF_`（如 `EFF_RESTRAINING_DIFF`）
  - 可选通用系数：`CF_`（保留给非能量类修正）
- API 字段命名：
  - 张量：`physics_tensor`
  - 十神分值：`physics_tensor.deity_scores`
  - 格局候选：`structure_candidates`
  - 格局确认：`confirmed_structure`

## 4. Plugin Protocol（强制接口）

所有插件必须实现统一协议（可通过抽象基类或约定实现）：

- `consume(context) -> dict`
  - 声明依赖输入（例如 `StructureSkill` 必须消费 `deity_scores`）
- `produce(context) -> dict`
  - 输出必须包含：`confidence`、`evidence`
- `audit(context) -> dict`
  - 返回可审计链路：公式、参数键、关键中间值

建议统一元信息：

- `skill_id`（唯一）
- `skill_version`（语义化版本）
- `rule_version`（规则集版本）
- `enabled`（开关）

## 5. 能量守恒锚点

- 禁止插件内部自建五行底层分值。
- 任何能量加减都必须引用：
  - 上游 `physics_tensor` 或
  - DB 参数键（如 `EFF_*`）
- 插件内出现业务常数（如 `0.6`、`1.2`）视为违规。

### 5.1 物理常数封版记录

- 2026-04-02（L1 封版）：
  - 经过 `run_physics_regression.py` 回归审计，丁巳无根案在 `CF_FLOATING_DECAY=0.10` 达到逻辑共识峰值。
  - 正式将 `CF_FLOATING_DECAY` 设为系统基准值 `0.10`（代码默认值 + DB 运行值）。

## 6. 数据库约束

- 参数与规则表必须支持热更新。
- 规则表至少包含：
  - `rule_key`
  - `enabled`
  - `payload_json`（条件与阈值）
  - `updated_at`
- 所有写入必须可审计（建议保留历史版本表或变更日志）。

## 7. 错误与回退机制

- 参数缺失：
  - 优先加载 DB
  - 缺失时使用安全默认值并在 `meta.warnings` 标记
- 插件失败：
  - 不中断主链路，返回降级结果并写入 `audit` 说明
- 规则异常：
  - 跳过异常规则，保留其余规则执行

## 8. 前后端契约

- 后端必须稳定输出字段结构，不得随意改名。
- 前端必须对缺字段做兼容（空态渲染，不崩溃）。
- UI 术语必须与十神标准命名一致。

### 8.1 L1 硬路由契约（封版）

- 会话共识写入：`session_consensus`（`session_id`, `decision_key`, `confirmed_value`, `reasoning`, `created_at`）。
- 推演覆盖来源：`PhysicsInferenceSkill.consume(session_id)` 读取共识并强制覆盖参数。
- 可观测输出（后端）：
  - `physics_tensor.audit_log.param_version_id`：
    - 无覆盖：`<version_id>`
    - 有覆盖：`<version_id>|hr:<param_key[,param_key...]>`
  - `physics_tensor.audit_log.trace.hard_route_logs`：记录每个覆盖动作。
  - `audit_summary[Core].payload.hard_route_logs`：供前端时间轴可视化。
- 可观测输出（前端）：
  - `AuditSidebar` 在 `Core` 步骤展示蓝色“强制覆盖”徽章（支持多参数换行）。
  - `TenGodNumericList` 仅对受影响十神显示锁定图标（影响域隔离，不全量上锁）。

## 9. 开发流程（SOP）

1. 在 `docs/engine` 更新公式与规则说明。
2. 在 DB 增加/调整参数或规则（含版本标记）。
3. 插件实现仅引用 DB + 上游张量。
4. 用基准样例（如 1990 案例）回归验证。
5. 更新 `skill_version` / `rule_version`，记录变更摘要。

## 10. 当前基准样例

- 样例：`1990-01-01 00:00`（solar）
- 用途：
  - 验证 `physics_tensor` 稳定输出
  - 验证十神分值与格局候选的解释一致性

---

本文件是 0.13 实验室插件开发的强制基线。后续新增 Skill（Structure/Conflict/Health/Annual 等）均需遵循本规范。
