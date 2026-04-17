import type { CSSProperties } from "react";

import type { StreamBoardViewModel } from "./models";

export function buildStreamBoardViewDerivedState(viewModel: StreamBoardViewModel) {
  const hardRouteLogs = ((((viewModel.physicsAudit as { trace?: { hard_route_logs?: string[] } } | null)?.trace?.hard_route_logs) || []) as string[]);
  const climateSeason = String(
    ((((viewModel.physicsAudit as { trace?: { climate_adjustment?: { season?: string } } } | null)?.trace?.climate_adjustment?.season) || "")),
  );
  const energyPeakAbs = Math.max(0, ...Object.values(viewModel.deityEnergyAxes).map((value) => Number(value?.absolute_energy || 0)));
  const workExpectation = Number((viewModel.finalWorkVector || {}).work_expectation || 0);
  const backfireRiskVal = Number((viewModel.finalWorkVector || {}).backfire_risk || 0);
  const releasedEnergyVal = Number((viewModel.finalWorkVector || {}).released_energy || 0);
  const streamThemeStyle = {
    "--stream-bg-color": viewModel.streamThemeChroma.bgColor,
    "--stream-overload-color": viewModel.streamThemeChroma.isConflictOverload ? "rgba(130,0,20,0.35)" : "transparent",
  } as CSSProperties;
  const summaryVersionLabel = `${viewModel.finalVerdictVersionId || `Conclusion v1.${viewModel.conclusionVersion}`} (Based on Physics v${String((viewModel.physicsAudit as { param_version_id?: string } | null)?.param_version_id || "--").slice(0, 8)})`;
  const hasVerdictHistory = viewModel.finalVerdictHistory.length > 1;

  return {
    hardRouteLogs,
    climateSeason,
    energyPeakAbs,
    workExpectation,
    backfireRiskVal,
    releasedEnergyVal,
    streamThemeStyle,
    summaryVersionLabel,
    hasVerdictHistory,
  };
}
