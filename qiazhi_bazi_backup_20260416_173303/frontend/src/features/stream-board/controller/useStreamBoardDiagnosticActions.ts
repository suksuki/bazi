import { useCallback } from "react";
import type { Lang, BaziMetadata } from "@/types/bazi";
import type { PhysicsLabConfig, PluginSwitches, PluginWeights, SeedPayload } from "@/features/stream-board/models";
import { API_BASE } from "../constants";
import { buildBlindSchoolFeaturesPayload, buildPhysicsConfigPayload, buildStreamBoardEnabledPlugins } from "./streamBoardPure";
import { interpolateColor } from "./streamBoardPure";

export interface StreamBoardDiagnosticDeps {
  metadata: BaziMetadata | null;
  lastSeedPayload: SeedPayload | null;
  labConfig: PhysicsLabConfig;
  pluginSwitches: PluginSwitches;
  /** URL ``?pure_physics_audit=1`` 时省略格局插件 */
  purePhysicsAudit?: boolean;
  pluginWeights: PluginWeights;
  lang: Lang;
  finalStructureFinalDecisionV0: Record<string, unknown> | null;
  referenceYearRef: React.MutableRefObject<number>;
  setStressTestResult: React.Dispatch<React.SetStateAction<Record<string, unknown> | null>>;
  setGenderComparisonResult: React.Dispatch<React.SetStateAction<Record<string, unknown> | null>>;
  setResultLogs: React.Dispatch<React.SetStateAction<string[]>>;
}

