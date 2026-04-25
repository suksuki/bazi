# V17 Rebirth Constitution

## Product North Star

- 产品需求宪法：[docs/V17_PRODUCT_REQUIREMENTS_CONSTITUTION.md](docs/V17_PRODUCT_REQUIREMENTS_CONSTITUTION.md)。
- 产品路线与进化策略：[docs/V17_PRODUCT_ROADMAP_AND_EVOLUTION_STRATEGY_2026-04-25.md](docs/V17_PRODUCT_ROADMAP_AND_EVOLUTION_STRATEGY_2026-04-25.md)。
- 证据链学习系统：[docs/V17_EVIDENCE_CHAIN_LEARNING_SYSTEM_2026-04-25.md](docs/V17_EVIDENCE_CHAIN_LEARNING_SYSTEM_2026-04-25.md)。
- 后续产品、架构、UI、Prompt、插件、权限和学习闭环设计，默认都必须围绕这组中心文档展开。

## Scope

- Active workspace: `v17_rebirth/` only.
- Allowed legacy dependency: `core/physics` as read-only reference.
- Forbidden migration: any legacy narrative, UI, or business orchestration logic.

## Core Architectural Laws

1. **Narrative Pipeline First**
   - Every user-facing sentence must flow through:
   - `NarrativeSanitizer -> SemanticFusion -> render_text`.
2. **Will Collapse**
   - User intent is a first-class signal (`will_proxy`) and must bias narrative tone in real time.
3. **Protocol Lock**
   - Frontend renders only `payload.render_text`.
   - Frames missing `render_text` are treated as invalid signal.
4. **Bridge, Not Clone**
   - Infrastructure can reuse DB/LLM connection capability only.
   - Every V17 write operation must include `origin = "v17_origin"`.

## V17 Narrative Frame Contract (Draft)

```json
{
  "timestamp": "ISO-8601",
  "layer": "NARRATOR|SNAPSHOT|ACTION_TAKEN",
  "payload": {
    "render_text": "human-readable narrative sentence",
    "god_rings": {
      "god_of_use": [],
      "god_of_taboo": []
    },
    "will_proxy": "stable|aggressive"
  }
}
```

## Python

- **3.12+**：后端与脚本以该版本为准；`qiazhi/.python-version` 供 pyenv/asdf 对齐。
- 首次或从旧版 venv 升级：在仓库根执行  
  `./qiazhi/v17_rebirth/scripts/bootstrap_qiazhi_venv_312.sh`  
  生成 `qiazhi/.venv` 后再跑 `scripts/restart_v17_stack_macos.sh`。

### 自动化测试

- 说明与命令矩阵：[docs/TESTING.md](docs/TESTING.md)。  
- 当前用户验收用例：[docs/V17_USER_ACCEPTANCE_USE_CASES_2026-04-24.md](docs/V17_USER_ACCEPTANCE_USE_CASES_2026-04-24.md)。
- 仓库根一键：`bash qiazhi/v17_rebirth/scripts/run_automated_tests.sh`（优先使用 `qiazhi/.venv`，覆盖后端 pytest、集成、审计门禁与前端 `pnpm run test:ci`）。

### 当前产品/运行重点（2026-04-25）

