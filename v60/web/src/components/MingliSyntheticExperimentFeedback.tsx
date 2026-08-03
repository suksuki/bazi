import type { ReactNode } from "react";

export function MingliSyntheticSceneHeader({
  hasSnapshot,
  onBackToCurrent,
  onExit,
  onOpenReading,
  title,
  variant,
}: {
  hasSnapshot: boolean;
  onBackToCurrent: () => void;
  onExit: () => void;
  onOpenReading: () => void;
  title: string;
  variant: "A" | "B";
}) {
  return (
    <header className="mingli-scene-host-header">
      <button className="mingli-scene-exit" onClick={onExit} type="button">
        <span aria-hidden="true">←</span>
        回到生命树
      </button>
      <div className="mingli-scene-title">
        <p>阿布 Lab · 合成验证</p>
        <h1>{title}</h1>
        <span>{hasSnapshot ? `${variant} 组 · 研究合成命盘` : "离线运行 · 浏览器只读"}</span>
      </div>
      <div className="mingli-scene-surfaces" role="group" aria-label="命理阅读与 Lab">
        <button aria-pressed="false" onClick={onOpenReading} type="button">命理阅读</button>
        <button aria-pressed="false" onClick={onBackToCurrent} type="button">当前命盘</button>
        <button aria-pressed="true" type="button">合成验证</button>
      </div>
    </header>
  );
}

export function MingliSyntheticSwitchingFeedback({
  activeError,
  displayedVariant,
  loading,
  onRestoreLatest,
  onRetry,
  requestedVariant,
}: {
  activeError: string | null;
  displayedVariant: "A" | "B";
  loading: boolean;
  onRestoreLatest: () => void;
  onRetry: () => void;
  requestedVariant: "A" | "B";
}) {
  return (
    <>
      {loading && (
        <div className="mingli-synthetic-switching" role="status">
          正在读取 {requestedVariant} 组；当前仍显示 {displayedVariant} 组
        </div>
      )}
      {activeError && (
        <div className="mingli-synthetic-load-error" role="alert">
          <strong>{requestedVariant} 组读取失败，当前仍显示 {displayedVariant} 组。</strong>
          <span>没有补跑模型，也没有把旧舞台冒充成新变体。</span>
          <div>
            <button onClick={onRetry} type="button">重试 {requestedVariant} 组</button>
            <button onClick={onRestoreLatest} type="button">改读最新封存结果</button>
          </div>
        </div>
      )}
    </>
  );
}

export function MingliSyntheticEmptyState({
  activeError,
  canRestoreLatest,
  catalogError,
  loading,
  onRestoreLatest,
  onRetry,
  suiteSummary,
}: {
  activeError: string | null;
  canRestoreLatest: boolean;
  catalogError: string | null;
  loading: boolean;
  onRestoreLatest: () => void;
  onRetry: () => void;
  suiteSummary?: ReactNode;
}) {
  return (
    <div className="mingli-synthetic-empty" role="status">
      {suiteSummary}
      {loading ? (
        <p>正在读取离线封存的 A／B 实验……</p>
      ) : catalogError || activeError ? (
        <>
          <p>
            {activeError
              ? "当前链接的封存结果不可用；不会拿别的命盘顶替。"
              : catalogError?.startsWith("mingli_synthetic_suite")
                ? "当前批次链接与封存课题不一致；不会拿其他运行顶替。"
                : "封存实验暂时无法读取；不会在浏览器补跑模型。"}
          </p>
          <div>
            <button onClick={onRetry} type="button">重新读取</button>
            {activeError && canRestoreLatest && (
              <button onClick={onRestoreLatest} type="button">
                改读最新封存结果
              </button>
            )}
          </div>
        </>
      ) : (
        <p>尚无封存实验结果，请通过离线 Lab runner 生成。</p>
      )}
    </div>
  );
}

export function MingliSyntheticStageBoundary({
  inferenceLimit,
}: {
  inferenceLimit: string;
}) {
  return (
    <footer className="mingli-stage-boundary">
      <span>Owner 命盘只做回归；合成命盘负责控制变量、发现漂移和推动方法升级。</span>
      <small>{inferenceLimit}</small>
    </footer>
  );
}
