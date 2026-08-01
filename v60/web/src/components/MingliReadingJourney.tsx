import type { MingliReadingLayer } from "../mingliStageNavigation";
import type {
  MingliReadingSummaryProjection,
  MingliStageProjection,
} from "../mingliStageTypes";

const LAYERS: Array<{
  id: MingliReadingLayer;
  professional: string;
  product: string;
  organ: string;
}> = [
  { id: "principle", professional: "理法", product: "命局原理", organ: "枝" },
  { id: "image", professional: "象法", product: "生命意象", organ: "叶" },
  { id: "themes", professional: "应事", product: "人生主题", organ: "花" },
  { id: "timing", professional: "应期", product: "时间趋势", organ: "果" },
];

const DOMAIN_LABELS = {
  career: "事业",
  wealth: "财富",
  relationship: "关系",
} as const;

export function MingliReadingJourney({
  summary,
  layer,
  onAskGuide,
  onExpandTime,
  onLayerChange,
  stage,
}: {
  summary: MingliReadingSummaryProjection | null;
  layer: MingliReadingLayer;
  onAskGuide: () => void;
  onExpandTime: () => void;
  onLayerChange: (layer: MingliReadingLayer) => void;
  stage: MingliStageProjection;
}) {
  const narrator = stage.narrator_actor_id === "DUODUO_NARRATOR_V1" ? "多多" : "阿布";
  const hasFormalReading = summaryMatchesStage(summary, stage);
  return (
    <aside
      aria-label="命理四层阅读"
      className="mingli-reading-journey"
      data-layer={layer}
      data-reading-scope={hasFormalReading ? "formal" : "synthetic-boundary"}
    >
      <div className="mingli-reading-branch" aria-hidden="true">
        <i /><i /><i />
      </div>
      <nav aria-label="命理四层" className="mingli-reading-nodes">
        {LAYERS.map((item) => (
          <button
            aria-pressed={layer === item.id}
            className={`is-${item.id}`}
            key={item.id}
            onClick={() => onLayerChange(item.id)}
            type="button"
          >
            <i aria-hidden="true">{item.organ}</i>
            <span><small>{item.professional}</small><strong>{item.product}</strong></span>
          </button>
        ))}
      </nav>

      <section className="mingli-reading-story">
        <MingliReadingLayerContent
          hasFormalReading={hasFormalReading}
          layer={layer}
          onExpandTime={onExpandTime}
          stage={stage}
          summary={summary}
        />
        <button className="mingli-reading-ask-guide" onClick={onAskGuide} type="button">
          请{narrator}讲解当前舞台
          <span aria-hidden="true">坐标、关系边界、声音与舞台一起开始 →</span>
        </button>
      </section>
    </aside>
  );
}

export function summaryMatchesStage(
  summary: MingliReadingSummaryProjection | null,
  stage: MingliStageProjection,
) {
  return summary !== null
    && summary.case_ref === stage.case_ref
    && summary.chart_version_ref === stage.chart_version_ref
    && summary.life_case_revision_ref === stage.life_case_revision_ref
    && summary.reading_ref === stage.reading_ref
    && summary.reading_hash === stage.reading_hash;
}

export function MingliReadingLayerContent({
  hasFormalReading,
  layer,
  onExpandTime,
  stage,
  summary,
}: {
  hasFormalReading: boolean;
  layer: MingliReadingLayer;
  onExpandTime: () => void;
  stage: MingliStageProjection;
  summary: MingliReadingSummaryProjection | null;
}) {
  return (
    <>
      {layer === "principle" && (
        <PrincipleLayer
          hasFormalReading={hasFormalReading}
          stage={stage}
          summary={summary}
        />
      )}
      {layer === "image" && <ImageLayer stage={stage} />}
      {layer === "themes" && (
        <ThemeLayer
          hasFormalReading={hasFormalReading}
          stage={stage}
          summary={summary}
        />
      )}
      {layer === "timing" && (
        <TimingLayer onExpandTime={onExpandTime} stage={stage} />
      )}
    </>
  );
}

function LayerHeading({
  eyebrow,
  title,
  status,
}: {
  eyebrow: string;
  title: string;
  status: string;
}) {
  return (
    <header className="mingli-reading-story-heading">
      <p>{eyebrow}</p>
      <h2>{title}</h2>
      <span>{status}</span>
    </header>
  );
}

