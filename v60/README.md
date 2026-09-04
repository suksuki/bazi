# 阿布知命 V60

V60 是当前唯一实施目标。公开产品只保留私密命盘、分层断命和“阿布说”；
生命树首页、命理枝、枝叶花果动画以及六柱 3D 粒子舞台继续沿用既有视觉语言。

## 公开路径

```text
登录 / 私密档案
→ 生命树档案叶
→ 命理枝
→ 枝、叶、花、果对应的分层断命
→ 阿布说：同一份已落库断语、字幕、声音与六柱粒子同步
```

公开地址为 `/experience`，本地默认地址是
`http://127.0.0.1:8060/experience`。

Owner 已授权把当前受控测试版部署到 Server 13。生产入口为
`https://dblife.com/experience`；部署结构、数据库恢复与验收凭证见
[`docs/26_V60_SERVER13_DEPLOYMENT_RECEIPT.md`](docs/26_V60_SERVER13_DEPLOYMENT_RECEIPT.md)。
这次部署不改变 `publication_allowed=false` 的专业审阅边界。

公开 Runtime 只注册 System、Identity、Mingli、Stage、Focused Reading、
Focused Speech 和 Public Experience。合成命盘、实验、Suite、训练与蒸馏能力保留在
Mingli 内部研究边界，默认 `V60_INTERNAL_SURFACES_ENABLED=false`，没有公开入口。

## 事实与表达边界

```text
确定性本地算法
→ Canonical 命盘事实与岁运坐标
→ 本地 Qwen 按一个具体主题生成文字
→ 本地规范化、坐标校验和公开安全门
→ 落库 Focused Pass
→ 断命正文与阿布说共同读取
```

- Qwen 不重算四柱，不直接写 Canonical Fact。
- 每次产品请求只处理一个主题，默认 `qwen3.8:27b`、非思考模式、
  `num_ctx=4096`、`num_predict=320`。
- 未生成的主题按需请求；已有结果直接复用。
- 阿布说不会再次调用断命模型，只为同一份文字按需准备声音。
- 专属声音使用音频时间轴驱动逐句字幕、角色状态和六柱粒子强调；设备语音降级不伪造
  精确语义同步。
- 当前结果仍是 Owner 审阅候选，不宣称已经获得高级命理师专业资格。

## 代码与数据边界

- `backend/src/abu_v60/mingli/`：命盘、证据、判断、Focused Reading 与内部训练。
- `backend/src/abu_v60/media/`：阿布说、TTS、字幕时间轴和媒体注册。
- `backend/src/abu_v60/experience/`：私密生命树 Home 投影。
- `web/src/`：生命树、命理枝、共享四／六柱舞台和阿布说。
- `db/migrations/`：独立 PostgreSQL 迁移历史；当前数据库只保留
  `identity`、`mingli`、`cognition`、`media` 和 `platform` 业务 schema。
- `v50/` 仅是迁移来源，不是 V60 Runtime 依赖。

## 本地启动

```bash
cd /Users/liujin/DEV/AIProjects/bazi/v60
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/pip install -e '.[dev]'
npm --prefix web install

createdb qiazhi_v60
.venv/bin/alembic upgrade head
.venv/bin/python tools/sync_asset_registry.py
npm --prefix web run build
.venv/bin/python tools/local_runtime.py start
```

运行管理：

```bash
.venv/bin/python tools/local_runtime.py check
.venv/bin/python tools/local_runtime.py status
.venv/bin/python tools/local_runtime.py restart
.venv/bin/python tools/local_runtime.py stop
```

本地管理器默认把命理 Agent 指向 `http://dblife.com:11888` 的
`qwen3.8:27b`，并保持模型 30 分钟。显式环境变量仍可覆盖开发参数。

## 验证

```bash
.venv/bin/ruff check backend/src backend/tests tools
.venv/bin/pytest
npm --prefix web run build
npm --prefix web run audit:public-exposure
npm --prefix web run audit:mingli-shared-scene-contract
npm --prefix web run audit:mingli-synthetic-lab-contract
.venv/bin/python tools/verify_media_library.py
.venv/bin/python tools/audit_runtime_architecture.py
```

当前发布与交互正本见：

- [`docs/25_V60_MINIMAL_PUBLIC_RELEASE.md`](docs/25_V60_MINIMAL_PUBLIC_RELEASE.md)
- [`docs/17_V60_MINGLI_STAGE_AND_SYNCHRONIZED_NARRATION.md`](docs/17_V60_MINGLI_STAGE_AND_SYNCHRONIZED_NARRATION.md)
- [`docs/23_V60_QWEN38_MINGLI_INTEGRATION_AND_PRACTITIONER_REVIEW.md`](docs/23_V60_QWEN38_MINGLI_INTEGRATION_AND_PRACTITIONER_REVIEW.md)
- [`docs/20_V60_SYNTHETIC_MINGLI_METHOD_LAB.md`](docs/20_V60_SYNTHETIC_MINGLI_METHOD_LAB.md)
