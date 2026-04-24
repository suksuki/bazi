"use client";

import { translateTerm, translateTermList, type AppLanguage } from "@/lib/i18n";

type LooseRecord = Record<string, unknown>;

function asRecord(value: unknown): LooseRecord {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as LooseRecord) : {};
}

function asString(value: unknown, fallback = ""): string {
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return fallback;
}

function asNumber(value: unknown, fallback = 0): number {
  const next = Number(value);
  return Number.isFinite(next) ? next : fallback;
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.map((item) => String(item || "").trim()).filter(Boolean)
    : [];
}

function asStringMatrix(value: unknown): string[] {
  if (typeof value === "string") {
    return value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }
  return asStringArray(value);
}

function candidateTone(score: number): string {
  if (score >= 0.75) return "border-emerald-500/30 bg-emerald-950/25 text-emerald-200";
  if (score >= 0.45) return "border-cyan-500/30 bg-cyan-950/25 text-cyan-200";
  return "border-zinc-700 bg-zinc-950/70 text-zinc-300";
}

function netTone(value: number): string {
  if (value >= 0.4) return "text-emerald-300";
  if (value <= -0.2) return "text-rose-300";
  return "text-zinc-300";
}

function scopeLabel(value: string): string {
  const normalized = value.trim().toLowerCase();
  if (normalized === "natal" || normalized === "natal_basis") return "原局";
  if (normalized === "luck") return "大运";
  if (normalized === "flow") return "流年";
  if (normalized === "runtime" || normalized === "mixed") return "运流联动";
  return value || "来源待定";
}

function biasPairs(value: unknown): Array<[string, number]> {
  return Object.entries(asRecord(value))
    .map(([god, raw]) => [god, asNumber(raw)] as [string, number])
    .filter(([god, score]) => Boolean(god) && score > 0)
    .sort((left, right) => right[1] - left[1]);
}

function stageBiasRows(value: unknown) {
  return Object.entries(asRecord(value))
    .map(([god, raw]) => {
      const row = asRecord(raw);
      return {
        god: String(god || "").trim(),
        lu: asNumber(row.lu),
        blade: asNumber(row.blade),
        general: asNumber(row.general),
        useBoost: asNumber(row.use_boost),
        tabooBoost: asNumber(row.taboo_boost),
        stabilityBoost: asNumber(row.stability_boost),
        volatilityBoost: asNumber(row.volatility_boost),
      };
    })
    .filter((row) => row.god && Math.max(row.lu, row.blade, row.general, row.useBoost, row.tabooBoost) > 0)
    .sort(
      (left, right) =>
        right.useBoost + right.tabooBoost + right.lu + right.blade - (left.useBoost + left.tabooBoost + left.lu + left.blade),
    )
    .slice(0, 6);
}

