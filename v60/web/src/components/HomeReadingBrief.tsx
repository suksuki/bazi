import type { HomeReadingBrief as ReadingBrief } from "../homeApi";

const DOMAIN_LABELS = {
  career: "事业",
  wealth: "财富",
  relationship: "关系",
} as const;

export function HomeReadingBrief({
  brief,
  busy,
  canCompare,
  comparisonAvailable,
  onCompare,
}: {
  brief: ReadingBrief;
  busy: boolean;
  canCompare: boolean;
  comparisonAvailable: boolean;
  onCompare: () => void;
}) {
  return (
    <article className="home-reading-brief" data-brief-ref={brief.brief_ref}>
      <header>
        <span>
          <small>本次命理读取</small>
          <strong>{brief.headline}</strong>
        </span>
        <em>证据化初判</em>
      </header>

      <p className="home-reading-qualification">
        <strong>{brief.qualification.fact_count}</strong> 条正式事实 ·{" "}
        <strong>{brief.qualification.candidate_count}</strong> 条结构候选 ·{" "}
        <strong>{brief.qualification.timing_coordinate_count}</strong> 层时序坐标
        <span>{brief.qualification.meaning}</span>
      </p>

      <section className="home-reading-confirmed">
        <h3>已经确认</h3>
        <ul>
          {brief.confirmed.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="home-reading-focus">
        <small>当前最值得追查</small>
        <strong>{brief.focus.label}</strong>
        <p>{brief.focus.statement}</p>
        {brief.focus.rationale && <blockquote>{brief.focus.rationale}</blockquote>}
        {brief.focus.support && (
          <div className="home-reading-support">
            <span>直接事实 {brief.focus.support.direct_fact_count}</span>
            <span>关系上下文 {brief.focus.support.context_fact_count}</span>
            <span>明干参与 {brief.focus.support.visible_occurrence_count}</span>
            <span>藏干成员 {brief.focus.support.hidden_occurrence_count}</span>
            <small>
              仍待核验：{brief.focus.support.unresolved.join("、")}
            </small>
          </div>
        )}
        {!brief.focus.candidate_ref && canCompare && (
          <div className="home-reading-compare">
            <button
              disabled={busy || !comparisonAvailable}
              onClick={onCompare}
              type="button"
            >
              {busy ? "正在核查…" : "核查结构主线"}
            </button>
            <small>
              {comparisonAvailable
                ? "规则无法排序时，交给受证据约束的 Gemma4 比较；结果只决定核查顺序。"
                : "当前推理服务未连接，候选继续保持未排序。"}
            </small>
          </div>
        )}
        <em>{brief.focus.meaning}</em>
      </section>

      <section className="home-reading-domain-windows">
        <h3>现实观察窗口</h3>
        {brief.life_domains.map((item) => (
          <div key={item.domain}>
            <span>
              <strong>{DOMAIN_LABELS[item.domain]}</strong>
              <small>{item.evidence_count} 条证据</small>
            </span>
            <p>{item.question}</p>
          </div>
        ))}
      </section>

      <details className="home-reading-boundaries">
        <summary>这次读取还不能断言什么</summary>
        <ul>
          {brief.boundaries.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </details>
    </article>
  );
}
