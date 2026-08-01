import type { MingliReadingLayer } from "../mingliStageNavigation";
import type {
  MingliAgentReading,
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
  personality: "性情",
  career: "事业",
  wealth: "财富",
  relationship: "关系",
  family: "家庭",
} as const;

const DOMAIN_ORDER = [
  "personality",
  "career",
  "wealth",
  "relationship",
  "family",
] as const;

const DAY_MASTER_LABELS = {
  STRONG: "日主偏强",
  WEAK: "日主偏弱",
  BALANCED: "日主相对均衡",
  FOLLOWING_TENDENCY: "日主呈从势倾向",
  SPECIALIZED_TENDENCY: "命局呈专旺倾向",
  UNCERTAIN: "日主状态仍需复核",
} as const;

export function MingliReadingJourney({
  summary,
  layer,
  onAskGuide,
  onExpandTime,
  onGenerateAgent,
  onLayerChange,
  agentError = null,
  agentGenerating = false,
  stage,
}: {
  summary: MingliReadingSummaryProjection | null;
  layer: MingliReadingLayer;
  onAskGuide: () => void;
  onExpandTime: () => void;
  onGenerateAgent?: () => void;
  onLayerChange: (layer: MingliReadingLayer) => void;
  agentError?: string | null;
  agentGenerating?: boolean;
  stage: MingliStageProjection;
}) {
  const narrator = stage.narrator_actor_id === "DUODUO_NARRATOR_V1" ? "多多" : "阿布";
  const hasFormalReading = summaryMatchesStage(summary, stage);
  const hasAgentReading = hasFormalReading && summary?.agent_reading !== null;
  return (
    <aside
      aria-label="命理四层阅读"
      className="mingli-reading-journey"
      data-layer={layer}
      data-reading-scope={hasAgentReading ? "agent-reading" : "awaiting-agent"}
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
          agentError={agentError}
          agentGenerating={agentGenerating}
          onExpandTime={onExpandTime}
          onGenerateAgent={onGenerateAgent}
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
  agentError = null,
  agentGenerating = false,
  hasFormalReading,
  layer,
  onExpandTime,
  onGenerateAgent,
  stage,
  summary,
}: {
  agentError?: string | null;
  agentGenerating?: boolean;
  hasFormalReading: boolean;
  layer: MingliReadingLayer;
  onExpandTime: () => void;
  onGenerateAgent?: () => void;
  stage: MingliStageProjection;
  summary: MingliReadingSummaryProjection | null;
}) {
  const agentReading = hasFormalReading ? summary?.agent_reading ?? null : null;
  if (agentReading === null) {
    return (
      <AgentPendingLayer
        agentError={agentError}
        agentGenerating={agentGenerating}
        generationAvailable={summary?.agent_generation_available ?? false}
        layer={layer}
        onGenerateAgent={onGenerateAgent}
        stage={stage}
      />
    );
  }
  return (
    <>
      {layer === "principle" && (
        <PrincipleLayer reading={agentReading} />
      )}
      {layer === "image" && <ImageLayer reading={agentReading} stage={stage} />}
      {layer === "themes" && <ThemeLayer reading={agentReading} />}
      {layer === "timing" && (
        <TimingLayer
          onExpandTime={onExpandTime}
          reading={agentReading}
          stage={stage}
        />
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

function AgentPendingLayer({
  agentError,
  agentGenerating,
  generationAvailable,
  layer,
  onGenerateAgent,
  stage,
}: {
  agentError: string | null;
  agentGenerating: boolean;
  generationAvailable: boolean;
  layer: MingliReadingLayer;
  onGenerateAgent?: () => void;
  stage: MingliStageProjection;
}) {
  const selected = LAYERS.find((item) => item.id === layer) ?? LAYERS[0];
  const pillars = stage.columns
    .filter((column) => column.source_layer === "NATAL")
    .map((column) => column.pillar)
    .join(" · ");
  const canGenerate = generationAvailable
    && onGenerateAgent !== undefined
    && stage.reading_ref !== null;
  return (
    <div className="mingli-reading-layer">
      <LayerHeading
        eyebrow={`${selected.professional}${selected.organ} · ${selected.product}`}
        title={generationAvailable
          ? `让阿布完整读一遍${stage.display_name}的命局`
          : "这张命盘先不交给尚未合格的模型"}
        status={agentGenerating ? "正在研判" : generationAvailable ? "等待研判" : "专业校准中"}
      />
      <div className="mingli-principle-lines">
        <p>{pillars}</p>
        <p>{generationAvailable
          ? "阿布会把月令、透藏、根位、结构竞争、做功路径与岁运放回同一张命盘里判断。"
          : "四柱与岁运已经排定；当前阿布还没有通过整盘判断、命局取舍与岁运层次的专业校准。"}</p>
      </div>
      <article className="mingli-reading-focus">
        <small>一次整盘研判</small>
        <strong>{agentGenerating
          ? "阿布正在通读全盘……"
          : generationAvailable ? "不套模板，不逐项拼句" : "宁可暂缺，也不拿套话冒充判断"}</strong>
        <p>{generationAvailable
          ? "完成后，命局原理、生命意象、人生主题与时间趋势会一起长在这根命理枝上。"
          : "通过合成对照盘与专业复核后，这里才会开放完整研判。"}</p>
      </article>
      {canGenerate && (
        <button
          className="mingli-time-expand"
          disabled={agentGenerating}
          onClick={onGenerateAgent}
          type="button"
        >
          {agentGenerating ? "正在形成整盘判断…" : "开始命理师研判"}
        </button>
      )}
      {agentError && (
        <p className="mingli-reading-boundary" role="alert">
          本次研判没有完整完成，请稍后再试；已有命盘不会受到影响。
        </p>
      )}
    </div>
  );
}

function PrincipleLayer({ reading }: { reading: MingliAgentReading }) {
  const output = reading.output;
  const primary = output.hypotheses.find(
    (item) => item.role === "PRIMARY",
  )!;
  const alternative = output.hypotheses.find(
    (item) => item.role === "ALTERNATIVE",
  );
  return (
    <div className="mingli-reading-layer">
      <LayerHeading
        eyebrow="理法枝 · 整盘总纲"
        title={output.first_look}
        status={DAY_MASTER_LABELS[output.day_master_state]}
      />
      <div className="mingli-principle-lines">
        <p>{output.whole_chart_thesis}</p>
        <p>{output.day_master_rationale}</p>
      </div>
      <article className="mingli-reading-focus">
        <small>主解释 · {primary.name}</small>
        <strong>{primary.thesis}</strong>
        <p>{output.work_path.path_statement}</p>
      </article>
      {alternative && (
        <p className="mingli-reading-boundary">
          竞争解释：{alternative.name}。{alternative.thesis}
        </p>
      )}
    </div>
  );
}

function ImageLayer({
  reading,
  stage,
}: {
  reading: MingliAgentReading;
  stage: MingliStageProjection;
}) {
  const dayMaster = stage.columns.find((column) => column.slot === "NATAL_DAY")?.stem ?? "命";
  const image = reading.output.life_image;
  return (
    <div className="mingli-reading-layer">
      <LayerHeading
        eyebrow="象法叶 · 整盘成象"
        title={image.title}
        status="由命局结构生发"
      />
      <div className="mingli-image-placeholder">
        <i aria-hidden="true">{dayMaster}</i>
        <p>{image.image}</p>
      </div>
      <div className="mingli-principle-lines"><p>{image.explanation}</p></div>
    </div>
  );
}

function ThemeLayer({ reading }: { reading: MingliAgentReading }) {
  return (
    <div className="mingli-reading-layer">
      <LayerHeading
        eyebrow="人生应事花 · 从结构落到生活"
        title="这份命局如何进入性情、事业、财富与关系"
        status="条件性应事"
      />
      <div className="mingli-theme-list">
        {DOMAIN_ORDER.map((domain) => {
          const item = reading.output.domains[domain];
          return (
          <article key={domain}>
            <small>{DOMAIN_LABELS[domain]}</small>
            <strong>{item.headline}</strong>
            <p>{item.conclusion}</p>
            <span>{item.causal_chain.join(" → ")}</span>
          </article>
          );
        })}
      </div>
    </div>
  );
}

function TimingLayer({
  onExpandTime,
  reading,
  stage,
}: {
  onExpandTime: () => void;
  reading: MingliAgentReading;
  stage: MingliStageProjection;
}) {
  const expanded = stage.stage_mode === "NATAL_DAYUN_YEAR_6";
  const timing = reading.output.timing;
  return (
    <div className="mingli-reading-layer">
      <LayerHeading
        eyebrow="岁运应期果 · 原局为体，岁运为用"
        title={timing.natal_baseline}
        status={expanded ? "六柱同场" : "本命四柱"}
      />
      <div className="mingli-theme-list">
        <article>
          <small>当前大运 · {stage.current_dayun_label}</small>
          <strong>十年环境如何改变原局发力方式</strong>
          <p>{timing.dayun.conclusion}</p>
        </article>
        <article>
          <small>当前流年</small>
          <strong>今年触发了什么</strong>
          <p>{timing.annual.conclusion}</p>
          <span>{timing.annual.activation_chain.join(" → ")}</span>
        </article>
      </div>
      {!expanded && (
        <button className="mingli-time-expand" onClick={onExpandTime} type="button">
          展开大运与流年六柱
        </button>
      )}
      <p className="mingli-reading-boundary">
        可复核信号：{timing.verification_signals.join("；")}
      </p>
    </div>
  );
}
