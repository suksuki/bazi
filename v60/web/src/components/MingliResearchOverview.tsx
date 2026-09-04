import type { CSSProperties } from "react";
import type { RuntimeMediaManifest } from "../publicRuntimeTypes";
import { resolveHomeWorldLight } from "../homeWorldLight";
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
}: {
  media: RuntimeMediaManifest;
  onExit: () => void;
  onOpenNarration: () => void;
  onOpenSixPillar: () => void;
}) {
  const worldLight = resolveHomeWorldLight();
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
      data-public-exposure="SIX_PILLAR_AND_ABU_SAYS_DEMOS"
      data-world-light={worldLight}
      style={style}
    >
      <MingliLabRealmHeader
        backLabel="回到生命树"
        eyebrow="ABU LAB · METHOD RESEARCH"
        onBack={onExit}
        status="测试开放 · 2 项演示"
        title="阿布 LAB · 研究"
      />
      <main className="mingli-lab-watercourt" aria-labelledby="mingli-lab-title">
        <span className="mingli-lab-mist is-far" aria-hidden="true" />
        <span className="mingli-lab-mist is-near" aria-hidden="true" />
        <header className="mingli-lab-world-heading">
          <small>ABU LAB · METHOD RESEARCH</small>
          <h1 id="mingli-lab-title">把命理变成可以观察、比较和验证的东西。</h1>
          <p>当前开放六柱与阿布说演示。</p>
        </header>

        <section className="mingli-lab-project-field" data-public-demo-count="2" aria-label="阿布 LAB 公开演示">
          <button className="mingli-lab-project is-six" onClick={onOpenSixPillar} type="button">
            <SixPillarInstrument />
            <span className="mingli-lab-project-copy">
              <small>演示一 · 四柱／六柱共享舞台</small>
              <strong>六柱演示</strong>
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
              <small>演示二 · 已进入真实舞台</small>
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
          <p>多多陪你试看六柱与阿布说；研究训练台不向测试者开放。</p>
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
          当前测试入口只包含六柱与阿布说；两者共用同一命盘、舞台与演出时间轴。
        </footer>
      </main>
    </div>
  );
}
