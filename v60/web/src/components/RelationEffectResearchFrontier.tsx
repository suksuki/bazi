import type {
  HomeRelationEffectRequiredRuleDimension,
  HomeRelationEffectResearchFrontierEnvelope,
  HomeRelationEffectRuleDemand,
} from "../homeRelationEffectFrontierTypes";
import type { HomeSourceUsabilityScopeId } from "../homeSourceUsabilityTypes";

const SLOT_LABELS = {
  year: "年柱",
  month: "月柱",
  day: "日柱",
  hour: "时柱",
} as const;

const RULE_DIMENSION_LABELS: Record<
  HomeRelationEffectRequiredRuleDimension,
  string
> = {
  APPLICABILITY_CONTEXT: "适用语境",
  EFFECT_DIRECTION: "作用方向",
  COMPLETION_CONDITIONS: "成立条件",
  BLOCKING_CONDITIONS: "阻断条件",
  COUNTER_EVIDENCE: "反证",
  PROFESSIONAL_PROVENANCE: "专业依据",
};

const SCOPE_LABELS: Record<HomeSourceUsabilityScopeId, string> = {
  EXACT_IDENTITY_ONLY: "仅严格同干",
  ELEMENT_AFFINITY_INCLUDED: "纳入同五行",
};

export function RelationEffectResearchFrontier({
  frontier,
  mode,
}: {
  frontier: HomeRelationEffectResearchFrontierEnvelope;
  mode: "summary" | "detailed";
}) {
  return (
    <section
      className="relation-effect-frontier"
      data-frontier-hash={frontier.frontier_hash}
      data-frontier-ref={frontier.frontier_ref}
      data-canonical-write-allowed={frontier.canonical_write_allowed}
      data-decision-created={frontier.decision_created}
      data-gate-invoked={frontier.gate_invoked}
      data-probability-claim-allowed={frontier.probability_claim_allowed}
      data-professional-verdict-allowed={
        frontier.professional_verdict_allowed
      }
      data-provider-invoked={frontier.provider_invoked}
      data-selection-authority={frontier.selection_authority}
      data-source-discussion={frontier.source_discussion_disposition}
      data-mode={mode}
    >
      <header>
        <span>
          <small>来源关系之后</small>
          <strong>关系作用规则需求</strong>
        </span>
        <em>研究顺序，不是结论</em>
      </header>

      <div className="relation-effect-frontier-counts">
        <span>
          <b>{frontier.scope_invariant_rule_demand_count}</b>
          跨口径作用规则
        </span>
        <span>
          <b>{frontier.match_scope_rule_first_count}</b>
          先补匹配口径
        </span>
        <span>
          <b>{frontier.admitted_effect_rule_count}</b>
          已准入作用规则
        </span>
      </div>

      <p className="relation-effect-frontier-boundary">
        这里只决定先补哪类规则；关系作用与来源可用性仍为{" "}
        <code>UNRESOLVED</code>。
      </p>

      {frontier.demands.length === 0 ? (
        <p className="relation-effect-frontier-empty">
          当前没有关系交点触发规则需求；系统没有据此增加任何下游判断。
        </p>
      ) : (
        mode === "detailed" && (
          <div
            className="relation-effect-demand-list"
            data-demand-count={frontier.demand_count}
          >
            {frontier.demands.map((demand, index) => (
              <RelationEffectDemand
                demand={demand}
                index={index}
                key={demand.demand_ref}
              />
            ))}
          </div>
        )
      )}

      <footer>
        <span>成员关系事实</span>
        <span>六维规则缺口</span>
        <span>只读 · 未创建 Decision</span>
      </footer>
    </section>
  );
}

function RelationEffectDemand({
  demand,
  index,
}: {
  demand: HomeRelationEffectRuleDemand;
  index: number;
}) {
  const isScopeInvariant =
    demand.dependency_status === "SCOPE_INVARIANT_RULE_DEMAND";

  return (
    <details
      className="relation-effect-demand"
      data-demand-ref={demand.demand_ref}
      data-dependency-status={demand.dependency_status}
      open
    >
      <summary>
        <span>
          <small>需求 {index + 1}</small>
          <strong>
            {isScopeInvariant ? "先补关系作用规则" : "先补匹配口径规则"}
          </strong>
        </span>
        <em>{isScopeInvariant ? "跨两种口径共现" : "仅宽口径出现"}</em>
      </summary>

      <div className="relation-effect-coordinate-grid">
        <span>
          <small>明干载体</small>
          <strong>
            {SLOT_LABELS[demand.visible_slot]} · {demand.visible_stem}
          </strong>
          <code>
            {demand.source_match_kind === "EXACT_IDENTITY"
              ? "EXACT_IDENTITY"
              : "SAME_ELEMENT_DIFFERENT_IDENTITY"}
          </code>
        </span>
        <span>
          <small>来源关系坐标</small>
          <strong>
            {SLOT_LABELS[demand.source_slot]} {demand.source_branch}
            <i>
              {demand.relation_type === "six_clash_membership"
                ? "六冲成员"
                : "六合成员"}
            </i>
            {SLOT_LABELS[demand.peer_slot]} {demand.peer_branch}
          </strong>
          <code>{demand.relation_fact_ref}</code>
        </span>
      </div>

      <section className="relation-effect-scope-presence">
        <header>
          <strong>命中的匹配口径</strong>
          <small>{demand.scope_presence.length} 个</small>
        </header>
        <div>
          {demand.scope_presence.map((scopeId) => (
            <span key={scopeId}>
              <b>{SCOPE_LABELS[scopeId]}</b>
              <code>{scopeId}</code>
            </span>
          ))}
        </div>
      </section>

      <section className="relation-effect-rule-gaps">
        <header>
          <strong>尚缺规则证据</strong>
          <small>{demand.required_rule_dimensions.length} 维</small>
        </header>
        <div>
          {demand.required_rule_dimensions.map((dimension) => (
            <span key={dimension}>
              <b>{RULE_DIMENSION_LABELS[dimension]}</b>
              <code>{dimension}</code>
            </span>
          ))}
        </div>
      </section>

      <dl className="relation-effect-demand-identity">
        <IdentityRow label="Carrier" value={demand.carrier_ref} />
        <IdentityRow label="Source evidence" value={demand.source_evidence_ref} />
        <IdentityRow label="Source review" value={demand.source_review_ref} />
        <IdentityRow label="Relation fact" value={demand.relation_fact_ref} />
        <IdentityRow label="Intersection" value={demand.intersection_ref} />
        <IdentityRow label="Demand" value={demand.demand_ref} />
      </dl>

      <p className="relation-effect-demand-boundary">
        当前只有成员关系与研究依赖；作用状态{" "}
        <code>{demand.effect_status}</code>，来源可用性{" "}
        <code>{demand.usability_status}</code>。
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