function PrincipleLayer({
  hasFormalReading,
  stage,
  summary,
}: {
  hasFormalReading: boolean;
  stage: MingliStageProjection;
  summary: MingliReadingSummaryProjection | null;
}) {
  if (!hasFormalReading) {
    const pillars = stage.columns.filter((column) => column.source_layer === "NATAL");
    return (
      <div className="mingli-reading-layer">
        <LayerHeading
          eyebrow="理法枝 · 角色合成设定"
          title={`${stage.display_name}的四柱坐标已经锁定`}
          status="尚无正式 Reading"
        />
        <div className="mingli-principle-lines">
          {pillars.map((column) => (
            <p key={column.column_ref}>{column.label}为 {column.pillar}。</p>
          ))}
        </div>
        <article className="mingli-reading-focus">
          <small>当前允许的用途</small>
          <strong>原型角色与声画舞台演示</strong>
          <p>这里只使用该角色自己的 canonical 合成坐标和已准入关系成员。</p>
        </article>
        <p className="mingli-reading-boundary">
          这不是专业复核后的命理 Reading，也不会复用当前 Owner 的结论、人生主题或时间判断。
        </p>
      </div>
    );
  }
  const brief = summary!.reading_brief;
  return (
    <div className="mingli-reading-layer">
      <LayerHeading eyebrow="理法枝 · 已确认与未决分开" title={brief.headline} status="正式 Reading" />
      <div className="mingli-principle-lines">
        {brief.confirmed.map((statement) => <p key={statement}>{statement}</p>)}
      </div>
      <article className="mingli-reading-focus">
        <small>当前可讨论重点</small>
        <strong>{brief.focus.label}</strong>
        <p>{brief.focus.statement}</p>
      </article>
      <p className="mingli-reading-boundary">{brief.boundaries[0] ?? "没有足够证据的专业结论保持未决。"}</p>
    </div>
  );
}

function ImageLayer({ stage }: { stage: MingliStageProjection }) {
  const dayMaster = stage.columns.find((column) => column.slot === "NATAL_DAY")?.stem ?? "命";
  const synthetic = stage.subject_id !== "current" || !stage.reading_ref;
  return (
    <div className="mingli-reading-layer">
      <LayerHeading
        eyebrow="象法叶 · 证据缺口可见"
        title={synthetic ? `${stage.display_name}尚未建立正式生命意象` : "生命意象尚未进入正式命理正本"}
        status="等待专业准入"
      />
      <div className="mingli-image-placeholder">
        <i aria-hidden="true">{dayMaster}</i>
        <p>生命树可以表达气质和空间感，但当前树形参数只具备视觉隐喻语义。</p>
      </div>
      <p className="mingli-reading-boundary">
        系统尚未取得足以讨论冷暖燥湿、物象或人物象的正式 Projection，因此这里保留原型的位置和体验，不伪造象法结论。
      </p>
    </div>
  );
}

function ThemeLayer({
  hasFormalReading,
  stage,
  summary,
}: {
  hasFormalReading: boolean;
  stage: MingliStageProjection;
  summary: MingliReadingSummaryProjection | null;
}) {
  if (!hasFormalReading) {
    return (
      <div className="mingli-reading-layer">
        <LayerHeading
          eyebrow="人生应事花 · 角色边界"
          title={`${stage.display_name}尚未建立人生应事窗口`}
          status="不借用 Owner Reading"
        />
        <div className="mingli-theme-list">
          <article>
            <small>角色合成设定</small>
            <strong>只有坐标，没有人生断语</strong>
            <p>合成八字支持原型舞台、关系成员与角色讲述验收，不等于专业命理师已经完成事业、财富或关系判断。</p>
            <span>未来必须由该角色自己的正式证据和专业复核生成。</span>
          </article>
        </div>
        <p className="mingli-reading-boundary">系统不会把其他 Case 的人生主题拼接到这个角色。</p>
      </div>
    );
  }
  return (
    <div className="mingli-reading-layer">
      <LayerHeading eyebrow="人生应事花 · 现实观察窗口" title="哪些人生主题值得继续观察" status="不是事件预测" />
      <div className="mingli-theme-list">
        {summary!.reading_brief.life_domains.map((item) => (
          <article key={item.domain}>
            <small>{DOMAIN_LABELS[item.domain]}</small>
            <strong>{item.label}</strong>
            <p>{item.statement}</p>
            <span>{item.question}</span>
          </article>
        ))}
      </div>
      <p className="mingli-reading-boundary">这些是有限证据支持的注意窗口，不是吉凶、概率或必然事件。</p>
    </div>
  );
}

function TimingLayer({
  onExpandTime,
  stage,
}: {
  onExpandTime: () => void;
  stage: MingliStageProjection;
}) {
  const expanded = stage.stage_mode === "NATAL_DAYUN_YEAR_6";
  const coordinates = expanded
    ? stage.columns
        .filter((column) => column.source_layer !== "NATAL")
        .map((column) => ({
          layer: column.label,
          pillar: column.pillar,
          ten_god_label: "确定坐标",
        }))
    : [{ layer: "大运", pillar: stage.current_dayun_label, ten_god_label: "确定坐标" }];
  return (
    <div className="mingli-reading-layer">
      <LayerHeading
        eyebrow="岁运应期果 · 同一舞台的时间层"
        title={expanded ? "本命、大运与所选流年已经同时在场" : "先保留本命，再展开完整时间层"}
        status={expanded ? "六柱坐标已锁定" : "当前为本命四柱"}
      />
      <div className="mingli-timing-list">
        {coordinates.map((coordinate) => (
          <span key={`${coordinate.layer}:${coordinate.pillar}`}>
            <small>{coordinate.layer}</small>
            <strong>{coordinate.pillar}</strong>
            <em>{coordinate.ten_god_label}</em>
          </span>
        ))}
      </div>
      {!expanded && (
        <button className="mingli-time-expand" onClick={onExpandTime} type="button">
          展开大运与流年六柱
        </button>
      )}
      <p className="mingli-reading-boundary">
        时间坐标与六冲／六合成员关系可以展示；激活、关系作用、应事强度和吉凶仍未决。
      </p>
    </div>
  );
}
