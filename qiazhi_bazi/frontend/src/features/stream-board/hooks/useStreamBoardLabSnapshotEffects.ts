"use client";

import { type Dispatch, type MutableRefObject, type SetStateAction, useEffect, useLayoutEffect } from "react";

import type { NavigationInfo } from "../controller/streamBoardTypes";
import {
  applyLabSnapshotHydrationPatch,
  buildLabSnapshotHydrationPatch,
  type LabSnapshotHydrationSinks,
} from "../controller/labSnapshotHydration";
import type { LabSnapshot } from "../stores/LabSessionContext";
import type { BaziMetadata } from "@/types/bazi";
import { normalizedSnapshotDecisionIds } from "../controller/streamBoardPure";
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
  setSnapshotAvailable: (v: boolean) => void;
  setConfirmedDecisionIds: (v: string[]) => void;
  setResolvedCardIds: (v: string[]) => void;
  setSelectionResetToken: Dispatch<SetStateAction<number>>;
};

/**
 * 实验室 snapshot → 本地 React 状态：首屏灌回、导航诊断、Inbox 与 snapshot 可用标志。
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
  }, [p.labSnapshot, p.lastSeedPayload, p.metadata]);

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
  }, [p.labSnapshot]);

  useEffect(() => {
    p.setSnapshotAvailable(Boolean(p.labSnapshot));
  }, [p.labSnapshot, p.setSnapshotAvailable]);

  useLayoutEffect(() => {
    const n = p.inboxResetNonce;
    if (n === 0 || n === p.inboxNonceHandledRef.current) return;
    p.inboxNonceHandledRef.current = n;
    p.setConfirmedDecisionIds(normalizedSnapshotDecisionIds(p.labSnapshot?.decision_selection_ids));
    p.setResolvedCardIds((p.labSnapshot?.resolved_card_ids || []).map((x) => String(x)));
    p.setSelectionResetToken((v) => v + 1);
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
