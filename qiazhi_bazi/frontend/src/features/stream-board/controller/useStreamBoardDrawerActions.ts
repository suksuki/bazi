import { useCallback } from "react";
import type { FinalVerdictHistoryItem } from "@/features/stream-board/models";

export interface StreamBoardDrawerDeps {
  deityScores: Record<string, number>;
  deityTraceDetails: Record<string, Record<string, unknown>>;
  finalVerdictHistory: FinalVerdictHistoryItem[];
  setLogicDrawerTitle: (val: string) => void;
  setLogicDrawerFocus: (val: string) => void;
  setLogicDrawerDetails: (val: string[]) => void;
  setLogicDrawerTrace: (val: Record<string, unknown> | null) => void;
  setLogicDrawerOpen: (val: boolean) => void;
}

export function useStreamBoardDrawerActions(depsRef: React.MutableRefObject<StreamBoardDrawerDeps>) {
  const openLogicDrawer = useCallback((payload: { title: string; focus: string; details: string[]; deityTrace?: Record<string, unknown> }) => {
    const deps = depsRef.current;
    deps.setLogicDrawerTitle(payload.title);
    deps.setLogicDrawerFocus(payload.focus);
    deps.setLogicDrawerDetails(payload.details);
    deps.setLogicDrawerTrace(payload.deityTrace || null);
    deps.setLogicDrawerOpen(true);
  }, [depsRef]);

  const openLogicDrawerByDeity = useCallback((deity: string) => {
    const deps = depsRef.current;
    const trace = deps.deityTraceDetails?.[deity] as Record<string, unknown> | undefined;
    openLogicDrawer({
      title: `${deity} 演算路径`,
      focus: deity,
      details: [`${deity}: ${Number(deps.deityScores[deity] ?? 0).toFixed(2)}%`, "来自 Result Summary 点击下钻。"],
      deityTrace: trace,
    });
  }, [depsRef, openLogicDrawer]);

  const onEvidenceItemClick = useCallback((evidence: string) => {
    const text = String(evidence || "");
    const deityNames = ["比肩", "劫财", "食神", "伤官", "正财", "偏财", "正官", "七杀", "正印", "偏印"];
    const hit = deityNames.find((name) => text.includes(name));
    if (hit) {
      openLogicDrawerByDeity(hit);
      return;
    }

    openLogicDrawer({
      title: "证据条目下钻",
      focus: "Logical Evidence",
      details: [text, "该证据暂未映射到特定十神，已展示原始条目。"],
    });
  }, [openLogicDrawerByDeity, openLogicDrawer]);

  const showVerdictHistory = useCallback(() => {
    const deps = depsRef.current;
    if (deps.finalVerdictHistory.length === 0) return;

    const lines = deps.finalVerdictHistory
      .map((item, index) => `#${index + 1} ${item.versionId} @ ${new Date(item.createdAt).toLocaleString()}`)
      .concat(["---"])
      .concat(
        deps.finalVerdictHistory.flatMap((item) => [
          `【${item.versionId}】`,
          item.body,
          ...(item.changeLog.physics_diff || []).map((change) => `[物理] ${change}`),
          ...(item.changeLog.consensus_diff || []).map((change) => `[共识] ${change}`),
          ...(item.changeLog.text_diff_hint ? [`[判词] ${item.changeLog.text_diff_hint}`] : []),
          ...(item.logicalEvidence || []).slice(0, 6).map((evidence) => `[证据] ${evidence}`),
          "",
        ]),
      );

    openLogicDrawer({
      title: "Result Summary 版本回放",
      focus: "Final Verdict History",
      details: lines,
    });
  }, [depsRef, openLogicDrawer]);

  return { openLogicDrawer, openLogicDrawerByDeity, onEvidenceItemClick, showVerdictHistory };
}
