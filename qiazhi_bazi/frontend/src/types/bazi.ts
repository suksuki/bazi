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
  /** 结构化意志，如 UPDATE_PHYSICS_PARAM */
  decision_kinds?: string[];
  /** UPDATE_PHYSICS_PARAM 时写入 physics / interaction 的键值 */
  physics_param_payload?: Record<string, unknown>;
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

/** 个人命盘实例上的柔性能量干预（不修改全局 physics_interaction_params） */
export type ManualEnergyPatchEntry = {
  delta_by_deity: Record<string, number>;
  param_key?: string;
  suggested_value?: number;
  reason?: string;
  confirmed_at: string;
  source_card_id?: string;
};

export type ManualEnergyPatchState = {
  /** 协议版本（避免使用字段名 schema） */
  patch_protocol?: string;
  seed_hash: string;
  entries: ManualEnergyPatchEntry[];
};

/** 与 Seed Hash 绑定的持久化侧车：断语归档等 */
export type SemanticVerdictArchiveEntry = {
  id: string;
  text: string;
  seed_hash: string;
  confirmed_at: string;
  source_card_id?: string;
};

/** persistence_layer 侧车：结构化意志（与 semantic_verdicts 并列） */
export type PersistenceConfirmedPhysicsWill = {
  verdict_id?: string;
  kinds?: string[];
  payload?: Record<string, unknown>;
};

export type PersistenceLayer = {
  persistence_protocol?: string;
  semantic_verdicts?: SemanticVerdictArchiveEntry[];
  confirmed_verdicts?: PersistenceConfirmedPhysicsWill[];
  /** 意志归档时的大运锚；与当前 temporal / 请求 dayun 不一致时后端提示复核 */
  will_temporal_anchor_dayun?: string;
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
  verdict_anchor_layer?: {
    narrative_version_id?: string;
    assertions?: VerdictAssertionAnchor[];
    /** 终审 LLM 整合后的主判词（无指纹注释；断言区首位展示） */
    final_verdict?: string;
    /** 物理预判 Markdown 骨架：由 VF 折叠，Orchestrator 每轮刷新 */
    verdict_skeleton?: string;
  };
  /** 强模型可选回写；与终判 JSON 顶级 reasoning_feedback_loop 对齐 */
  reasoning_feedback_loop?: unknown;
  /** 当前生辰指纹下、用户对十神分值的柔性加减（引擎重算后仍按 seed 合并回灌） */
  manual_energy_patch?: ManualEnergyPatchState | null;
  /** 用户确认的语义断语归档（与 seed_hash 强绑定） */
  persistence_layer?: PersistenceLayer | null;
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
