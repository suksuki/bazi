"use client";

import { useLayoutEffect, type MutableRefObject } from "react";
import type { BaziMetadata, TimelineSnapshot } from "@/types/bazi";
import { API_BASE } from "@/features/stream-board/constants";
import {
  buildBlindSchoolFeaturesPayload,
  extractMetricSnapshotFromPhysics,
  seedPayloadSignature,
} from "@/features/stream-board/controller/streamBoardPure";
import type {
  MetricSnapshot,
  SilentBoardCtx,
  SilentRecalcPersistSnapshotPayload,
  SilentRecalcPhysicsSetters,
} from "@/features/stream-board/controller/streamBoardTypes";
import type { DeityComponent, DeityEnergyAxis, LogicDiff, SeedPayload } from "@/features/stream-board/models";
import type { LabStoreState } from "@/features/stream-board/stores/LabSessionContext";

export type UseStreamBoardSilentRecalculateLayoutParams = {
  reCalculateAbsSilentlyImplRef: MutableRefObject<() => Promise<void>>;
  lastSeedPayloadRef: MutableRefObject<SeedPayload | null>;
  isSnapshotRestoringRef: MutableRefObject<boolean>;
  isRestoringRef: MutableRefObject<boolean>;
  labStateRef: MutableRefObject<LabStoreState>;
  verdictRecalcBarrierRef: MutableRefObject<boolean>;
  silentRecalcDeferredRef: MutableRefObject<boolean>;
  silentRecalcInFlightRef: MutableRefObject<boolean>;
  silentCtxRef: MutableRefObject<SilentBoardCtx>;
  settersRef: MutableRefObject<SilentRecalcPhysicsSetters>;
  refreshHealthRef: MutableRefObject<() => Promise<{ dbOk: boolean; llmOk: boolean }>>;
  referenceYearRef: MutableRefObject<number>;
  updateLogicDiffRef: MutableRefObject<(current: MetricSnapshot, forceBaseline?: boolean) => LogicDiff>;
  persistSnapshotRef: MutableRefObject<(payload: SilentRecalcPersistSnapshotPayload) => void>;
  bumpSyncBarrierSeq: () => void;
  scheduleInteractionHubPersist: () => void;
};

/**
 * 将静默 analyze-seed 重算实现挂到 ref，供插件配置漂移、显式重算等调用。
 * 与终判 barrier / 灌入还原互斥逻辑保留在实现体内，便于单测与主编排瘦身。
 */
