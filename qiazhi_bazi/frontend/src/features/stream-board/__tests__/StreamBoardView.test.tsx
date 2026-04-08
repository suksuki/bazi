import React, { type ReactNode } from "react";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { StreamBoardView } from "@/features/stream-board/StreamBoardView";
import type { StreamBoardViewModel } from "@/features/stream-board/models";

vi.mock("@/components/AuditSidebar", () => ({
  AuditSidebar: ({ topSlot, middleSlot }: { topSlot?: ReactNode; middleSlot?: ReactNode }) => (
    <div>
      <div data-testid="audit-top">{topSlot}</div>
      <div data-testid="audit-middle">{middleSlot}</div>
    </div>
  ),
}));

vi.mock("@/components/BaziCard", () => ({
  BaziCard: () => <div data-testid="bazi-card">Bazi</div>,
}));

vi.mock("@/components/TenGodNumericList", () => ({
  TenGodNumericList: () => <div data-testid="ten-god-list">TenGod</div>,
}));

vi.mock("@/components/SeedInput", () => ({
  SeedInput: ({ onSubmit }: { onSubmit: (payload: { date: string; time: string; calendar: "solar" | "lunar" }) => Promise<void> }) => (
    <button type="button" onClick={() => void onSubmit({ date: "1990-01-01", time: "00:00", calendar: "solar" })}>
      submit-seed
    </button>
  ),
}));

vi.mock("@/components/AuditorBriefing", () => ({
  AuditorBriefing: () => <div data-testid="auditor-briefing">briefing</div>,
}));

vi.mock("@/components/LogDrawer", () => ({
  LogDrawer: () => <div data-testid="log-drawer">drawer</div>,
}));

vi.mock("@/components/ArbiterLogicDrawer", () => ({
  ArbiterLogicDrawer: () => <div data-testid="logic-drawer">logic</div>,
}));

function createViewModel(overrides: Partial<StreamBoardViewModel> = {}): StreamBoardViewModel {
  return {
    lang: "ZH",
    setLang: vi.fn(),
    busy: false,
    drawerOpen: false,
    setDrawerOpen: vi.fn(),
    consultationId: 12,
    metadata: null,
    timeline: null,
    selectedBranch: undefined,
    setSelectedBranch: vi.fn(),
    auditItems: [],
    health: { dbOk: true, llmOk: true },
    llmModelName: "gpt",
    i18nCalls: 0,
    deityScores: {},
    deityEnergyAxes: {},
    deityComponents: {},
    deityTraceDetails: {},
    hoveredDeity: undefined,
    setHoveredDeity: vi.fn(),
    confirmedConflicts: [],
    llmDiagnosticData: null,
    physicsParams: {},
    auditorProposalCards: [],
    autoConvertedParamKey: null,
    consensusHistory: [],
    cards: [
      {
        id: "conflict-1",
        title: "冲突确认：子午冲",
        markdown: "系统检测到 子午冲。",
        conflictDetail: "子午冲",
        displayText: "子午冲",
        cardType: "conflict",
      },
    ],
    resultLogs: [],
    finalVerdictBody: "",
    finalVerdictChangeLog: {},
    finalLogicalEvidence: [],
    finalWorkVector: null,
    finalVerdictHistory: [],
    selectionResetToken: 0,
    finalVerdictVersionId: "",
    conclusionVersion: 0,
    summaryChanged: false,
    l1Certified: false,
    physicsAudit: null,
    physicsConfidence: null,
    physicsEvidence: [],
    labConfig: {
      WEIGHT_LUCK: 0.4,
      WEIGHT_YEAR: 0.2,
      BASE_BACKFIRE_RISK: 0.2,
      HIGH_IMBALANCE_RISK: 0.35,
      TOMB_LOCK_RATE: 0.9,
    },
    setLabConfig: vi.fn(),
    showPhysicsAudit: false,
    setShowPhysicsAudit: vi.fn(),
    mergedSteps: [],
    logicDrawerOpen: false,
    logicDrawerTitle: "Logic",
    logicDrawerFocus: "",
    logicDrawerDetails: [],
    logicDrawerTrace: null,
    setLogicDrawerOpen: vi.fn(),
    onSeedSubmit: vi.fn().mockResolvedValue(undefined),
    addAuditorProposalToInbox: vi.fn(),
    onExecuteDecision: vi.fn().mockResolvedValue(undefined),
    openLogicDrawer: vi.fn(),
    openLogicDrawerByDeity: vi.fn(),
    onEvidenceItemClick: vi.fn(),
    showVerdictHistory: vi.fn(),
    onRollback: vi.fn().mockResolvedValue(undefined),
    applyCurrentSqlPatch: vi.fn().mockResolvedValue(undefined),
    applyLabConfigAndRecalculate: vi.fn().mockResolvedValue(undefined),
    t: (text) => text,
    ...overrides,
  };
}

describe("StreamBoardView", () => {
  it("wires the decision inbox selection flow to the controller callback", async () => {
    const viewModel = createViewModel();
    render(<StreamBoardView {...viewModel} />);

    await act(async () => {
      fireEvent.click(screen.getByLabelText("勾选 子午冲"));
    });
    await waitFor(() => expect(screen.getByRole("button", { name: /执行全局裁决/ })).toBeEnabled());

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /执行全局裁决/ }));
    });

    expect(viewModel.onExecuteDecision).toHaveBeenCalledWith([
      expect.objectContaining({ id: "conflict-1", conflictDetail: "子午冲" }),
    ]);
  });

  it("shows the auditor briefing when a logic proposal is present", () => {
    render(
      <StreamBoardView
        {...createViewModel({
          llmDiagnosticData: {
            alignment_score: 30,
            logic_proposal: { param_key: "CF_FLOATING_DECAY", sql_patch: "update" },
          },
        })}
      />,
    );

    expect(screen.getByTestId("auditor-briefing")).toBeInTheDocument();
  });

  it("renders physics confidence and evidence when available", () => {
    render(
      <StreamBoardView
        {...createViewModel({
          physicsAudit: { param_version_id: "v-demo" },
          physicsConfidence: 0.87,
          physicsEvidence: ["solar_term=立春", "conflict_count=1"],
        })}
      />,
    );

    expect(screen.getByText("Physics Confidence:")).toBeInTheDocument();
    expect(screen.getByText("87%")).toBeInTheDocument();
    expect(screen.getByText(/solar_term=立春/)).toBeInTheDocument();
  });
});
