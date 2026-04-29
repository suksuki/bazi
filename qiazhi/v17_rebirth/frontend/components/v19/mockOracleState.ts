import type { OracleUiState } from "./types";

const reviewedRulesReason = {
  zh: "尚未由 reviewed rules 支持",
  en: "not yet supported by reviewed rules",
  ko: "검토된 규칙에서 아직 지원되지 않습니다",
};

export const mockOracleState: OracleUiState = {
  state: "replay_ready",
  locale: "en",
  birthInput: {
    date: "1990-05-12",
    time: "10:30",
    place: "Beijing, China",
    timezone: "UTC+8",
    calendarType: "solar",
    completeness: "complete",
  },
  chart: {
    maxVisibleSignals: 5,
    signals: [
      {
        label: { zh: "日主", en: "Day Master", ko: "일간" },
        value: "weak",
        category: "day_master",
        confidence: 0.72,
        source: {
          sourceType: "strength",
          sourceKey: "day_master_state.tendency",
          sourceVersion: "v19.strength.v1",
        },
      },
      {
        label: { zh: "结构", en: "Structure", ko: "구조" },
        value: "unstable",
        category: "structure",
        confidence: 0.68,
        source: {
          sourceType: "structure",
          sourceKey: "structural_stability.state",
          sourceVersion: "v19.structure.v1",
        },
      },
      {
        label: { zh: "比劫与财", en: "Peer vs Wealth", ko: "비겁 대 재성" },
        value: "wealth_weak",
        category: "conflict",
        confidence: 0.7,
        source: {
          sourceType: "inference",
          sourceKey: "internal_conflicts.peer_vs_wealth",
          sourceVersion: "v19.inference_schema.v1",
        },
      },
      {
        label: { zh: "流动", en: "Flow", ko: "흐름" },
        value: "blocked",
        category: "flow",
        confidence: 0.64,
        source: {
          sourceType: "inference",
          sourceKey: "energy_flow.output_to_wealth",
          sourceVersion: "v19.inference_schema.v1",
        },
      },
      {
        label: { zh: "季节", en: "Season", ko: "계절" },
        value: "late_spring",
        category: "structure",
        confidence: 0.83,
        source: {
          sourceType: "core_feature",
          sourceKey: "month_command.season",
          sourceVersion: "v19.core_feature.v1",
        },
      },
    ],
  },
  inference: {
    defaultCollapsed: true,
    signals: [
      {
        signalKey: "day_master_state.tendency",
        label: { zh: "日主状态", en: "Day master state", ko: "일간 상태" },
        value: "leaning_weak",
        category: "day_master",
        confidence: 0.72,
        shortReason: {
          zh: "通根与得令支持不足",
          en: "Root and month support are limited",
          ko: "통근과 월령 지원이 제한적입니다",
        },
        sources: [
          {
            sourceType: "strength",
            sourceKey: "root_strength",
            sourceVersion: "v19.strength.v1",
          },
          {
            sourceType: "strength",
            sourceKey: "month_command",
            sourceVersion: "v19.strength.v1",
          },
        ],
        expandable: true,
      },
      {
        signalKey: "structural_stability.state",
        label: { zh: "结构稳定性", en: "Structural stability", ko: "구조 안정성" },
        value: "conflicted",
        category: "structure",
        confidence: 0.68,
        shortReason: {
          zh: "合冲信号同时存在",
          en: "Combination and clash signals are both present",
          ko: "합과 충 신호가 함께 존재합니다",
        },
        sources: [
          {
            sourceType: "structure",
            sourceKey: "relation_hits.combination",
            sourceVersion: "v19.structure.v1",
          },
          {
            sourceType: "structure",
            sourceKey: "relation_hits.clash",
            sourceVersion: "v19.structure.v1",
          },
        ],
        expandable: true,
      },
      {
        signalKey: "internal_conflicts.peer_vs_wealth",
        label: { zh: "内部冲突", en: "Internal conflict", ko: "내부 충돌" },
        value: "peer_overwhelms_wealth",
        category: "conflict",
        confidence: 0.7,
        shortReason: {
          zh: "比劫压力高于财星承载",
          en: "Peer pressure exceeds wealth support",
          ko: "비겁 압력이 재성 지지보다 큽니다",
        },
        sources: [
          {
            sourceType: "inference",
            sourceKey: "internal_conflicts.peer_vs_wealth.direction",
            sourceVersion: "v19.inference_schema.v1",
          },
        ],
        expandable: true,
      },
      {
        signalKey: "energy_flow.output_to_wealth",
        label: { zh: "能量流动", en: "Energy flow", ko: "에너지 흐름" },
        value: "blocked",
        category: "flow",
        confidence: 0.64,
        shortReason: {
          zh: "食伤到财的路径未完全形成",
          en: "The output-to-wealth path is not fully formed",
          ko: "식상에서 재성으로 가는 경로가 완전히 형성되지 않았습니다",
        },
        sources: [
          {
            sourceType: "inference",
            sourceKey: "energy_flow.output_to_wealth",
            sourceVersion: "v19.inference_schema.v1",
          },
        ],
        expandable: true,
      },
    ],
  },
  themes: [
    {
      themeId: "wealth_structure",
      label: { zh: "财富结构", en: "Wealth Structure", ko: "재물 구조" },
      enabled: true,
      requiredSignals: ["internal_conflicts.peer_vs_wealth"],
    },
    {
      themeId: "income_stability",
      label: { zh: "收入稳定性", en: "Income Stability", ko: "수입 안정성" },
      enabled: true,
      requiredSignals: ["structural_stability.state"],
    },
    {
      themeId: "risk_opportunity",
      label: { zh: "风险与机会", en: "Risk & Opportunity", ko: "위험과 기회" },
      enabled: true,
      requiredSignals: ["uncertainty_sources"],
    },
    {
      themeId: "career",
      label: { zh: "事业", en: "Career", ko: "직업" },
      enabled: false,
      disabledReason: reviewedRulesReason,
    },
    {
      themeId: "relationship",
      label: { zh: "感情", en: "Relationship", ko: "관계" },
      enabled: false,
      disabledReason: reviewedRulesReason,
    },
    {
      themeId: "health",
      label: { zh: "健康", en: "Health", ko: "건강" },
      enabled: false,
      disabledReason: reviewedRulesReason,
    },
    {
      themeId: "full_chart_general_reading",
      label: { zh: "完整命盘总论", en: "Full Chart General Reading", ko: "전체 명식 총론" },
      enabled: false,
      disabledReason: reviewedRulesReason,
    },
  ],
  selectedThemeId: "income_stability",
  result: {
    trust: {
      verifierStatus: "passed",
      confidence: 0.7,
      evidenceCount: 8,
      contractHash: "0x7a3f...9c2d",
      schemaVersion: "v1.9.2",
      mappingVersion: "v1.4.0",
      engineVersion: "v19.core.v1",
      verifierVersion: "v19.verifier.mock",
    },
    summary: {
      maxLines: 2,
      items: [
        {
          key: "income_stability",
          label: { zh: "收入稳定性", en: "Income Stability", ko: "수입 안정성" },
          value: "low",
          sources: [
            {
              sourceType: "contract",
              sourceKey: "result.summary.income_stability",
              sourceVersion: "v19.contract.mock",
            },
          ],
        },
        {
          key: "volatility",
          label: { zh: "波动性", en: "Volatility", ko: "변동성" },
          value: "high",
          sources: [
            {
              sourceType: "mapping",
              sourceKey: "wealth.structural_stability_to_stability",
              sourceVersion: "v19.mapping_registry.v1",
            },
          ],
        },
      ],
    },
    uncertainty: [
      {
        label: { zh: "不确定性", en: "Uncertainty", ko: "불확실성" },
        value: "medium",
        category: "uncertainty",
        confidence: 0.62,
        source: {
          sourceType: "inference",
          sourceKey: "uncertainty_sources.mixed_signal",
          sourceVersion: "v19.inference_schema.v1",
        },
      },
    ],
    risk: [
      {
        label: { zh: "复核建议", en: "Review", ko: "검토" },
        value: "major_decisions",
        category: "risk",
        source: {
          sourceType: "verifier",
          sourceKey: "review_recommended",
          sourceVersion: "v19.verifier.mock",
        },
      },
    ],
    actions: [
      { type: "feedback", enabled: true },
      { type: "replay", enabled: true },
      {
        type: "ask_followup",
        enabled: false,
        reason: {
          zh: "原型阶段暂不支持追问",
          en: "follow-up questions are not enabled in this prototype",
          ko: "이 프로토타입에서는 후속 질문을 지원하지 않습니다",
        },
      },
    ],
  },
  evidence: {
    visibleCount: 2,
    expandable: true,
    evidence: [
      {
        evidenceId: "ev_day_master_weak",
        label: { zh: "日主承载偏弱", en: "Day Master Support Weak", ko: "일간 지지 약함" },
        signalKey: "day_master_state.tendency",
        detail: {
          zh: "Signal: day_master_state = leaning_weak. Effect: support capacity = limited.",
          en: "Signal: day_master_state = leaning_weak. Effect: support capacity = limited.",
          ko: "Signal: day_master_state = leaning_weak. Effect: support capacity = limited.",
        },
        strength: "high",
        verifierStatus: "passed",
        sources: [
          {
            sourceType: "strength",
            sourceKey: "day_master_state.tendency",
            sourceVersion: "v19.strength.v1",
          },
        ],
      },
      {
        evidenceId: "ev_resource_limited",
        label: { zh: "资源支持有限", en: "Resource Limited", ko: "자원 제한" },
        signalKey: "ten_god_structure.seal",
        detail: {
          zh: "Signal: seal_support = low. Effect: stabilization support = limited.",
          en: "Signal: seal_support = low. Effect: stabilization support = limited.",
          ko: "Signal: seal_support = low. Effect: stabilization support = limited.",
        },
        strength: "medium",
        verifierStatus: "passed",
        sources: [
          {
            sourceType: "inference",
            sourceKey: "ten_god_structure.seal.strength",
            sourceVersion: "v19.inference_schema.v1",
          },
        ],
      },
      {
        evidenceId: "ev_flow_blocked",
        label: { zh: "转化路径受阻", en: "Flow Path Blocked", ko: "흐름 경로 차단" },
        signalKey: "energy_flow.output_to_wealth",
        detail: {
          zh: "Signal: output_to_wealth = blocked. Effect: conversion path = weak.",
          en: "Signal: output_to_wealth = blocked. Effect: conversion path = weak.",
          ko: "Signal: output_to_wealth = blocked. Effect: conversion path = weak.",
        },
        strength: "medium",
        verifierStatus: "warning",
        sources: [
          {
            sourceType: "inference",
            sourceKey: "energy_flow.output_to_wealth",
            sourceVersion: "v19.inference_schema.v1",
          },
        ],
      },
    ],
  },
  feedback: {
    predictionId: "pr_v19_mock_8f1a2b3c4d5e",
    allowedValues: ["accurate", "partly_accurate", "unclear", "wrong", "unsafe_or_unsupported"],
    submitted: false,
  },
  replay: {
    predictionId: "pr_v19_mock_8f1a2b3c4d5e",
    contractHash: "0x7a3f4b8e9c2d",
    verifierStatus: "passed",
    publicSafe: true,
    anchors: [
      {
        label: { zh: "Core 引擎", en: "Core Engine", ko: "Core 엔진" },
        value: "v19.core.v1",
        source: { sourceType: "core_feature", sourceKey: "engine_version", sourceVersion: "v19.core.v1" },
      },
      {
        label: { zh: "Inference Schema", en: "Inference Schema", ko: "Inference Schema" },
        value: "v1.9.2",
        source: { sourceType: "inference", sourceKey: "schema_version", sourceVersion: "v1.9.2" },
      },
      {
        label: { zh: "Mapping Registry", en: "Mapping Registry", ko: "Mapping Registry" },
        value: "v1.4.0",
        source: { sourceType: "mapping", sourceKey: "mapping_registry_version", sourceVersion: "v1.4.0" },
      },
      {
        label: { zh: "Verifier", en: "Verifier", ko: "Verifier" },
        value: "passed",
        source: { sourceType: "verifier", sourceKey: "verifier_status", sourceVersion: "v19.verifier.mock" },
      },
    ],
  },
};

