# V40 Phase 49: Auth-Derived User Role Context

日期：2026-07-01

## 背景

Phase 46 为了快速验证命理师视角，临时允许：

```text
/v40/ui?role=practitioner
```

这只适合开发期。它会把“身份”放到前端 URL，长期会导致：

1. 普通用户、命理师、admin 边界不清；
2. Practitioner Lens 看起来像 UI 开关，而不是后端权限投影；
3. 后续接真实登录时又要改页面流程；
4. 主系统容易重新混入 admin 管理逻辑。

Phase 49 的目标是把身份来源收束为服务端会话上下文。

## 产品原则

V40 用户主系统只保留三种产品身份：

```text
guest -> 游客
user -> 普通用户
practitioner -> 命理师
```

Admin 不再是用户侧产品身份。Admin Control Plane 独立运行；如果 admin 进入主系统，则只被映射为特殊 practitioner，不获得管理能力。

## 新合同

新增：

```text
UserAppSessionContext
```

核心字段：

| 字段 | 作用 |
| --- | --- |
| `role_key` | 用户侧投影身份，只能是 guest/user/practitioner |
| `role_context` | 对应权限上下文 |
| `authenticated` | 当前是否来自 header/cookie 会话 |
| `source` | 身份来源，例如 header/cookie/env/default |
| `admin_mapped_to_practitioner` | admin 是否被降格映射到命理师视角 |
| `admin_control_plane_separated` | 永远为 true |

## 新接口

```text
GET /api/v40/session/context
```

返回当前用户侧会话上下文。前台页面启动时先调用它，再决定：

1. 显示普通用户、游客或命理师身份；
2. 报告 runtime 使用哪个 `RoleContext`；
3. Practitioner Lens 是否出现；
4. Probe、feedback、conversation 的 `created_by_role` 使用哪个角色。

## 身份解析顺序

当前阶段先支持轻量解析，后续可接真实登录系统：

```text
X-V40-User-Role header
-> v40_user_role cookie
-> V40_USER_APP_ROLE env
-> default user
```

如果解析到 `admin`：

```text
admin -> practitioner
admin_control_plane_separated = true
admin_mapped_to_practitioner = true
```

## Runtime 接入

报告入口：

```text
POST /api/v40/readings/native-report
POST /api/v40/runtime/native-bazi
```

现在会优先使用 `UserAppSessionContext` 推导出的 `role_context`。直连 API 的历史 `role_key` 暂时保留兼容，以免打断已有 migration/test/runtime 脚本；用户前台不再从 URL 写入角色。

## UI 改造

前台 `/v40/ui` 必须满足：

1. 不读取 `window.location.search`；
2. 不使用 `URLSearchParams` 推导身份；
3. 不支持 `?role=practitioner`；
4. 页面启动调用 `/api/v40/session/context`；
5. 报告、Probe、对话、命理师校准都使用 session role；
6. 页面不暴露 provider/model/prompt/acceptance/policy/debug/admin 控制面。

## 边界

Phase 49 不做：

1. 完整登录注册；
2. Admin Console 权限系统；
3. Practitioner Review Queue；
4. ConsentGrant；
5. 线上 cookie 签名与 session store。

这些进入 Phase 50+。

## 验收

完成标准：

1. `/api/v40/session/context` 默认返回 user；
2. header `x-v40-user-role: practitioner` 返回 practitioner；
3. header `x-v40-user-role: admin` 在主系统中映射为 practitioner；
4. `/v40/ui` 不再包含 URL role hook；
5. `/v40/ui` 使用 session context 构造报告和对话；
6. Practitioner Lens 仍由 role context 控制；
7. V40 全量测试通过。
