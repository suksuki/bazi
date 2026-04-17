"use client";

/**
 * V12.99：终判/断言展示的规范入口（与 NDJSON 增量驱动的 LiveVerdictDisplay 对齐）。
 * 过渡动画在 LiveVerdictDisplay 语义层实现，此处保持薄封装便于路由与文档引用。
 */
export { LiveVerdictDisplay as FinalVerdictView } from "./LiveVerdictDisplay";
export type { LiveVerdictDisplayProps as FinalVerdictViewProps } from "./LiveVerdictDisplay";
