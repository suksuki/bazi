import type { HomeSnapshot } from "../homeApi";

type DecisionTraceMode = "mingli" | "abu" | "lab";
type Comparison = HomeSnapshot["lab"]["mechanism_comparison"];
type Qualification = HomeSnapshot["mingli"]["mechanism_qualification"];
type Reading = HomeSnapshot["mingli"]["reading"];

const AUTHORITY_LABELS: Record<
  Exclude<Comparison["authority"], null>,
  string
> = {
  RULE_ENGINE: "规则引擎",
  LLM_REASONER: "有界推理比较",
};

const CHECK_STATUS_LABELS = {
  PARTIAL: "部分材料",
  MISSING: "证据缺失",
  NOT_ADMITTED: "规则未准入",
  UNRESOLVED: "仍待核证",
} as const;

const INPUT_SCOPE_LABELS = {
  SOURCE_USABILITY: "来源可用性",
  TIMING_ACTIVATION: "时序激活",
  MECHANISM_QUALIFICATION: "机制资格",
  PROFESSIONAL_ADMISSION: "专业准入",
  CALIBRATION: "校准与概率",
} as const;

const ADMITTED_SCOPE_LABELS = {
  MECHANISM_CANDIDATE_EVIDENCE: "原局机制候选证据",
} as const;

