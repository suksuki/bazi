import type {
  BranchRelation,
  ChartStructureOk,
  FiveElement,
  PillarName,
  StrengthTendency,
} from "./chartStructureTypes";
import type {
  IncomeStabilityInferenceBundle,
  IncomeStabilityInferenceSignal,
  IncomeStabilitySignalValue,
} from "./incomeStabilityInferenceTypes";

const CONTROLS: Record<FiveElement, FiveElement> = {
  wood: "earth",
  earth: "water",
  water: "fire",
  fire: "metal",
  metal: "wood",
};

const PILLAR_NAMES: PillarName[] = ["year", "month", "day", "hour"];

export function deriveIncomeStabilityInference(chart: ChartStructureOk): IncomeStabilityInferenceBundle {
  const wealthElement = CONTROLS[chart.day_master.element];
  const touchedWealthPillars = findWealthPillars(chart, wealthElement);
  const wealthRelationCounts = countWealthRelations(chart.branch_relations, touchedWealthPillars);
  const clashCount = chart.branch_relations.filter((relation) => relation.type === "six_clash").length;
  const threeHarmonyCount = chart.branch_relations.filter((relation) => relation.type === "three_harmony").length;

  const selfCapacity = mapSelfCapacity(chart.simplified_strength.tendency);
  const wealthPresence = mapWealthPresence(chart.ten_god_counts.direct_wealth + chart.ten_god_counts.indirect_wealth);
  const wealthAccessibility = mapWealthAccessibility({
    wealthPresence,
    clashCount: wealthRelationCounts.clash,
    combinationCount: wealthRelationCounts.combination,
  });
  const volatility = mapVolatility(clashCount);
  const structureBinding = threeHarmonyCount > 0 ? "present" : "none";
  const incomeStability = mapIncomeStability({
    selfCapacity,
    wealthPresence,
    wealthAccessibility,
    volatility,
    structureBinding,
  });

  return {
    status: "ok",
    supported_theme: "income_stability",
    touched_wealth_pillars: touchedWealthPillars,
    signals: [
      {
        key: "self_capacity",
        value: selfCapacity,
        sources: [{ source: "simplified_strength", path: "simplified_strength.tendency" }],
      },
      {
        key: "wealth_presence",
        value: wealthPresence,
        sources: [
          { source: "ten_god_counts", path: "ten_god_counts.direct_wealth" },
          { source: "ten_god_counts", path: "ten_god_counts.indirect_wealth" },
        ],
      },
      {
        key: "wealth_accessibility",
        value: wealthAccessibility,
        sources: [
          { source: "pillars", path: "pillars.*.stem_element|branch_element" },
          { source: "branch_relations", path: "branch_relations[type=six_clash|six_combination]" },
        ],
      },
      {
        key: "volatility",
        value: volatility,
        sources: [{ source: "branch_relations", path: "branch_relations[type=six_clash]" }],
      },
      {
        key: "structure_binding",
        value: structureBinding,
        sources: [{ source: "branch_relations", path: "branch_relations[type=three_harmony]" }],
      },
      {
        key: "income_stability",
        value: incomeStability,
        sources: [
          { source: "simplified_strength", path: "simplified_strength.tendency" },
          { source: "ten_god_counts", path: "ten_god_counts.direct_wealth|indirect_wealth" },
          { source: "branch_relations", path: "branch_relations" },
        ],
      },
    ],
  };
}

function findWealthPillars(chart: ChartStructureOk, wealthElement: FiveElement): PillarName[] {
  return PILLAR_NAMES.filter((name) => {
    const pillar = chart.pillars[name];
    return pillar.stem_element === wealthElement || pillar.branch_element === wealthElement;
  });
}

function countWealthRelations(relations: BranchRelation[], touchedWealthPillars: PillarName[]): {
  clash: number;
  combination: number;
} {
  const touched = new Set(touchedWealthPillars);
  let clash = 0;
  let combination = 0;

  for (const relation of relations) {
    const touchesWealth = relation.pillar_names.some((name) => touched.has(name));
    if (!touchesWealth) {
      continue;
    }

    if (relation.type === "six_clash") {
      clash += 1;
    }

    if (relation.type === "six_combination" || relation.type === "three_harmony") {
      combination += 1;
    }
  }

  return { clash, combination };
}

function mapSelfCapacity(tendency: StrengthTendency): IncomeStabilitySignalValue {
  if (tendency === "strong") {
    return "high";
  }

  if (tendency === "weak") {
    return "low";
  }

  return "medium";
}

function mapWealthPresence(wealthCount: number): IncomeStabilitySignalValue {
  if (wealthCount <= 0) {
    return "none";
  }

  if (wealthCount === 1) {
    return "low";
  }

  if (wealthCount <= 3) {
    return "medium";
  }

  return "high";
}

function mapWealthAccessibility({
  wealthPresence,
  clashCount,
  combinationCount,
}: {
  wealthPresence: IncomeStabilitySignalValue;
  clashCount: number;
  combinationCount: number;
}): IncomeStabilitySignalValue {
  if (wealthPresence === "none") {
    return "not_applicable";
  }

  if (clashCount > 0 && combinationCount > 0) {
    return "conflicted";
  }

  if (clashCount > 0) {
    return "disrupted";
  }

  if (combinationCount > 0) {
    return "bound";
  }

  return "clear";
}

function mapVolatility(clashCount: number): IncomeStabilitySignalValue {
  if (clashCount <= 0) {
    return "low";
  }

  if (clashCount === 1) {
    return "medium";
  }

  return "high";
}

function mapIncomeStability({
  selfCapacity,
  wealthPresence,
  wealthAccessibility,
  volatility,
  structureBinding,
}: {
  selfCapacity: IncomeStabilitySignalValue;
  wealthPresence: IncomeStabilitySignalValue;
  wealthAccessibility: IncomeStabilitySignalValue;
  volatility: IncomeStabilitySignalValue;
  structureBinding: IncomeStabilitySignalValue;
}): IncomeStabilitySignalValue {
  if (wealthPresence === "none" || selfCapacity === "low" || volatility === "high" || wealthAccessibility === "disrupted") {
    return "unstable";
  }

  if (wealthAccessibility === "conflicted") {
    return "mixed";
  }

  if (selfCapacity === "high" && volatility === "low") {
    return "stable";
  }

  if (structureBinding === "present") {
    return "mixed";
  }

  return "mixed";
}
