import type { MingliSyntheticExperimentCatalog } from "../mingliSyntheticLabTypes";
import type { MingliSyntheticSuiteRunComparison } from "../mingliSyntheticSuiteSelection";
import type { MingliSyntheticSuiteRunSelection } from "../mingliSyntheticSuiteTypes";
import { MingliSyntheticSuiteTrainingComparison } from "./MingliSyntheticSuiteComparison";

export function MingliSyntheticSuiteSummary({
  comparison,
  currentExperimentRef,
  experiments,
  onSelect,
  onSelectRun,
  selection,
}: {
  comparison: MingliSyntheticSuiteRunComparison | null;
  currentExperimentRef: string | null;
  experiments: MingliSyntheticExperimentCatalog;
  onSelect: (experimentRef: string, runRef: string) => void;
  onSelectRun: (selection: MingliSyntheticSuiteRunSelection) => void;
  selection: MingliSyntheticSuiteRunSelection;
}) {
  const { review, run, suite } = selection;
  const independentCount = review.items.filter(
    (item) => item.model_independence === "PASS",
  ).length;
  const suiteIndependent = review.counts.sealed === review.counts.experiments
    && review.counts.runner_errors === 0
    && independentCount === review.counts.experiments
    && review.items.every((item) => item.review_contract_status === "CURRENT")
    && review.error_clusters.length === 0;
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
          {independentCount}/{review.counts.experiments} 模型独立 · {review.counts.review_required} 需校正
        </span>
      </header>
      <div className="mingli-synthetic-suite-verdict" data-pass={suiteIndependent}>
        <strong>{suiteIndependent ? "本轮模型独立通过" : "本轮尚未模型独立"}</strong>
        <span>
          {suiteIndependent
            ? "全部课题在当前评尺下无服务端专业修正。"
            : "封存结果可用于继续训练；修正后的产品输出仍与模型原生能力分开计算。"}
        </span>
      </div>
      <MingliSyntheticSuiteTrainingComparison
        comparison={comparison}
        currentCandidate={run.candidate_identity}
        onSelectRun={onSelectRun}
      />
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
