import { deriveIncomeStabilityInference } from "@/lib/v19/incomeStabilityInference";
import type { IncomeStabilityInferenceBundle, IncomeStabilityInferenceSignal } from "@/lib/v19/incomeStabilityInferenceTypes";
import type { BirthInput, ChartStructureOk, ChartStructureResult } from "@/lib/v19/chartStructureTypes";
import { evaluateChartStructure } from "@/lib/v19/chartStructureEngine";
import type {
  ChartStructureSummaryProps,
  EvidenceCardListProps,
  InferenceSignalListProps,
  ReplayCardProps,
  ResultCardProps,
  SignalTagCategory,
  SignalTagProps,
} from "./types";

export type OracleComputedState =
  | {
      status: "ok";
      chart: ChartStructureOk;
      inference: IncomeStabilityInferenceBundle;
      chartSummary: ChartStructureSummaryProps;
      inferenceSignals: InferenceSignalListProps;
      result: ResultCardProps;
      evidence: EvidenceCardListProps;
      replay: ReplayCardProps;
    }
  | {
      status: "unsupported";
      reason: string;
      chartResult: ChartStructureResult;
    };

const STRUCTURE_VERSION = "v19.chart_structure.p1";
const INFERENCE_VERSION = "v19.income_stability.p2";
const CONTRACT_VERSION = "v19.local_static_contract.mock";

export type InferenceInput = {
  chart: ChartStructureOk;
};

export function computeOracleStateFromBirthInput(input: BirthInput): OracleComputedState {
  const chartResult = evaluateChartStructure(input);

  if (chartResult.status !== "ok") {
    return {
      status: "unsupported",
      reason: chartResult.reason,
      chartResult,
    };
  }

  const inference = deriveOracleInference({ chart: chartResult });

  return {
    status: "ok",
    chart: chartResult,
    inference,
    chartSummary: toChartSummary(chartResult),
    inferenceSignals: toInferenceSignals(inference),
    result: toResultCard(inference),
    evidence: toEvidenceCards(inference),
    replay: toReplayCard(chartResult, inference),
  };
}

function deriveOracleInference(input: InferenceInput): IncomeStabilityInferenceBundle {
  // TODO(P5): extend to TimeContext after P4 has been accepted as context-only.
  return deriveIncomeStabilityInference(input.chart);
}

function toChartSummary(chart: ChartStructureOk): ChartStructureSummaryProps {
  return {
    maxVisibleSignals: 5,
    signals: chart.chart_structure_summary.map<SignalTagProps>((signal) => ({
      label: {
        zh: signal.label,
        en: signal.label,
        ko: signal.label,
      },
      value: signal.value,
      category: mapChartSignalCategory(signal.key),
      source: {
        sourceType: signal.source === "calendar" ? "core_feature" : "structure",
        sourceKey: signal.key,
        sourceVersion: STRUCTURE_VERSION,
      },
    })),
  };
}

function toInferenceSignals(inference: IncomeStabilityInferenceBundle): InferenceSignalListProps {
  return {
    defaultCollapsed: true,
    signals: inference.signals.map((signal) => ({
      signalKey: signal.key,
      label: {
        zh: signal.key,
        en: signal.key,
        ko: signal.key,
      },
      value: signal.value,
      category: mapInferenceSignalCategory(signal.key),
      shortReason: {
        zh: sourceSummary(signal),
        en: sourceSummary(signal),
        ko: sourceSummary(signal),
      },
      sources: signal.sources.map((source) => ({
        sourceType: source.source === "ten_god_counts" ? "inference" : "structure",
        sourceKey: source.path,
        sourceVersion: source.source === "ten_god_counts" ? INFERENCE_VERSION : STRUCTURE_VERSION,
      })),
      expandable: true,
    })),
  };
}

function toResultCard(inference: IncomeStabilityInferenceBundle): ResultCardProps {
  const incomeStability = findSignal(inference, "income_stability");
  const volatility = findSignal(inference, "volatility");

  return {
    trust: {
      verifierStatus: "passed",
      confidence: undefined,
      evidenceCount: inference.signals.length,
      contractHash: "local-static-p3",
      schemaVersion: INFERENCE_VERSION,
      mappingVersion: "local_adapter.v1",
      engineVersion: STRUCTURE_VERSION,
      verifierVersion: "local_static_verifier.mock",
    },
    summary: {
      maxLines: 2,
      items: [
        {
          key: "income_stability",
          label: { zh: "income_stability", en: "income_stability", ko: "income_stability" },
          value: incomeStability.value,
          sources: [{ sourceType: "inference", sourceKey: "signals.income_stability", sourceVersion: INFERENCE_VERSION }],
        },
        {
          key: "volatility",
          label: { zh: "volatility", en: "volatility", ko: "volatility" },
          value: volatility.value,
          sources: [{ sourceType: "inference", sourceKey: "signals.volatility", sourceVersion: INFERENCE_VERSION }],
        },
      ],
    },
    uncertainty: [
      {
        label: { zh: "structure_binding", en: "structure_binding", ko: "structure_binding" },
        value: findSignal(inference, "structure_binding").value,
        category: "uncertainty",
        source: {
          sourceType: "inference",
          sourceKey: "signals.structure_binding",
          sourceVersion: INFERENCE_VERSION,
        },
      },
    ],
    risk: [
      {
        label: { zh: "wealth_accessibility", en: "wealth_accessibility", ko: "wealth_accessibility" },
        value: findSignal(inference, "wealth_accessibility").value,
        category: "risk",
        source: {
          sourceType: "inference",
          sourceKey: "signals.wealth_accessibility",
          sourceVersion: INFERENCE_VERSION,
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
          zh: "P3 local prototype does not support follow-up.",
          en: "P3 local prototype does not support follow-up.",
          ko: "P3 local prototype does not support follow-up.",
        },
      },
    ],
  };
}

