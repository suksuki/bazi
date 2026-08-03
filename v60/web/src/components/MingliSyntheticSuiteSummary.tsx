import type { MingliSyntheticExperimentCatalog } from "../mingliSyntheticLabTypes";
import type { MingliSyntheticSuiteRunSelection } from "../mingliSyntheticSuiteTypes";

export function MingliSyntheticSuiteSummary({
  currentExperimentRef,
  experiments,
  onSelect,
  selection,
}: {
  currentExperimentRef: string | null;
  experiments: MingliSyntheticExperimentCatalog;
  onSelect: (experimentRef: string, runRef: string) => void;
  selection: MingliSyntheticSuiteRunSelection;
}) {
  const { review, run, suite } = selection;
  const titles = new Map(
    experiments.experiments.map((item) => [item.experiment_ref, item.title]),
  );
  return (
    <section className="mingli-synthetic-suite-summary" aria-label="本轮合成训练">
      <header>
        <div>
          <small>本轮训练 · {run.suite_mode}</small>
          <strong>{suite.title}</strong>
        </div>
        <span data-status={run.status}>
          {review.counts.sealed} 封存 · {review.counts.runner_errors} 执行失败 · {review.counts.review_required} 需复核
        </span>
      </header>
      <div className="mingli-synthetic-suite-topics" aria-label="训练课题">
        {review.items.map((item) => {
          const active = item.experiment_ref === currentExperimentRef;
          return (
            <button
              aria-current={active ? "true" : undefined}
              data-status={item.execution_status}
              disabled={item.execution_status !== "SEALED" || !item.experiment_run_ref}
              key={item.experiment_ref}
              onClick={() => item.experiment_run_ref && onSelect(
                item.experiment_ref,
                item.experiment_run_ref,
              )}
              type="button"
            >
              <span aria-hidden="true">
                {item.execution_status === "ERROR" ? "×" : item.review_required ? "!" : "✓"}
              </span>
              <span>{titles.get(item.experiment_ref) ?? "未识别课题"}</span>
            </button>
          );
        })}
      </div>
      {review.error_clusters.length > 0 && (
        <div className="mingli-synthetic-suite-clusters" aria-label="仍卡在哪里">
          <small>仍卡在哪里</small>
          <div>
            {review.error_clusters.map((cluster) => (
              <span key={cluster.key} title={cluster.key}>
                {cluster.label} × {cluster.occurrence_count}
              </span>
            ))}
          </div>
        </div>
      )}
      <p>{suite.inference_limit}</p>
    </section>
  );
}
