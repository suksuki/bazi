"use client";

import { useState } from "react";

import type { FinalVerdictChangeLog, FinalVerdictHistoryItem } from "../models";
import type { StreamBoardHydrationSnapshot } from "./streamBoardSnapshotTypes";

/**
 * 终审文案、结构候选、版本与结论摘要相关状态（Stream Board 子域）。
 */
export function useStreamBoardVerdictState(initialSnapshot: StreamBoardHydrationSnapshot) {
  const [conclusionVersion, setConclusionVersion] = useState(0);
  const [lastConclusionText, setLastConclusionText] = useState("");
  const [summaryChanged, setSummaryChanged] = useState(false);
  const [finalVerdictBody, setFinalVerdictBody] = useState(() => String(initialSnapshot?.final_verdict?.body || ""));
  const [finalVerdictChangeLog, setFinalVerdictChangeLog] = useState<FinalVerdictChangeLog>(
    () => (initialSnapshot?.final_verdict?.change_log || {}) as FinalVerdictChangeLog,
  );
  const [finalVerdictVersionId, setFinalVerdictVersionId] = useState(() =>
    String(initialSnapshot?.final_verdict?.version_id || ""),
  );
  const [finalLogicalEvidence, setFinalLogicalEvidence] = useState<string[]>(() => {
    const le = initialSnapshot?.final_verdict?.logical_evidence;
    return Array.isArray(le) ? le.map((x) => String(x)) : [];
  });
  const [finalWorkVector, setFinalWorkVector] = useState<Record<string, unknown> | null>(
    () => (initialSnapshot?.final_verdict?.work_vector as Record<string, unknown>) || null,
  );
  const [finalTopologyGraphV1, setFinalTopologyGraphV1] = useState<Record<string, unknown> | null>(
    () => (initialSnapshot?.final_verdict?.topology_graph_v1 as Record<string, unknown>) || null,
  );
  const [finalStructureCandidatesV0, setFinalStructureCandidatesV0] = useState<Record<string, unknown> | null>(
    () => (initialSnapshot?.final_verdict?.structure_candidates_v0 as Record<string, unknown>) || null,
  );
  const [finalStructureFinalDecisionV0, setFinalStructureFinalDecisionV0] = useState<Record<string, unknown> | null>(
    () => (initialSnapshot?.final_verdict?.structure_final_decision_v0 as Record<string, unknown>) || null,
  );
  const [finalVerdictHistory, setFinalVerdictHistory] = useState<FinalVerdictHistoryItem[]>([]);

  return {
    conclusionVersion,
    setConclusionVersion,
    lastConclusionText,
    setLastConclusionText,
    summaryChanged,
    setSummaryChanged,
    finalVerdictBody,
    setFinalVerdictBody,
    finalVerdictChangeLog,
    setFinalVerdictChangeLog,
    finalVerdictVersionId,
    setFinalVerdictVersionId,
    finalLogicalEvidence,
    setFinalLogicalEvidence,
    finalWorkVector,
    setFinalWorkVector,
    finalTopologyGraphV1,
    setFinalTopologyGraphV1,
    finalStructureCandidatesV0,
    setFinalStructureCandidatesV0,
    finalStructureFinalDecisionV0,
    setFinalStructureFinalDecisionV0,
    finalVerdictHistory,
    setFinalVerdictHistory,
  };
}
