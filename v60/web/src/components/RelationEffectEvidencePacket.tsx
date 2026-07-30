import type { HomeSnapshot } from "../homeApi";
import { isRelationEffectEvidencePacketDisplayable } from "../homeRelationEffectEvidencePacketGuard";
import type {
  HomeRelationEffectEvidenceDemandPacket,
  HomeRelationEffectEvidenceDimensionSlot,
  HomeRelationEffectProfessionalArtifactKind,
} from "../homeRelationEffectEvidencePacketTypes";

const SLOT_LABELS = {
  year: "年柱",
  month: "月柱",
  day: "日柱",
  hour: "时柱",
} as const;

const DIMENSION_LABELS = {
  APPLICABILITY_CONTEXT: "适用语境",
  EFFECT_DIRECTION: "作用方向",
  COMPLETION_CONDITIONS: "成立条件",
  BLOCKING_CONDITIONS: "阻断条件",
  COUNTER_EVIDENCE: "反证",
  PROFESSIONAL_PROVENANCE: "专业依据",
} as const;

const PATH_LABELS = {
  DETERMINISTIC_RELATION_FACT_AVAILABLE: ["关系事实", "已记录"],
  PROFESSIONAL_RULE_EVIDENCE_BLOCKED: ["专业证据", "材料阻断"],
  OWNER_PROFESSIONAL_REVIEW_NOT_INVOKED: ["Owner 审阅", "未启动"],
  KNOWLEDGE_ADMISSION_NOT_ELIGIBLE: ["Knowledge 准入", "未具备"],
  READING_RULE_PROFILE_QUALIFICATION_NOT_AUTHORIZED: [
    "新 Reading 资格化",
    "未授权",
  ],
  EFFECT_DECISION_WITHHELD: ["作用决策", "暂缓"],
} as const;

const ARTIFACT_LABELS: Record<
  HomeRelationEffectProfessionalArtifactKind,
  string
> = {
  PROFESSIONAL_APPLICABILITY_RULE: "专业适用范围规则",
  PROFESSIONAL_EFFECT_DIRECTION_RULE: "专业作用方向规则",
  PROFESSIONAL_COMPLETION_RULE: "专业成立条件规则",
  PROFESSIONAL_BLOCKING_RULE: "专业阻断条件规则",
  PROFESSIONAL_COUNTER_EVIDENCE_PROTOCOL: "专业反证协议",
  PROFESSIONAL_SOURCE_MANIFEST: "专业来源清单",
  PROFESSIONAL_SOURCE_CITATION: "命题级可定位引文",
  OWNER_PROFESSIONAL_REVIEW_RECEIPT: "Owner 专业审阅回执",
};

const PROFESSIONAL_PATH_LABELS = {
  COMPLETE_PROFESSIONAL_EVIDENCE_PACKET: "补齐专业证据包",
  OWNER_PROFESSIONAL_REVIEW_APPROVED: "Owner 专业审阅通过",
  KNOWLEDGE_IMMUTABLE_RULE_PROFILE_ADMITTED: "Knowledge 准入不可变规则版本",
  NEW_READING_BINDS_ADMITTED_RULE_PROFILE: "新 Reading 绑定该规则版本",
  DETERMINISTIC_RULE_APPLICATION_OR_UNRESOLVED:
    "确定性应用规则，或继续 UNRESOLVED",
} as const;

