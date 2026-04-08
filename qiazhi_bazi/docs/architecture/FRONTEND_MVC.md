# Frontend MVC Guide

更新时间：`2026-04-08`

## 1. 目标

前端 MVC 在本仓库中的含义不是传统 class-based MVC，而是更适合 React/Next 的职责拆分：

- `page` 充当路由装配层
- `controller hook` 充当控制器
- `view/component` 充当展示层
- `utils/constants/types` 充当轻量 model/support 层

## 2. 推荐模式

```text
src/features/<feature>/
├── use<Feature>Controller.ts
├── <Feature>View.tsx
├── utils.ts
├── constants.ts
├── types.ts
└── __tests__/
```

## 3. 现有示例

### Stream Board

- 入口：[frontend/src/components/StreamBoard.tsx](/home/hlsystem/bazi/qiazhi_bazi/frontend/src/components/StreamBoard.tsx:1)
- Controller：[frontend/src/features/stream-board/useStreamBoardController.ts](/home/hlsystem/bazi/qiazhi_bazi/frontend/src/features/stream-board/useStreamBoardController.ts:1)
- View：[frontend/src/features/stream-board/StreamBoardView.tsx](/home/hlsystem/bazi/qiazhi_bazi/frontend/src/features/stream-board/StreamBoardView.tsx:1)

### Admin Settings

- 入口：[frontend/src/app/admin/settings/page.tsx](/home/hlsystem/bazi/qiazhi_bazi/frontend/src/app/admin/settings/page.tsx:1)
- Controller：[frontend/src/features/admin-settings/useAdminSettingsController.ts](/home/hlsystem/bazi/qiazhi_bazi/frontend/src/features/admin-settings/useAdminSettingsController.ts:1)
- View：[frontend/src/features/admin-settings/AdminSettingsView.tsx](/home/hlsystem/bazi/qiazhi_bazi/frontend/src/features/admin-settings/AdminSettingsView.tsx:1)

## 4. 何时拆分

满足以下任一条件就应该考虑拆：

- 文件超过约 `180` 行
- 同时包含网络请求、状态管理、布局渲染
- 有 3 个以上 `useEffect`
- 有明显的“纯计算”代码段可以单测
- UI 与业务判断互相交织难以阅读

## 5. 测试建议

- `controller`：集成测试，mock `fetch/localStorage/timers`
- `view`：交互测试，检查 callback wiring
- `utils`：纯单元测试

## 6. 当前前端测试分层

- `StreamBoardView`：view 级交互测试
- `useStreamBoardController`：controller 回归测试
- `admin-settings`：controller 集成测试
- `decision-inbox / bazi-card / ten-god-list / auditor-briefing`：helper 单测
