import type { Session } from "../publicRuntimeTypes";
import type { PublicRuntimeMediaManifest, RuntimeAssetDelivery } from "../publicRuntimeTypes";
import type { PublicHomeSnapshot } from "../publicHomeApi";
import type {
  MingliFocus,
  MingliReadingSummaryProjection,
  MingliStageProjection,
} from "../mingliStageTypes";
import {
  publicFocusedPassRecord,
  PUBLIC_READING_TOPICS,
  publicReadingCopy,
} from "../publicReadingPresentation";
import { PublicAbuSays } from "./PublicAbuSays";

export type PublicReadingMode = "READING" | "ABU";

const PILLAR_LABELS = {
  year: "年柱",
  month: "月柱",
  day: "日柱",
  hour: "时柱",
} as const;

export function PublicReadingWorkspace({
  brand,
  media,
  session,
  home,
  stage,
  summary,
  mode,
  focus,
  loading,
  switchingCase,
  generatingFocus,
  error,
  onModeChange,
  onFocusChange,
  onCaseChange,
  onNewCase,
  onLogout,
  onRetry,
}: {
  brand: RuntimeAssetDelivery;
  media: PublicRuntimeMediaManifest;
  session: Session;
  home: PublicHomeSnapshot;
  stage: MingliStageProjection | null;
  summary: MingliReadingSummaryProjection | null;
  mode: PublicReadingMode;
  focus: MingliFocus;
  loading: boolean;
  switchingCase: boolean;
  generatingFocus: MingliFocus | null;
  error: string | null;
  onModeChange: (mode: PublicReadingMode) => void;
  onFocusChange: (focus: MingliFocus) => void;
  onCaseChange: (caseRef: string) => Promise<void>;
  onNewCase: () => void;
  onLogout: () => Promise<void>;
  onRetry: () => Promise<void>;
}) {
  const activeCase = home.case_options.find((item) => item.active) ?? home.case_options[0];
  const topic = PUBLIC_READING_TOPICS.find((item) => item.focus === focus) ?? PUBLIC_READING_TOPICS[0];
  const copy = summary ? publicReadingCopy(summary, focus) : null;
  const record = summary ? publicFocusedPassRecord(summary, focus) : null;
  const focusIsGenerating = generatingFocus === focus;

  return (
    <div className="public-workspace">
      <header className="public-header">
        <a className="public-brand" href="/experience" aria-label="阿布知命首页">
          <img src={brand.url} alt="阿布知命" />
        </a>
        <div className="public-header-actions">
          <label className="public-case-select">
            <span>当前命盘</span>
            <select
              aria-label="切换命盘"
              disabled={switchingCase}
              value={activeCase?.case_ref ?? ""}
              onChange={(event) => void onCaseChange(event.target.value)}
            >
              {home.case_options.map((item) => (
                <option key={item.case_ref} value={item.case_ref}>{item.display_name}</option>
              ))}
            </select>
          </label>
          <button className="public-quiet-button" onClick={onNewCase} type="button">＋ 新命盘</button>
          <button className="public-account-button" onClick={() => void onLogout()} type="button">
            <span>{session.account.display_name.slice(0, 1)}</span>
            退出
          </button>
        </div>
      </header>

      <main className="public-reading-main">
        <section className="public-chart-intro" aria-labelledby="chart-title">
          <div>
            <p className="public-kicker">{activeCase?.calendar_type === "lunar" ? "农历命盘" : "公历命盘"} · 私密档案</p>
            <h1 id="chart-title">{home.profile.display_name}的命盘</h1>
            <p>
              {activeCase?.birth_date} {activeCase?.birth_time} · {activeCase?.birth_location}
            </p>
          </div>
          <div className="public-pillars" aria-label="四柱命盘">
            {(Object.keys(PILLAR_LABELS) as Array<keyof typeof PILLAR_LABELS>).map((slot) => {
              const pillar = home.chart.pillars[slot] || "--";
              return (
                <div className={slot === "day" ? "is-day-pillar" : ""} key={slot}>
                  <span>{PILLAR_LABELS[slot]}</span>
                  <strong>{pillar.slice(0, 1)}</strong>
                  <strong>{pillar.slice(1, 2)}</strong>
                  {slot === "day" && <small>日主</small>}
                </div>
              );
            })}
          </div>
        </section>

        <nav className="public-mode-switch" aria-label="阅读方式">
          <button aria-pressed={mode === "READING"} className={mode === "READING" ? "is-active" : ""} onClick={() => onModeChange("READING")} type="button">
            <span>断命</span>
            <small>清晰阅读完整判断</small>
          </button>
          <button aria-pressed={mode === "ABU"} className={mode === "ABU" ? "is-active" : ""} onClick={() => onModeChange("ABU")} type="button">
            <span>阿布说</span>
            <small>让阿布当面讲给你听</small>
          </button>
        </nav>

        <nav className="public-topic-nav" aria-label="断命主题">
          {PUBLIC_READING_TOPICS.map((item) => (
            <button
              aria-pressed={focus === item.focus}
              className={focus === item.focus ? "is-active" : ""}
              key={item.focus}
              onClick={() => onFocusChange(item.focus)}
              type="button"
            >
              <span>{item.label}</span>
              <small>{item.hint}</small>
              {generatingFocus === item.focus && <i aria-label="正在生成" />}
            </button>
          ))}
        </nav>

        {error && (
          <div className="public-inline-error" role="alert">
            <span>{error}</span>
            <button onClick={() => void onRetry()} type="button">重新读取</button>
          </div>
        )}

        {loading || !stage || !summary || !copy ? (
          <section className="public-reading-loading" aria-live="polite">
            <div className="public-loading-mark"><span /><span /><span /></div>
            <h2>正在展开命盘</h2>
            <p>四柱先由本地算法确定，断命内容随后按主题读取。</p>
          </section>
        ) : mode === "ABU" ? (
          <PublicAbuSays
            copy={copy}
            cue={media.cues.abu_idle}
            generating={focusIsGenerating}
            record={record}
            stage={stage}
            topicLabel={topic.label}
          />
        ) : (
          <section className="public-reading-layout">
            <article className="public-reading-card">
              <header>
                <div>
                  <p className="public-kicker">{topic.label} · 结论先行</p>
                  <h2>{focusIsGenerating ? "这一层正在补充细断" : topic.hint}</h2>
                </div>
                <span className={copy.source === "FOCUSED_MODEL" ? "is-model" : ""}>
                  {focusIsGenerating
                    ? "阿布正在细看"
                    : copy.source === "FOCUSED_MODEL"
                      ? "分层初断"
                      : "基础命盘"}
                </span>
              </header>
              <p className="public-reading-lead">{copy.lead}</p>
              {copy.paragraphs.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
              {focusIsGenerating && (
                <div className="public-generation-note" role="status">
                  <span />
                  基础结论已显示。Qwen 正在只处理“{topic.label}”这一项，完成后会自动更新。
                </div>
              )}
            </article>

            <aside className="public-reading-aside">
              <details>
                <summary>为什么这样说</summary>
                <div>
                  <p className="public-evidence-pillars">
                    {Object.entries(home.chart.pillars).map(([slot, pillar]) => (
                      <span key={slot}>{PILLAR_LABELS[slot as keyof typeof PILLAR_LABELS]} {pillar}</span>
                    ))}
                  </p>
                  {copy.evidence.length ? (
                    <ul>{copy.evidence.map((item) => <li key={item}>{item}</li>)}</ul>
                  ) : (
                    <p>当前先保留四柱坐标，不用单一符号代替整盘判断。</p>
                  )}
                </div>
              </details>
              <div className="public-abu-invite">
                <span className="public-abu-mini">阿</span>
                <div>
                  <strong>想听得更自然？</strong>
                  <p>同一份断语，阿布可以直接讲给你听，不会重新算一遍。</p>
                </div>
                <button onClick={() => onModeChange("ABU")} type="button">让阿布说</button>
              </div>
              <p className="public-boundary-note">
                AI 传统文化参考 · 结果仍在持续校准。重要的人生、健康、法律与财务决定，请结合现实信息和专业意见。
              </p>
            </aside>
          </section>
        )}
      </main>
    </div>
  );
}
