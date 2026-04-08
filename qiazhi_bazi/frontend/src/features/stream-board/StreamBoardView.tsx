"use client";

import React from "react";
import { ArbiterLogicDrawer } from "@/components/ArbiterLogicDrawer";
import { AuditSidebar } from "@/components/AuditSidebar";
import { AuditorBriefing } from "@/components/AuditorBriefing";
import { BaziCard } from "@/components/BaziCard";
import { DecisionInbox } from "@/components/DecisionInbox";
import { LogicGlitchOverlay } from "@/components/LogicGlitchOverlay";
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
    finalTopologyGraphV1,
    finalStructureCandidatesV0,
    finalStructureFinalDecisionV0,
    stressTestResult,
    genderComparisonResult,
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
    pluginSwitches,
    setPluginSwitches,
    pluginWeights,
    setPluginWeights,
    streamThemeChroma,
    rerunFinalVerdictWithWeights,
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
    runStressTest,
    runGenderComparison,
    t,
  } = viewModel;

  const hardRouteLogs = ((((physicsAudit as { trace?: { hard_route_logs?: string[] } } | null)?.trace?.hard_route_logs) || []) as string[]);
  const climateSeason = String(
    ((((physicsAudit as { trace?: { climate_adjustment?: { season?: string } } } | null)?.trace?.climate_adjustment?.season) || "")),
  );
  const [labOpen, setLabOpen] = React.useState(true);
  const [labGroupsOpen, setLabGroupsOpen] = React.useState({
    timing: true,
    riskTomb: true,
    climateTopology: true,
  });
  const streamThemeStyle = {
    "--stream-bg-color": streamThemeChroma.bgColor,
    "--stream-overload-color": streamThemeChroma.isConflictOverload ? "rgba(130,0,20,0.35)" : "transparent",
  } as React.CSSProperties;

  const labGroups = [
    {
      key: "timing" as const,
      title: "时运权重",
      items: [
        ["WEIGHT_LUCK", 0, 1, 0.01],
        ["WEIGHT_YEAR", 0, 1, 0.01],
      ],
    },
    {
      key: "riskTomb" as const,
      title: "风险与墓库",
      items: [
        ["BASE_BACKFIRE_RISK", 0, 1, 0.01],
        ["HIGH_IMBALANCE_RISK", 0, 1, 0.01],
        ["TOMB_LOCK_RATE", 0, 1, 0.01],
      ],
    },
    {
      key: "climateTopology" as const,
      title: "气候与拓扑",
      items: [
        ["CLIMATE_INTENSITY", 0, 1, 0.01],
        ["STEM_RESONANCE_BOOST", 1, 3, 0.05],
        ["TRANSFER_DISTANCE_DECAY", 0, 0.5, 0.01],
        ["WORK_MIN_THRESHOLD", 0, 3, 0.1],
      ],
    },
  ];

  return (
    <main
      data-testid="stream-board-root"
      style={streamThemeStyle}
      className="mx-auto min-h-dvh w-full max-w-[1400px] px-3 py-4 transition-colors duration-500"
    >
      <div
        className="fixed inset-0 -z-10 transition-all duration-500"
        style={{
          background:
            "radial-gradient(120% 90% at 80% 10%, rgba(255,215,120,0.06), transparent 52%), linear-gradient(135deg, var(--stream-bg-color), #0f0f12 65%)",
          boxShadow: `inset 0 0 80px var(--stream-overload-color)`,
        }}
      />
      <LogicGlitchOverlay active={streamThemeChroma.isConflictOverload && streamThemeChroma.hasPolarityReversal} />
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
                tombLockRate={labConfig.TOMB_LOCK_RATE}
                tombReleased={Number((finalWorkVector || {}).released_energy || 0) > 0}
                climateIntensity={labConfig.CLIMATE_INTENSITY}
                climateSeason={climateSeason}
                onOpenLogic={openLogicDrawer}
                onHoverDeity={setHoveredDeity}
              />
            </div>
          ) : null}
        />

        <div className="flex-1 space-y-3">
          <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-3">
            <div className="mb-2 flex items-center justify-between">
              <button
                type="button"
                onClick={() => setLabOpen((v) => !v)}
                className="flex flex-1 items-center justify-between rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-left text-xs text-zinc-200 hover:bg-zinc-800"
              >
                <span className="text-sm font-medium text-zinc-200">Lab Console</span>
                <span>{labOpen ? "收起" : "展开"}</span>
              </button>
            </div>
            {labOpen ? (
              <div className="space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-[11px] text-zinc-300">
                    <span>插件管理</span>
                    <label className="inline-flex items-center gap-1">
                      <input
                        type="checkbox"
                        checked={pluginSwitches.blindSchool}
                        onChange={(e) => setPluginSwitches((prev) => ({ ...prev, blindSchool: e.target.checked }))}
                      />
                      盲派
                    </label>
                    <label className="inline-flex items-center gap-1">
                      <input
                        type="checkbox"
                        checked={pluginSwitches.wangshuai}
                        onChange={(e) => setPluginSwitches((prev) => ({ ...prev, wangshuai: e.target.checked }))}
                      />
                      旺衰
                    </label>
                    <label className="inline-flex items-center gap-1">
                      <input
                        type="checkbox"
                        checked={pluginSwitches.wealthRisk}
                        onChange={(e) => setPluginSwitches((prev) => ({ ...prev, wealthRisk: e.target.checked }))}
                      />
                      财富评估
                    </label>
                  </div>
                  <label className="inline-flex items-center gap-2 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-[11px] text-zinc-300">
                    <input
                      type="checkbox"
                      checked={Number(labConfig.SHOW_WEAK_WORK_PATHS || 0) > 0.5}
                      onChange={(e) => {
                        setLabConfig((prev) => ({
                          ...prev,
                          SHOW_WEAK_WORK_PATHS: e.target.checked ? 1 : 0,
                        }));
                      }}
                    />
                    逻辑透深（显示微弱路径）
                  </label>
                  <button
                    type="button"
                    onClick={() => setLabGroupsOpen({ timing: true, riskTomb: true, climateTopology: true })}
                    className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-[11px] text-zinc-300 hover:bg-zinc-800"
                  >
                    展开全部参数组
                  </button>
                  <button
                    type="button"
                    onClick={() => setLabGroupsOpen({ timing: false, riskTomb: false, climateTopology: false })}
                    className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-[11px] text-zinc-300 hover:bg-zinc-800"
                  >
                    收起全部参数组
                  </button>
                  <button
                    type="button"
                    onClick={() => void applyLabConfigAndRecalculate()}
                    className="rounded-md border border-cyan-500/40 bg-cyan-500/10 px-2 py-1 text-xs text-cyan-200"
                  >
                    应用并重算
                  </button>
                </div>
                {labGroups.map((group) => (
                  <div key={group.key} className="rounded-xl border border-zinc-800 bg-zinc-950 p-2">
                    <button
                      type="button"
                      onClick={() => setLabGroupsOpen((prev) => ({ ...prev, [group.key]: !prev[group.key] }))}
                      className="flex w-full items-center justify-between rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-left text-xs text-zinc-200 hover:bg-zinc-800"
                    >
                      <span>{group.title}</span>
                      <span>{labGroupsOpen[group.key] ? "收起" : "展开"}</span>
                    </button>
                    {labGroupsOpen[group.key] ? (
                      <div className="mt-2 grid grid-cols-1 gap-2 md:grid-cols-2">
                        {group.items.map(([key, min, max, step]) => (
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
                    ) : null}
                  </div>
                ))}
              </div>
            ) : null}
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
            topologyGraph={finalTopologyGraphV1 || {}}
            structureCandidates={finalStructureCandidatesV0 || {}}
            structureFinalDecision={finalStructureFinalDecisionV0 || {}}
            metadata={metadata || {}}
            stressTestResult={stressTestResult || {}}
            genderComparisonResult={genderComparisonResult || {}}
            highlightVerdict={false}
            onExecuteDecision={(selected) => onExecuteDecision(selected as InboxCard[])}
            onVerdictDeityClick={openLogicDrawerByDeity}
            onStrategicDeityHover={setHoveredDeity}
            onEvidenceClick={onEvidenceItemClick}
            onShowVersionHistory={showVerdictHistory}
            hasVerdictHistory={finalVerdictHistory.length > 1}
            selectionResetToken={selectionResetToken}
            summaryVersionLabel={`${finalVerdictVersionId || `Conclusion v1.${conclusionVersion}`} (Based on Physics v${String((physicsAudit as { param_version_id?: string } | null)?.param_version_id || "--").slice(0, 8)})`}
            summaryChanged={summaryChanged}
            l1Certified={l1Certified}
            t={t}
            onStressTest={runStressTest}
            onGenderCompare={runGenderComparison}
            pluginWeights={pluginWeights}
            onPluginWeightsChange={setPluginWeights}
            onApplyPluginWeights={rerunFinalVerdictWithWeights}
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
