import type {
  HomeExplanationClaim,
  HomeMingliExplanation,
} from "../homeExplanationTypes";

const STATUS_LABELS = {
  CONFIRMED: "已确认",
  CANDIDATE: "候选解释",
  OBSERVE: "现实观察",
} as const;

export function MingliEvidenceExplanation({
  explanation,
  mode = "all",
}: {
  explanation: HomeMingliExplanation;
  mode?: "all" | "candidates";
}) {
  const claims =
    mode === "candidates"
      ? explanation.claims.filter((item) => item.epistemic_status === "CANDIDATE")
      : explanation.claims;
  if (!claims.length) return null;

  return (
    <section
      className="mingli-explanation"
      data-explanation-ref={explanation.explanation_ref}
    >
      <header>
        <span>
          <small>{mode === "all" ? "判断依据" : "候选证据链"}</small>
          <strong>
            {mode === "all"
              ? `${explanation.confirmed_count} 项确认 · ${explanation.candidate_count} 条候选 · ${explanation.observation_count} 个观察窗口`
              : `${claims.length} 条结构候选仍在比较`}
          </strong>
        </span>
        <em>{authorityLabel(explanation.decision_authority)}</em>
      </header>
      <p className="mingli-explanation-decision">{explanation.decision_meaning}</p>
      <div className="mingli-explanation-list">
        {claims.map((claim) => (
          <ExplanationClaim key={claim.claim_ref} claim={claim} />
        ))}
      </div>
    </section>
  );
}

function ExplanationClaim({ claim }: { claim: HomeExplanationClaim }) {
  return (
    <details
      className="mingli-explanation-claim"
      data-status={claim.epistemic_status.toLowerCase()}
    >
      <summary>
        <span>{STATUS_LABELS[claim.epistemic_status]}</span>
        <strong>{claim.title}</strong>
        <i aria-hidden="true">＋</i>
      </summary>
      <div className="mingli-explanation-body">
        <p>{claim.statement}</p>
        <section>
          <h4>支持它的材料</h4>
          <ul>
            {claim.support_evidence.map((item) => (
              <li key={item.evidence_ref}>
                <span data-evidence-status={item.epistemic_status.toLowerCase()} />
                {item.summary}
              </li>
            ))}
          </ul>
        </section>
        <section>
          <h4>反证与未知</h4>
          {claim.counter_evidence.length ? (
            <ul>
              {claim.counter_evidence.map((item) => (
                <li key={item.evidence_ref}>{item.summary}</li>
              ))}
            </ul>
          ) : (
            <p>
              {claim.counter_evidence_status === "NOT_ADMITTED"
                ? "反证模型尚未正式准入，因此不能把“没有反证”当作支持。"
                : "这项确定性事实不需要竞争解释。"}
            </p>
          )}
          {claim.unresolved_questions.length > 0 && (
            <div className="mingli-unresolved-list">
              {claim.unresolved_questions.map((item) => (
                <span key={item}>{item}</span>
              ))}
            </div>
          )}
        </section>
        <p className="mingli-explanation-boundary">{claim.boundary}</p>
      </div>
    </details>
  );
}

function authorityLabel(
  authority: HomeMingliExplanation["decision_authority"],
): string {
  if (authority === "LLM_REASONER") return "Gemma4 有界比较";
  if (authority === "RULE_ENGINE") return "规则比较";
  return "系统确定事实";
}
