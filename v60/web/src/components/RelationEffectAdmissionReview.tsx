import type { HomeSnapshot } from "../homeApi";
import type {
  HomeRelationEffectAdmissionDimension,
  HomeRelationEffectAdmissionReviewEnvelope,
  HomeRelationEffectProposalDimensionStatus,
  HomeRelationEffectRuleAdmissionAssessment,
} from "../homeRelationEffectAdmissionTypes";
import { isRelationEffectAdmissionReviewDisplayable } from "../homeRelationEffectAdmissionGuard";

const SLOT_LABELS = {
  year: "年柱",
  month: "月柱",
  day: "日柱",
  hour: "时柱",
} as const;

const DIMENSION_LABELS: Record<
  HomeRelationEffectAdmissionDimension,
  string
> = {
  APPLICABILITY_CONTEXT: "适用语境",
  EFFECT_DIRECTION: "作用方向",
  COMPLETION_CONDITIONS: "成立条件",
  BLOCKING_CONDITIONS: "阻断条件",
  COUNTER_EVIDENCE: "反证",
  PROFESSIONAL_PROVENANCE: "专业依据",
};

const SUBMISSION_STATUS_LABELS: Record<
  HomeRelationEffectProposalDimensionStatus,
  string
> = {
  VERIFIED: "已提交材料",
  PARTIAL: "部分材料",
  COMPETING: "解释竞争",
  UNSUPPORTED: "材料不支持",
  MISSING: "缺失",
};

export function RelationEffectAdmissionReview({
  home,
  mode,
}: {
  home: HomeSnapshot;
  mode: "summary" | "detailed";
}) {
  const review = home.mingli.relation_effect_admission_review;
  const bindings = {
    frontier: home.mingli.relation_effect_frontier,
    reading: home.mingli.reading,
    lab: home.lab,
  };
  if (!isRelationEffectAdmissionReviewDisplayable(review, bindings)) {
    return (
      <section
        aria-label="关系作用规则审查暂不可显示"
        className="relation-effect-admission-review is-withheld"
        data-mode={mode}
        data-review-status="WITHHELD"
      >
        <strong>规则审查暂不展示</strong>
        <p>版本、同源身份或权限边界不完整，页面不会补写候选规则。</p>
      </section>
    );
  }

  const triggered = review.disposition === "REJECTED_PRE_ADMISSION";
  return (
    <section
      aria-label="关系作用规则预准入审查"
      className="relation-effect-admission-review"
      data-canonical-write-allowed={review.canonical_write_allowed}
      data-decision-created={review.decision_created}
      data-disposition={review.disposition}
      data-frontier-hash={review.frontier_hash}
      data-frontier-ref={review.frontier_ref}
      data-gate-invoked={review.gate_invoked}
      data-knowledge-promotion-request-created={
        review.knowledge_promotion_request_created
      }
      data-mode={mode}
      data-owner-professional-review-invoked={
        review.owner_professional_review_invoked
      }
      data-probability-claim-allowed={review.probability_claim_allowed}
      data-professional-verdict-allowed={
        review.professional_verdict_allowed
      }
      data-provider-invoked={review.provider_invoked}
      data-read-only={review.read_only}
      data-review-hash={review.review_hash}
      data-review-ref={review.review_ref}
      data-review-status="AVAILABLE"
      data-review-version={review.review_version}
      data-selection-authority={review.selection_authority}
    >
      <header>
        <span>
          <small>关系作用规则 · 预准入</small>
          <strong>自动受损捷径审查</strong>
        </span>
        <em>{triggered ? "未准入" : "未触发"}</em>
      </header>

      <div className="relation-effect-admission-counts">
        <span>
          <b>{review.reviewed_demand_count}</b>
          审查
        </span>
        <span>
          <b>{review.admitted_effect_rule_count}</b>
          准入
        </span>
        <span>
          <b>{review.deferred_match_scope_demand_refs.length}</b>
          等待口径
        </span>
      </div>

      <p className="relation-effect-admission-summary">
        {triggered
          ? "系统拒绝把成员关系直接改写成来源自动受损或自动不可用；拒绝的是捷径，不是否定关系作用。"
          : "当前没有严格同干的子午六冲来源坐标进入这项预准入审查。"}
      </p>

      {mode === "detailed" && triggered && (
        <div
          className="relation-effect-admission-assessments"
          data-assessment-count={review.assessments.length}
        >
          {review.assessments.map((assessment) => (
            <AdmissionAssessment
              assessment={assessment}
              key={assessment.assessment_ref}
              review={review}
            />
          ))}
        </div>
      )}

      {mode === "detailed" && !triggered && (
        <p className="relation-effect-admission-empty">
          没有适用坐标，因此没有展示候选捷径、竞争解释或作用结论。
        </p>
      )}

      <footer>
        <span>作用状态 · {review.effect_status}</span>
        <span>来源可用性 · {review.usability_status}</span>
        <span>只读 · 未创建 Decision</span>
      </footer>
    </section>
  );
}

