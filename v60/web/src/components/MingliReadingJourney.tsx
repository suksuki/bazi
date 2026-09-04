import type { MingliReadingLayer } from "../mingliStageNavigation";
import type {
  MingliReadingClaim,
  MingliReadingClaimGraph,
  MingliReadingClaimSemanticKey,
} from "../mingliClaimGraphTypes";
import type {
  MingliAgentOutput,
  MingliFocus,
  MingliReadingSummaryProjection,
  MingliStageProjection,
} from "../mingliStageTypes";
import { claimIsAdmitted, claimStatusLabel } from "../mingliClaimPresentation";
import { ClaimReviewNotice } from "./MingliClaimPresentation";
import {
  MingliFocusedPendingLayer,
  MingliFocusedReadingLayer,
} from "./MingliFocusedReadingLayer";

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

const DOMAIN_SEMANTIC_KEYS = {
  personality: "DOMAIN_PERSONALITY",
  career: "DOMAIN_CAREER",
  wealth: "DOMAIN_WEALTH",
  relationship: "DOMAIN_RELATIONSHIP",
  family: "DOMAIN_FAMILY",
} as const;

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
  onGenerateAgent?: (focus: MingliFocus) => void;
  onLayerChange: (layer: MingliReadingLayer) => void;
  agentError?: string | null;
  agentGenerating?: boolean;
  stage: MingliStageProjection;
}) {
  const narrator = stage.narrator_actor_id === "DUODUO_NARRATOR_V1" ? "多多" : "阿布";
  const hasFormalReading = summaryMatchesStage(summary, stage);
  const hasClaimGraph = hasFormalReading && summary?.claim_graph !== null;
  return (
    <aside
      aria-label="命理四层阅读"
      className="mingli-reading-journey"
      data-layer={layer}
      data-claim-graph-ref={hasClaimGraph ? summary?.claim_graph?.graph_ref : undefined}
      data-reading-scope={hasClaimGraph ? "shared-claim-graph" : "awaiting-agent"}
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
  actionsVisible = true,
  agentError = null,
  agentGenerating = false,
  hasFormalReading,
  layer,
  onExpandTime,
  onGenerateAgent,
  stage,
  summary,
}: {
  actionsVisible?: boolean;
  agentError?: string | null;
  agentGenerating?: boolean;
  hasFormalReading: boolean;
  layer: MingliReadingLayer;
  onExpandTime: () => void;
  onGenerateAgent?: (focus: MingliFocus) => void;
  stage: MingliStageProjection;
  summary: MingliReadingSummaryProjection | null;
}) {
  const claimGraph = hasFormalReading ? summary?.claim_graph ?? null : null;
  const focusedPasses = hasFormalReading
    ? [
        ...(summary?.focused_reading?.passes ?? []),
        ...(summary?.focused_pass_records.map((record) => record.pass_result) ?? []),
      ]
    : [];
  if (focusedPasses.length > 0) {
    return (
      <MingliFocusedReadingLayer
        actionsVisible={actionsVisible}
        agentError={agentError}
        agentGenerating={agentGenerating}
        generationAvailable={summary?.focused_generation_available ?? false}
        layer={layer}
        onExpandTime={onExpandTime}
        onGenerateAgent={onGenerateAgent}
        passes={focusedPasses}
        stage={stage}
      />
    );
  }
  if (claimGraph === null) {
    return (
      <MingliFocusedPendingLayer
        agentError={agentError}
        agentGenerating={agentGenerating}
        generationAvailable={summary?.focused_generation_available ?? false}
        layer={layer}
        onGenerateAgent={onGenerateAgent}
        stage={stage}
      />
    );
  }
  return (
    <>
      {layer === "principle" && (
        <PrincipleLayer
          claimGraph={claimGraph}
          decision={summary?.agent_reading?.output.hypothesis_decision ?? null}
        />
      )}
      {layer === "image" && <ImageLayer claimGraph={claimGraph} stage={stage} />}
      {layer === "themes" && <ThemeLayer claimGraph={claimGraph} />}
      {layer === "timing" && (
        <TimingLayer
          actionsVisible={actionsVisible}
          claimGraph={claimGraph}
          onExpandTime={onExpandTime}
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

function PrincipleLayer({
  claimGraph,
  decision,
}: {
  claimGraph: MingliReadingClaimGraph;
  decision: MingliAgentOutput["hypothesis_decision"] | null;
}) {
  const wholeChart = claim(claimGraph, "WHOLE_CHART");
  const dayMaster = claim(claimGraph, "DAY_MASTER");
  const primary = claimGraph.claims.find((item) => item.role === "PRIMARY")!;
  const alternative = claimGraph.claims.find((item) => item.role === "ALTERNATIVE");
  const workPath = claim(claimGraph, "WORK_PATH");
  const dayMasterState = dayMaster.codes[0] as keyof typeof DAY_MASTER_LABELS;
  const wholeChartAdmitted = claimIsAdmitted(wholeChart);
  const dayMasterAdmitted = claimIsAdmitted(dayMaster);
  const primaryAdmitted = claimIsAdmitted(primary);
  const workPathAdmitted = claimIsAdmitted(workPath);
  return (
    <div className="mingli-reading-layer">
      <LayerHeading
        eyebrow="理法枝 · 整盘总纲"
        title={wholeChartAdmitted
          ? wholeChart.headline
          : primaryAdmitted ? primary.headline : "整盘主线仍需重写"}
        status={`${dayMasterAdmitted
          ? DAY_MASTER_LABELS[dayMasterState] ?? "日主状态待校准"
          : "日主状态待校准"} · ${claimStatusLabel(wholeChart)}`}
      />
      <div className="mingli-principle-lines">
        {wholeChartAdmitted && <p>{wholeChart.statement}</p>}
        {dayMasterAdmitted && <p>{dayMaster.statement}</p>}
        {wholeChartAdmitted && wholeChart.assessment_codes.length > 0 && (
          <ClaimReviewNotice context="整盘总纲" item={wholeChart} />
        )}
        {!dayMasterAdmitted && <ClaimReviewNotice context="日主判断" item={dayMaster} />}
        {!wholeChartAdmitted && <ClaimReviewNotice item={wholeChart} />}
      </div>
      {primaryAdmitted ? (
        <article className="mingli-reading-focus" data-claim-status={primary.status}>
          <small>主解释 · {primary.headline}</small>
          <strong>{primary.statement}</strong>
          {primary.assessment_codes.length > 0 && (
            <ClaimReviewNotice context="主解释" item={primary} />
          )}
          {workPathAdmitted
            ? <p>{workPath.statement}</p>
            : <ClaimReviewNotice context="原局做功路径" item={workPath} />}
          {decision && <p>为什么取它：{decision.winner.rationale}</p>}
        </article>
      ) : (
        <ClaimReviewNotice item={primary} />
      )}
      {alternative && claimIsAdmitted(alternative) && (
        <p className="mingli-reading-boundary">
          竞争解释：{alternative.headline}。{alternative.statement}
          {decision && ` 暂不采用：${decision.loser.rationale}`}
        </p>
      )}
    </div>
  );
}

function ImageLayer({
  claimGraph,
  stage,
}: {
  claimGraph: MingliReadingClaimGraph;
  stage: MingliStageProjection;
}) {
  const dayMaster = stage.columns.find((column) => column.slot === "NATAL_DAY")?.stem ?? "命";
  const image = claim(claimGraph, "LIFE_IMAGE");
  const admitted = claimIsAdmitted(image);
  return (
    <div className="mingli-reading-layer">
      <LayerHeading
        eyebrow="象法叶 · 整盘成象"
        title={admitted ? image.headline : "生命意象正在按整盘主线重写"}
        status={claimStatusLabel(image)}
      />
      {admitted ? (
        <>
          <div className="mingli-image-placeholder">
            <i aria-hidden="true">{dayMaster}</i>
            <p>{image.causal_chain[0]}</p>
          </div>
          <div className="mingli-principle-lines"><p>{image.statement}</p></div>
        </>
      ) : <ClaimReviewNotice item={image} />}
    </div>
  );
}

function ThemeLayer({ claimGraph }: { claimGraph: MingliReadingClaimGraph }) {
  return (
    <div className="mingli-reading-layer">
      <LayerHeading
        eyebrow="人生应事花 · 从结构落到生活"
        title="这份命局如何进入性情、事业、财富与关系"
        status="阿布初断 · 可继续校准"
      />
      <div className="mingli-theme-list">
        {DOMAIN_ORDER.map((domain) => {
          const item = claim(claimGraph, DOMAIN_SEMANTIC_KEYS[domain]);
          return (
          <article data-claim-status={item.status} key={domain}>
            <small>{DOMAIN_LABELS[domain]}</small>
            {claimIsAdmitted(item) ? (
              <>
                <strong>{item.headline}</strong>
                <p>{item.statement}</p>
                <span>{item.causal_chain.join(" → ")}</span>
                {item.assessment_codes.length > 0 && (
                  <ClaimReviewNotice item={item} />
                )}
              </>
            ) : <ClaimReviewNotice item={item} />}
          </article>
          );
        })}
      </div>
    </div>
  );
}

function TimingLayer({
  actionsVisible,
  claimGraph,
  onExpandTime,
  stage,
}: {
  actionsVisible: boolean;
  claimGraph: MingliReadingClaimGraph;
  onExpandTime: () => void;
  stage: MingliStageProjection;
}) {
  const expanded = stage.stage_mode === "NATAL_DAYUN_YEAR_6";
  const natal = claim(claimGraph, "TIMING_NATAL");
  const dayun = claim(claimGraph, "TIMING_DAYUN");
  const annual = claim(claimGraph, "TIMING_ANNUAL");
  const question = claim(claimGraph, "DISCRIMINATING_QUESTION");
  const natalAdmitted = claimIsAdmitted(natal);
  return (
    <div className="mingli-reading-layer">
      <LayerHeading
        eyebrow="岁运应期果 · 原局为体，岁运为用"
        title={natalAdmitted ? natal.statement : "原局基线正在重新校准"}
        status={expanded ? "六柱同场" : "本命四柱"}
      />
      {!natalAdmitted && <ClaimReviewNotice context="原局基线" item={natal} />}
      <div className="mingli-theme-list">
        <article>
          <small>当前大运 · {stage.current_dayun_label}</small>
          <strong>十年环境如何改变原局发力方式</strong>
          {claimIsAdmitted(dayun) ? (
            <>
              <p>{dayun.statement}</p>
              <span>{dayun.causal_chain.join(" → ")}</span>
            </>
          ) : <ClaimReviewNotice item={dayun} />}
        </article>
        <article>
          <small>当前流年</small>
          <strong>今年触发了什么</strong>
          {claimIsAdmitted(annual) ? (
            <>
              <p>{annual.statement}</p>
              <span>{annual.causal_chain.join(" → ")}</span>
            </>
          ) : <ClaimReviewNotice item={annual} />}
        </article>
      </div>
      {actionsVisible && !expanded && (
        <button className="mingli-time-expand" onClick={onExpandTime} type="button">
          展开大运与流年六柱
        </button>
      )}
      <p className="mingli-reading-boundary">
        为了校准这次初断，阿布会继续问：{question.statement}
      </p>
    </div>
  );
}

function claim(
  graph: MingliReadingClaimGraph,
  semanticKey: MingliReadingClaimSemanticKey,
): MingliReadingClaim {
  const item = graph.claims.find((candidate) => candidate.semantic_key === semanticKey);
  if (item === undefined) throw new Error(`mingli_claim_missing:${semanticKey}`);
  return item;
}
