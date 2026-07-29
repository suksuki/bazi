import type { DreamSnapshot } from "../api";
import type {
  FocusSourcesHandler,
  SemanticFocus,
} from "../semanticFocus";

export function MingliUnit({
  focus,
  onFocusSources,
  snapshot,
}: {
  focus: SemanticFocus | null;
  onFocusSources: FocusSourcesHandler;
  snapshot: DreamSnapshot;
}) {
  const mingli = snapshot.projections.mingli;
  const visibleFacts = focus ? focus.labFacts : mingli.facts;
  return (
    <>
      <p className="rail-kicker">同一 LifeCase · 正式命盘</p>
      <h2>命盘事实与版本</h2>
      <div className="pillar-row">
        {(["year", "month", "day", "hour"] as const).map((slot) => (
          <span key={slot}>{mingli.pillars[slot]}</span>
        ))}
      </div>
      {visibleFacts.map((fact) => (
        <div className="lab-fact" key={fact.fact_ref}>
          <strong>{factTitle(fact)}</strong>
          <span>{factBoundary(fact)}</span>
          <details className="source-disclosure">
            <summary>查看来源凭据</summary>
            <code>{fact.source_ref}</code>
          </details>
          <button
            className="focus-return-command"
            type="button"
            onClick={() =>
              onFocusSources(
                [fact.fact_ref, fact.source_ref],
                ["EVIDENCE_LEAF", "STRUCTURE_BRANCH"],
              )
            }
          >
            回到树上的命纹叶
          </button>
        </div>
      ))}
      {visibleFacts.length === 0 && (
        <p className="projection-empty">当前焦点没有命盘事实；它属于世界经历。</p>
      )}
      <p className="lab-boundary">
        {mingli.authority} · 只读 · {mingli.chart_version_ref}
      </p>
    </>
  );
}

function factTitle(
  fact: DreamSnapshot["projections"]["mingli"]["facts"][number],
): string {
  if (fact.fact_type === "six_harmony_membership") {
    const left =
      typeof fact.fact_json.left_branch === "string"
        ? fact.fact_json.left_branch
        : fact.subject_ref;
    const right =
      typeof fact.fact_json.right_branch === "string"
        ? fact.fact_json.right_branch
        : fact.object_ref;
    return `${left}与${right}具备六合成员关系`;
  }
  if (fact.fact_type === "timing_snapshot") {
    const coordinates = Array.isArray(fact.fact_json.coordinates)
      ? fact.fact_json.coordinates
      : [];
    const labels = coordinates
      .map((item) => {
        if (
          typeof item !== "object" ||
          item === null ||
          !("pillar" in item) ||
          !("layer" in item)
        ) {
          return null;
        }
        const label =
          item.layer === "DAYUN"
            ? "大运"
            : item.layer === "ANNUAL"
              ? "流年"
              : "流月";
        return `${label}${String(item.pillar)}`;
      })
      .filter(Boolean);
    return labels.length ? labels.join(" · ") : "已冻结的时序坐标";
  }
  if (fact.fact_type === "life_domain_attention") {
    const observations = Array.isArray(fact.fact_json.observations)
      ? fact.fact_json.observations
      : [];
    const career = observations.find(
      (item) =>
        typeof item === "object" &&
        item !== null &&
        "domain" in item &&
        item.domain === "career",
    );
    if (
      typeof career === "object" &&
      career !== null &&
      "label" in career &&
      "signal_status" in career
    ) {
      return `${String(career.label)} · ${signalLabel(String(career.signal_status))}`;
    }
    return "现实领域的有限观察窗口";
  }
  return "已提交的命盘结构事实";
}

function factBoundary(
  fact: DreamSnapshot["projections"]["mingli"]["facts"][number],
): string {
  if (fact.fact_type === "life_domain_attention") {
    return "只提示值得观察的领域 · 不预测事件与结果";
  }
  if (fact.fact_type === "timing_snapshot") {
    return "冻结时序坐标 · 不等于现实事件已经发生";
  }
  return "正式关系事实 · 已锁定版本";
}

function signalLabel(status: string): string {
  if (status === "TIMING_MECHANISM_OVERLAP") {
    return "时序与结构证据交叠";
  }
  if (status === "TIMING_AND_MECHANISM_PRESENT") {
    return "时序与结构证据并存";
  }
  if (status === "TIMING_ONLY") {
    return "目前仅有时序证据";
  }
  if (status === "MECHANISM_ONLY") {
    return "目前仅有结构候选";
  }
  return "暂无有限证据";
}
