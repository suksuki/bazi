import type { MingliReadingLayer } from "../mingliStageNavigation";
import type {
  MingliFocus,
  MingliFocusedPassResult,
  MingliStageProjection,
} from "../mingliStageTypes";

const LAYER_LABELS = {
  principle: { professional: "理法", product: "命局原理", organ: "枝" },
  image: { professional: "象法", product: "生命意象", organ: "叶" },
  themes: { professional: "应事", product: "人生主题", organ: "花" },
  timing: { professional: "应期", product: "时间趋势", organ: "果" },
} as const;

export function MingliFocusedPendingLayer({
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
  onGenerateAgent?: (focus: MingliFocus) => void;
  stage: MingliStageProjection;
}) {
  const selected = LAYER_LABELS[layer];
  const pillars = stage.columns
    .filter((column) => column.source_layer === "NATAL")
    .map((column) => column.pillar)
    .join(" · ");
  const canGenerate = generationAvailable
    && onGenerateAgent !== undefined
    && stage.reading_ref !== null;
  return (
    <div className="mingli-reading-layer">
      <FocusedLayerHeading
        eyebrow={`${selected.professional}${selected.organ} · ${selected.product}`}
        title={generationAvailable
          ? `先读${stage.display_name}的原局总纲`
          : `${stage.display_name}的分层初断尚未生成`}
        status={agentGenerating
          ? "正在研判"
          : generationAvailable ? "等待你开始" : "推演服务未就绪"}
      />
      <div className="mingli-principle-lines">
        <p>{pillars}</p>
        <p>{generationAvailable
          ? "先用一次短问确定原局主线；你点到意象、事业财富、关系家庭或岁运时，再分别生成那一层。"
          : "四柱与岁运已经排定；服务恢复后，阿布会从整盘主线开始判断，而不是填充栏目套话。"}</p>
      </div>
      <article className="mingli-reading-focus">
        <small>短上下文 · 一次一问</small>
        <strong>{agentGenerating
          ? "阿布正在判断原局总纲……"
          : generationAvailable ? "先把整盘主线定下来" : "命盘已经保存，不需要重新录入"}</strong>
        <p>{generationAvailable
          ? "每段只拿必要事实问本地模型；原文会留给研发期教师审读，页面使用本地整理后的正文。"
          : "推演服务恢复后，可以从当前档案直接继续。"}</p>
      </article>
      {canGenerate && (
        <button
          className="mingli-time-expand"
          disabled={agentGenerating}
          onClick={() => onGenerateAgent?.("STRUCTURE")}
          type="button"
        >
          {agentGenerating ? "正在判断原局总纲…" : "先断原局总纲"}
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

export function MingliFocusedReadingLayer({
  actionsVisible,
  agentError,
  agentGenerating,
  generationAvailable,
  layer,
  onExpandTime,
  onGenerateAgent,
  passes,
  stage,
}: {
  actionsVisible: boolean;
  agentError: string | null;
  agentGenerating: boolean;
  generationAvailable: boolean;
  layer: MingliReadingLayer;
  onExpandTime: () => void;
  onGenerateAgent?: (focus: MingliFocus) => void;
  passes: MingliFocusedPassResult[];
  stage: MingliStageProjection;
}) {
  const byFocus = new Map(passes.map((item) => [item.focus, item]));
  const selected = layer === "principle"
    ? [byFocus.get("STRUCTURE")]
    : layer === "image"
      ? [byFocus.get("LIFE_IMAGE_PERSONALITY")]
      : layer === "themes"
        ? [byFocus.get("CAREER_WEALTH"), byFocus.get("RELATIONSHIP_FAMILY")]
        : [byFocus.get("TIMING")];
  const complete = selected.filter(
    (item): item is MingliFocusedPassResult => item !== undefined,
  );
  const requestedFocuses: MingliFocus[] = layer === "principle"
    ? ["STRUCTURE"]
    : layer === "image"
      ? ["LIFE_IMAGE_PERSONALITY"]
      : layer === "themes"
        ? ["CAREER_WEALTH", "RELATIONSHIP_FAMILY"]
        : ["TIMING"];
  const missing = requestedFocuses.filter((focus) => !byFocus.has(focus));
  const hasReviewFlag = complete.some((item) => item.normalization_codes.length > 0)
    || (layer !== "principle"
      && (byFocus.get("STRUCTURE")?.normalization_codes.length ?? 0) > 0);
  const heading = {
    principle: ["理法枝 · 原局总纲", `${stage.display_name}的命局主线`],
    image: ["象法叶 · 生命意象", `${stage.display_name}的性情与生命意象`],
    themes: ["应事花 · 人生主题", `${stage.display_name}的事业、财富与关系`],
    timing: ["应期果 · 时间趋势", `${stage.display_name}的当前岁运`],
  }[layer];
  return (
    <div className="mingli-reading-layer">
      <FocusedLayerHeading
        eyebrow={heading[0]}
        title={heading[1]}
        status="本地模型分层初断 · 待持续校准"
      />
      {complete.map((item) => (
        <article className="mingli-reading-focus" key={item.focus}>
          <small>{focusedPassLabel(item.focus)}</small>
          <FocusedPassText text={item.normalized_text} />
        </article>
      ))}
      {missing.map((focus) => (
        <article className="mingli-reading-focus" key={focus}>
          <small>{focusedPassLabel(focus)}</small>
          <strong>这一问还没有生成</strong>
          <p>只会提交本层所需的命盘事实，并沿用已经保存的原局总纲。</p>
          {actionsVisible && generationAvailable && onGenerateAgent !== undefined && (
            <button
              className="mingli-time-expand"
              disabled={agentGenerating}
              onClick={() => onGenerateAgent(focus)}
              type="button"
            >
              {agentGenerating ? "阿布正在判断…" : `继续看${focusedPassLabel(focus)}`}
            </button>
          )}
        </article>
      ))}
      {actionsVisible && layer === "timing" && stage.stage_mode === "NATAL_4" && (
        <button className="mingli-time-expand" onClick={onExpandTime} type="button">
          展开当前大运与流年舞台
        </button>
      )}
      {hasReviewFlag && (
        <p className="mingli-reading-boundary">
          本段已触发本地边界标记，请把它视为可继续校准的初断，不作为定论。
        </p>
      )}
      {agentError && (
        <p className="mingli-reading-boundary" role="alert">
          本次专问没有完整返回，请稍后再试；已经保存的层次不会受到影响。
        </p>
      )}
    </div>
  );
}

function FocusedLayerHeading({
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

function FocusedPassText({ text }: { text: string }) {
  return (
    <div className="mingli-principle-lines">
      {text.split("\n").filter(Boolean).map((line, index) => (
        <p key={`${index}:${line.slice(0, 16)}`}>{line}</p>
      ))}
    </div>
  );
}

function focusedPassLabel(focus: MingliFocus): string {
  return {
    STRUCTURE: "原局结构",
    LIFE_IMAGE_PERSONALITY: "生命意象与性情",
    CAREER_WEALTH: "事业与财富",
    RELATIONSHIP_FAMILY: "关系与家庭",
    TIMING: "当前大运与流年",
  }[focus];
}