export function MechanismDecisionTrace({
  comparison,
  mode,
  qualification,
  reading,
}: {
  comparison: Comparison;
  mode: DecisionTraceMode;
  qualification: Qualification;
  reading: Reading;
}) {
  const trace = comparison.decision_trace;
  const selectedCandidateRef =
    trace?.selected_candidate_ref ?? comparison.selected_candidate_ref;
  const selectedCandidate = qualification.candidates.find(
    (candidate) => candidate.candidate_ref === selectedCandidateRef,
  );
  const blockingChecks =
    selectedCandidate?.checks.filter((check) => check.status !== "PRESENT") ?? [];

  if (!comparison.decision_ref || !selectedCandidateRef) {
    const pendingTitle =
      comparison.candidate_count === 0
        ? "当前没有可比较候选"
        : comparison.candidate_count === 1
          ? "单条候选尚未记录顺序"
          : "候选仍在并列核查";
    const pendingCopy =
      comparison.candidate_count === 0
        ? "当前真实命盘没有达到本版结构候选门槛；页面不会补造候选或 Decision。"
        : comparison.candidate_count === 1
          ? "当前有 1 条结构候选，但尚未形成规则引擎 Decision；页面不会自行写入。"
          : `当前有 ${comparison.candidate_count} 条结构候选，但还没有一份已记录的关注排序。系统不会在页面里自行挑选。`;
    return (
      <section
        className="mechanism-decision-trace is-pending"
        data-candidate-count={comparison.candidate_count}
        data-mode={mode}
        data-pending-kind={
          comparison.candidate_count === 0
            ? "NO_CANDIDATE"
            : comparison.candidate_count === 1
              ? "SINGLE_CANDIDATE"
              : "MULTIPLE_CANDIDATES"
        }
        data-status="NOT_RUN"
      >
        <header>
          <span>
            <small>关注顺序</small>
            <strong>{pendingTitle}</strong>
          </span>
          <em>尚无 Decision</em>
        </header>
        <p>{pendingCopy}</p>
      </section>
    );
  }

  const authorityCode = trace?.authority ?? comparison.authority;
  const authority = authorityCode
    ? AUTHORITY_LABELS[authorityCode]
    : "已记录的关注排序";
  const selectedLabel =
    selectedCandidate?.pattern_label ?? selectedCandidateRef;
  const readingBound = reading.decision_refs.includes(comparison.decision_ref);
  const decisionRef = trace?.decision_ref ?? comparison.decision_ref;
  const decisionHash = trace?.decision_hash ?? comparison.decision_hash;
  const ruleEngineRoute = trace?.authority === "RULE_ENGINE";
  const recordedRationale =
    ruleEngineRoute
      ? "当前只有一条达到注意力比较门槛的候选；规则引擎据此把它记录为唯一关注项。"
      : comparison.rationale_summary ??
        trace?.route_reason ??
        "这份 Decision 没有记录可展示的理由。";

  return (
    <section
      className="mechanism-decision-trace"
      data-decision-hash={decisionHash}
      data-decision-ref={decisionRef}
      data-mode={mode}
      data-reading-bound={readingBound}
      data-selected-candidate-ref={selectedCandidateRef}
      data-status={comparison.status}
      data-trace-version={trace?.trace_version}
      data-trace-integrity={trace?.trace_integrity_status ?? "UNAVAILABLE"}
    >
      <header>
        <span>
          <small>同一份关注排序</small>
          <strong>{selectedLabel}</strong>
        </span>
        <span className="mechanism-decision-authority">
          <em>{authority}</em>
          <small>
            {trace
              ? `${trace.trace_integrity_status} · 身份与覆盖已核验`
              : "Decision trace 不可用"}
          </small>
        </span>
      </header>

      <div className="mechanism-decision-trace-grid">
        <section>
          <h3>为什么先追查它？</h3>
          <blockquote>{recordedRationale}</blockquote>
          <p>
            {trace?.selection_rationale_contract ===
            "DETERMINISTIC_SINGLE_CANDIDATE_ROUTE_REASON_ONLY"
              ? "这是固定的单候选路由原因，不是专业选择理由。"
              : trace?.selection_rationale_contract ===
                  "FREE_TEXT_NO_DISTINCT_SELECTION_BASIS_FIELD"
                ? "当前契约只有一段整体理由，没有独立的候选区分理由字段。"
                : "当前投影没有提供独立的候选区分理由字段。"}
            上文按原记录显示；系统不会根据数量、口径或未决项补写选中原因。
          </p>
        </section>

        <section>
          <h3>为什么还不能裁决？</h3>
          {selectedCandidate ? (
            <>
              <p>
                这条候选仍有 {blockingChecks.length} 项条件未完整满足；
                关注顺序不等于有效做功、可用性或专业结论。
              </p>
              <div className="mechanism-decision-gap-summary">
                {blockingChecks.map((check) => (
                  <span data-status={check.status.toLowerCase()} key={check.dimension}>
                    <b>{check.label}</b>
                    <small>
                      {check.status === "PRESENT"
                        ? "已有"
                        : CHECK_STATUS_LABELS[check.status]}
                    </small>
                  </span>
                ))}
              </div>
              {mode === "lab" && (
                <div className="mechanism-decision-gap-detail">
                  {blockingChecks.map((check) => (
                    <article key={check.dimension}>
                      <strong>{check.label}</strong>
                      <p>{check.meaning}</p>
                      <small>还需要：{check.next_evidence}</small>
                    </article>
                  ))}
                </div>
              )}
            </>
          ) : (
            <p>
              当前 qualification 中找不到所选候选的同源条目，因此页面不会补造门槛说明。
            </p>
          )}
        </section>
      </div>

      <div className="mechanism-decision-coverage">
        <span>
          {trace?.candidate_coverage_semantics ===
          "RULE_ENGINE_SINGLE_ATTENTION_CANDIDATE"
            ? "规则唯一候选 "
            : "候选覆核 "}
          {trace
            ? `${trace.reviewed_candidate_refs.length}/${trace.attention_candidate_refs.length}`
            : `未知/${comparison.candidate_count}`}
        </span>
        <span>
          绑定证据 {trace?.bound_evidence_refs.length ?? "未知"}
        </span>
        <span>
          {trace?.evidence_use_semantics ===
          "REQUEST_BOUND_NOT_PROVIDER_USED"
            ? "规则未引用 Provider 证据"
            : `实际采用 ${
                trace?.evidence_refs_used.length ??
                comparison.evidence_refs_used.length
              }`}
        </span>
        <span>
          {trace?.candidate_coverage_complete
            ? "候选覆盖完整"
            : "候选覆盖未获 server 验证"}
        </span>
        <span>
          {trace?.selected_evidence_bound
            ? trace.selected_evidence_use_semantics ===
              "REQUEST_BOUND_RULE_NOT_PROVIDER_CITED"
              ? "所选证据已绑定 · 规则未引用"
              : "所选证据已绑定并由 Provider 引用"
            : "所选证据未获 server 验证"}
        </span>
        <span>{readingBound ? "Reading 已绑定" : "Reading 未绑定"}</span>
      </div>

      {trace && (
        <div className="mechanism-decision-input-scope">
          <span>
            <b>本次纳入</b>
            {trace.admitted_input_scopes
              .map((scope) => ADMITTED_SCOPE_LABELS[scope])
              .join("、")}
          </span>
          <span>
            <b>本次未绑定</b>
            {trace.unbound_input_scopes
              .map((scope) => INPUT_SCOPE_LABELS[scope])
              .join("、")}
          </span>
          <small>
            VERIFIED 只确认 Decision 身份、候选与证据引用覆盖完整，
            不确认专业正确、强弱、作用或结果。
          </small>
          <small>
            {trace.provider_confidence_semantics ===
            "NOT_RECORDED_RULE_ENGINE_ROUTE"
              ? "规则引擎路线没有调用 Provider，也没有记录 Provider confidence。"
              : "Provider confidence 仅是未校准的原始记录，不作为产品判断权威；页面不展示其数值。"}
          </small>
        </div>
      )}

      <details className="mechanism-decision-identity">
        <summary>查看 immutable Decision 凭据</summary>
        <dl>
          <div>
            <dt>Decision ref</dt>
            <dd>
              <code>{decisionRef}</code>
            </dd>
          </div>
          <div>
            <dt>Decision hash</dt>
            <dd>
              <code>{decisionHash}</code>
            </dd>
          </div>
          <div>
            <dt>Reading ref</dt>
            <dd>
              <code>{reading.reading_ref}</code>
            </dd>
          </div>
          {trace && (
            <>
              <IdentityRow label="Kernel" value={trace.kernel_version} />
              <IdentityRow label="Request" value={trace.request_id} />
              <IdentityRow label="Subject" value={trace.subject_ref} />
              <IdentityRow label="Route reason" value={trace.route_reason} />
              <IdentityRow
                label="Gate receipt"
                value={trace.gate_receipt_ref ?? trace.gate_disposition}
              />
              <IdentityRow label="Gate reason" value={trace.gate_reason} />
              <IdentityRow label="Proposal" value={trace.proposal_ref ?? "NOT_REQUIRED"} />
              <IdentityRow
                label="Provider"
                value={trace.provider_id ?? "RULE_ENGINE"}
              />
              <IdentityRow label="Model" value={trace.model_ref ?? "NOT_USED"} />
              <IdentityRow label="Prompt" value={trace.prompt_ref ?? "NOT_USED"} />
              <IdentityRow
                label="Counter refs"
                value={
                  ruleEngineRoute
                    ? "0 · 规则引擎路线未调用 Provider"
                    : `${trace.provider_counter_evidence_refs.length} · 仅绑定引用，不是专业反证`
                }
              />
            </>
          )}
        </dl>
      </details>

      <p className="mechanism-decision-boundary">
        {trace?.decision_record_allowed
          ? ruleEngineRoute
            ? "规则 Decision 已记录（无需 Gate）"
            : "Reasoner Decision 已通过 Gate 准入"
          : "Decision 记录状态未知"}
        {" · "}
        {trace?.professional_selection_qualified === false
          ? "专业选择未合格"
          : "专业选择状态未知"}
        {" · "}
        {trace?.professional_verdict_allowed === false
          ? "专业裁决未授权"
          : "专业裁决状态未知"}
        {" · "}
        {trace?.probability_claim_allowed === false
          ? "概率主张未授权"
          : "概率权限未知"}
        {" · "}
        {trace?.canonical_domain_write_allowed === false
          ? "canonical 命理回写禁止"
          : "canonical 回写状态未知"}
        {" · "}
        当前 Reading 只读
      </p>
    </section>
  );
}

function IdentityRow({
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
