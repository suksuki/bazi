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
  selectedCandidateRef = null,
}: {
  qualification: HomeMechanismQualification;
  detailed?: boolean;
  selectedCandidateRef?: string | null;
}) {
  if (!qualification.candidates.length) return null;
  const candidates = [...qualification.candidates].sort((left, right) => {
    const leftSelected = left.candidate_ref === selectedCandidateRef;
    const rightSelected = right.candidate_ref === selectedCandidateRef;
    if (leftSelected !== rightSelected) return leftSelected ? -1 : 1;
    return 0;
  });

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
        {candidates.map((candidate) => {
          const selected = candidate.candidate_ref === selectedCandidateRef;
          return (
            <details
              data-candidate-ref={candidate.candidate_ref}
              data-selected={selected}
              key={candidate.candidate_ref}
            >
              <summary>
                <span>
                  <strong>{candidate.pattern_label}</strong>
                  <small>
                    {selected && "当前优先追查 · "}
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
          );
        })}
      </div>
      <p className="mechanism-qualification-boundary">
        结构候选不是有效做功。任何缺失项都不会被前端或阿布自动补齐。
      </p>
    </section>
  );
}
