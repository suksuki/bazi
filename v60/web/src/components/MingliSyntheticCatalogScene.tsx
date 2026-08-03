import { useEffect, useMemo, useState, type CSSProperties } from "react";
import type { RuntimeMediaManifest } from "../api";
import { resolveHomeWorldLight } from "../homeWorldLight";
import type { MingliSyntheticLabRoute } from "../mingliSyntheticLabNavigation";
import type { MingliSyntheticExperimentCatalogEntry } from "../mingliSyntheticLabTypes";
import {
  projectMingliResearchStatus,
  routeToSyntheticExperiment,
  syntheticFamilyLabel,
  syntheticOutcomeLabel,
} from "../mingliResearchProjection";
import { latestSyntheticSuiteRunSelection } from "../mingliSyntheticSuiteSelection";
import { useMingliResearchCatalog } from "../useMingliResearchCatalog";
import { MingliLabRealmHeader } from "./MingliLabRealmHeader";
import { TransparentCharacterMedia } from "./TransparentCharacterMedia";

function ExperimentThread({
  active,
  experiment,
  onSelect,
}: {
  active: boolean;
  experiment: MingliSyntheticExperimentCatalogEntry;
  onSelect: () => void;
}) {
  return (
    <button
      aria-pressed={active}
      className="mingli-synthetic-thread"
      data-outcome={experiment.latest_outcome ?? "NOT_RUN"}
      onClick={onSelect}
      type="button"
    >
      <i aria-hidden="true" />
      <span>
        <small>{syntheticFamilyLabel(experiment.family)}</small>
        <strong>{experiment.title}</strong>
        <em>{experiment.question}</em>
        <b>{syntheticOutcomeLabel(experiment.latest_outcome)}</b>
      </span>
    </button>
  );
}