function AdmissionAssessment({
  assessment,
  review,
}: {
  assessment: HomeRelationEffectRuleAdmissionAssessment;
  review: HomeRelationEffectAdmissionReviewEnvelope;
}) {
  return (
    <details
      className="relation-effect-admission-assessment"
      data-assessment-hash={assessment.assessment_hash}
      data-assessment-ref={assessment.assessment_ref}
      data-candidate-truth-status={assessment.candidate_truth_status}
      data-disposition={assessment.disposition}
      open
    >
      <summary>
        <span>
          <small>具体捷径</small>
          <strong>
            {SLOT_LABELS[assessment.visible_slot]} {assessment.visible_stem} ·{" "}
            {SLOT_LABELS[assessment.source_slot]}午／
            {SLOT_LABELS[assessment.peer_slot]}子
          </strong>
        </span>
        <em>拒绝预准入</em>
      </summary>

      <blockquote>{assessment.proposal_claim}</blockquote>
      <p className="relation-effect-admission-truth-boundary">
        这条候选的真假没有被判定；当前只证明它不能越过专业准入边界。
      </p>

      <section className="relation-effect-held-interpretations">
        <header>
          <strong>三种竞争解释</strong>
          <small>全部 HELD · 没有选择</small>
        </header>
        <div>
          {assessment.interpretations.map((interpretation, index) => (
            <article
              data-effect-atom-created={interpretation.effect_atom_created}
              data-interpretation-id={interpretation.interpretation_id}
              data-interpretation-ref={interpretation.interpretation_ref}
              data-selected={interpretation.selected}
              data-status={interpretation.status}
              key={interpretation.interpretation_ref}
            >
              <span>
                <b>解释 {index + 1}</b>
                <em>{interpretation.status}</em>
              </span>
              <p>{interpretation.summary}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="relation-effect-admission-dimensions">
        <header>
          <strong>六维准入状态</strong>
          <small>0 / {assessment.dimension_assessments.length} 满足</small>
        </header>
        <div>
          {assessment.dimension_assessments.map((dimension) => (
            <article
              data-dimension-id={dimension.dimension_id}
              data-satisfied={dimension.satisfied}
              data-submission-status={dimension.submission_status}
              key={dimension.dimension_id}
            >
              <span>
                <b>{DIMENSION_LABELS[dimension.dimension_id]}</b>
                <em>
                  {SUBMISSION_STATUS_LABELS[dimension.submission_status]}
                </em>
              </span>
              <p>{dimension.gap}</p>
              <div aria-label={`${DIMENSION_LABELS[dimension.dimension_id]}当前凭据`}>
                {dimension.current_basis_refs.length ? (
                  dimension.current_basis_refs.map((ref) => (
                    <code key={ref}>{ref}</code>
                  ))
                ) : (
                  <small>当前没有可绑定凭据</small>
                )}
              </div>
            </article>
          ))}
        </div>
      </section>

      <dl className="relation-effect-admission-identity">
        <IdentityRow label="Review ref" value={review.review_ref} />
        <IdentityRow label="Review hash" value={review.review_hash} />
        <IdentityRow label="Assessment ref" value={assessment.assessment_ref} />
        <IdentityRow label="Assessment hash" value={assessment.assessment_hash} />
        <IdentityRow label="Frontier ref" value={review.frontier_ref} />
        <IdentityRow label="Frontier hash" value={review.frontier_hash} />
        <IdentityRow label="Reading ref" value={review.reading_ref} />
        <IdentityRow label="Reading hash" value={review.reading_hash} />
        <IdentityRow label="Policy ref" value={assessment.policy_ref} />
        <IdentityRow label="Policy hash" value={assessment.policy_hash} />
        <IdentityRow label="Proposal ref" value={assessment.proposal_ref} />
        <IdentityRow label="Proposal hash" value={assessment.proposal_hash} />
      </dl>

      <p className="relation-effect-admission-boundary">
        未调用 Provider、专业审阅、Knowledge promotion、Gate 或 Decision；
        没有创建作用原子，也没有判定来源可用或不可用。
      </p>
    </details>
  );
}

function IdentityRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>
        <code>{value}</code>
      </dd>
    </div>
  );
}
