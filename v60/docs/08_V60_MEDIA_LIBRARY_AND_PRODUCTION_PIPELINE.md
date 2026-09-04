# V60 媒体库与制作管线

状态：当前 Runtime 正本
同步日期：2026-09-04

## 1. 目标

媒体库把原始素材、处理过程、Owner 授权、运行交付和前端 Cue 分开记录，使页面播放的
每一个文件都能追溯到固定 Hash。媒体只能表达已经成立的产品状态，不能创造命理事实、
修改断语或改变用户档案。

```text
Owner 授权素材
→ immutable source
→ 技术／角色 QA
→ 可复现后处理
→ process manifest
→ Runtime delivery
→ asset registry + media catalog
→ Cue binding
```

## 2. 正本文件

- `assets/registry.json`：公开文件路径、类型、版本与 SHA-256。
- `media/catalog.json`：媒体身份、来源、交付、角色身份与 Cue。
- `media/manifests/`：冻结视觉包和处理回执。
- `media/sources/`：不可覆盖的源素材版本。
- `media/masters/`：可复现中间母版。
- `media/review/`：不进入 Runtime 的审阅产物。
- `web/public/assets/`：通过注册表准入的公开交付。

Runtime 不硬编码公开媒体路径；`abu_v60.media.runtime` 从两个正本文件校验 Hash 后投影
前端绑定。前端只接收可达页面需要的绑定。

## 3. 当前角色与 Cue

角色身份：

- `ABU_CHARACTER_V60_V1`：当前阿布主身份；运动素材只绑定坐姿循环。
- `DODO_CHARACTER_V108_V1`：Home 日间陪伴角色；保留冻结兼容身份。

Runtime Cue：

```text
cue.mingli.abu-idle.v1
→ media.abu.v60.seated-idle.v1
→ VP9 alpha / animated WebP / reduced-motion poster

cue.mingli.dodo-idle.v1
→ media.dodo.v108.idle-transparent.v1
→ VP9 alpha / animated WebP / reduced-motion poster
```

不存在“文件还在，所以可以播放”的隐式准入。Cue、媒体项和每个交付资产必须同时是
`RUNTIME_REGISTERED`，缺失角色、文件或 Hash 漂移都必须失败关闭。

## 4. 当前场景资产

公开投影只包含：

- 品牌 Logo 与登录生命树背景；
- Home 日／夜背景、日／夜 Logo 和档案叶；
- 命理枝日／夜视频、起始帧和 Poster；
- 内部共享舞台所需的水庭日／夜背景；
- 阿布与多多的透明角色交付。

登录背景只承担品牌氛围，不携带入口、状态或交互语义。完整 LAB 默认无公开路由；共享
舞台资产存在不等于研究功能对外开放。

## 5. 阿布说声音与字幕

断语文字先通过 Mingli 的落库与公开安全门。用户主动点击播放后，TTS 服务按句或分句
生成音频片段，服务端以真实 WAV 帧数拼出单调递增的 Cue 时间轴。前端使用音频
`currentTime` 同时驱动字幕、角色状态和六柱粒子强调。

音频、字幕与粒子不各自拥有计时器。暂停、缓冲、继续和播放结束都以同一个音频时钟为
准。设备语音降级没有服务端 Cue，因此不得伪造精确字幕或柱位同步。

## 6. 源素材规则

1. 源素材进入 `media/sources/<ASSET_ID>/vN/source.<ext>`。
2. 同一版本不可覆盖；内容变化必须增加版本。
3. Ingest receipt 记录字节数、SHA-256、容器、分辨率、帧率、时长、音轨和授权。
4. 后处理脚本必须记录输入 Hash、参数、工具版本、输出 Hash 和交付角色。
5. Alpha 视频至少提供 VP9 WebM、WebP 和静态 Poster。
6. Review 文件、原始音轨和生成提示词不进入公开构建。
7. 自动播放声音必须由用户手势触发，并尊重暂停与系统无障碍设置。

## 7. 校验

```bash
cd /Users/liujin/DEV/AIProjects/bazi/v60
.venv/bin/python tools/verify_media_library.py
.venv/bin/python tools/audit_media_technical_contracts.py
.venv/bin/python tools/sync_asset_registry.py
npm --prefix web run build
npm --prefix web run audit:public-exposure
```

验收必须覆盖：源与交付文件存在、Hash 一致、Cue 交付完整、公开构建无额外媒体、
reduced-motion 可用、字幕时间轴单调且不超过音频时长。