export function MingliSyntheticCatalogScene({
  media,
  onBack,
  onOpenExperiment,
}: {
  media: RuntimeMediaManifest;
  onBack: () => void;
  onOpenExperiment: (route: MingliSyntheticLabRoute) => void;
}) {
  const worldLight = resolveHomeWorldLight();
  const catalog = useMingliResearchCatalog();
  const [selectedRef, setSelectedRef] = useState<string | null>(null);
  const status = useMemo(
    () => catalog.experiments && catalog.suites
      ? projectMingliResearchStatus(catalog.experiments, catalog.suites)
      : null,
    [catalog.experiments, catalog.suites],
  );
  const latestSuite = useMemo(
    () => catalog.suites
      ? latestSyntheticSuiteRunSelection(catalog.suites)
      : null,
    [catalog.suites],
  );
  const selected = catalog.experiments?.experiments.find(
    (experiment) => experiment.experiment_ref === selectedRef,
  ) ?? catalog.experiments?.experiments[0] ?? null;

  useEffect(() => {
    if (!selectedRef && catalog.experiments?.experiments[0]) {
      setSelectedRef(catalog.experiments.experiments[0].experiment_ref);
    }
  }, [catalog.experiments, selectedRef]);

  const background = worldLight === "day"
    ? media.assets.mingli_lab_day_background
    : media.assets.mingli_lab_night_background;
  const cue = media.cues.dodo_idle;
  const style = {
    "--mingli-lab-watercourt": `url("${background.url}")`,
  } as CSSProperties;
  const openSelected = () => {
    if (!selected || !catalog.suites || !selected.latest_run_ref) return;
    onOpenExperiment(routeToSyntheticExperiment(selected, catalog.suites));
  };

  return (
    <div
      className="mingli-synthetic-catalog-realm"
      data-world-light={worldLight}
      style={style}
    >
      <MingliLabRealmHeader
        backLabel="回到阿布 LAB"
        eyebrow="SYNTHETIC BAZI · SEALED REVIEW"
        onBack={onBack}
        status={status
          ? `${status.latestSuiteSealed}/${status.latestSuiteTotal} 封存 · ${status.reviewRequiredCount} 项待复核`
          : "正在读取封存现场"}
        title="八字合成验证"
      />
      <main className="mingli-synthetic-catalog" aria-labelledby="synthetic-catalog-title">
        <span className="mingli-lab-mist is-far" aria-hidden="true" />
        <span className="mingli-lab-mist is-near" aria-hidden="true" />
        <header className="mingli-synthetic-catalog-heading">
          <small>命局流 · 已揭晓封存复盘</small>
          <h1 id="synthetic-catalog-title">命局流正在经过这里</h1>
          <p>多数判断安静地通过；只有不能独立站住的部分，才浮到专业复核门前。</p>
        </header>

        {catalog.loading && !catalog.experiments ? (
          <section className="mingli-synthetic-catalog-state" role="status">
            正在从真实运行目录取回研究课题……
          </section>
        ) : !catalog.experiments || !catalog.suites ? (
          <section className="mingli-synthetic-catalog-state" role="alert">
            <strong>研究目录暂时没有展开。</strong>
            <span>研究权限尚未开放或目录暂不可用；不会用原型常量或其他命盘冒充真实复盘。</span>
            <button onClick={catalog.retry} type="button">重新读取</button>
          </section>
        ) : (
          <div className="mingli-synthetic-catalog-grid">
            <aside className="mingli-synthetic-thread-rail" aria-label="真实研究课题">
              <header><small>研究课题架</small><strong>{status?.experimentCount} 个真实课题</strong></header>
              {catalog.experiments.experiments.map((experiment) => (
                <ExperimentThread
                  active={experiment.experiment_ref === selected?.experiment_ref}
                  experiment={experiment}
                  key={experiment.experiment_ref}
                  onSelect={() => setSelectedRef(experiment.experiment_ref)}
                />
              ))}
            </aside>

            <section className="mingli-synthetic-current" aria-live="polite">
              <div className="mingli-synthetic-flow" aria-label="自动验证流程">
                {['合法命局族', '批量碰撞', '异常聚类', '专业复核'].map((label, index) => (
                  <span key={label}><i>{index + 1}</i><b>{label}</b></span>
                ))}
              </div>
              {selected && (
                <article className="mingli-synthetic-selected-study">
                  <small>{syntheticFamilyLabel(selected.family)}</small>
                  <h2>{selected.title}</h2>
                  <p>{selected.question}</p>
                  <dl>
                    <div><dt>A 组</dt><dd>{selected.changed_input.A}</dd></div>
                    <div><dt>B 组</dt><dd>{selected.changed_input.B}</dd></div>
                    <div><dt>封存运行</dt><dd>{selected.runs.length} 次</dd></div>
                    <div><dt>最新结果</dt><dd>{syntheticOutcomeLabel(selected.latest_outcome)}</dd></div>
                  </dl>
                  <blockquote>{selected.inference_limit}</blockquote>
                  <button
                    disabled={!selected.latest_run_ref}
                    onClick={openSelected}
                    type="button"
                  >
                    {selected.latest_run_ref ? "查看真实封存现场" : "等待首个封存现场"}
                    <span aria-hidden="true">→</span>
                  </button>
                  {!selected.latest_run_ref && (
                    <em>当前课题没有 Snapshot，不借用其他命盘冒充复盘。</em>
                  )}
                </article>
              )}
            </section>

            <aside className="mingli-synthetic-review-gate" aria-label="真实研究状态">
              <header><small>当前训练</small><strong>{latestSuite?.suite.title ?? "尚无 Suite"}</strong></header>
              <div className="mingli-synthetic-real-counts">
                <span><b>{status?.latestSuiteSealed ?? 0}</b><small>本轮封存</small></span>
                <span><b>{status?.reviewRequiredCount ?? 0}</b><small>待复核</small></span>
                <span><b>{status?.errorClusterCount ?? 0}</b><small>错误簇</small></span>
              </div>
              <section>
                {catalog.suites.modes.map((mode) => (
                  <p data-availability={mode.availability} key={mode.mode}>
                    <strong>{mode.mode}</strong>
                    <span>{mode.availability === "ACTIVE" ? "当前可用" : "Owner Gate 后开放"}</span>
                  </p>
                ))}
              </section>
              <footer>
                页面只读 GET，不在浏览器调用模型；这里是已揭晓复盘，不冒充盲审。
                {catalog.error && (
                  <button onClick={catalog.retry} type="button">
                    上次刷新失败，保留当前现场；重新读取
                  </button>
                )}
              </footer>
            </aside>
          </div>
        )}

        <div className="mingli-synthetic-catalog-guide">
          <p>先看哪里没有独立站住，再进入封存现场。</p>
          <TransparentCharacterMedia
            active
            alt="多多，合成验证研究向导"
            className="mingli-synthetic-catalog-character"
            cueRef={cue.cue_ref}
            poster={cue.deliveries.REDUCED_MOTION_POSTER}
            video={cue.deliveries.VP9_ALPHA_WEBM}
            webp={cue.deliveries.ANIMATED_WEBP}
          />
        </div>
      </main>
    </div>
  );
}
