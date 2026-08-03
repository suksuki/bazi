import type { MingliSyntheticLabRoute } from "../mingliSyntheticLabNavigation";
import {
  findSyntheticSuiteRun,
  firstReviewRequiredSyntheticSuiteRoute,
  firstSyntheticSuiteRoute,
} from "../mingliSyntheticSuiteSelection";
import type { MingliSyntheticSuiteCatalog } from "../mingliSyntheticSuiteTypes";
import type {
  MingliSyntheticTrainingRequest,
  MingliSyntheticTrainingReviewDisposition,
} from "../mingliSyntheticTrainingTypes";
import { useMingliSyntheticTraining } from "../useMingliSyntheticTraining";

const ACTIVE = new Set(["QUEUED", "RUNNING", "SEALING"]);

export function MingliSyntheticTrainingConsole({
  catalog,
  onCatalogRefresh,
  onOpenExperiment,
}: {
  catalog: MingliSyntheticSuiteCatalog;
  onCatalogRefresh: () => void;
  onOpenExperiment: (route: MingliSyntheticLabRoute) => void;
}) {
  const training = useMingliSyntheticTraining(onCatalogRefresh);
  const recommended = training.status?.suites.find(
    (suite) => suite.suite_ref === training.status?.recommended_suite_ref,
  ) ?? null;
  const activeRequest = training.runRequest && ACTIVE.has(training.runRequest.status)
    ? training.runRequest
    : null;
  const referencedSuite = training.runRequest
    ? training.status?.suites.find((item) => item.suite_ref === training.runRequest?.suite_ref) ?? null
    : null;
  const exactRequestSuite = training.runRequest
    && referencedSuite
    && training.runRequest.execution_fingerprint === referencedSuite.execution_fingerprint
    ? referencedSuite
    : null;
  const suite = activeRequest ? referencedSuite ?? recommended : exactRequestSuite ?? recommended;
  const terminalRequest = !activeRequest
    && training.runRequest
    && exactRequestSuite
    ? training.runRequest
    : null;
  const relevantRequest = activeRequest ?? terminalRequest;
  const resultRef = relevantRequest?.suite_run_ref ?? suite?.sealed_suite_run_ref ?? null;
  const selection = resultRef ? findSyntheticSuiteRun(catalog, resultRef) : null;
  const reviewRoute = selection ? firstReviewRequiredSyntheticSuiteRoute(selection) : null;
  const route = reviewRoute ?? (selection ? firstSyntheticSuiteRoute(selection) : null);
  const candidate = training.status?.candidate_identity;

  const openResult = () => {
    if (route) onOpenExperiment(route);
  };

  return (
    <section className="mingli-training-console" aria-label="创建合成命局训练">
      <header>
        <span><i aria-hidden="true" />服务端训练任务</span>
        <strong>{suite?.title ?? "正在核对当前候选"}</strong>
      </header>

      {candidate && (
        <div className="mingli-training-candidate">
          <span><small>当前模型</small><b>{candidate.model_ref}</b></span>
          <span><small>方法版本</small><b>{tail(candidate.agent_profile_ref)}</b></span>
          <span><small>提示版本</small><b>{tail(candidate.prompt_ref)}</b></span>
        </div>
      )}

      {training.loading && !training.status ? (
        <p className="mingli-training-state" role="status">正在锁定模型、方法与实验指纹……</p>
      ) : training.error && !training.status ? (
        <div className="mingli-training-state is-error" role="alert">
          <span>训练入口暂时不可用；既有封存目录仍然保留。</span>
          <button onClick={training.refresh} type="button">重新核对</button>
        </div>
      ) : !suite ? (
        <p className="mingli-training-state">当前没有已准入的 DEV Suite。</p>
      ) : relevantRequest && ACTIVE.has(relevantRequest.status) ? (
        <TrainingProgress request={relevantRequest} />
      ) : relevantRequest?.status === "FAILED" ? (
        <div className="mingli-training-state is-error" role="alert">
          <strong>本次任务没有形成可信封存。</strong>
          <span>{trainingErrorLabel(relevantRequest.error_code)}</span>
          {suite.candidate_state === "READY_FOR_DEV_RUN" && (
            <button
              disabled={training.starting}
              onClick={() => void training.start(suite)}
              type="button"
            >
              重新创建任务
            </button>
          )}
        </div>
      ) : relevantRequest?.status === "SUCCEEDED" ? (
        <TrainingResult
          actionLabel={reviewRoute ? "进入首个待复核现场" : "查看已封存现场"}
          clusters={selection?.review.error_clusters ?? []}
          disposition={relevantRequest.review_disposition}
          onOpen={openResult}
          onNext={
            recommended
              && recommended.suite_ref !== suite.suite_ref
              && recommended.candidate_state === "READY_FOR_DEV_RUN"
              ? () => void training.start(recommended)
              : null
          }
          onRetry={
            relevantRequest.review_disposition === "EXECUTION_REPAIR_REQUIRED"
              && suite.candidate_state === "READY_FOR_DEV_RUN"
              ? () => void training.start(suite)
              : null
          }
          resultReady={Boolean(route)}
          retrying={training.starting}
        />
      ) : suite.candidate_state === "READY_FOR_DEV_RUN" ? (
        <div className="mingli-training-ready">
          <p>{suite.question}</p>
          <div>
            <span><b>{suite.experiment_count}</b><small>陌生课题</small></span>
            <span><b>DEV</b><small>只进研发复核</small></span>
          </div>
          <button
            disabled={training.starting}
            onClick={() => void training.start(suite)}
            type="button"
          >
            {training.starting ? "正在创建……" : "开始验证当前方法"}
            <span aria-hidden="true">→</span>
          </button>
        </div>
      ) : (
        <TrainingResult
          actionLabel={reviewRoute ? "进入首个待复核现场" : "查看已封存现场"}
          clusters={selection?.review.error_clusters ?? []}
          disposition={relevantRequest?.review_disposition ?? dispositionFromSelection(selection)}
          onOpen={openResult}
          onNext={null}
          onRetry={null}
          resultReady={Boolean(route)}
          retrying={false}
        />
      )}

      {training.error && training.status && (
        <button className="mingli-training-inline-error" onClick={training.refresh} type="button">
          状态刷新失败，保留当前现场；重新读取
        </button>
      )}
      <footer>
        浏览器只创建绑定任务；命盘、模型、Prompt、Gold 与运行身份全部由服务端锁定。
      </footer>
    </section>
  );
}