export function useStreamBoardSilentRecalculateLayout({
  reCalculateAbsSilentlyImplRef,
  lastSeedPayloadRef,
  isSnapshotRestoringRef,
  isRestoringRef,
  labStateRef,
  verdictRecalcBarrierRef,
  silentRecalcDeferredRef,
  silentRecalcInFlightRef,
  silentCtxRef,
  settersRef,
  refreshHealthRef,
  referenceYearRef,
  updateLogicDiffRef,
  persistSnapshotRef,
  bumpSyncBarrierSeq,
  scheduleInteractionHubPersist,
}: UseStreamBoardSilentRecalculateLayoutParams) {
  useLayoutEffect(() => {
    reCalculateAbsSilentlyImplRef.current = async () => {
      const seed = lastSeedPayloadRef.current;
      if (!seed || isSnapshotRestoringRef.current || isRestoringRef.current) return;
      if (labStateRef.current.isFinalized) return;
      if (verdictRecalcBarrierRef.current) {
        silentRecalcDeferredRef.current = true;
        return;
      }
      if (silentRecalcInFlightRef.current) return;
      silentRecalcInFlightRef.current = true;
      const c = silentCtxRef.current;
      const set = settersRef.current;
      try {
        const latestHealth = await refreshHealthRef.current();
        const response = await fetch(`${API_BASE}/api/v1/analyze-seed`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            date: seed.date,
            time: seed.time,
            calendar: seed.calendar,
            gender: seed.gender,
            lang: c.lang,
            latitude: 31.2304,
            longitude: 121.4737,
            session_id: c.consultationId ?? undefined,
            physics_config: c.labConfig,
            enabled_plugins: [
              ...(c.pluginSwitches.blindSchool ? ["classical.blind_school.v1"] : []),
              ...(c.pluginSwitches.wangshuai ? ["classical.wangshuai.v1"] : []),
              ...(c.pluginSwitches.wealthRisk ? ["modern.wealth_risk.v1"] : []),
            ],
            blind_school_features: buildBlindSchoolFeaturesPayload(c.pluginSwitches),
            reference_year: referenceYearRef.current,
          }),
        });
        if (!response.ok) return;
        const data = await response.json();
        const tensor = (data.physics_tensor || null) as Record<string, unknown> | null;
        if (!tensor || typeof tensor !== "object") return;

        set.setMetadata(data.metadata as BaziMetadata);
        set.setTimeline((data.timeline ?? null) as TimelineSnapshot | null);
        if (tensor.deity_scores && typeof tensor.deity_scores === "object") {
          set.setDeityScores(tensor.deity_scores as Record<string, number>);
        }
        if (tensor.deity_energy_axes && typeof tensor.deity_energy_axes === "object") {
          set.setDeityEnergyAxes(tensor.deity_energy_axes as Record<string, DeityEnergyAxis>);
        }
        if (tensor.deity_components && typeof tensor.deity_components === "object") {
          set.setDeityComponents(tensor.deity_components as Record<string, DeityComponent>);
        }
        if (tensor.deity_trace_details && typeof tensor.deity_trace_details === "object") {
          set.setDeityTraceDetails(tensor.deity_trace_details as Record<string, Record<string, unknown>>);
        } else if ((tensor.meta as Record<string, unknown> | undefined)?.deity_trace_details) {
          set.setDeityTraceDetails(
            (tensor.meta as Record<string, unknown>).deity_trace_details as Record<string, Record<string, unknown>>,
          );
        } else {
          set.setDeityTraceDetails({});
        }
        if (tensor.audit_log && typeof tensor.audit_log === "object") {
          set.setPhysicsAudit(tensor.audit_log as Record<string, unknown>);
        }
        set.setPhysicsConfidence(typeof tensor.confidence === "number" ? tensor.confidence : null);
        if (Array.isArray(tensor.evidence)) {
          set.setPhysicsEvidence(tensor.evidence.map((item: unknown) => String(item)));
        } else {
          set.setPhysicsEvidence([]);
        }
        const pMeta = (tensor.meta || {}) as Record<string, unknown>;
        if (pMeta.params && typeof pMeta.params === "object") {
          set.setPhysicsParams(pMeta.params as Record<string, number>);
        }
        const ge = pMeta.global_entropy;
        set.setGlobalEntropy(typeof ge === "number" && Number.isFinite(ge) ? ge : null);

        const currentMetric = extractMetricSnapshotFromPhysics(tensor);
        updateLogicDiffRef.current(currentMetric, c.confirmedDecisionIds.length === 0 || !c.baselineMetrics);
        persistSnapshotRef.current({
          physics_tensor: tensor,
          metadata: data.metadata as Record<string, unknown>,
          timeline: (data.timeline ?? null) as Record<string, unknown> | null,
          llm_prompt: data.llm_prompt || "",
          audit_summary: data.audit_summary,
          consultationIdOverride: c.consultationId,
          healthOverride: latestHealth,
          seedSignatureOverride: seedPayloadSignature(seed),
        });
        bumpSyncBarrierSeq();
        scheduleInteractionHubPersist();
      } catch {
        /* silent */
      } finally {
        silentRecalcInFlightRef.current = false;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- ref 身份稳定；与旧 controller 一致仅随 bumpSync / hub 定时器策略重建
  }, [bumpSyncBarrierSeq, scheduleInteractionHubPersist]);
}
