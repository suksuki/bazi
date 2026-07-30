import { useState } from "react";

import type { HomeSnapshot } from "../homeApi";
import { isRelationEffectEvidenceMaterialStateDisplayable } from "../homeRelationEffectEvidenceMaterialGuard";
import { isRelationEffectEvidenceRequestStateDisplayable } from "../homeRelationEffectEvidenceRequestGuard";
import type { HomeRelationEffectEvidenceRequestReceipt } from "../homeRelationEffectEvidenceRequestTypes";
import { createRelationEffectEvidenceRequest } from "../relationEffectEvidenceRequestApi";
import { RelationEffectEvidenceMaterialControl } from "./RelationEffectEvidenceMaterial";

const PILLAR_LABELS = {
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

export function RelationEffectEvidenceRequestSummary({
  home,
}: {
  home: HomeSnapshot;
}) {
  const packet = home.mingli.relation_effect_evidence_packet;
  const receipt =
    home.mingli.relation_effect_evidence_request_receipt;
  const safe = isRelationEffectEvidenceRequestStateDisplayable(receipt, {
    packet,
    lab: home.lab,
  });
  const materials =
    home.mingli.relation_effect_evidence_materials;
  const materialsSafe =
    isRelationEffectEvidenceMaterialStateDisplayable(materials, {
      packet,
      receipt,
      lab: home.lab,
    });
  if (!safe || !materialsSafe) return <Withheld mode="summary" />;
  if (!receipt) return null;

  return (
    <section
      aria-label="关系作用补证准备请求摘要"
      className="relation-effect-evidence-request-summary"
      data-evidence-role={receipt.evidence_role}
      data-receipt-hash={receipt.receipt_hash}
      data-receipt-ref={receipt.receipt_ref}
      data-request-state="RECORDED"
    >
      <span>
        <small>专业证据准备</small>
        <strong>补证准备请求已登记</strong>
      </span>
      <span>
        <b>{materials.length}</b> 份未核验候选元数据 ·{" "}
        <b>0 / {receipt.requested_dimension_slot_count}</b> 就绪
      </span>
      <p>
        候选元数据不是专业材料、专业证据、专业审阅或作用 Decision。
      </p>
    </section>
  );
}

export function RelationEffectEvidenceRequestControl({
  home,
  onChanged,
}: {
  home: HomeSnapshot;
  onChanged: () => Promise<void>;
}) {
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const packet = home.mingli.relation_effect_evidence_packet;
  const receipt =
    home.mingli.relation_effect_evidence_request_receipt;
  const safe = isRelationEffectEvidenceRequestStateDisplayable(receipt, {
    packet,
    lab: home.lab,
  });
  const materialsSafe =
    isRelationEffectEvidenceMaterialStateDisplayable(
      home.mingli.relation_effect_evidence_materials,
      { packet, receipt, lab: home.lab },
    );

  if (!safe || !materialsSafe) return <Withheld mode="detailed" />;
  if (packet.status !== "EVIDENCE_INTAKE_REQUIRED") return null;

  const createRequest = async () => {
    setWorking(true);
    setError(null);
    try {
      await createRelationEffectEvidenceRequest(packet);
      await onChanged();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setWorking(false);
    }
  };

  if (!receipt) {
    return (
      <section
        aria-label="登记关系作用补证准备请求"
        className="relation-effect-evidence-request"
        data-request-state="NOT_RECORDED"
      >
        <header>
          <span>
            <small>专业证据准备 · 当前尚未登记</small>
            <strong>把六维缺口登记为补证准备清单</strong>
          </span>
          <em>0 材料 · 0 / {packet.required_dimension_slot_count}</em>
        </header>
        <p>
          系统只会锁定当前规则证据包、精确需求和六维缺口，不接收或生成任何材料。
        </p>
        <button
          data-request-command="CREATE"
          disabled={working}
          onClick={() => void createRequest()}
          type="button"
        >
          {working ? "正在登记…" : "登记补证准备请求"}
        </button>
        <small>
          {
            "当前没有自动执行方；不接收文件、URL 或自由文本，也不会启动专业审阅、Knowledge 准入、Gate 或 Decision。"
          }
        </small>
        {error && <p role="alert">{error}</p>}
      </section>
    );
  }

  return (
    <RecordedRequest
      home={home}
      onChanged={onChanged}
      receipt={receipt}
    />
  );
}

function RecordedRequest({
  home,
  onChanged,
  receipt,
}: {
  home: HomeSnapshot;
  onChanged: () => Promise<void>;
  receipt: HomeRelationEffectEvidenceRequestReceipt;
}) {
  const packet = home.mingli.relation_effect_evidence_packet;
  return (
    <section
      aria-label="关系作用补证准备请求回执"
      className="relation-effect-evidence-request is-recorded"
      data-evidence-role={receipt.evidence_role}
      data-professional-evidence-count={
        receipt.professional_evidence_count
      }
      data-professional-material-count={
        receipt.professional_material_count
      }
      data-ready-dimension-slot-count={
        receipt.ready_dimension_slot_count
      }
      data-receipt-hash={receipt.receipt_hash}
      data-receipt-ref={receipt.receipt_ref}
      data-request-state="RECORDED"
      data-request-status={receipt.status}
    >
      <header>
        <span>
          <small>专业证据准备 · 请求回执</small>
          <strong>补证准备请求已登记</strong>
        </span>
        <em>不是证据</em>
      </header>

      <div className="relation-effect-evidence-request-counts">
        <span>
          <b>{receipt.request_item_count}</b>
          精确需求
        </span>
        <span>
          <b>0</b>
          专业材料
        </span>
        <span>
          <b>0 / {receipt.requested_dimension_slot_count}</b>
          规则证据
        </span>
      </div>

      <dl className="relation-effect-evidence-request-identity">
        <IdentityRow label="Receipt ref" value={receipt.receipt_ref} />
        <IdentityRow label="Receipt hash" value={receipt.receipt_hash} />
        <IdentityRow label="Packet ref" value={receipt.packet_ref} />
        <IdentityRow label="Packet hash" value={receipt.packet_hash} />
      </dl>

      <div className="relation-effect-evidence-request-items">
        {receipt.request_items.map((item, index) => {
          const demand = packet.demand_packets.find(
            (candidate) =>
              candidate.demand_packet_ref === item.demand_packet_ref,
          );
          if (!demand) return null;
          return (
            <article
              data-demand-packet-ref={item.demand_packet_ref}
              data-request-item-ref={item.request_item_ref}
              key={item.request_item_ref}
            >
              <header>
                <span>
                  <small>精确需求 {index + 1}</small>
                  <strong>
                    {PILLAR_LABELS[demand.visible_slot]}{" "}
                    {demand.visible_stem} ·{" "}
                    {PILLAR_LABELS[demand.source_slot]}
                    {demand.source_branch}／
                    {PILLAR_LABELS[demand.peer_slot]}
                    {demand.peer_branch}
                  </strong>
                </span>
                <em>{item.requested_dimension_slot_count} 维待补</em>
              </header>
              <div>
                {item.dimension_slots.map((slot) => (
                  <span
                    data-dimension-id={slot.dimension_id}
                    data-ready={slot.ready}
                    data-requested-slot-ref={slot.slot_ref}
                    key={slot.slot_ref}
                  >
                    <b>{DIMENSION_LABELS[slot.dimension_id]}</b>
                    <span>{slot.requirement}</span>
                    <small>下一步：{slot.next_action}</small>
                  </span>
                ))}
              </div>
            </article>
          );
        })}
      </div>

      <RelationEffectEvidenceMaterialControl
        home={home}
        onChanged={onChanged}
      />

      <p className="relation-effect-evidence-request-boundary">
        当前补证准备请求仍是 0 专业材料、0 专业证据；候选书目元数据不会改变
        Owner 专业审阅、Knowledge 准入或作用与来源可用性的
        UNRESOLVED 状态。
      </p>
    </section>
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

function Withheld({ mode }: { mode: "summary" | "detailed" }) {
  return (
    <section
      aria-label="关系作用补证准备请求暂不可显示"
      className="relation-effect-evidence-request is-withheld"
      data-mode={mode}
      data-request-state="WITHHELD"
    >
      <strong>补证准备请求暂不展示</strong>
      <p>回执版本、同源身份或权限边界不完整，页面不会展示或登记请求。</p>
    </section>
  );
}
