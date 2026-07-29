import type {
  HomeMechanismQualification,
  MechanismQualificationStatus,
} from "../homeQualificationTypes";

const STATUS_LABELS: Record<MechanismQualificationStatus, string> = {
  PRESENT: "已有",
  PARTIAL: "部分",
  MISSING: "缺失",
  NOT_ADMITTED: "未准入",
  UNRESOLVED: "待核证",
};

export function MechanismQualificationMatrix({
  qualification,
  detailed = false,
}: {
  qualification: HomeMechanismQualification;
  detailed?: boolean;
}) {
  if (!qualification.candidates.length) return null;

  return (
    <section
      className="mechanism-qualification"
      data-qualification-ref={qualification.qualification_ref}
      data-detail={detailed}
    >
      <header>
        <span>
          <small>做功证据清单</small>
          <strong>已有、缺失与可推翻条件</strong>
        </span>
        <em>不计算分数</em>
      </header>
      <p>{qualification.summary}</p>
      <div className="mechanism-qualification-list">
        {qualification.candidates.map((candidate) => (
          <details key={candidate.candidate_ref}>
            <summary>
              <span>
                <strong>{candidate.pattern_label}</strong>
                <small>
                  {candidate.evidence_present_count} 项有材料 ·{" "}
                  {candidate.unresolved_or_unadmitted_count} 项待补
                </small>
              </span>
              <i aria-hidden="true">＋</i>
            </summary>
            <div className="mechanism-qualification-checks">
              {candidate.checks.map((check) => (
                <article
                  data-status={check.status.toLowerCase()}
                  key={check.dimension}
                >
                  <header>
                    <strong>{check.label}</strong>
                    <span>{STATUS_LABELS[check.status]}</span>
                  </header>
                  <p>{check.meaning}</p>
                  {detailed && (
                    <>
                      <dl>
                        <div>
                          <dt>还需要</dt>
                          <dd>{check.next_evidence}</dd>
                        </div>
                        <div>
                          <dt>什么会推翻</dt>
                          <dd>{check.falsifier}</dd>
                        </div>
                      </dl>
                      {check.evidence_refs.length > 0 && (
                        <small>绑定证据 {check.evidence_refs.length} 条</small>
                      )}
                    </>
                  )}
                </article>
              ))}
            </div>
          </details>
        ))}
      </div>
      <p className="mechanism-qualification-boundary">
        结构候选不是有效做功。任何缺失项都不会被前端或阿布自动补齐。
      </p>
    </section>
  );
}
