import type {
  MingliSyntheticExperimentCatalog,
  MingliSyntheticExperimentCatalogEntry,
  MingliSyntheticVariant,
} from "../mingliSyntheticLabTypes";
import {
  formatSyntheticRunLabel,
} from "../mingliSyntheticSuiteSelection";
import type {
  MingliSyntheticSuiteRunItem,
  MingliSyntheticSuiteRunSelection,
} from "../mingliSyntheticSuiteTypes";

export function MingliSyntheticExperimentToolbar({
  boundSuiteItem,
  catalog,
  displayedVariant,
  experiment,
  hasSealedRun,
  onSelectExperiment,
  onSelectRun,
  onSelectVariant,
  selectedRunRef,
  suiteSelection,
}: {
  boundSuiteItem: MingliSyntheticSuiteRunItem | null;
  catalog: MingliSyntheticExperimentCatalog | null;
  displayedVariant: MingliSyntheticVariant;
  experiment: MingliSyntheticExperimentCatalogEntry | null;
  hasSealedRun: boolean;
  onSelectExperiment: (experimentRef: string) => void;
  onSelectRun: (runRef: string) => void;
  onSelectVariant: (variant: MingliSyntheticVariant) => void;
  selectedRunRef: string | null;
  suiteSelection: MingliSyntheticSuiteRunSelection | null;
}) {
  return (
    <div className="mingli-scene-toolbar" aria-label="选择合成命盘实验成员">
      <label className="mingli-synthetic-selector">
        <small>研究课题</small>
        <select
          aria-label="选择合成实验"
          disabled={!catalog}
          onChange={(event) => onSelectExperiment(event.target.value)}
          value={experiment?.experiment_ref ?? ""}
        >
          {!experiment && <option value="">未识别的研究课题</option>}
          {catalog?.experiments.map((item, index) => (
            <option key={item.experiment_ref} value={item.experiment_ref}>
              {index + 1} · {item.title}
            </option>
          ))}
        </select>
      </label>
      {suiteSelection && boundSuiteItem ? (
        <div
          className="mingli-synthetic-seal"
          aria-label="本轮批次锁定"
          title={suiteSelection.run.suite_run_ref}
        >
          <small>本轮批次锁定</small>
          <strong>训练结果已锁定</strong>
        </div>
      ) : (
        <label className="mingli-synthetic-selector mingli-synthetic-run-selector">
          <small>封存复盘</small>
          <select
            aria-label="选择封存运行"
            disabled={!experiment || experiment.runs.length === 0}
            onChange={(event) => onSelectRun(event.target.value)}
            value={selectedRunRef ?? ""}
          >
            {experiment?.runs.length ? experiment.runs.map((run) => (
              <option key={run.run_ref} value={run.run_ref}>
                {formatSyntheticRunLabel(
                  run.created_at,
                  run.model_independence,
                  run.review_contract_status,
                )}
              </option>
            )) : <option value="">尚未生成</option>}
          </select>
        </label>
      )}
      <div className="mingli-stage-mode" role="group" aria-label="选择 A 或 B 命盘">
        {(["A", "B"] as const).map((variant) => (
          <button
            aria-pressed={displayedVariant === variant}
            disabled={!hasSealedRun}
            key={variant}
            onClick={() => onSelectVariant(variant)}
            type="button"
          >
            {variant} · {experiment?.changed_input[variant] ?? "--:--"}
          </button>
        ))}
      </div>
      <span className="mingli-synthetic-read-only">只读结果 · 页面不会调用模型</span>
    </div>
  );
}