export function useStreamBoardDiagnosticActions(depsRef: React.MutableRefObject<StreamBoardDiagnosticDeps>) {
  const runStressTest = useCallback(async (scenario: string) => {
    const deps = depsRef.current;
    if (!deps.metadata) return;
    const parts = String(scenario || "").split(/[,\s/]+/).filter(Boolean);
    const yearPillar = parts[0] || "";
    const luckPillar = parts[1] || "";
    const response = await fetch(`${API_BASE}/api/v1/analyze/stress-test`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        metadata: deps.metadata,
        gender: ((deps.metadata as Record<string, unknown>)?.gender as string) || "male",
        physics_config: buildPhysicsConfigPayload(deps.labConfig),
        baseline_structure_final_decision: deps.finalStructureFinalDecisionV0 || {},
        year_pillar: yearPillar,
        luck_pillar: luckPillar,
        enabled_plugins: buildStreamBoardEnabledPlugins(deps.pluginSwitches, {
          purePhysicsAudit: Boolean(deps.purePhysicsAudit),
        }),
        lang: deps.lang,
      }),
    });
    const data = await response.json().catch(() => ({}));
    if (response.ok && data?.ok) {
      deps.setStressTestResult(data as Record<string, unknown>);
      deps.setResultLogs((prev) => [
        ...prev,
        `🧪 压力测试 ${yearPillar}${luckPillar ? `/${luckPillar}` : ""} -> rollback=${Boolean(data.rollback_triggered)} ΔAbs=${Number(data.delta_abs || 0).toFixed(2)}`,
      ]);
    } else {
      deps.setResultLogs((prev) => [...prev, `❌ 压力测试失败：${String(data?.detail || "unknown")}`]);
    }
  }, [depsRef]);

  const runGenderComparison = useCallback(async () => {
    const deps = depsRef.current;
    if (!deps.lastSeedPayload) return;
    const base = {
      date: deps.lastSeedPayload.date,
      time: deps.lastSeedPayload.time,
      calendar: deps.lastSeedPayload.calendar,
      lang: deps.lang,
      latitude: 31.2304,
      longitude: 121.4737,
      physics_config: buildPhysicsConfigPayload(deps.labConfig),
      enabled_plugins: buildStreamBoardEnabledPlugins(deps.pluginSwitches, {
        purePhysicsAudit: Boolean(deps.purePhysicsAudit),
      }),
      blind_school_features: buildBlindSchoolFeaturesPayload(deps.pluginSwitches),
      reference_year: deps.referenceYearRef.current,
    };
    const [maleResp, femaleResp] = await Promise.all([
      fetch(`${API_BASE}/api/v1/analyze-seed`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...base, gender: "male" }),
      }),
      fetch(`${API_BASE}/api/v1/analyze-seed`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...base, gender: "female" }),
      }),
    ]);
    const maleData = await maleResp.json().catch(() => ({}));
    const femaleData = await femaleResp.json().catch(() => ({}));
    const maleAxes = (maleData?.physics_tensor?.deity_energy_axes || {}) as Record<string, { absolute_energy?: number }>;
    const femaleAxes = (femaleData?.physics_tensor?.deity_energy_axes || {}) as Record<string, { absolute_energy?: number }>;
    const malePeakAbs = Math.max(0, ...Object.values(maleAxes).map((v) => Number(v?.absolute_energy || 0)));
    const femalePeakAbs = Math.max(0, ...Object.values(femaleAxes).map((v) => Number(v?.absolute_energy || 0)));

    const [maleVerdictResp, femaleVerdictResp] = await Promise.all([
      fetch(`${API_BASE}/api/v1/final-verdict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          metadata: maleData?.metadata || {},
          physics_tensor: maleData?.physics_tensor || {},
          selected_cards: [],
          consensus_history: [],
          enabled_plugins: buildStreamBoardEnabledPlugins(deps.pluginSwitches, {
            purePhysicsAudit: Boolean(deps.purePhysicsAudit),
          }),
          plugin_weights: {
            "classical.blind_school.v1": Number(deps.pluginWeights.blindSchool || 0),
            "classical.wangshuai.v1": Number(deps.pluginWeights.wangshuai || 0),
          },
          clear_previous_verdict: true,
          force_clear_cache: true,
          lang: deps.lang,
        }),
      }),
      fetch(`${API_BASE}/api/v1/final-verdict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          metadata: femaleData?.metadata || {},
          physics_tensor: femaleData?.physics_tensor || {},
          selected_cards: [],
          consensus_history: [],
          enabled_plugins: buildStreamBoardEnabledPlugins(deps.pluginSwitches, {
            purePhysicsAudit: Boolean(deps.purePhysicsAudit),
          }),
          plugin_weights: {
            "classical.blind_school.v1": Number(deps.pluginWeights.blindSchool || 0),
            "classical.wangshuai.v1": Number(deps.pluginWeights.wangshuai || 0),
          },
          clear_previous_verdict: true,
          force_clear_cache: true,
          lang: deps.lang,
        }),
      }),
    ]);
    const maleVerdict = await maleVerdictResp.json().catch(() => ({}));
    const femaleVerdict = await femaleVerdictResp.json().catch(() => ({}));
    const maleWork = Number(maleVerdict?.work_vector?.work_expectation || 0);
    const femaleWork = Number(femaleVerdict?.work_vector?.work_expectation || 0);
    const toPathBreakScore = (verdict: Record<string, unknown>) => {
      const vectors = (((verdict?.work_vector as { work_vectors?: Array<Record<string, unknown>> } | undefined)?.work_vectors) || []);
      const ziwu = vectors.filter((item) => String(item?.detail || "").includes("子午冲"));
      if (ziwu.length === 0) return 0;
      const scores = ziwu.map((item) => {
        const gain = Number(item?.unlock_gain || 0);
        const risk = Number(item?.backfire_risk || 0);
        if (gain <= 0) return 1;
        return Math.max(0, Math.min(1, risk / gain));
      });
      return Math.max(...scores);
    };
    const malePathBreakScore = toPathBreakScore(maleVerdict as Record<string, unknown>);
    const femalePathBreakScore = toPathBreakScore(femaleVerdict as Record<string, unknown>);
    const totalWeight = Math.max(0.0001, Number(deps.pluginWeights.blindSchool || 0) + Number(deps.pluginWeights.wangshuai || 0));
    const blindRatio = Number(deps.pluginWeights.blindSchool || 0) / totalWeight;
    const maleThemeColor = interpolateColor("#2D4F1E", "#1A1A1A", blindRatio);
    const femaleThemeColor = interpolateColor("#2D4F1E", "#1A1A1A", 1 - blindRatio);
    const summary = `若为坤造（女），当前做功净值从 ${maleWork.toFixed(2)} 变化为 ${femaleWork.toFixed(2)}；子午冲损毁度 男${Math.round(malePathBreakScore * 100)}% / 女${Math.round(femalePathBreakScore * 100)}%。`;

    deps.setGenderComparisonResult({
      male_dayun: String(maleData?.timeline?.dayun || ""),
      female_dayun: String(femaleData?.timeline?.dayun || ""),
      male_peak_abs: malePeakAbs,
      female_peak_abs: femalePeakAbs,
      male_work_net: maleWork,
      female_work_net: femaleWork,
      male_path_break_score: malePathBreakScore,
      female_path_break_score: femalePathBreakScore,
      male_theme_color: maleThemeColor,
      female_theme_color: femaleThemeColor,
      summary,
    });
    deps.setResultLogs((prev) => [...prev, `🧭 性别镜像对比完成：男(${maleWork.toFixed(2)}) vs 女(${femaleWork.toFixed(2)})`]);
  }, [depsRef]);

  return { runStressTest, runGenderComparison };
}
