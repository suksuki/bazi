import type {
  HomeSourceUsabilityCarrier,
  HomeSourceUsabilityPrerequisiteEnvelope,
  HomeSourceUsabilityRequirement,
  HomeSourceUsabilityRequirementId,
  HomeSourceUsabilityScope,
  HomeSourceUsabilityScopeId,
} from "../homeSourceUsabilityTypes";

const SLOT_LABELS = {
  year: "年柱",
  month: "月柱",
  day: "日柱",
  hour: "时柱",
} as const;

const SCOPE_LABELS: Record<HomeSourceUsabilityScopeId, string> = {
  EXACT_IDENTITY_ONLY: "严格同干",
  ELEMENT_AFFINITY_INCLUDED: "同五行扩展",
};

const REQUIREMENT_LABELS: Record<HomeSourceUsabilityRequirementId, string> = {
  MATCH_SCOPE_RULE: "匹配口径",
  RELATION_EFFECT_RULE: "关系作用",
  SEASONAL_CAPACITY_RULE: "月令与承载",
  MULTI_SOURCE_AGGREGATION_RULE: "多来源聚合",
  ROOT_USABILITY_RULE: "来源可用性",
  PROFESSIONAL_ADMISSION: "专业准入",
};

const REQUIREMENT_STATUS_LABELS: Record<
  HomeSourceUsabilityRequirement["status"],
  string
> = {
  NOT_ADMITTED: "规则未准入",
  NOT_TRIGGERED: "本载体未触发",
  UNRESOLVED: "仍待解决",
};

export function SourceUsabilityPrerequisitePanel({
  mode,
  readiness,
}: {
  mode: "summary" | "detailed";
  readiness: HomeSourceUsabilityPrerequisiteEnvelope;
}) {
  return (
    <section
      className="source-usability-prerequisite"
      data-mode={mode}
      data-prerequisite-ref={readiness.prerequisite_ref}
      data-prerequisite-hash={readiness.prerequisite_hash}
      data-ready-carrier-count={readiness.ready_carrier_count}
    >
      <header>
        <span>
          <small>下一层证据门槛</small>
          <strong>来源可用性还不能裁定</strong>
        </span>
        <em>{readiness.ready_carrier_count} 个达到门槛</em>
      </header>

      <div className="source-usability-scope-summary">
        <ScopeSummary
          clearCount={readiness.exact_identity_only_clear_count}
          label={SCOPE_LABELS.EXACT_IDENTITY_ONLY}
          reviewCount={readiness.exact_identity_only_review_required_count}
          scopeId="EXACT_IDENTITY_ONLY"
        />
        <ScopeSummary
          clearCount={readiness.element_affinity_included_clear_count}
          label={SCOPE_LABELS.ELEMENT_AFFINITY_INCLUDED}
          reviewCount={
            readiness.element_affinity_included_review_required_count
          }
          scopeId="ELEMENT_AFFINITY_INCLUDED"
        />
      </div>

      <div className="source-usability-boundary">
        <span>
          <b>{readiness.competing_carrier_count}</b>
          个载体存在口径竞争
        </span>
        <span>
          <b>{readiness.ready_carrier_count}</b>
          个可进入可用性讨论
        </span>
      </div>

      <p>
        两种口径都是只读研究范围。关系命中与未命中可以复核，但系统还没有权威规则选择口径、
        解释关系作用或合并多个来源。
      </p>

      {mode === "detailed" && (
        <div className="source-usability-carrier-list">
          {readiness.carriers.map((carrier, index) => (
            <SourceUsabilityCarrier
              carrier={carrier}
              expanded={index === 0}
              key={carrier.carrier_ref}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function ScopeSummary({
  clearCount,
  label,
  reviewCount,
  scopeId,
}: {
  clearCount: number;
  label: string;
  reviewCount: number;
  scopeId: HomeSourceUsabilityScopeId;
}) {
  return (
    <article data-scope-id={scopeId}>
      <strong>
        {label} · {clearCount + reviewCount} 个来源
      </strong>
      <span>
        <b>{clearCount}</b>
        未触发关系复核
      </span>
      <span className={reviewCount ? "needs-review" : undefined}>
        <b>{reviewCount}</b>
        待关系复核
      </span>
    </article>
  );
}

function SourceUsabilityCarrier({
  carrier,
  expanded,
}: {
  carrier: HomeSourceUsabilityCarrier;
  expanded: boolean;
}) {
  return (
    <article
      className="source-usability-carrier"
      data-carrier-ref={carrier.carrier_ref}
      data-discussion-ready={carrier.discussion_ready}
    >
      <header>
        <span>
          <small>明干载体</small>
          <strong>
            {SLOT_LABELS[carrier.visible_slot]} {carrier.visible_stem}
          </strong>
        </span>
        <em>门槛未满足</em>
      </header>

      <div className="source-usability-carrier-scopes">
        {carrier.scopes.map((scope) => (
          <CarrierScope key={scope.scope_ref} scope={scope} />
        ))}
      </div>

      <details className="source-usability-requirements" open={expanded}>
        <summary>查看 {carrier.requirements.length} 项核验条件</summary>
        <div>
          {carrier.requirements.map((requirement) => (
            <RequirementGap
              key={requirement.requirement_id}
              requirement={requirement}
            />
          ))}
        </div>
      </details>
    </article>
  );
}

function CarrierScope({ scope }: { scope: HomeSourceUsabilityScope }) {
  return (
    <section data-scope-id={scope.scope_id} data-scope-ref={scope.scope_ref}>
      <header>
        <strong>{SCOPE_LABELS[scope.scope_id]}</strong>
        <small>研究口径</small>
      </header>
      <dl>
        <div>
          <dt>来源</dt>
          <dd>{scope.source_review_count}</dd>
        </div>
        <div>
          <dt>未触发复核</dt>
          <dd>{scope.clear_count}</dd>
        </div>
        <div>
          <dt>待关系复核</dt>
          <dd>{scope.relation_review_count}</dd>
        </div>
        <div>
          <dt>关系交点</dt>
          <dd>{scope.intersection_count}</dd>
        </div>
      </dl>
      <p>关系作用待定 · 来源可用性待定 · 无选择权</p>
    </section>
  );
}

function RequirementGap({
  requirement,
}: {
  requirement: HomeSourceUsabilityRequirement;
}) {
  return (
    <article data-requirement-id={requirement.requirement_id}>
      <header>
        <strong>{REQUIREMENT_LABELS[requirement.requirement_id]}</strong>
        <em>{REQUIREMENT_STATUS_LABELS[requirement.status]}</em>
      </header>
      <p>{requirement.meaning}</p>
      <small>还需要：{requirement.next_evidence}</small>
    </article>
  );
}