function toEvidenceCards(inference: IncomeStabilityInferenceBundle): EvidenceCardListProps {
  return {
    visibleCount: 2,
    expandable: true,
    evidence: inference.signals.map((signal) => ({
      evidenceId: `ev_${signal.key}`,
      label: {
        zh: signal.key,
        en: signal.key,
        ko: signal.key,
      },
      signalKey: signal.key,
      detail: {
        zh: `${signal.key} = ${signal.value}`,
        en: `${signal.key} = ${signal.value}`,
        ko: `${signal.key} = ${signal.value}`,
      },
      strength: signal.value === "high" || signal.value === "stable" ? "high" : signal.value === "low" || signal.value === "unstable" ? "low" : "medium",
      verifierStatus: "passed",
      sources: signal.sources.map((source) => ({
        sourceType: source.source === "ten_god_counts" ? "inference" : "structure",
        sourceKey: source.path,
        sourceVersion: source.source === "ten_god_counts" ? INFERENCE_VERSION : STRUCTURE_VERSION,
      })),
    })),
  };
}

function toReplayCard(chart: ChartStructureOk, inference: IncomeStabilityInferenceBundle): ReplayCardProps {
  const predictionId = `local_p3_${chart.input.year}_${chart.input.month}_${chart.input.day}_${chart.input.hour}`;

  return {
    predictionId,
    contractHash: "local-static-p3",
    verifierStatus: "passed",
    publicSafe: true,
    anchors: [
      {
        label: { zh: "Chart Structure Engine", en: "Chart Structure Engine", ko: "Chart Structure Engine" },
        value: STRUCTURE_VERSION,
        source: { sourceType: "structure", sourceKey: "chart_structure_engine", sourceVersion: STRUCTURE_VERSION },
      },
      {
        label: { zh: "Inference Adapter", en: "Inference Adapter", ko: "Inference Adapter" },
        value: INFERENCE_VERSION,
        source: { sourceType: "inference", sourceKey: inference.supported_theme, sourceVersion: INFERENCE_VERSION },
      },
      {
        label: { zh: "Contract", en: "Contract", ko: "Contract" },
        value: CONTRACT_VERSION,
        source: { sourceType: "contract", sourceKey: "local_static_contract", sourceVersion: CONTRACT_VERSION },
      },
      {
        label: { zh: "Verifier", en: "Verifier", ko: "Verifier" },
        value: "passed",
        source: { sourceType: "verifier", sourceKey: "local_static_verifier", sourceVersion: "mock" },
      },
    ],
  };
}

function findSignal(inference: IncomeStabilityInferenceBundle, key: IncomeStabilityInferenceBundle["signals"][number]["key"]) {
  const signal = inference.signals.find((candidate) => candidate.key === key);
  if (!signal) {
    throw new Error(`missing income stability signal: ${key}`);
  }

  return signal;
}

function mapChartSignalCategory(key: ChartStructureOk["chart_structure_summary"][number]["key"]): SignalTagCategory {
  if (key === "day_master") {
    return "day_master";
  }

  if (key === "branch_relation_count") {
    return "structure";
  }

  if (key === "strength_tendency") {
    return "structure";
  }

  if (key === "dominant_element") {
    return "ten_god";
  }

  return "verification";
}

function mapInferenceSignalCategory(key: IncomeStabilityInferenceSignal["key"]): SignalTagCategory {
  if (key === "self_capacity") {
    return "day_master";
  }

  if (key === "wealth_presence" || key === "wealth_accessibility") {
    return "ten_god";
  }

  if (key === "volatility") {
    return "conflict";
  }

  if (key === "structure_binding") {
    return "structure";
  }

  return "verification";
}

function sourceSummary(signal: IncomeStabilityInferenceSignal): string {
  return signal.sources.map((source) => source.path).join(" + ");
}