- 多语言主链：中文、英文、韩文共用 `frontend/lib/i18n.ts`，前端文案与 LLM verdict prompt 都必须走统一字典或 `ui()` helper。
- 多终端 UI：登录/注册入口、Oracle 主页面、Admin 页面均按桌面/手机 Chrome 响应式验收。
- 授权控制：`admin / manager / practitioner / user` 通过 `frontend/lib/accessControl.ts` 与后端 auth profile 共同约束页面和 API；`user` 只看简明断语，`practitioner` 进入专业证据链工作台。
- 命理师准入：当前使用期注册直接创建 `practitioner`，注册页不显示“申请命理师”选项；历史 `user` 账号可在主页面提交命理师申请，`manager / admin` 仍可在用户权限面板审核。
- 命理师贡献画像：用户权限面板汇总 feedback / case / benchmark / contribution score；学习候选会读取贡献等级调整人工复核优先级，但不会自动修改参数。
- 学习治理审计：manager/admin 可对学习候选写入 `watch / approved_for_experiment / rejected` 审计意见；准入实验不等于发布或调参。
- 实验队列：已准入候选会生成 dry-run experiment queue，列出候选 patch 范围、必跑回归命令和回滚安全门。
- 学习评分：shadow run 结果进入 scorecard，记录 synthetic/practitioner benchmark、改善/退化和 promote/rework/reject 结论。
- 发布控制：admin 发布记录必须包含测试报告和回滚方案，当前只留痕，不自动写配置。
- 治理归档：Admin 可导出学习治理审计包，包含候选、审计、实验、scorecard 和发布记录。
- 出生信息：支持阳历/阴历，阴历包含闰月开关；相关回归见 `tests/test_lunar_calendar_conversion.py`。
- 八字断言：主按钮为 `掐指一算`，LLM 回复应为短断语；深度解释和 Prompt 审计留在 `深度解读 / 幕后观察`。
- 宏观象主题层：`v17.macro.theme.v1` 在 L3 汇总财富、事业、感情、性格的主题激活度、证据、机会和风险；UI 位于运势分析专题中枢，LLM 只消费结构化摘要。
- 主题解码设计：专题断言将先由 `topic_decoder` 产出 `wealth_profile.v1` 等结构化画像，再交给财富/事业/感情/性格专属 Prompt；详见 `docs/V17_TOPIC_DECODER_AND_WEALTH_PROFILE_2026-04-26.md`。
- 财富画像：`modern.topic.wealth_profile.v1` 已实现只读 `v17.topic.wealth_profile.v1`，用于审计财富来源、主通道、可用状态、风险和承接条件；当前不生成财富断言。
- LLM 协作层：LLM 分为 `Weaver / Reviewer / Arbiter / Analyst` 四个受治理角色；除短断语外，只能产出结构化复核、仲裁建议和学习归因，不得直接改写物理层、参数或发布状态。
- 证据与学习主线：`evidence_bundle`、`practitioner_feedback` 与 `practitioner_cases` 构成“证据 -> 命理师反馈 -> 真实案例库 -> 学习候选”的 P1-P4 闭环；专业账号可从单条证据直接提交反馈并收录命理师基准候选，反馈 payload 使用 `v17.evidence.learning_material.v1` 标记学习意图、学习价值和边界标签，系统会把反馈和案例归因为只读的 `manual_review_required` 学习候选。
- 0.13 部署：使用 `scripts/update_v17_from_git.sh` 拉取、构建、重启并做健康检查。

### 可调环境变量（可选）

- `QIAZHI_V17_FUSE_MAX_PARALLEL`：全局 LLM 并发上限，默认 `3`。
- `QIAZHI_V17_FUSE_HARD_SEC`：LLM `fuse()` 整段请求硬熔断秒数，默认 `10.0`。
- `QIAZHI_V17_LLM_TTFT_SEC`：首字（首 token）预算，默认 `20.0`。
- `QIAZHI_V17_SSE_STALL_SEC`：SSE 行间最大等待，默认 `30`。
- `QIAZHI_V17_SSE_HEARTBEAT_SEC`：叙事流无 NARRATOR 产出时下发 `HEARTBEAT` 的间隔，默认 `2.0`。
- `QIAZHI_V17_FUSE_MAX_TOKENS`：LLM fuse 默认输出上限，默认 `520`。
- `QIAZHI_V17_JUDGE_MAX_TOKENS`：判词角色输出上限，默认 `420`。
- `QIAZHI_V17_WEAVER_MAX_TOKENS`：织造角色输出上限，默认 `520`。

## Boot Sequence (Current Milestone)

- [x] Create vacuum workspace `v17_rebirth`.
- [x] Implement backend `RealtimeNarrativePipeline` skeleton.
- [x] Implement frontend `V17_PurpleVerdictCard` protocol-locked renderer.
- [x] Implement infrastructure bridges for DB/Admin/LLM configuration.

## 参考演练样例

- Read-only physics adapter: `backend/adapters/physics_adapter.py`
- WebStream render demo: `frontend/components/V17_WebStreamDemo.tsx`

## Systemd Deployment (V17.2)

- Unit files:
  - `deploy/systemd/v17-backend.service`
  - `deploy/systemd/v17-frontend.service`
- Nginx template:
  - `deploy/nginx/dblife.com.conf`
- One-time install:
  - `scripts/install_systemd_services.sh`
- Restart both services:
  - `scripts/restart_v17_stack.sh`
- Backup local runtime DBs before risky deploys:
  - `scripts/backup_v17_runtime_dbs.sh`
- Post-deploy smoke check:
  - `scripts/check_v17_deploy.sh`
  - Optional credentialed login check:
    `V17_ADMIN_IDENTIFIER=admin V17_ADMIN_PASSWORD=... scripts/check_v17_deploy.sh`
