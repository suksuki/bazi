"use client";

import { useState } from "react";

import type { DeityComponent, DeityEnergyAxis } from "../models";
import type { StreamBoardHydrationSnapshot } from "./streamBoardSnapshotTypes";

/** physics_tensor 在 UI 上的切片：十神分、审计摘要、气候熵等 */
export function useStreamBoardPhysicsState(initialSnapshot: StreamBoardHydrationSnapshot) {
  const [deityScores, setDeityScores] = useState<Record<string, number>>(
    () => ((initialSnapshot?.physics_tensor?.deity_scores as Record<string, number> | undefined) || {}),
  );
  const [deityEnergyAxes, setDeityEnergyAxes] = useState<Record<string, DeityEnergyAxis>>(
    () => ((initialSnapshot?.physics_tensor?.deity_energy_axes as Record<string, DeityEnergyAxis> | undefined) || {}),
  );
  const [deityComponents, setDeityComponents] = useState<Record<string, DeityComponent>>(
    () => ((initialSnapshot?.physics_tensor?.deity_components as Record<string, DeityComponent> | undefined) || {}),
  );
  const [deityTraceDetails, setDeityTraceDetails] = useState<Record<string, Record<string, unknown>>>(
    () =>
      ((initialSnapshot?.physics_tensor?.deity_trace_details as Record<string, Record<string, unknown>> | undefined) ||
        {}),
  );
  const [physicsAudit, setPhysicsAudit] = useState<Record<string, unknown> | null>(null);
  const [physicsConfidence, setPhysicsConfidence] = useState<number | null>(null);
  const [physicsEvidence, setPhysicsEvidence] = useState<string[]>([]);
  const [physicsParams, setPhysicsParams] = useState<Record<string, number>>({});
  const [globalEntropy, setGlobalEntropy] = useState<number | null>(null);

  return {
    deityScores,
    setDeityScores,
    deityEnergyAxes,
    setDeityEnergyAxes,
    deityComponents,
    setDeityComponents,
    deityTraceDetails,
    setDeityTraceDetails,
    physicsAudit,
    setPhysicsAudit,
    physicsConfidence,
    setPhysicsConfidence,
    physicsEvidence,
    setPhysicsEvidence,
    physicsParams,
    setPhysicsParams,
    globalEntropy,
    setGlobalEntropy,
  };
}
