export type Lang = "ZH" | "EN" | "KO";

export type Pillar = {
  stem: string;
  branch: string;
  energy_value?: number;
};

export type FourPillars = {
  year: Pillar;
  month: Pillar;
  day: Pillar;
  hour: Pillar;
};

export type ConflictPoint = {
  id?: string;
  kind: string;
  positions: string[];
  detail: string;
  source?: string;
};

export type PluginSelectionTraceEntry = {
  plugin_id: string;
  layer_id: string;
  status: string;
  reason: string;
};

/** v2 记忆体：用户签发归档 */
export type ConfirmedVerdictRecord = {
  verdict_id: string;
  body_excerpt: string;
  confirmed_at: string;
  source_metadata_hash: string;
  evidence_refs: string[];
  /** 签发所用 LLM model id（与 llm_meta.model_name 对齐） */
  model_id?: string;
  /** 语义裁决后不再展示的 Decision Inbox 卡片 id（如 inbox-sanhe-丑巳酉） */
  suppressed_inbox_card_ids?: string[];
};

/** 终判再生审计（与后端 VerdictRegenerationEvent 对齐） */
export type VerdictRegenerationEvent = {
  occurred_at?: string;
  reason?: string;
  trigger?: string;
  model_id?: string;
  version_id?: string;
  previous_version_id?: string;
};

/** 每次终判生成的模型指纹（与后端 VerdictModelStamp 对齐） */
export type VerdictModelStamp = {
  occurred_at?: string;
  model_id?: string;
  version_id?: string;
};

/** 与后端 history_context.learning_annotation 对齐（entries 由前端合并追加） */
export type LearningAnnotationEntry = {
  occurred_at?: string;
  kind?: string;
  version_id?: string;
  model_id?: string;
  previous_version_id?: string;
  reason?: string;
  trigger?: string;
  diff?: {
    previous_verdict_excerpt?: string;
    new_verdict_excerpt?: string;
    previous_assertion_ids?: string[];
    new_assertion_ids?: string[];
  };
};

export type LearningAnnotation = {
  schema?: string;
  entries?: LearningAnnotationEntry[];
};

export type VerdictAssertionAnchor = {
  assertion_id?: string;
  text?: string;
  evidence_refs?: string[];
};

export type InferenceTraceStep = {
  step_index?: number;
  layer_id?: string;
  plugin_id?: string;
  input_summary?: string;
  match_score?: number | null;
  output_summary?: string;
  arbitration_note?: string;
};

export type BaziMetadata = {
  version: string;
  pillars: FourPillars | null;
  conflict_matrix: { points: ConflictPoint[] };
  flow_state: string;
  notes: string;
  plugin_selection_trace?: PluginSelectionTraceEntry[];
  /** 记忆体扩展版本 */
  memory_schema_version?: string;
  temporal_context?: Record<string, unknown>;
  history_context?: {
    confirmed_verdicts?: ConfirmedVerdictRecord[];
    regeneration_events?: VerdictRegenerationEvent[];
    verdict_model_stamps?: VerdictModelStamp[];
    learning_annotation?: LearningAnnotation;
  };
  inference_trace?: { version?: string; steps?: InferenceTraceStep[] };
  verdict_anchor_layer?: { narrative_version_id?: string; assertions?: VerdictAssertionAnchor[] };
  /** 强模型可选回写；与终判 JSON 顶级 reasoning_feedback_loop 对齐 */
  reasoning_feedback_loop?: unknown;
};

export type TimelineSnapshot = {
  dayun: string;
  liunian: string;
  reference_year: number;
};

export type DecisionStep = {
  id: string;
  title: string;
  answer?: string;
  createdAt: string;
};
