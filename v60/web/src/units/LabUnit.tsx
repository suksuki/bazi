import type { DreamSnapshot } from "../api";
import type {
  FocusSourcesHandler,
  SemanticFocus,
} from "../semanticFocus";

export function LabUnit({
  focus,
  onFocusSources,
  snapshot,
}: {
  focus: SemanticFocus | null;
  onFocusSources: FocusSourcesHandler;
  snapshot: DreamSnapshot;
}) {
  const lab = snapshot.projections.lab;
  const visibleFacts = focus ? focus.labFacts : lab.facts;
  const visibleFactRefs = new Set(visibleFacts.map((fact) => fact.fact_ref));
  const visibleCandidates = focus
    ? lab.candidate_paths.filter((candidate) =>
        candidate.evidence_refs.some((ref) => visibleFactRefs.has(ref)),
      )
    : lab.candidate_paths;
  return (
    <>
      <p className="rail-kicker">证据检查 · 沙箱只读</p>
      <h2>结构候选与未决边界</h2>
      {visibleCandidates.map((candidate) => (
        <article className="candidate-path" key={candidate.candidate_ref}>
          <span className="candidate-kicker">结构候选</span>
          <strong>{candidate.label}</strong>
          <div className="candidate-participants" aria-label="候选参与者">
            {candidate.participants.map((participant) => (
              <span key={participant.participant_ref}>{participant.label}</span>
            ))}
          </div>
          <div className="candidate-qualification">
            <span>
              结构证据 ·{" "}
              {candidate.structure_evidence_status === "SATISFIED" ? "已核验" : "未通过"}
            </span>
            <span>有效做功 · 尚未准入</span>
          </div>
          <p>关系事实已成立；作用、承载、时机与专业准入仍待核证。</p>
          <button
            className="focus-return-command"
            type="button"
            onClick={() =>
              onFocusSources(
                candidate.evidence_refs,
                ["STRUCTURE_BRANCH", "EVIDENCE_LEAF"],
              )
            }
          >
            回到树上的结构主脉
          </button>
        </article>
      ))}
      {visibleCandidates.length === 0 && (
        <p className="projection-empty">当前证据不足以形成结构候选。</p>
      )}
      {visibleFacts.map((fact) => (
        <div className="lab-fact" key={fact.fact_ref}>
          <strong>{factLabel(fact)}</strong>
          <span>事实存在；作用、容量与专业准入仍待核证</span>
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
        <p className="projection-empty">当前焦点没有可进入 Lab 的命盘事实。</p>
      )}
      <div className="lab-status-grid">
        <span>
          结构证据 · {lab.qualification_summary.structure_evidence_satisfied} 条已核验
        </span>
        <span>解释 · {statusLabel(lab.decision_route.status)}</span>
        <span>作用 · {statusLabel(lab.effect_status)}</span>
        <span>容量 · {statusLabel(lab.capacity_status)}</span>
        <span>专业准入 · {statusLabel(lab.professional_admission_status)}</span>
      </div>
      <p className="lab-boundary">Lab 不反写 LifeCase，也不把候选冒充正式结论。</p>
    </>
  );
}

function factLabel(
  fact: DreamSnapshot["projections"]["lab"]["facts"][number],
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
    return `${left}与${right}的六合成员关系`;
  }
  return "已提交的命盘结构事实";
}

function statusLabel(status: string): string {
  if (status === "SATISFIED") return "已核验";
  if (status === "REJECTED") return "未通过";
  if (status === "NOT_ADMITTED") return "尚未准入";
  if (status === "UNRESOLVED") return "尚未解决";
  return "待核证";
}
