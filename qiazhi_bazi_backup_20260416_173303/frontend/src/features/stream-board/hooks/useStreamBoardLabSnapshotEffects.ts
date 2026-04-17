"use client";

import {
  type Dispatch,
  type MutableRefObject,
  type SetStateAction,
  useLayoutEffect,
} from "react";

import type { NavigationInfo } from "../controller/streamBoardTypes";
import {
  applyLabSnapshotHydrationPatch,
  buildLabSnapshotHydrationPatch,
  type LabSnapshotHydrationSinks,
} from "../controller/labSnapshotHydration";
import type { LabSnapshot } from "../stores/LabSessionContext";
import type { BaziMetadata } from "@/types/bazi";
import { mergeDecisionIdsPreferLocal, normalizedSnapshotDecisionIds } from "../controller/streamBoardPure";
import type { SeedPayload } from "../models";

type Params = {
  metadata: BaziMetadata | null;
  labSnapshot: LabSnapshot | null;
  lastSeedPayload: SeedPayload | null;
  inboxResetNonce: number;
  isSnapshotRestoringRef: MutableRefObject<boolean>;
  inboxNonceHandledRef: MutableRefObject<number>;
  navHandledRef: MutableRefObject<boolean>;
  /** 每帧更新 current，避免把 sinks 对象放进 effect 依赖导致无限重跑 */
  hydrationSinksRef: MutableRefObject<LabSnapshotHydrationSinks>;
  setConfirmedDecisionIds: Dispatch<SetStateAction<string[]>>;
  /** 与 useState 一致，支持函数式更新（inbox 重置时与快照并集，避免冲掉本地已裁决） */
  setResolvedCardIds: Dispatch<SetStateAction<string[]>>;
  setSelectionResetToken: Dispatch<SetStateAction<number>>;
};

/**
 * 实验室 snapshot → 本地 React 状态：首屏灌回、导航诊断、Inbox 同步。
 */
export function useStreamBoardLabSnapshotEffects(p: Params) {
  useLayoutEffect(() => {
    if (p.metadata !== null) return;
    const patch = buildLabSnapshotHydrationPatch(p.labSnapshot, p.lastSeedPayload);
    if (!patch) return;

    p.isSnapshotRestoringRef.current = true;
    try {
      applyLabSnapshotHydrationPatch(patch, p.hydrationSinksRef.current);
    } finally {
      queueMicrotask(() => {
        p.isSnapshotRestoringRef.current = false;
      });
    }
  }, [p.labSnapshot, p.lastSeedPayload, p.metadata, p.hydrationSinksRef, p.isSnapshotRestoringRef]);

  useLayoutEffect(() => {
    if (p.navHandledRef.current) return;
    if (typeof window === "undefined") return;
    p.navHandledRef.current = true;
    const params = new URLSearchParams(window.location.search);
    const hasSnapshot = Boolean(p.labSnapshot);
    const hasActiveSession = Boolean(p.labSnapshot?.active_session_id);
    const hasValidSnapshot = hasSnapshot && hasActiveSession;
    const navEntry = performance.getEntriesByType("navigation")[0] as PerformanceNavigationTiming | undefined;
    const navType = (navEntry?.type || "unknown") as NavigationInfo["navType"];
    const isReload = navType === "reload";
    const isBackForward = navType === "back_forward";
    const resumeFromMarker = false;
    let intent: NavigationInfo["intent"] = "FRESH_START";

    if (hasValidSnapshot && (isReload || isBackForward || resumeFromMarker)) {
      intent = "RESTORE_AUDIT";
    } else {
      intent = "FRESH_START";
    }

    const navInfo: NavigationInfo = {
      navType,
      hasValidSnapshot,
      intent,
    };
    const debugMode = (params.get("debug") || "").trim() === "1";
    if (debugMode) {
      // eslint-disable-next-line no-console
      console.info("[StateRecoveryAuditor]", navInfo);
    }
  }, [p.labSnapshot, p.navHandledRef]);

  useLayoutEffect(() => {
    const n = p.inboxResetNonce;
    if (n === 0 || n === p.inboxNonceHandledRef.current) return;
    p.inboxNonceHandledRef.current = n;
    const snapIds = normalizedSnapshotDecisionIds(p.labSnapshot?.decision_selection_ids);
    p.setConfirmedDecisionIds((prev) => mergeDecisionIdsPreferLocal(prev, snapIds));
    const incoming = (p.labSnapshot?.resolved_card_ids || []).map((x) => String(x));
    p.setResolvedCardIds((prev) => [...new Set([...prev, ...incoming])]);
    p.setSelectionResetToken((v) => v + 1);
    // 依赖刻意拆到具体字段：整包 `p` 常在父组件每次渲染新建，会误触发 inbox 重置。
    // eslint-disable-next-line react-hooks/exhaustive-deps -- narrow deps; full `p` unstable from parent
  }, [
    p.inboxResetNonce,
    p.labSnapshot?.decision_selection_ids,
    p.labSnapshot?.resolved_card_ids,
    p.inboxNonceHandledRef,
    p.setConfirmedDecisionIds,
    p.setResolvedCardIds,
    p.setSelectionResetToken,
  ]);
}
