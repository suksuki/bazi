import type { HomeSourceDiscussionAbstentionReceipt } from "../homeSourceDiscussionTypes";

export function SourceDiscussionAbstentionReceipt({
  mode,
  receipt,
}: {
  mode: "summary" | "detailed";
  receipt: HomeSourceDiscussionAbstentionReceipt;
}) {
  return (
    <section
      className="source-discussion-abstention"
      data-disposition={receipt.disposition}
      data-mode={mode}
      data-receipt-hash={receipt.receipt_hash}
      data-receipt-ref={receipt.receipt_ref}
    >
      <header>
        <span>
          <small>下游讨论授权</small>
          <strong>拒答凭据</strong>
        </span>
        <em>当前拒答</em>
      </header>

      <div className="source-discussion-question">
        <span>
          <small>当前问题</small>
          <strong>“这些来源怎样作用、现在能不能用？”</strong>
        </span>
        <span className="source-discussion-readiness">
          <b>
            {receipt.ready_carrier_count} / {receipt.carrier_count}
          </b>
          <small>个明干载体达到门槛</small>
        </span>
      </div>

      <p>
        当前只允许展示来源坐标、准入关系事实与证据缺口；不判断关系作用，也不判断可用或不可用。
      </p>

      <details
        className="source-discussion-receipt-detail"
        open={mode === "detailed" || undefined}
      >
        <summary>查看拒答凭据</summary>
        <dl>
          <ReceiptIdentity label="Disposition" value={receipt.disposition} />
          <ReceiptIdentity label="Reason" value={receipt.reason} />
          <ReceiptIdentity
            label="Prerequisite ref"
            value={receipt.prerequisite_ref}
          />
          <ReceiptIdentity
            label="Prerequisite hash"
            value={receipt.prerequisite_hash}
          />
          <ReceiptIdentity label="Receipt ref" value={receipt.receipt_ref} />
          <ReceiptIdentity label="Receipt hash" value={receipt.receipt_hash} />
        </dl>

        {mode === "detailed" && (
          <section
            className="source-discussion-blockers"
            data-blocker-count={receipt.blocking_requirement_ids.length}
          >
            <header>
              <strong>阻断条件 IDs</strong>
              <small>{receipt.blocking_requirement_ids.length} 项</small>
            </header>
            <div>
              {receipt.blocking_requirement_ids.map((requirementId) => (
                <code key={requirementId}>{requirementId}</code>
              ))}
            </div>
          </section>
        )}

        <p className="source-discussion-write-boundary">
          本拒答未调用 Provider · 未创建新 Decision · 未回写
        </p>
      </details>
    </section>
  );
}

function ReceiptIdentity({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>
        <code>{value}</code>
      </dd>
    </div>
  );
}
