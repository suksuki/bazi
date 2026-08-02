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