function TrainingProgress({ request }: { request: MingliSyntheticTrainingRequest }) {
  return (
    <div className="mingli-training-progress" role="status" aria-live="polite">
      <span>{progressLabel(request)}</span>
      <strong>{request.completed_count}/{request.total_count} 个课题完成</strong>
      <div aria-hidden="true">
        {Array.from({ length: request.total_count }, (_, index) => (
          <i data-done={index < request.completed_count} key={index} />
        ))}
      </div>
      <p>离开或刷新不会取消任务；完成前不展示 Gold，也不提前跳入旧结果。</p>
    </div>
  );
}

function TrainingResult({
  actionLabel,
  clusters,
  disposition,
  onNext,
  onOpen,
  onRetry,
  resultReady,
  retrying,
}: {
  actionLabel: string;
  clusters: Array<{ key: string; label: string; occurrence_count: number }>;
  disposition: MingliSyntheticTrainingReviewDisposition | null;
  onNext: (() => void) | null;
  onOpen: () => void;
  onRetry: (() => void) | null;
  resultReady: boolean;
  retrying: boolean;
}) {
  return (
    <div className="mingli-training-result">
      <small>本轮 Suite 结果已经封存</small>
      <strong>{dispositionLabel(disposition)}</strong>
      {clusters.length ? (
        <div>
          {clusters.map((cluster) => (
            <span key={cluster.key}>{cluster.label} × {cluster.occurrence_count}</span>
          ))}
        </div>
      ) : (
        <p>当前评尺下没有形成错误簇；这仍只是 DEV 结果。</p>
      )}
      <button disabled={!resultReady} onClick={onOpen} type="button">
        {resultReady ? actionLabel : "本轮没有可打开的封存现场"}
        <span aria-hidden="true">→</span>
      </button>
      {onRetry && (
        <button disabled={retrying} onClick={onRetry} type="button">
          {retrying ? "正在重新创建……" : "修复后重新验证"}
        </button>
      )}
      {onNext && (
        <button disabled={retrying} onClick={onNext} type="button">
          {retrying ? "正在创建下一组……" : "继续下一组验证"}
        </button>
      )}
    </div>
  );
}

function progressLabel(request: MingliSyntheticTrainingRequest): string {
  if (request.status === "QUEUED") return "任务已入队，等待私有模型";
  if (request.status === "SEALING") return "全部课题完成，正在锁定 Suite";
  if (request.progress_event === "ERROR") return `第 ${request.current_position} 个课题执行受阻`;
  if (request.progress_event === "SEALED") return `第 ${request.current_position} 个课题已封存`;
  return `正在运行第 ${Math.max(1, request.current_position)} 个课题`;
}

function dispositionLabel(
  value: MingliSyntheticTrainingReviewDisposition | null,
): string {
  switch (value) {
    case "MODEL_INDEPENDENT_DEV":
      return "当前方法在本组 DEV 中独立站住";
    case "EXPERIMENT_REVISION_REQUIRED":
      return "实验结构需要先修订";
    case "EXECUTION_REPAIR_REQUIRED":
      return "执行链需要先修复";
    case "CANDIDATE_REVISION_REQUIRED":
      return "错误已归簇，等待方法回炉";
    default:
      return "当前方法已经测过，不重复冒充新训练";
  }
}

function dispositionFromSelection(
  selection: ReturnType<typeof findSyntheticSuiteRun>,
): MingliSyntheticTrainingReviewDisposition | null {
  if (!selection) return null;
  if (selection.review.counts.runner_errors > 0) return "EXECUTION_REPAIR_REQUIRED";
  if (selection.review.items.some((item) => item.outcome === "INVALID_EXPERIMENT")) {
    return "EXPERIMENT_REVISION_REQUIRED";
  }
  if (selection.review.counts.review_required || selection.review.error_clusters.length) {
    return "CANDIDATE_REVISION_REQUIRED";
  }
  return "MODEL_INDEPENDENT_DEV";
}

function trainingErrorLabel(errorCode: string | null): string {
  if (!errorCode) return "服务端没有返回可复核的错误码。";
  if (errorCode.includes("PROVIDER")) return "私有模型暂时不可用，可以稍后重试。";
  return `服务端已封存失败码：${errorCode}`;
}

function tail(value: string): string {
  const segment = value.split(".").at(-1);
  return segment ? `.${segment}` : value;
}
