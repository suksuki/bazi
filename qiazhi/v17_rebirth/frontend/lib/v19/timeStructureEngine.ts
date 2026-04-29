import type { ChartStructureOk, EarthlyBranch, Gender, HeavenlyStem } from "./chartStructureTypes";
import type { FlowYear, LuckCycle, LuckCycleDirection, TimeRelations } from "./timeStructureTypes";

const HEAVENLY_STEMS: HeavenlyStem[] = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"];

const EARTHLY_BRANCHES: EarthlyBranch[] = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];

const SIX_COMBINATIONS: Array<[EarthlyBranch, EarthlyBranch]> = [
  ["子", "丑"],
  ["寅", "亥"],
  ["卯", "戌"],
  ["辰", "酉"],
  ["巳", "申"],
  ["午", "未"],
];

const SIX_CLASHES: Array<[EarthlyBranch, EarthlyBranch]> = [
  ["子", "午"],
  ["丑", "未"],
  ["寅", "申"],
  ["卯", "酉"],
  ["辰", "戌"],
  ["巳", "亥"],
];

const THREE_HARMONIES: Array<[EarthlyBranch, EarthlyBranch, EarthlyBranch]> = [
  ["申", "子", "辰"],
  ["亥", "卯", "未"],
  ["寅", "午", "戌"],
  ["巳", "酉", "丑"],
];

export function deriveFlowYear(chart: ChartStructureOk, selectedYear: number): FlowYear {
  const pillar = getFlowYearPillar(selectedYear);

  return {
    year: selectedYear,
    pillar,
    relations_with_natal: deriveRelationsWithNatal(chart, pillar.branch),
  };
}

export function deriveLuckCycles(chart: ChartStructureOk, options: { gender: Gender; cycleCount?: number }): {
  direction: LuckCycleDirection;
  start_age_note: string;
  cycles: LuckCycle[];
} {
  const direction = getLuckCycleDirection(chart.pillars.year.stem, options.gender);
  const cycleCount = options.cycleCount ?? 8;
  const monthPillarIndex = getPillarCycleIndex(chart.pillars.month.stem, chart.pillars.month.branch);

  return {
    direction,
    start_age_note: "approximate_start_age_pending_solar_term_engine",
    cycles: Array.from({ length: cycleCount }, (_, index) => {
      const cycleIndex = mod(monthPillarIndex + (direction === "forward" ? index + 1 : -(index + 1)), 60);
      const startAge = 8 + index * 10;

      return {
        start_age: startAge,
        end_age: startAge + 9,
        pillar: {
          stem: HEAVENLY_STEMS[cycleIndex % 10],
          branch: EARTHLY_BRANCHES[cycleIndex % 12],
        },
        relations_with_natal: deriveRelationsWithNatal(chart, EARTHLY_BRANCHES[cycleIndex % 12]),
      };
    }),
  };
}

function getFlowYearPillar(year: number): FlowYear["pillar"] {
  const cycleIndex = mod(year - 4, 60);

  return {
    stem: HEAVENLY_STEMS[cycleIndex % 10],
    branch: EARTHLY_BRANCHES[cycleIndex % 12],
  };
}

function getLuckCycleDirection(yearStem: HeavenlyStem, gender: Gender): LuckCycleDirection {
  const yangStem = ["甲", "丙", "戊", "庚", "壬"].includes(yearStem);
  return (yangStem && gender === "male") || (!yangStem && gender === "female") ? "forward" : "reverse";
}

function getPillarCycleIndex(stem: HeavenlyStem, branch: EarthlyBranch): number {
  for (let index = 0; index < 60; index += 1) {
    if (HEAVENLY_STEMS[index % 10] === stem && EARTHLY_BRANCHES[index % 12] === branch) {
      return index;
    }
  }

  return 0;
}

function deriveRelationsWithNatal(chart: ChartStructureOk, flowYearBranch: EarthlyBranch): TimeRelations {
  const natalBranches = Object.values(chart.pillars).map((pillar) => pillar.branch);
  const clashes = new Set<string>();
  const combinations = new Set<string>();

  for (const pair of SIX_CLASHES) {
    if (pair.includes(flowYearBranch) && natalBranches.some((branch) => branch !== flowYearBranch && pair.includes(branch))) {
      clashes.add(pair.join(""));
    }
  }

  for (const pair of SIX_COMBINATIONS) {
    if (pair.includes(flowYearBranch) && natalBranches.some((branch) => branch !== flowYearBranch && pair.includes(branch))) {
      combinations.add(pair.join(""));
    }
  }

  for (const harmony of THREE_HARMONIES) {
    if (!harmony.includes(flowYearBranch)) {
      continue;
    }

    const natalHitCount = harmony.filter((branch) => branch !== flowYearBranch && natalBranches.includes(branch)).length;
    if (natalHitCount >= 2) {
      combinations.add(harmony.join(""));
    }
  }

  return {
    clashes: [...clashes],
    combinations: [...combinations],
  };
}

function mod(value: number, divisor: number): number {
  return ((value % divisor) + divisor) % divisor;
}