function formatSigned(value: number): string {
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}`;
}

function fluxTone(value: number): string {
  if (value >= 0.35) return "text-emerald-300";
  if (value <= -0.2) return "text-rose-300";
  return "text-zinc-300";
}

function effectScoreSummary(god: string, raw: unknown) {
  const row = asRecord(raw);
  return {
    god,
    net: asNumber(row.net_utility),
    resolved: asNumber(row.resolved_utility),
    resolvedFlux: asNumber(row.resolved_utility_flux, asNumber(row.resolved_utility)),
    rawBenefit: asNumber(row.raw_benefit),
    rawHarm: asNumber(row.raw_harm),
    contest: asNumber(row.contest_pressure),
    release: asNumber(row.release_pressure),
    contestPairs: asStringMatrix(row.contest_pairs),
    contestWeight: asNumber(row.contest_weight),
    releaseWeight: asNumber(row.release_weight),
    benefit: asNumber(row.benefit_score),
    harm: asNumber(row.harm_score),
    stability: asNumber(row.stability_score),
    activation: asNumber(row.activation_score),
    tension: asNumber(row.flux_tension_load),
    reinforce: asNumber(row.flux_reinforce_load),
    outSupport: asNumber(row.flux_out_support),
    outResist: asNumber(row.flux_out_resist),
    outNet: asNumber(row.flux_out_net),
    authorityEnergy: asNumber(row.authority_energy),
    authorityStability: asNumber(row.authority_stability),
    authorityVolatility: asNumber(row.authority_volatility),
    authorityProfile: asString(row.authority_profile).trim(),
    authorityReason: asString(row.authority_reason).trim(),
  };
}

export function V17_GodRingExplainCard({
  godRings,
  focusedDecisionId,
  onFocusDecision,
  lang = "zh",
}: {
  godRings?: Record<string, unknown>;
  focusedDecisionId?: string;
  onFocusDecision?: (decisionId: string) => void;
  lang?: AppLanguage;
}) {
  const ui = (zh: string, en: string, ko: string) => (lang === "en" ? en : lang === "ko" ? ko : zh);
  const term = (value: string) => translateTerm(lang, value);
  const termList = (values: string[]) => translateTermList(lang, values);
  const row = asRecord(godRings);
  const displayMode = asString(row.display_mode).trim();
  const authorityMode = displayMode === "authority";
  const mode = asString(row.mode, authorityMode ? "authority" : "pending").trim();
  const source = asString(row.source, "待定").trim();
  const confidence = asNumber(row.confidence);
  const pathCount = asNumber(row.core_path_count);

  const useGods = asStringArray(row.god_of_use);
  const tabooGods = asStringArray(row.god_of_taboo);
  const tongguanGods = asStringArray(row.tongguan_gods);
  const useCandidates = Array.isArray(row.core_use_candidates)
    ? (row.core_use_candidates as LooseRecord[])
    : [];
  const tabooCandidates = Array.isArray(row.core_taboo_candidates)
    ? (row.core_taboo_candidates as LooseRecord[])
    : [];
  const dualRoleCandidates = Array.isArray(row.dual_role_candidates)
    ? (row.dual_role_candidates as LooseRecord[])
    : [];
  const effectScores = asRecord(row.effect_scores);
  const graphMeta = asRecord(row.core_graph_meta);
  const positiveTargets = asRecord(graphMeta.positive_targets);
  const negativeTargets = asRecord(graphMeta.negative_targets);
  const pathPreview = Array.isArray(row.core_paths_preview)
    ? (row.core_paths_preview as LooseRecord[])
    : [];
  const judgementBias = asRecord(row.judgement_bias);
  const judgementProtocol = asRecord(row.judgement_bias_protocol);
  const judgementSummary = asRecord(judgementProtocol.summary);
  const blindTheme = asRecord(row.blind_theme);
  const blindBias = asRecord(row.blind_bias);
  const blindProtocol = asRecord(row.blind_bias_protocol);
  const blindSummary = asRecord(blindProtocol.summary);
  const stageBias = stageBiasRows(row.stage_bias);
  const stageProtocol = asRecord(row.stage_bias_protocol);
  const stageSummary = asRecord(stageProtocol.summary);
  const judgementUseBias = biasPairs(judgementBias.use_bias).slice(0, 6);
  const judgementTabooBias = biasPairs(judgementBias.taboo_bias).slice(0, 6);
  const blindUseBias = biasPairs(blindBias.use_bias).slice(0, 6);
  const blindTabooBias = biasPairs(blindBias.taboo_bias).slice(0, 6);
  const blindHouseRoles = asRecord(blindTheme.house_roles);
  const blindInside = Object.entries(blindHouseRoles)
    .filter(([, role]) => asString(role).trim() === "inside")
    .map(([god]) => god);
  const blindOutside = Object.entries(blindHouseRoles)
    .filter(([, role]) => asString(role).trim() === "outside")
    .map(([god]) => god);
  const blindBridge = Object.entries(blindHouseRoles)
    .filter(([, role]) => asString(role).trim() === "bridge")
    .map(([god]) => god);
  const blindSwitches = asStringArray(blindProtocol.runtime_switches || blindTheme.runtime_switches).slice(0, 3);
  const judgementBiasEntries = Array.isArray(row.judgement_bias_entries)
    ? (row.judgement_bias_entries as LooseRecord[])
        .map((item) => {
          const entry = asRecord(item);
          const sourceLabel = asString(entry.source_label || entry.decision_label || entry.plugin_id).trim();
          const reason = asString(entry.reason).trim();
          const decisionId = asString(entry.decision_id).trim();
          const usePairs = biasPairs(entry.use_bias);
          const tabooPairs = biasPairs(entry.taboo_bias);
          if (!sourceLabel || (!usePairs.length && !tabooPairs.length)) return null;
          return { sourceLabel, reason, decisionId, usePairs, tabooPairs };
        })
        .filter(Boolean) as Array<{
          sourceLabel: string;
          reason: string;
          decisionId: string;
          usePairs: Array<[string, number]>;
          tabooPairs: Array<[string, number]>;
        }>
    : [];

  const effectRows = Object.entries(effectScores)
    .map(([god, raw]) => effectScoreSummary(god, raw))
    .sort(
      (left, right) =>
        Math.abs(right.resolvedFlux) - Math.abs(left.resolvedFlux) ||
        Math.abs(right.net) - Math.abs(left.net),
    )
    .slice(0, 6);
  const fluxFocusRows = Array.from(
    new Set([
      ...useGods,
      ...tabooGods,
      ...tongguanGods,
      ...effectRows.slice(0, 4).map((item) => item.god),
    ]),
  )
    .map((god) => {
      const match = effectRows.find((item) => item.god === god);
      return match ?? effectScoreSummary(god, effectScores[god]);
    })
    .filter((item) => item.god)
    .slice(0, 6);

  return (
    <section className="rounded-2xl border border-cyan-500/20 bg-[linear-gradient(180deg,rgba(8,47,73,0.36),rgba(9,9,11,0.84))] p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-[11px] uppercase tracking-[0.24em] text-cyan-300/80">
            God Ring Explain
          </div>
          <h3 className="mt-2 text-sm font-semibold text-cyan-50">{ui("体用裁决说明", "Body-Use Authority Explanation", "체용 판정 설명")}</h3>
          <p className="mt-1 text-[11px] leading-6 text-zinc-400">
            {ui(
              "这里展示核心层如何把六柱、大运、流年与关系做功折算成用神、忌神和双刃神。",
              "This explains how the core layer converts six pillars, luck, flow year, and relation work into useful gods, taboo gods, and dual-role gods.",
              "핵심 계층이 육주·대운·세운·관계 작용을 용신, 기신, 양면 신으로 환산하는 방식을 보여 줍니다.",
            )}
          </p>
        </div>
        <div className="flex flex-wrap gap-2 text-[10px]">
          <span
            className={`rounded-full border px-3 py-1 ${
              authorityMode
                ? "border-emerald-500/30 bg-emerald-950/20 text-emerald-200"
                : "border-amber-500/30 bg-amber-950/20 text-amber-200"
            }`}
          >
            {authorityMode ? ui("权威体用", "Authority active", "권위 체용") : ui("等待权威裁决", "Waiting for authority", "권위 판정 대기")}
          </span>
          <span className="rounded-full border border-cyan-500/20 bg-cyan-950/25 px-3 py-1 text-cyan-200">
            {ui("模式", "Mode", "모드")} {mode}
          </span>
          <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-300">
            {ui("置信", "Confidence", "신뢰도")} {Math.round(confidence * 100)}%
          </span>
          <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-300">
            {ui("路径", "Paths", "경로")} {pathCount}
          </span>
        </div>
      </div>

      {!authorityMode ? (
        <div className="mt-4 rounded-xl border border-dashed border-amber-500/25 bg-amber-950/15 px-4 py-3 text-[12px] leading-6 text-amber-100/90">
          {ui(
            "当前尚未拿到核心层的权威体用结果。主页面已经停止把“主导/弱势十神”冒充成用神/忌神；待核心路径完成后，这里会亮起完整解释。",
            "The core authority result is not available yet. The main page no longer treats dominant or weak ten-gods as useful/taboo gods; once the core paths finish, the full explanation appears here.",
            "핵심 계층의 권위 체용 결과가 아직 없습니다. 메인 화면은 더 이상 주도/약세 십신을 용신/기신으로 가장하지 않으며, 핵심 경로가 완성되면 이곳에 전체 설명이 표시됩니다.",
          )}
        </div>
      ) : (
        <>
          <div className="mt-4 grid gap-4 xl:grid-cols-[0.96fr,1.04fr]">
            <div className="grid gap-4">
              <div className="rounded-xl border border-zinc-800 bg-zinc-950/55 p-3">
                <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                  <div className="text-[11px] font-semibold text-zinc-300">{ui("体用候选", "Body-use candidates", "체용 후보")}</div>
                  <div className="text-[10px] text-zinc-500">{ui("来源", "Source", "출처")} {term(source)}</div>
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  <div>
                    <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-emerald-300">{ui("用神候选", "Useful candidates", "용신 후보")}</div>
                    <div className="flex flex-wrap gap-2">
                      {(useCandidates.length
                        ? useCandidates
                        : useGods.map((god) => ({ god, score: confidence })) as LooseRecord[]
                      ).map((item, idx) => {
                        const god = asString(item.god || useGods[idx] || "").trim();
                        const score = asNumber(item.score, confidence);
                        const profile = asString(item.authority_profile).trim();
                        return (
                          <div key={`use_${god}_${idx}`} className={`rounded-full border px-3 py-1 text-[10px] ${candidateTone(score)}`}>
                            <div>{ui("用", "Use", "용")} {term(god || "未定")} · {Math.round(score * 100)}%</div>
                            {profile ? <div className="mt-0.5 text-[9px] text-zinc-400">{profile}</div> : null}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                  <div>
                    <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-rose-300">{ui("忌神候选", "Taboo candidates", "기신 후보")}</div>
                    <div className="flex flex-wrap gap-2">
                      {(tabooCandidates.length
                        ? tabooCandidates
                        : tabooGods.map((god) => ({ god, score: confidence })) as LooseRecord[]
                      ).map((item, idx) => {
                        const god = asString(item.god || tabooGods[idx] || "").trim();
                        const score = asNumber(item.score, confidence);
                        const profile = asString(item.authority_profile).trim();
                        return (
                          <div
                            key={`taboo_${god}_${idx}`}
                            className={`rounded-full border px-3 py-1 text-[10px] ${
                              score >= 0.5
                                ? "border-rose-500/30 bg-rose-950/20 text-rose-200"
                                : "border-amber-500/30 bg-amber-950/20 text-amber-200"
                            }`}
                          >
                            <div>{ui("忌", "Taboo", "기")} {term(god || "未定")} · {Math.round(score * 100)}%</div>
                            {profile ? <div className="mt-0.5 text-[9px] text-zinc-400">{profile}</div> : null}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>

              {stageBias.length ? (
                <div className="rounded-xl border border-zinc-800 bg-zinc-950/55 p-3">
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <div className="text-[11px] font-semibold text-zinc-300">{ui("禄刃阶段偏置", "Lu/Blade Stage Bias", "록·인 단계 편향")}</div>
                    <div className="text-[10px] text-zinc-500">
                      {asString(stageProtocol.contract).trim()
                        ? `${asString(stageProtocol.contract).trim()} · ${ui("条目", "entries", "항목")} ${asNumber(stageSummary.entry_count)}`
                        : ui("为何会推用 / 推忌", "Why it pushes use/taboo", "왜 용/기를 미는가")}
                    </div>
                  </div>
                  <div className="mb-2 text-[10px] leading-5 text-zinc-500">
                    {ui(
                      "阶段偏置只作为 authority 的承接/波动修正，不回写 L0/L1 物理根分。",
                      "Stage bias only modifies authority acceptance/volatility and does not write back to L0/L1 physical root scores.",
                      "단계 편향은 authority 의 수용/변동 보정으로만 쓰이며 L0/L1 물리 근점수에 되쓰지 않습니다.",
                    )}
                  </div>
                  <div className="space-y-2 text-[10px] text-zinc-300">
                    {stageBias.map((entry) => (
                      <div key={`stage_bias_${entry.god}`} className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="font-medium text-zinc-100">{term(entry.god)}</span>
                          <span className="text-zinc-500">
                            {ui("禄", "Lu", "록")} {entry.lu.toFixed(2)} · {ui("刃", "Blade", "인")} {entry.blade.toFixed(2)} · {ui("长生", "Growth", "장생")} {entry.general.toFixed(2)}
                          </span>
                        </div>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {entry.useBoost > 0 ? (
                            <span className="rounded-full border border-emerald-500/30 bg-emerald-950/25 px-3 py-1 text-emerald-200">
                              {ui("推用", "Use bias", "용신 편향")} +{entry.useBoost.toFixed(2)}
                            </span>
                          ) : null}
                          {entry.tabooBoost > 0 ? (
                            <span className="rounded-full border border-rose-500/30 bg-rose-950/25 px-3 py-1 text-rose-200">
                              {ui("推忌", "Taboo bias", "기신 편향")} +{entry.tabooBoost.toFixed(2)}
                            </span>
                          ) : null}
                          {entry.stabilityBoost > 0 ? (
                            <span className="rounded-full border border-cyan-500/30 bg-cyan-950/25 px-3 py-1 text-cyan-200">
                              {ui("稳定", "Stability", "안정")} +{entry.stabilityBoost.toFixed(2)}
                            </span>
                          ) : null}
                          {entry.volatilityBoost > 0 ? (
                            <span className="rounded-full border border-amber-500/30 bg-amber-950/25 px-3 py-1 text-amber-200">
                              {ui("波动", "Volatility", "변동")} +{entry.volatilityBoost.toFixed(2)}
                            </span>
                          ) : null}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}

              {Object.keys(blindTheme).length || blindUseBias.length || blindTabooBias.length ? (
                <div className="rounded-xl border border-zinc-800 bg-zinc-950/55 p-3">
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <div className="text-[11px] font-semibold text-zinc-300">{ui("盲派专题并行桥接", "Blind-school parallel bridge", "맹파 병렬 브리지")}</div>
                    <div className="text-[10px] text-zinc-500">
                      {asString(blindProtocol.contract).trim() || "v17.blind.bias.v1"} · {asString(blindProtocol.authority_bridge_mode).trim() || "bias_only"}
                    </div>
                  </div>
                  <div className="mb-2 text-[10px] leading-5 text-zinc-500">
                    {ui(
                      "盲派作为独立专题并行输出体态、家里家外与换挡信息，只做 soft bias，不覆盖子平 authority。",
                      "The blind-school topic runs independently and outputs body mode, inner/outer roles, and runtime shifts. It only provides soft bias and never overrides ZiPing authority.",
                      "맹파 주제는 독립적으로 체태, 안팎 역할, 전환 정보를 출력합니다. soft bias 만 제공하며 자평 authority 를 덮지 않습니다.",
                    )}
                  </div>
                  <div className="flex flex-wrap gap-2 text-[10px]">
                    {asString(blindTheme.primary_route).trim() ? (
                      <span className="rounded-full border border-fuchsia-500/30 bg-fuchsia-950/20 px-3 py-1 text-fuchsia-200">
                        {ui("主线", "Route", "주선")} {term(asString(blindTheme.primary_route).trim())}
                      </span>
                    ) : null}
                    {asString(blindTheme.body_mode).trim() ? (
                      <span className="rounded-full border border-cyan-500/30 bg-cyan-950/20 px-3 py-1 text-cyan-200">
                        {ui("体态", "Body mode", "체태")} {term(asString(blindTheme.body_mode).trim())}
                      </span>
                    ) : null}
                    {asNumber(blindSummary.use_total) > 0 ? (
                      <span className="rounded-full border border-emerald-500/30 bg-emerald-950/20 px-3 py-1 text-emerald-200">
                        {ui("推用", "Use bias", "용신 편향")} +{asNumber(blindSummary.use_total).toFixed(2)}
                      </span>
                    ) : null}
                    {asNumber(blindSummary.taboo_total) > 0 ? (
                      <span className="rounded-full border border-rose-500/30 bg-rose-950/20 px-3 py-1 text-rose-200">
                        {ui("推忌", "Taboo bias", "기신 편향")} +{asNumber(blindSummary.taboo_total).toFixed(2)}
                      </span>
                    ) : null}
                  </div>
                  {(blindInside.length || blindOutside.length || blindBridge.length) ? (
                    <div className="mt-3 flex flex-wrap gap-2 text-[10px]">
                      {blindInside.length ? (
                        <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-200">
                          {ui("家里", "Inside", "안")} {termList(blindInside)}
                        </span>
                      ) : null}
                      {blindOutside.length ? (
                        <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-200">
                          {ui("家外", "Outside", "밖")} {termList(blindOutside)}
                        </span>
                      ) : null}
                      {blindBridge.length ? (
                        <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-200">
                          {ui("桥位", "Bridge", "교량")} {termList(blindBridge)}
                        </span>
                      ) : null}
                    </div>
                  ) : null}
                  {blindSwitches.length ? (
                    <div className="mt-3 rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2 text-[10px] text-zinc-300">
                      {ui("换挡", "Runtime shifts", "전환")}：{termList(blindSwitches)}
                    </div>
                  ) : null}
                  <div className="mt-3 grid gap-3 md:grid-cols-2">
                    <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                      <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-emerald-300">{ui("盲派推用", "Blind-school use bias", "맹파 용신 편향")}</div>
                      <div className="flex flex-wrap gap-2">
                        {blindUseBias.length ? (
                          blindUseBias.map(([god, score]) => (
                            <span key={`blind_use_${god}`} className="rounded-full border border-emerald-500/20 bg-emerald-950/20 px-3 py-1 text-[10px] text-emerald-200">
                              {term(god)} +{score.toFixed(2)}
                            </span>
                          ))
                        ) : (
                          <span className="text-[11px] text-zinc-500">{ui("当前未形成显著推用。", "No significant use bias yet.", "아직 뚜렷한 용신 편향이 없습니다.")}</span>
                        )}
                      </div>
                    </div>
                    <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                      <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-rose-300">{ui("盲派推忌", "Blind-school taboo bias", "맹파 기신 편향")}</div>
                      <div className="flex flex-wrap gap-2">
                        {blindTabooBias.length ? (
                          blindTabooBias.map(([god, score]) => (
                            <span key={`blind_taboo_${god}`} className="rounded-full border border-rose-500/20 bg-rose-950/20 px-3 py-1 text-[10px] text-rose-200">
                              {term(god)} +{score.toFixed(2)}
                            </span>
                          ))
                        ) : (
                          <span className="text-[11px] text-zinc-500">{ui("当前未形成显著推忌。", "No significant taboo bias yet.", "아직 뚜렷한 기신 편향이 없습니다.")}</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ) : null}

              <div className="rounded-xl border border-zinc-800 bg-zinc-950/55 p-3">
                <div className="mb-2 text-[11px] font-semibold text-zinc-300">{ui("双刃神与引动热区", "Dual-role Gods & Activation Hotspots", "양면 신과 인동 열점")}</div>
                <div className="grid gap-3 lg:grid-cols-2">
                  <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                    <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-fuchsia-300">{ui("双刃神", "Dual-role gods", "양면 신")}</div>
                    <div className="flex flex-wrap gap-2">
                      {dualRoleCandidates.length ? (
                        dualRoleCandidates.map((item, idx) => {
                          const god = asString(item.god).trim();
                          const benefit = asNumber(item.benefit);
                          const risk = asNumber(item.risk);
                          return (
                            <span
                              key={`dual_${god}_${idx}`}
                              className="rounded-full border border-fuchsia-500/30 bg-fuchsia-950/20 px-3 py-1 text-[10px] text-fuchsia-200"
                            >
                              {term(god || "未定")} · {ui("利", "benefit", "이익")} {benefit.toFixed(2)} / {ui("害", "risk", "위험")} {risk.toFixed(2)}
                            </span>
                          );
                        })
                      ) : (
                        <span className="text-[11px] text-zinc-500">{ui("当前无显著双刃神。", "No significant dual-role gods yet.", "아직 뚜렷한 양면 신이 없습니다.")}</span>
                      )}
                    </div>
                  </div>
                  <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                    <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-cyan-300">{ui("引动热区", "Activation hotspots", "인동 열점")}</div>
                    <div className="space-y-2">
                      <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                        <div className="mb-1 text-[10px] text-zinc-500">{ui("正向引动", "Positive activation", "정방향 인동")}</div>
                        <div className="flex flex-wrap gap-2">
                          {Object.keys(positiveTargets).length ? (
                            Object.entries(positiveTargets).map(([god, raw]) => (
                              <span
                                key={`pos_${god}`}
                                className="rounded-full border border-emerald-500/20 bg-emerald-950/20 px-2 py-1 text-[10px] text-emerald-200"
                              >
                                {term(god)} {asNumber(raw).toFixed(2)}
                              </span>
                            ))
                          ) : (
                            <span className="text-[11px] text-zinc-500">{ui("暂无。", "None.", "없음.")}</span>
                          )}
                        </div>
                      </div>
                      <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                        <div className="mb-1 text-[10px] text-zinc-500">{ui("负向引动", "Negative activation", "부정 인동")}</div>
                        <div className="flex flex-wrap gap-2">
                          {Object.keys(negativeTargets).length ? (
                            Object.entries(negativeTargets).map(([god, raw]) => (
                              <span
                                key={`neg_${god}`}
                                className="rounded-full border border-amber-500/20 bg-amber-950/20 px-2 py-1 text-[10px] text-amber-200"
                              >
                                {term(god)} {asNumber(raw).toFixed(2)}
                              </span>
                            ))
                          ) : (
                            <span className="text-[11px] text-zinc-500">{ui("暂无。", "None.", "없음.")}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid gap-4">
              <div className="rounded-xl border border-zinc-800 bg-zinc-950/55 p-3">
                <div className="mb-3 flex items-center justify-between gap-2">
                  <div className="text-[11px] font-semibold text-zinc-300">{ui("判定 Bias 账本", "Judgement Bias Ledger", "판정 Bias 장부")}</div>
                  <div className="text-[10px] text-zinc-500">
                    {asString(judgementProtocol.contract).trim()
                      ? `${asString(judgementProtocol.contract).trim()} · ${ui("条目", "entries", "항목")} ${asNumber(judgementSummary.entry_count)} · ${ui("目标", "targets", "대상")} ${asNumber(judgementSummary.target_count)}`
                      : ui("谁在推动体用", "What is pushing body-use", "무엇이 체용을 미는가")}
                  </div>
                </div>
                <div className="mb-3 text-[10px] leading-5 text-zinc-500">
                  {ui(
                    "L2 judgement 只输出 bias / evidence / narrative hint，用来影响体用裁决，不直接改写 L0/L1 物理结算。",
                    "L2 judgement only outputs bias, evidence, and narrative hints to influence body-use authority. It does not rewrite L0/L1 physical settlement.",
                    "L2 judgement 는 bias/evidence/narrative hint 만 출력해 체용 판정에 영향을 주며 L0/L1 물리 결산을 다시 쓰지 않습니다.",
                  )}
                </div>
                <div className="grid gap-3 lg:grid-cols-2">
                  <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                    <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-emerald-300">{ui("用侧推动", "Use-side push", "용측 추진")}</div>
                    <div className="flex flex-wrap gap-2">
                      {judgementUseBias.length ? (
                        judgementUseBias.map(([god, score]) => (
                          <span
                            key={`judgement_use_${god}`}
                            className="rounded-full border border-emerald-500/30 bg-emerald-950/25 px-3 py-1 text-[10px] text-emerald-200"
                          >
                            {term(god)} +{score.toFixed(2)}
                          </span>
                        ))
                      ) : (
                        <span className="text-[11px] text-zinc-500">{ui("暂无。", "None.", "없음.")}</span>
                      )}
                    </div>
                  </div>
                  <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                    <div className="mb-2 text-[10px] uppercase tracking-[0.16em] text-rose-300">{ui("忌侧推动", "Taboo-side push", "기측 추진")}</div>
                    <div className="flex flex-wrap gap-2">
                      {judgementTabooBias.length ? (
                        judgementTabooBias.map(([god, score]) => (
                          <span
                            key={`judgement_taboo_${god}`}
                            className="rounded-full border border-rose-500/30 bg-rose-950/25 px-3 py-1 text-[10px] text-rose-200"
                          >
                            {term(god)} +{score.toFixed(2)}
                          </span>
                        ))
                      ) : (
                        <span className="text-[11px] text-zinc-500">{ui("暂无。", "None.", "없음.")}</span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="mt-3 space-y-2 text-[10px] text-zinc-400">
                  {judgementBiasEntries.length ? (
                    judgementBiasEntries.slice(0, 6).map((entry, idx) => {
                      const isFocused = Boolean(entry.decisionId && focusedDecisionId && entry.decisionId === focusedDecisionId);
                      return (
                        <div key={`bias_entry_${idx}_${entry.sourceLabel}`} className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <span className="font-medium text-zinc-100">{entry.sourceLabel}</span>
                            {entry.reason ? <span className="text-zinc-500">{entry.reason}</span> : null}
                          </div>
                          <div className="mt-1 space-y-1">
                            {entry.usePairs.length ? (
                              <div className="break-words text-emerald-200/90">
                                {ui("用侧", "Use side", "용측")}：{entry.usePairs.map(([god, score]) => `${term(god)} +${score.toFixed(2)}`).join(" · ")}
                              </div>
                            ) : null}
                            {entry.tabooPairs.length ? (
                              <div className="break-words text-rose-200/90">
                                {ui("忌侧", "Taboo side", "기측")}：{entry.tabooPairs.map(([god, score]) => `${term(god)} +${score.toFixed(2)}`).join(" · ")}
                              </div>
                            ) : null}
                          </div>
                          {entry.decisionId ? (
                            <div className="mt-2 flex flex-wrap items-center gap-2">
                              <span className="rounded-full border border-zinc-700 bg-zinc-900/70 px-2 py-1 text-[10px] text-zinc-300">
                                ID {entry.decisionId}
                              </span>
                              <button
                                type="button"
                                onClick={() => onFocusDecision?.(entry.decisionId)}
                                className={`rounded-full border px-2 py-1 transition ${
                                  isFocused
                                    ? "border-emerald-500/35 bg-emerald-950/25 text-emerald-200"
                                    : "border-cyan-500/20 bg-cyan-950/20 text-cyan-200 hover:bg-cyan-900/35"
                                }`}
                              >
                                {isFocused ? ui("已联动到决策", "Linked to decision", "결정에 연결됨") : ui("联动决策", "Link decision", "결정 연결")}
                              </button>
                            </div>
                          ) : null}
                        </div>
                      );
                    })
                  ) : (
                    <div className="rounded-lg border border-dashed border-zinc-800 px-3 py-4 text-zinc-500">
                      {ui("当前没有来自判定性插件的 bias 账本。", "No bias ledger from judgement plugins yet.", "판정성 플러그인에서 온 bias 장부가 아직 없습니다.")}
                    </div>
                  )}
                </div>
              </div>

              <div className="rounded-xl border border-zinc-800 bg-zinc-950/55 p-3">
                <div className="mb-3 flex items-center justify-between gap-2">
                  <div className="text-[11px] font-semibold text-zinc-300">{ui("M3 实时力场", "M3 Runtime Force Field", "M3 실시간 역장")}</div>
                  <div className="text-[10px] text-zinc-500">{ui("张力 / 放大 / 对外推拉", "Tension / amplification / outward push-pull", "장력 / 증폭 / 외부 추동")}</div>
                </div>
                <div className="space-y-2 text-[10px] text-zinc-400">
                  {fluxFocusRows.length ? (
                    fluxFocusRows.map((item) => {
                      const roles = [
                        useGods.includes(item.god) ? ui("用", "Use", "용") : "",
                        tabooGods.includes(item.god) ? ui("忌", "Taboo", "기") : "",
                        tongguanGods.includes(item.god) ? ui("通关", "Tongguan", "통관") : "",
                      ].filter(Boolean);
                      return (
                        <div key={`flux_${item.god}`} className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="font-medium text-zinc-100">{term(item.god)}</span>
                              {roles.length ? (
                                roles.map((label) => (
                                  <span
                                    key={`${item.god}_${label}`}
                                    className="rounded-full border border-cyan-500/20 bg-cyan-950/20 px-2 py-0.5 text-[10px] text-cyan-200"
                                  >
                                    {label}
                                  </span>
                                ))
                              ) : null}
                            </div>
                            <span className={`font-mono ${fluxTone(item.resolvedFlux)}`}>
                              {ui("流后净效", "Resolved net", "흐름 후 순효")} {formatSigned(item.resolvedFlux)}
                            </span>
                          </div>
                          <div className="mt-2 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                            <span>{ui("张力", "Tension", "장력")} {item.tension.toFixed(2)}</span>
                            <span>{ui("放大", "Amplify", "증폭")} {item.reinforce.toFixed(2)}</span>
                            <span>{ui("外推支撑", "Out support", "외부 지지")} {item.outSupport.toFixed(2)}</span>
                            <span>{ui("外推压制", "Out resist", "외부 저항")} {item.outResist.toFixed(2)}</span>
                          </div>
                          <div className="mt-2 flex flex-wrap gap-2">
                            <span className="rounded-full border border-zinc-700 bg-zinc-900/70 px-2 py-1 text-zinc-300">
                              {ui("外推净值", "Out net", "외부 순값")} {formatSigned(item.outNet)}
                            </span>
                            {item.tension > 0 ? (
                              <span className="rounded-full border border-amber-500/20 bg-amber-950/20 px-2 py-1 text-amber-200">
                                {ui("回路张力", "Loop tension", "회로 장력")} {item.tension.toFixed(2)}
                              </span>
                            ) : null}
                            {item.reinforce > 0 ? (
                              <span className="rounded-full border border-emerald-500/20 bg-emerald-950/20 px-2 py-1 text-emerald-200">
                                {ui("同向放大", "Same-direction amplification", "동향 증폭")} {item.reinforce.toFixed(2)}
                              </span>
                            ) : null}
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <div className="rounded-lg border border-dashed border-zinc-800 px-3 py-4 text-zinc-500">
                      {ui("当前还没有形成可展示的 M3 实时力场。", "No displayable M3 runtime force field has formed yet.", "아직 표시할 수 있는 M3 실시간 역장이 형성되지 않았습니다.")}
                    </div>
                  )}
                </div>
              </div>

              <div className="rounded-xl border border-zinc-800 bg-zinc-950/55 p-3">
                <div className="mb-3 flex items-center justify-between gap-2">
                  <div className="text-[11px] font-semibold text-zinc-300">{ui("效应分数", "Effect Scores", "효과 점수")}</div>
                  <div className="text-[10px] text-zinc-500">
                    raw / contest / release / resolved / flux
                  </div>
                </div>
                <div className="space-y-2 text-[10px] text-zinc-400">
                  {effectRows.length ? (
                    effectRows.map((item) => {
                      const god = item.god;
                      return (
                        <div key={god} className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                          <div className="flex items-center justify-between gap-3">
                            <span className="font-medium text-zinc-100">{term(god)}</span>
                            <span className={`font-mono ${netTone(item.net)}`}>
                              net {item.net.toFixed(2)} / resolved {item.resolved.toFixed(2)}
                            </span>
                          </div>
                          <div className="mt-2 grid gap-2 sm:grid-cols-2">
                            <span>{ui("原始利", "Raw benefit", "원시 이익")} {item.rawBenefit.toFixed(2)} / {ui("原始害", "Raw harm", "원시 해")} {item.rawHarm.toFixed(2)}</span>
                            <span>
                              {ui("对抗", "Contest", "대항")} {item.contest.toFixed(2)}（{ui("抑制权重", "resist weight", "억제 가중")} {item.contestWeight.toFixed(2)}） /
                              {ui("通道", "Channel", "통로")} {item.release.toFixed(2)}（{ui("提升权重", "release weight", "상승 가중")} {item.releaseWeight.toFixed(2)}）
                            </span>
                          </div>
                          <div className="mt-2 grid gap-2 sm:grid-cols-3">
                            <span>{ui("利", "Benefit", "이익")} {item.benefit.toFixed(2)}</span>
                            <span>{ui("害", "Harm", "해")} {item.harm.toFixed(2)}</span>
                            <span>{ui("稳定", "Stability", "안정")} {item.stability.toFixed(2)} / {ui("激活", "Activation", "활성")} {item.activation.toFixed(2)}</span>
                          </div>
                          <div className="mt-2 grid gap-2 sm:grid-cols-3">
                            <span>{ui("流后净效", "Resolved net", "흐름 후 순효")} {formatSigned(item.resolvedFlux)}</span>
                            <span>{ui("张力", "Tension", "장력")} {item.tension.toFixed(2)}</span>
                            <span>{ui("放大", "Amplify", "증폭")} {item.reinforce.toFixed(2)}</span>
                          </div>
                          {item.authorityProfile ? (
                            <div className="mt-2 rounded-lg border border-cyan-500/15 bg-cyan-950/10 px-3 py-2 text-[10px] text-cyan-100/90">
                              <div className="flex flex-wrap items-center justify-between gap-2">
                                <span className="font-medium">{item.authorityProfile}</span>
                                <span>
                                  {ui("能量", "Energy", "에너지")} {item.authorityEnergy.toFixed(2)} · {ui("稳定", "Stability", "안정")} {item.authorityStability.toFixed(2)} · {ui("波动", "Volatility", "변동")} {item.authorityVolatility.toFixed(2)}
                                </span>
                              </div>
                              {item.authorityReason ? <div className="mt-1 text-zinc-400">{item.authorityReason}</div> : null}
                            </div>
                          ) : null}
                          <div className="mt-2 flex flex-wrap gap-1.5">
                            {item.contestPairs.length ? (
                              item.contestPairs.map((pair) => (
                                <span
                                  key={`${god}_pair_${pair}`}
                                  className="rounded-full border border-zinc-700/90 bg-zinc-900/70 px-2 py-1 text-[10px] text-zinc-300"
                                >
                                  {ui("对抗对", "Contest pair", "대항 쌍")} {pair}
                                </span>
                              ))
                            ) : (
                              <span className="text-[11px] text-zinc-500">{ui("无显著对抗对", "No significant contest pairs", "뚜렷한 대항 쌍 없음")}</span>
                            )}
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <div className="rounded-lg border border-dashed border-zinc-800 px-3 py-4 text-zinc-500">
                      {ui("当前还没有可展示的效应分数。", "No displayable effect scores yet.", "아직 표시할 수 있는 효과 점수가 없습니다.")}
                    </div>
                  )}
                </div>
              </div>

              <div className="rounded-xl border border-zinc-800 bg-zinc-950/55 p-3">
                <div className="mb-3 flex items-center justify-between gap-2">
                  <div className="text-[11px] font-semibold text-zinc-300">{ui("做功路径预览", "Work-path Preview", "작용 경로 미리보기")}</div>
                  <div className="text-[10px] text-zinc-500">{ui("前 6 条核心链路", "Top 6 core paths", "상위 6개 핵심 경로")}</div>
                </div>
                <div className="space-y-2 text-[10px] text-zinc-400">
                  {pathPreview.length ? (
                    pathPreview.slice(0, 6).map((item, idx) => {
                      const target = asString(item.target_god, "未定目标").trim();
                      const pathType = asString(item.path_type, "path").trim();
                      const participants = asStringArray(item.participants);
                      const originScope = scopeLabel(asString(item.origin_scope).trim());
                      const net = asNumber(item.net_effect);
                      const evidence = asRecord(item.evidence);
                      const sourceLabel = asString(evidence.source_label || evidence.plugin_id || evidence.source).trim();
                      const decisionLabel = asString(evidence.decision_label).trim();
                      const decisionId = asString(evidence.decision_id).trim();
                      const conditionState = asString(evidence.condition_state).trim();
                      const layer = asString(evidence.layer).trim();
                      const isFocused = Boolean(decisionId && focusedDecisionId && decisionId === focusedDecisionId);
                      return (
                        <div key={`path_${idx}_${target}`} className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <span className="font-medium text-zinc-100">
                              {term(target)} · {term(pathType)}
                            </span>
                            <span className={`font-mono ${netTone(net)}`}>net {net.toFixed(2)}</span>
                          </div>
                          <div className="mt-1 text-zinc-500">
                            {participants.length ? translateTermList(lang, participants, " -> ") : ui("单点路径", "Single-point path", "단일점 경로")} · {term(originScope)}
                          </div>
                          {sourceLabel || decisionLabel || decisionId ? (
                            <div className="mt-2 flex flex-wrap gap-2 text-[10px]">
                              {sourceLabel ? (
                                <span className="rounded-full border border-cyan-500/20 bg-cyan-950/20 px-2 py-1 text-cyan-200">
                                  {ui("插件", "Plugin", "플러그인")} {sourceLabel}
                                </span>
                              ) : null}
                              {decisionLabel ? (
                                <span className="rounded-full border border-violet-500/20 bg-violet-950/20 px-2 py-1 text-violet-200">
                                  {ui("决策", "Decision", "결정")} {decisionLabel}
                                </span>
                              ) : null}
                              {decisionId ? (
                                <span className="rounded-full border border-zinc-700 bg-zinc-900/70 px-2 py-1 text-zinc-300">
                                  ID {decisionId}
                                </span>
                              ) : null}
                              {layer ? (
                                <span className="rounded-full border border-zinc-700 bg-zinc-900/70 px-2 py-1 text-zinc-300">
                                  {ui("层", "Layer", "층")} {layer}
                                </span>
                              ) : null}
                              {conditionState ? (
                                <span className="rounded-full border border-zinc-700 bg-zinc-900/70 px-2 py-1 text-zinc-300">
                                  {ui("态", "State", "상태")} {term(conditionState)}
                                </span>
                              ) : null}
                              {decisionId ? (
                                <button
                                  type="button"
                                  onClick={() => onFocusDecision?.(decisionId)}
                                  className={`rounded-full border px-2 py-1 transition ${
                                    isFocused
                                      ? "border-emerald-500/35 bg-emerald-950/25 text-emerald-200"
                                      : "border-violet-500/20 bg-violet-950/20 text-violet-200 hover:bg-violet-900/35"
                                  }`}
                                >
                                  {isFocused ? ui("已联动到决策", "Linked to decision", "결정에 연결됨") : ui("联动决策", "Link decision", "결정 연결")}
                                </button>
                              ) : null}
                            </div>
                          ) : null}
                          <div className="mt-2 grid gap-2 sm:grid-cols-4">
                            <span>{ui("激活", "Activation", "활성")} {asNumber(item.activation).toFixed(2)}</span>
                            <span>{ui("传导", "Transmission", "전도")} {asNumber(item.transmission).toFixed(2)}</span>
                            <span>{ui("损耗", "Loss", "손실")} {asNumber(item.loss).toFixed(2)}</span>
                            <span>{ui("稳定", "Stability", "안정")} {asNumber(item.stability).toFixed(2)}</span>
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <div className="rounded-lg border border-dashed border-zinc-800 px-3 py-4 text-zinc-500">
                      {ui("当前还没有做功路径预览。", "No work-path preview yet.", "아직 작용 경로 미리보기가 없습니다.")}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </section>
  );
}