export function RelationEffectEvidencePacket({
  home,
  mode,
}: {
  home: HomeSnapshot;
  mode: "summary" | "detailed";
}) {
  const packet = home.mingli.relation_effect_evidence_packet;
  if (
    !isRelationEffectEvidencePacketDisplayable(packet, {
      frontier: home.mingli.relation_effect_frontier,
      review: home.mingli.relation_effect_admission_review,
      reading: home.mingli.reading,
      lab: home.lab,
    })
  ) {
    return (
      <section
        aria-label="关系作用专业规则证据包暂不可显示"
        className="relation-effect-evidence-packet is-withheld"
        data-mode={mode}
        data-packet-status="WITHHELD"
      >
        <strong>专业规则证据包暂不展示</strong>
        <p>版本、同源身份或权限边界不完整，页面不会补写材料需求或作用结论。</p>
      </section>
    );
  }

  const triggered = packet.status === "EVIDENCE_INTAKE_REQUIRED";
  return (
    <section
      aria-label="关系作用专业规则证据包"
      className="relation-effect-evidence-packet"
      data-canonical-write-allowed={packet.canonical_write_allowed}
      data-decision-created={packet.decision_created}
      data-decision-request-created={packet.decision_request_created}
      data-effect-decision-status={packet.effect_decision_status}
      data-gate-invoked={packet.gate_invoked}
      data-knowledge-admission-eligible={packet.knowledge_admission_eligible}
      data-knowledge-promotion-request-created={
        packet.knowledge_promotion_request_created
      }
      data-ledger-invoked={packet.ledger_invoked}
      data-llm-allowed={packet.llm_allowed}
      data-mode={mode}
      data-owner-professional-review-invoked={
        packet.owner_professional_review_invoked
      }
      data-packet-hash={packet.packet_hash}
      data-packet-ref={packet.packet_ref}
      data-packet-status="AVAILABLE"
      data-packet-version={packet.packet_version}
      data-professional-verdict-allowed={
        packet.professional_verdict_allowed
      }
      data-provider-invoked={packet.provider_invoked}
      data-read-only={packet.read_only}
      data-reasoner-invoked={packet.reasoner_invoked}
      data-selection-authority={packet.selection_authority}
    >
      <header>
        <span>
          <small>关系作用 · 专业证据准备度</small>
          <strong>规则证据包</strong>
        </span>
        <em>{triggered ? "作用决策暂缓" : "当前未触发"}</em>
      </header>

      <div className="relation-effect-evidence-counts">
        <span>
          <b>
            {packet.ready_dimension_slot_count} /{" "}
            {packet.required_dimension_slot_count}
          </b>
          规则证据
        </span>
        <span>
          <b>{packet.professional_evidence_count}</b>
          专业材料
        </span>
        <span>
          <b>{packet.demand_packet_count}</b>
          关系需求
        </span>
      </div>

      {triggered ? (
        <>
          <p className="relation-effect-evidence-summary">
            当前运行基底只能定位事实与缺口，不是专业证据；六维材料未齐，不能讨论关系作用或来源可用性。
          </p>
          <DecisionPath path={packet.decision_path} />
        </>
      ) : (
        <p className="relation-effect-evidence-empty">
          当前没有严格目标关系触发专业证据包；系统没有伪造空候选或作用结论。
        </p>
      )}

      {mode === "detailed" && triggered && (
        <>
          <RequiredProfessionalPath path={packet.required_professional_path} />
          <div
            className="relation-effect-evidence-demands"
            data-demand-packet-count={packet.demand_packet_count}
          >
            {packet.demand_packets.map((demandPacket) => (
              <EvidenceDemandPacket
                demandPacket={demandPacket}
                key={demandPacket.demand_packet_ref}
              />
            ))}
          </div>
        </>
      )}

      <footer>
        <span>Readiness projection · 不是 Decision</span>
        <span>LLM／Provider／Gate 均未调用</span>
        <span>作用与来源可用性 · UNRESOLVED</span>
      </footer>
    </section>
  );
}

function RequiredProfessionalPath({
  path,
}: {
  path: HomeSnapshot["mingli"]["relation_effect_evidence_packet"]["required_professional_path"];
}) {
  return (
    <section
      className="relation-effect-future-path"
      data-path-semantics="FUTURE_AUTHORITY_PATH_NOT_EXECUTED"
    >
      <header>
        <strong>未来专业权威路径</strong>
        <small>尚未执行</small>
      </header>
      <ol>
        {path.map((step) => (
          <li data-professional-path-step={step} key={step}>
            {PROFESSIONAL_PATH_LABELS[step]}
          </li>
        ))}
      </ol>
      <p>
        这条路径必须生成新的 Knowledge 规则版本与新的 Reading；当前机制关注顺序
        Decision 不在本包证据链内。
      </p>
    </section>
  );
}

