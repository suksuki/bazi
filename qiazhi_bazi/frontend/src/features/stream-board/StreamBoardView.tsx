"use client";

import React from "react";
import { ArbiterLogicDrawer } from "@/components/ArbiterLogicDrawer";
import { AuditSidebar } from "@/components/AuditSidebar";
import { AuditorBriefing } from "@/components/AuditorBriefing";
import { BaziCard } from "@/components/BaziCard";
import { DecisionInbox } from "@/components/DecisionInbox";
import { LogDrawer } from "@/components/LogDrawer";
import { SeedInput } from "@/components/SeedInput";
import { TenGodNumericList } from "@/components/TenGodNumericList";
import { I18N } from "./constants";
import type { InboxCard, StreamBoardViewModel } from "./models";

export function StreamBoardView(viewModel: StreamBoardViewModel) {
  const {
    lang,
    setLang,
    busy,
    drawerOpen,
    setDrawerOpen,
    consultationId,
    metadata,
    timeline,
    selectedBranch,
    setSelectedBranch,
    auditItems,
    health,
    llmModelName,
    i18nCalls,
    deityScores,
    deityEnergyAxes,
    deityComponents,
    deityTraceDetails,
    hoveredDeity,
    setHoveredDeity,
    confirmedConflicts,
    llmDiagnosticData,
    physicsParams,
    auditorProposalCards,
    autoConvertedParamKey,
    consensusHistory,
    cards,
    resultLogs,
    finalVerdictBody,
    finalVerdictChangeLog,
    finalLogicalEvidence,
    finalWorkVector,
    finalVerdictHistory,
    selectionResetToken,
    finalVerdictVersionId,
    conclusionVersion,
    summaryChanged,
    l1Certified,
    physicsAudit,
    physicsConfidence,
    physicsEvidence,
    labConfig,
    setLabConfig,
    showPhysicsAudit,
    setShowPhysicsAudit,
    mergedSteps,
    logicDrawerOpen,
    logicDrawerTitle,
    logicDrawerFocus,
    logicDrawerDetails,
    logicDrawerTrace,
    setLogicDrawerOpen,
    onSeedSubmit,
    addAuditorProposalToInbox,
    onExecuteDecision,
    openLogicDrawer,
    openLogicDrawerByDeity,
    onEvidenceItemClick,
    showVerdictHistory,
    onRollback,
    applyCurrentSqlPatch,
    applyLabConfigAndRecalculate,
    t,
  } = viewModel;

  const hardRouteLogs = ((((physicsAudit as { trace?: { hard_route_logs?: string[] } } | null)?.trace?.hard_route_logs) || []) as string[]);

  return (
    <main className="mx-auto min-h-dvh w-full max-w-[1400px] px-3 py-4">
      <header className="mb-3 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">{t(I18N[lang].title)}</h1>
          <p className="text-xs text-zinc-500">{t(I18N[lang].subtitle)}</p>
          <span className="mt-1 inline-flex rounded-md border border-emerald-500/40 bg-emerald-500/10 px-2 py-0.5 text-[10px] text-emerald-300">
            Layer 1 Fully Aligned
          </span>
        </div>
        <div className="flex items-center gap-1">
          {(["ZH", "EN", "KO"] as const).map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => setLang(item)}
              className={`rounded-md px-2 py-1 text-xs ${lang === item ? "bg-amber-500 text-zinc-950" : "bg-zinc-800 text-zinc-300"}`}
            >
              {item}
            </button>
          ))}
          <button
            type="button"
            onClick={() => setDrawerOpen(true)}
            className="ml-1 rounded-md bg-zinc-800 px-2 py-1 text-xs text-zinc-300"
          >
            {t("历史")}
          </button>
        </div>
      </header>

      <div className="flex flex-col gap-3 md:flex-row">
        <AuditSidebar
          items={auditItems}
          dbOk={health.dbOk}
          llmOk={health.llmOk}
          llmModelName={llmModelName}
          i18nCalls={i18nCalls}
          sessionId={consultationId}
          t={t}
          topSlot={(
            <BaziCard
              metadata={metadata}
              timeline={timeline}
              deityScores={deityScores}
              deityEnergyAxes={deityEnergyAxes}
              rootDetailsByDeity={deityComponents}
              hoveredDeity={hoveredDeity}
              selected={selectedBranch}
              confirmedConflictDetails={confirmedConflicts}
              onPickBranch={setSelectedBranch}
              t={t}
              lang={lang}
            />
          )}
          middleSlot={Object.keys(deityScores).length > 0 ? (
            <div className="relative">
              <TenGodNumericList
                deityScores={deityScores}
                deityEnergyAxes={deityEnergyAxes}
                deityComponents={deityComponents}
                deityTraceDetails={deityTraceDetails}
                topAnomaly={llmDiagnosticData?.top_anomaly}
                consensusHistory={consensusHistory}
                hardRouteLogs={hardRouteLogs}
                onOpenLogic={openLogicDrawer}
                onHoverDeity={setHoveredDeity}
              />
            </div>
          ) : null}
        />

        <div className="flex-1 space-y-3">
          <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-3">
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-medium text-zinc-200">Lab Console</h3>
              <button
                type="button"
                onClick={() => void applyLabConfigAndRecalculate()}
                className="rounded-md border border-cyan-500/40 bg-cyan-500/10 px-2 py-1 text-xs text-cyan-200"
              >
                应用并重算
              </button>
            </div>
            <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
              {[
                ["WEIGHT_LUCK", 0, 1, 0.01],
                ["WEIGHT_YEAR", 0, 1, 0.01],
                ["BASE_BACKFIRE_RISK", 0, 1, 0.01],
                ["HIGH_IMBALANCE_RISK", 0, 1, 0.01],
                ["TOMB_LOCK_RATE", 0, 1, 0.01],
              ].map(([key, min, max, step]) => (
                <label key={key} className="text-xs text-zinc-300">
                  <div className="mb-1 flex items-center justify-between">
                    <span>{key}</span>
                    <span className="text-zinc-500">{Number(labConfig[key as keyof typeof labConfig]).toFixed(2)}</span>
                  </div>
                  <input
                    type="range"
                    min={Number(min)}
                    max={Number(max)}
                    step={Number(step)}
                    value={Number(labConfig[key as keyof typeof labConfig])}
                    onChange={(e) => {
                      const value = Number(e.target.value);
                      setLabConfig((prev) => ({ ...prev, [key]: value }));
                    }}
                    className="w-full"
                  />
                </label>
              ))}
            </div>
          </section>
          <SeedInput onSubmit={onSeedSubmit} busy={busy} t={t} />
          {llmDiagnosticData?.logic_proposal ? (
            <AuditorBriefing
              t={t}
              causalReasoning={llmDiagnosticData.causal_reasoning}
              tuningSuggestions={llmDiagnosticData.tuning_suggestions}
              logicProposal={llmDiagnosticData.logic_proposal}
              currentParams={physicsParams}
              alreadyAdded={auditorProposalCards.some((card) => card.proposal?.param_key === llmDiagnosticData.logic_proposal?.param_key)}
              autoConverted={autoConvertedParamKey === llmDiagnosticData.logic_proposal?.param_key}
              alignmentScore={llmDiagnosticData.alignment_score}
              structuredHit={llmDiagnosticData.structured_hit}
              repairMode={llmDiagnosticData.repair_mode}
              onAddToInbox={addAuditorProposalToInbox}
            />
          ) : null}
          <DecisionInbox
            cards={cards}
            resultLogs={resultLogs}
            verdictBody={finalVerdictBody}
            verdictChangeLog={finalVerdictChangeLog}
            logicalEvidence={finalLogicalEvidence}
            workVector={finalWorkVector || {}}
            highlightVerdict={false}
            onExecuteDecision={(selected) => onExecuteDecision(selected as InboxCard[])}
            onVerdictDeityClick={openLogicDrawerByDeity}
            onEvidenceClick={onEvidenceItemClick}
            onShowVersionHistory={showVerdictHistory}
            hasVerdictHistory={finalVerdictHistory.length > 1}
            selectionResetToken={selectionResetToken}
            summaryVersionLabel={`${finalVerdictVersionId || `Conclusion v1.${conclusionVersion}`} (Based on Physics v${String((physicsAudit as { param_version_id?: string } | null)?.param_version_id || "--").slice(0, 8)})`}
            summaryChanged={summaryChanged}
            l1Certified={l1Certified}
            t={t}
          />

          {physicsAudit ? (
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-3">
              {physicsConfidence !== null || physicsEvidence.length > 0 ? (
                <div className="mb-2 rounded-lg border border-zinc-700 bg-zinc-950/70 px-3 py-2 text-xs text-zinc-300">
                  <div className="flex items-center gap-2">
                    <span className="text-zinc-400">Physics Confidence:</span>
                    <span className="font-medium text-emerald-300">
                      {physicsConfidence !== null ? `${Math.round(physicsConfidence * 100)}%` : "--"}
                    </span>
                  </div>
                  {physicsEvidence.length > 0 ? (
                    <p className="mt-1 text-[11px] text-zinc-500">
                      Evidence: {physicsEvidence.slice(0, 2).join(" | ")}
                    </p>
                  ) : null}
                </div>
              ) : null}
              <button
                type="button"
                onClick={() => setShowPhysicsAudit((value) => !value)}
                className="rounded border border-zinc-700 bg-zinc-800 px-2 py-1 text-xs text-zinc-300"
              >
                {showPhysicsAudit ? "隐藏审计链路" : "查看审计链路"}
              </button>
              {showPhysicsAudit ? (
                <pre className="mt-2 max-h-64 overflow-auto rounded border border-zinc-800 bg-zinc-950 p-2 text-[11px] text-zinc-300">
                  {JSON.stringify(physicsAudit, null, 2)}
                </pre>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>

      <LogDrawer open={drawerOpen} steps={mergedSteps} onClose={() => setDrawerOpen(false)} onRollback={onRollback} t={t} />
      <ArbiterLogicDrawer
        open={logicDrawerOpen}
        title={logicDrawerTitle}
        focus={logicDrawerFocus}
        details={logicDrawerDetails.length ? logicDrawerDetails : [llmDiagnosticData?.causal_reasoning || "暂无批注内容。"]}
        deityTrace={logicDrawerTrace}
        auditSource={physicsAudit}
        onClose={() => setLogicDrawerOpen(false)}
        onApplySql={applyCurrentSqlPatch}
      />
    </main>
  );
}
