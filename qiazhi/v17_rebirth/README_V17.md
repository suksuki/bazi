# V17 Rebirth Constitution

## Product North Star

- 产品需求宪法：[docs/V17_PRODUCT_REQUIREMENTS_CONSTITUTION.md](docs/V17_PRODUCT_REQUIREMENTS_CONSTITUTION.md)。
- 后续产品、架构、UI、Prompt、插件、权限和学习闭环设计，默认都必须围绕这份中心文档展开。

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

### 当前产品/运行重点（2026-04-24）

- 多语言主链：中文、英文、韩文共用 `frontend/lib/i18n.ts`，前端文案与 LLM verdict prompt 都必须走统一字典或 `ui()` helper。
- 多终端 UI：登录/注册入口、Oracle 主页面、Admin 页面均按桌面/手机 Chrome 响应式验收。
- 授权控制：`admin / manager / user` 通过 `frontend/lib/accessControl.ts` 与后端 auth profile 共同约束页面和 API。
- 出生信息：支持阳历/阴历，阴历包含闰月开关；相关回归见 `tests/test_lunar_calendar_conversion.py`。
- 八字断言：主按钮为 `掐指一算`，LLM 回复应为短断语；深度解释和 Prompt 审计留在 `深度解读 / 幕后观察`。
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