function DecisionPath({
  path,
}: {
  path: HomeSnapshot["mingli"]["relation_effect_evidence_packet"]["decision_path"];
}) {
  return (
    <ol
      aria-label="专业规则准备路径，不是作用决策"
      className="relation-effect-decision-path"
      data-path-semantics="READINESS_PATH_NOT_DECISION"
    >
      {path.map((step) => (
        <li data-path-step={step} key={step}>
          <b>{PATH_LABELS[step][0]}</b>
          <em>{PATH_LABELS[step][1]}</em>
        </li>
      ))}
    </ol>
  );
}

function EvidenceDemandPacket({
  demandPacket,
}: {
  demandPacket: HomeRelationEffectEvidenceDemandPacket;
}) {
  return (
    <details
      className="relation-effect-evidence-demand"
      data-demand-packet-hash={demandPacket.demand_packet_hash}
      data-demand-packet-ref={demandPacket.demand_packet_ref}
      open
    >
      <summary>
        <span>
          <small>关系事实后的专业材料需求</small>
          <strong>
            {SLOT_LABELS[demandPacket.visible_slot]}{" "}
            {demandPacket.visible_stem} ·{" "}
            {SLOT_LABELS[demandPacket.source_slot]}午／
            {SLOT_LABELS[demandPacket.peer_slot]}子
          </strong>
        </span>
        <em>0 / 6 就绪</em>
      </summary>

      <div className="relation-effect-evidence-slots">
        {demandPacket.dimension_slots.map((slot) => (
          <EvidenceDimensionSlot key={slot.slot_ref} slot={slot} />
        ))}
      </div>

      <dl className="relation-effect-evidence-identity">
        <IdentityRow
          label="Demand packet"
          value={demandPacket.demand_packet_ref}
        />
        <IdentityRow label="Assessment" value={demandPacket.assessment_ref} />
        <IdentityRow label="Demand" value={demandPacket.demand_ref} />
        <IdentityRow
          label="Relation fact"
          value={demandPacket.relation_fact_ref}
        />
      </dl>

      <p className="relation-effect-evidence-boundary">
        当前 0 项专业材料；没有启动 Owner 专业审阅、Knowledge
        promotion、新 Reading 资格化或作用 Decision。
      </p>
    </details>
  );
}

function EvidenceDimensionSlot({
  slot,
}: {
  slot: HomeRelationEffectEvidenceDimensionSlot;
}) {
  return (
    <article
      className="relation-effect-evidence-slot"
      data-current-basis-status={slot.current_basis_status}
      data-dimension-id={slot.dimension_id}
      data-guidance-semantics={slot.guidance_semantics}
      data-professional-evidence-count={slot.professional_evidence_count}
      data-ready={slot.ready}
      data-slot-ref={slot.slot_ref}
      data-slot-status={slot.slot_status}
    >
      <header>
        <span>
          <small>专业规则维度</small>
          <strong>{DIMENSION_LABELS[slot.dimension_id]}</strong>
        </span>
        <em>材料缺失</em>
      </header>

      <p className="relation-effect-evidence-requirement">
        {slot.requirement}
      </p>

      <dl>
        <div className="relation-effect-evidence-context-basis">
          <dt>当前运行基底</dt>
          <dd>
            <b>不是专业证据材料</b>
            {slot.current_basis_refs.length ? (
              slot.current_basis_refs.map((ref) => (
                <code key={ref}>{ref}</code>
              ))
            ) : (
              <small>当前无运行基底引用</small>
            )}
          </dd>
        </div>
        <div>
          <dt>建议提交的材料类型</dt>
          <dd className="relation-effect-evidence-artifact-kinds">
            {slot.requested_artifact_kinds.map((kind) => (
              <span key={kind}>{ARTIFACT_LABELS[kind]}</span>
            ))}
          </dd>
        </div>
        <div>
          <dt>已绑定专业材料</dt>
          <dd>0 项 · 尚无 professional evidence ref</dd>
        </div>
      </dl>

      <p className="relation-effect-evidence-next-action">
        <b>下一步：</b>
        {slot.next_action}
      </p>
      <small>材料请求指南，不代表 Knowledge 已接受或准入。</small>
    </article>
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
