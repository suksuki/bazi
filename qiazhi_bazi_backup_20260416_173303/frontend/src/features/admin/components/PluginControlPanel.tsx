/** 插件治理面板入口；终审签发后滑块死锁在 `PluginManagementPanel` 内（订阅 `isFinalized`）。 */
export { PluginManagementPanel as PluginControlPanel } from "./PluginManagementPanel";
