import { useMemo, type CSSProperties } from "react";
import type { RuntimeMediaManifest } from "../api";
import { resolveHomeWorldLight } from "../homeWorldLight";
import { projectMingliResearchStatus } from "../mingliResearchProjection";
import { useMingliResearchCatalog } from "../useMingliResearchCatalog";
import { TransparentCharacterMedia } from "./TransparentCharacterMedia";
import { MingliLabRealmHeader } from "./MingliLabRealmHeader";

function SixPillarInstrument() {
  return (
    <span className="mingli-lab-six-instrument" aria-hidden="true">
      {Array.from({ length: 6 }, (_, index) => (
        <span className={index < 4 ? "is-natal" : "is-time"} key={index}>
          <i /><i /><b>{index < 4 ? "本命" : "时间"}</b>
        </span>
      ))}
    </span>
  );
}

function SynthesisInstrument({ count }: { count: number | null }) {
  return (
    <span className="mingli-lab-synthesis-instrument" aria-hidden="true">
      <span className="mingli-lab-synthesis-ring">
        {Array.from({ length: 8 }, (_, index) => (
          <i key={index} style={{ "--angle": `${index * 45}deg` } as CSSProperties} />
        ))}
      </span>
      <span className="mingli-lab-synthesis-core">
        <b>{count ?? "·"}</b>
        <small>SEALED</small>
      </span>
    </span>
  );
}

function AbuSaysInstrument() {
  return (
    <span className="mingli-lab-voice-instrument" aria-hidden="true">
      <span>声</span>
      <i>{Array.from({ length: 9 }, (_, index) => <b key={index} />)}</i>
    </span>
  );
}

export function MingliResearchOverview({
  media,
  onExit,
  onOpenNarration,
  onOpenSixPillar,
  onOpenSynthesis,
}: {
  media: RuntimeMediaManifest;
  onExit: () => void;
  onOpenNarration: () => void;
  onOpenSixPillar: () => void;
  onOpenSynthesis: () => void;
}) {
  const worldLight = resolveHomeWorldLight();
  const catalog = useMingliResearchCatalog();
  const status = useMemo(
    () => catalog.experiments && catalog.suites
      ? projectMingliResearchStatus(catalog.experiments, catalog.suites)
      : null,
    [catalog.experiments, catalog.suites],
  );
  const background = worldLight === "day"
    ? media.assets.mingli_lab_day_background
    : media.assets.mingli_lab_night_background;
  const cue = media.cues.dodo_idle;
  const style = {
    "--mingli-lab-watercourt": `url("${background.url}")`,
  } as CSSProperties;

  return (
    <div
      className="mingli-research-realm"
      data-catalog-loading={catalog.loading}
      data-world-light={worldLight}
      style={style}
    >
      <MingliLabRealmHeader
        backLabel="回到生命树"
        eyebrow="ABU LAB · METHOD RESEARCH"
        onBack={onExit}
        status={status
          ? `${status.experimentCount} 个真实课题 · ${status.archivedRunCount} 次封存`
          : catalog.error ? "研究目录尚未开放" : "正在读取真实研究目录"}
        title="阿布 LAB · 研究"
      />
      <main className="mingli-lab-watercourt" aria-labelledby="mingli-lab-title">
        <span className="mingli-lab-mist is-far" aria-hidden="true" />
        <span className="mingli-lab-mist is-near" aria-hidden="true" />
        <header className="mingli-lab-world-heading">
          <small>ABU LAB · METHOD RESEARCH</small>
          <h1 id="mingli-lab-title">把命理变成可以观察、比较和验证的东西。</h1>
          <p>这里研究方法，不存放案例。</p>
        </header>

        <section className="mingli-lab-project-field" aria-label="阿布 Lab 研究入口">
          <button className="mingli-lab-project is-synthesis" onClick={onOpenSynthesis} type="button">
            <SynthesisInstrument count={status?.sealedExperimentCount ?? null} />
            <span className="mingli-lab-project-copy">
              <small>{status
                ? `核心验证引擎 · ${status.experimentCount} 项真实实验已接入`
                : catalog.error
                  ? "核心验证引擎 · 研究权限尚未开放"
                  : "核心验证引擎 · 正在读取真实目录"}</small>
              <strong>八字合成验证</strong>
              <em>自动检查不变量、响应与越界；争议案例才进入专业复核。</em>
              <b>进入合成验证引擎 <span aria-hidden="true">→</span></b>
            </span>
          </button>

          <button className="mingli-lab-project is-six" onClick={onOpenSixPillar} type="button">
            <SixPillarInstrument />
            <span className="mingli-lab-project-copy">
              <small>真实应用 · 四柱／六柱共享舞台</small>
              <strong>六柱</strong>
              <em>当前接入六冲／六合成员事实；关系作用仍回到整盘裁决。</em>
              <span className="mingli-lab-coverage" aria-hidden="true">
                <i>四柱原盘</i><i>大运</i><i>流年</i><i>六冲</i><i>六合</i>
              </span>
              <b>打开关系坐标观察 <span aria-hidden="true">→</span></b>
            </span>
          </button>

          <button className="mingli-lab-project is-voice" onClick={onOpenNarration} type="button">
            <AbuSaysInstrument />
            <span className="mingli-lab-project-copy">
              <small>讲述模块 · 已进入真实舞台</small>
              <strong>阿布说</strong>
              <em>同一命例的声音、字幕、角色动作与关系动画共用音频主时钟。</em>
              <b>开启同步讲述 <span aria-hidden="true">→</span></b>
            </span>
          </button>

          <div className="mingli-lab-shared-runtime">
            <span aria-hidden="true">◇</span>
            <p><strong>六柱协同 × 阿布说</strong>导演、播放器与角色演出共用同一个 Scene Player。</p>
          </div>
        </section>

        <ol className="mingli-lab-research-cycle" aria-label="研究成果进入系统的过程">
          {['研究问题', 'Lab 验证', '成果冻结', '系统采用'].map((label, index) => (
            <li key={label}><i>{index + 1}</i><span>{label}</span></li>
          ))}
        </ol>

        <div className="mingli-lab-guide">
          <p>多多在这里陪你看方法；命盘本人仍只在自己的生命树上展开。</p>
          <TransparentCharacterMedia
            active
            alt="多多，阿布 Lab 研究向导"
            className="mingli-lab-guide-character"
            cueRef={cue.cue_ref}
            poster={cue.deliveries.REDUCED_MOTION_POSTER}
            video={cue.deliveries.VP9_ALPHA_WEBM}
            webp={cue.deliveries.ANIMATED_WEBP}
          />
        </div>
        <footer className="mingli-lab-constitution">
          <span aria-hidden="true">◇</span>
          案例只在自己的生命树与命局枝中展开；Lab 只生产、验证并发布可被系统采用的方法。
          {catalog.error && <button onClick={catalog.retry} type="button">研究目录暂不可用，重新读取</button>}
        </footer>
      </main>
    </div>
  );
}
