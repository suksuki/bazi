import type {
  MingliSyntheticExperimentCheck,
  MingliSyntheticExperimentSnapshot,
} from "../mingliSyntheticLabTypes";

const GROUPS = [
  ["EXPERIMENT_VALIDITY", "实验是否有效"],
  ["MUST_HOLD", "不该变的是否保持"],
  ["EXPECTED_CHANGE", "该变的判断是否改变"],
] as const;

export function MingliSyntheticExperimentInspector({
  snapshot,
}: {
  snapshot: MingliSyntheticExperimentSnapshot;
}) {
  const { definition, evaluation } = snapshot;
  return (
    <aside
      className="mingli-synthetic-inspector"
      aria-label="合成命盘成对验证结果"
    >
      <header>
        <p>Lab · Controlled Pair</p>
        <h2>{definition.title}</h2>
        <span>{definition.question}</span>
      </header>

      <section className="mingli-synthetic-pair" aria-label="A B 命盘输入对照">
        {(["A", "B"] as const).map((variant) => (
          <article
            data-active={snapshot.selected_variant === variant}
            key={variant}
          >
            <small>{variant} · {definition.changed_input[variant]}</small>
            <strong>{definition.full_pillar_delta[variant].join(" · ")}</strong>
          </article>
        ))}
      </section>

      <section className="mingli-synthetic-inference-limit">
        <small>这组实验能证明什么</small>
        <p>{definition.inference_limit}</p>
        <ul>
          {definition.known_collateral_deltas.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <TrainingTracks snapshot={snapshot} />

      <section
        className="mingli-synthetic-outcome"
        data-outcome={evaluation.outcome}
      >
        <small>封存结果 · {outcomeLabel(evaluation.outcome)}</small>
        <strong>{evaluation.summary}</strong>
        <span>
          保持项通过 {evaluation.hold_pass_count} 项 · 响应项通过 {evaluation.changed_pass_count} 项
        </span>
      </section>

      <ModelNormalizationTrace snapshot={snapshot} />

      {GROUPS.map(([group, label]) => {
        const checks = evaluation.checks.filter((item) => item.group === group);
        return (
          <section className="mingli-synthetic-checks" key={group}>
            <h3>{label}</h3>
            {checks.map((check) => <ExperimentCheck check={check} key={check.check_ref} />)}
          </section>
        );
      })}

      <footer>
        <strong>开发证据，不等于方法取得资格</strong>
        <span>Gold 未进入 Agent 输入；浏览器只读取已封存结果，不会发起模型调用。</span>
      </footer>
    </aside>
  );
}

function TrainingTracks({ snapshot }: { snapshot: MingliSyntheticExperimentSnapshot }) {
  const assessment = snapshot.training_assessment;
  const tracks = [
    {
      label: "实验有效性",
      status: assessment.experiment_validity,
      value: assessment.experiment_validity === "VALID" ? "控制成立" : "不可评价",
    },
    {
      label: "模型独立能力",
      status: assessment.model_independence,
      value: {
        PASS: "独立通过",
        FAIL: "尚未通过",
        NOT_EVALUABLE: "不可评价",
      }[assessment.model_independence],
    },
    {
      label: "产品结果",
      status: assessment.product_result,
      value: {
        SAFE_MODEL_DIRECT: "模型直出安全",
        SAFE_WITH_REPAIR: "规则校正后安全",
        WITHHELD: "暂不采用",
        NOT_EVALUABLE: "不可评价",
      }[assessment.product_result],
    },
  ];
  return (
    <section className="mingli-synthetic-training-assessment">
      <header>
        <small>三条结果轨道</small>
        <strong>{assessment.summary}</strong>
      </header>
      <div>
        {tracks.map((item) => (
          <article data-status={item.status} key={item.label}>
            <small>{item.label}</small>
            <strong>{item.value}</strong>
          </article>
        ))}
      </div>
      <span>
        原断证据：{assessment.trace_coverage === "FIELD_LEVEL"
          ? "A／B 均有字段级凭证"
          : assessment.trace_coverage === "PARTIAL"
            ? "仅部分成员有字段级凭证"
            : "历史运行只有修正码"}
      </span>
    </section>
  );
}

function ModelNormalizationTrace({
  snapshot,
}: {
  snapshot: MingliSyntheticExperimentSnapshot;
}) {
  const trace = snapshot.model_trace;
  return (
    <details className="mingli-synthetic-model-trace">
      <summary>
        <span>模型原断 → 系统校正</span>
        <strong>
          {trace.availability === "FIELD_LEVEL"
            ? `关键字段 ${trace.key_deltas.length} 项 / 总变化 ${trace.change_count ?? 0}`
            : "历史原断未封存"}
        </strong>
      </summary>
      {trace.availability === "LEGACY_NOT_CAPTURED" ? (
        <p>{trace.limitation}</p>
      ) : (
        <>
          <div className="mingli-synthetic-trace-stages">
            {trace.stage_counts.map((item) => (
              <span key={item.stage}>
                {stageLabel(item.stage)} · {item.change_count}
              </span>
            ))}
          </div>
          {trace.key_deltas.length ? (
            <div className="mingli-synthetic-trace-deltas">
              {trace.key_deltas.map((item) => (
                <article key={`${item.stage}:${item.path}`}>
                  <small>{pathLabel(item.path)} · {stageLabel(item.stage)}</small>
                  <dl>
                    <div>
                      <dt>模型原断</dt>
                      <dd>{item.before_present ? formatValue(item.before) : "未提供"}</dd>
                    </div>
                    <div>
                      <dt>系统校正</dt>
                      <dd>{item.after_present ? formatValue(item.after) : "已移除"}</dd>
                    </div>
                  </dl>
                </article>
              ))}
            </div>
          ) : (
            <p>本变体没有需要展开的专业字段校正。</p>
          )}
          <p>{trace.limitation}</p>
        </>
      )}
    </details>
  );
}

function ExperimentCheck({ check }: { check: MingliSyntheticExperimentCheck }) {
  return (
    <article data-status={check.status}>
      <div>
        <span aria-hidden="true">{check.status === "PASS" ? "✓" : "×"}</span>
        <strong>{check.statement}</strong>
      </div>
      <dl>
        <div><dt>A</dt><dd>{formatValue(check.A)}</dd></div>
        <div><dt>B</dt><dd>{formatValue(check.B)}</dd></div>
      </dl>
    </article>
  );
}

function outcomeLabel(outcome: MingliSyntheticExperimentSnapshot["evaluation"]["outcome"]) {
  return {
    PASS: "通过",
    PRODUCT_SAFE_MODEL_FAIL: "产品收敛，模型未独立通过",
    MODEL_FAIL: "模型未通过",
    INVALID_EXPERIMENT: "实验无效",
  }[outcome];
}

function stageLabel(stage: string): string {
  return {
    EVIDENCE_ID_NORMALIZATION: "证据编号整理",
    PACKET_FACT_BINDING: "命盘事实绑定",
    PROFESSIONAL_ADJUDICATION: "专业规则裁决",
    PROSE_EVIDENCE_REPAIR: "正文证据清理",
    OUTPUT_FORM_REPAIR: "结构整理",
    LOCAL_FIELD_REPAIR: "字段安全收敛",
  }[stage] ?? stage;
}

function pathLabel(path: string): string {
  const labels: Array<[string, string]> = [
    ["/regime_decision/effective_root_status", "有效根状态"],
    ["/regime_decision/effective_root_coordinates", "有效根坐标"],
    ["/regime_decision/classification", "日主判型"],
    ["/day_master_state", "日主工作状态"],
    ["/day_master_rationale", "日主判断说明"],
    ["/support_selection", "生扶事实选择"],
    ["/hypotheses", "竞争解释"],
    ["/hypothesis_decision", "主次解释裁决"],
    ["/work_path", "做功路径"],
  ];
  return labels.find(([prefix]) => path.startsWith(prefix))?.[1] ?? path;
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string" || typeof value === "number") return String(value);
  if (typeof value === "boolean") return value ? "是" : "否";
  if (Array.isArray(value)) return value.length ? value.map(formatValue).join(" · ") : "无";
  if (typeof value === "object") {
    return Object.entries(value)
      .map(([key, item]) => `${key}: ${formatValue(item)}`)
      .join("；");
  }
  return String(value);
}
