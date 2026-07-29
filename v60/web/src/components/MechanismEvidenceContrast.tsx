import type {
  HomeCandidateMechanismEvidenceDepth,
  HomeMechanismEvidenceDepth,
} from "../homeApi";

const ATTENTION_LABELS = {
  PRIMARY_ATTENTION: "当前优先追查",
  DIRECT_COMPETITOR: "直接竞争",
  UNRANKED: "并列候选",
} as const;
const ROLE_LABELS = {
  SOURCE: "起点",
  BRIDGE: "承接",
  TARGET: "去向",
} as const;
const CARRIER_LABELS = {
  VISIBLE_AND_HIDDEN: "明藏并见",
  VISIBLE_ONLY: "明干可见",
  HIDDEN_ONLY: "藏干成员",
} as const;
const TIMING_LABELS = {
  DAYUN: "大运",
  ANNUAL: "流年",
  MONTHLY: "流月",
} as const;
const RELATION_LABELS = {
  same_branch_membership: "同支",
  six_clash_membership: "六冲",
  six_harmony_membership: "六合",
} as const;

export function MechanismEvidenceContrast({
  depth,
  mode = "compact",
}: {
  depth: HomeMechanismEvidenceDepth;
  mode?: "compact" | "detailed";
}) {
  if (!depth.candidates.length) {
    return null;
  }
  const candidates = [...depth.candidates].sort(
    (left, right) =>
      attentionOrder(left.attention_status) -
        attentionOrder(right.attention_status) ||
      left.pattern_label.localeCompare(right.pattern_label, "zh-CN"),
  );

  const content = (
    <div
      className="mechanism-evidence-contrast"
      data-depth-ref={depth.depth_ref}
      data-mode={mode}
    >
      <header className="mechanism-evidence-contrast-header">
        <span>
          <strong>候选证据对照</strong>
          <small>
            {depth.selected_attention_candidate_ref
              ? "关注顺序已记录，但没有形成专业胜负"
              : "当前只并列展示可追查材料"}
          </small>
        </span>
        <em>不计分 · 不判旺衰</em>
      </header>
      <div className="mechanism-evidence-candidate-grid">
        {candidates.map((candidate) => (
          <CandidateEvidenceCard
            candidate={candidate}
            candidates={depth.candidates}
            key={candidate.candidate_ref}
          />
        ))}
      </div>
      <p className="mechanism-evidence-contrast-boundary">
        月支、根源、时序和关系在这里都只是可核查坐标；作用、容量、可用性与专业准入仍待证据。
      </p>
    </div>
  );

  if (mode === "compact") {
    return (
      <details className="mechanism-evidence-contrast-disclosure">
        <summary>为什么这些候选仍在竞争？</summary>
        {content}
      </details>
    );
  }
  return content;
}

function CandidateEvidenceCard({
  candidate,
  candidates,
}: {
  candidate: HomeCandidateMechanismEvidenceDepth;
  candidates: HomeCandidateMechanismEvidenceDepth[];
}) {
  return (
    <article
      className="mechanism-evidence-candidate"
      data-attention={candidate.attention_status}
    >
      <header>
        <strong>{candidate.pattern_label}</strong>
        <em>{ATTENTION_LABELS[candidate.attention_status]}</em>
      </header>
      <div className="mechanism-role-depth-list">
        {candidate.roles.map((role) => (
          <div key={role.role_id}>
            <span>{ROLE_LABELS[role.role_id]}</span>
            <strong>
              {Array.from(
                new Set([...role.visible_labels, ...role.hidden_labels]),
              ).join("／")}
            </strong>
            <small>{CARRIER_LABELS[role.carrier_state]}</small>
            <i>
              {role.month_branch_source_evidence_refs.length ||
              role.month_branch_occurrence_refs.length
                ? "月支坐标可见"
                : "月支承接未见"}
              {" · "}
              {role.exact_source_evidence_refs.length
                ? "同干跨层"
                : role.elemental_source_evidence_refs.length
                  ? "同五行跨层"
                  : "来源对应未见"}
            </i>
          </div>
        ))}
      </div>
      <EvidenceLine
        empty="当前时序没有与角色标签直接交叠"
        label="时序"
        values={candidate.timing_overlaps.map(
          (item) =>
            `${TIMING_LABELS[item.timing_layer]}·${item.timing_ten_god_label}→${item.matching_role_ids.map((role) => ROLE_LABELS[role as keyof typeof ROLE_LABELS]).join("／")}`,
        )}
      />
      <EvidenceLine
        empty="当前时序没有触及候选参与柱位的关系成员"
        label="关系"
        values={candidate.timing_relations.map(
          (item) =>
            `${TIMING_LABELS[item.timing_layer]}·${RELATION_LABELS[item.relation_type]}(${pillarLabel(item.natal_slot)})`,
        )}
      />
      <EvidenceLine
        empty="未见共享参与者形成的直接竞争"
        label="竞争"
        values={candidate.shared_participants.map((item) => {
          const competitor = candidates.find(
            (candidateItem) =>
              candidateItem.candidate_ref === item.competing_candidate_ref,
          );
          return `与${competitor?.pattern_label ?? "另一候选"}共享${item.shared_labels.join("／")}`;
        })}
      />
    </article>
  );
}

function EvidenceLine({
  empty,
  label,
  values,
}: {
  empty: string;
  label: string;
  values: string[];
}) {
  return (
    <p className={values.length ? undefined : "is-empty"}>
      <b>{label}</b>
      <span>{values.length ? values.join("；") : empty}</span>
    </p>
  );
}

function attentionOrder(
  status: HomeCandidateMechanismEvidenceDepth["attention_status"],
) {
  return status === "PRIMARY_ATTENTION"
    ? 0
    : status === "DIRECT_COMPETITOR"
      ? 1
      : 2;
}

function pillarLabel(slot: "year" | "month" | "day" | "hour") {
  return (
    {
      year: "年支",
      month: "月支",
      day: "日支",
      hour: "时支",
    } as const
  )[slot];
}
