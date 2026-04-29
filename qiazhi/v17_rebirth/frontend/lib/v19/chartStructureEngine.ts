import type {
  BirthInput,
  BranchRelation,
  ChartStructureOk,
  ChartStructureResult,
  ChartStructureSignal,
  EarthlyBranch,
  FiveElement,
  FiveElementCounts,
  HeavenlyStem,
  Pillar,
  PillarName,
  SimplifiedStrength,
  TenGod,
  TenGodCounts,
  YinYang,
} from "./chartStructureTypes";

const HEAVENLY_STEMS: HeavenlyStem[] = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"];

const EARTHLY_BRANCHES: EarthlyBranch[] = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];

const STEM_META: Record<HeavenlyStem, { element: FiveElement; yinYang: YinYang }> = {
  甲: { element: "wood", yinYang: "yang" },
  乙: { element: "wood", yinYang: "yin" },
  丙: { element: "fire", yinYang: "yang" },
  丁: { element: "fire", yinYang: "yin" },
  戊: { element: "earth", yinYang: "yang" },
  己: { element: "earth", yinYang: "yin" },
  庚: { element: "metal", yinYang: "yang" },
  辛: { element: "metal", yinYang: "yin" },
  壬: { element: "water", yinYang: "yang" },
  癸: { element: "water", yinYang: "yin" },
};

const BRANCH_MAIN_STEM: Record<EarthlyBranch, HeavenlyStem> = {
  子: "癸",
  丑: "己",
  寅: "甲",
  卯: "乙",
  辰: "戊",
  巳: "丙",
  午: "丁",
  未: "己",
  申: "庚",
  酉: "辛",
  戌: "戊",
  亥: "壬",
};

const GENERATES: Record<FiveElement, FiveElement> = {
  wood: "fire",
  fire: "earth",
  earth: "metal",
  metal: "water",
  water: "wood",
};

const CONTROLS: Record<FiveElement, FiveElement> = {
  wood: "earth",
  earth: "water",
  water: "fire",
  fire: "metal",
  metal: "wood",
};

const FIVE_ELEMENTS: FiveElement[] = ["wood", "fire", "earth", "metal", "water"];

const TEN_GODS: TenGod[] = [
  "peer",
  "rob_wealth",
  "eating_god",
  "hurting_officer",
  "indirect_wealth",
  "direct_wealth",
  "seven_killings",
  "direct_officer",
  "indirect_resource",
  "direct_resource",
];

const MONTH_BRANCH_SEQUENCE: EarthlyBranch[] = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"];

const MONTH_START_STEM_BY_YEAR_STEM: Record<HeavenlyStem, HeavenlyStem> = {
  甲: "丙",
  己: "丙",
  乙: "戊",
  庚: "戊",
  丙: "庚",
  辛: "庚",
  丁: "壬",
  壬: "壬",
  戊: "甲",
  癸: "甲",
};

const HOUR_START_STEM_BY_DAY_STEM: Record<HeavenlyStem, HeavenlyStem> = {
  甲: "甲",
  己: "甲",
  乙: "丙",
  庚: "丙",
  丙: "戊",
  辛: "戊",
  丁: "庚",
  壬: "庚",
  戊: "壬",
  癸: "壬",
};

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

const THREE_HARMONIES: Array<{ branches: [EarthlyBranch, EarthlyBranch, EarthlyBranch]; element: FiveElement }> = [
  { branches: ["申", "子", "辰"], element: "water" },
  { branches: ["亥", "卯", "未"], element: "wood" },
  { branches: ["寅", "午", "戌"], element: "fire" },
  { branches: ["巳", "酉", "丑"], element: "metal" },
];

const PILLAR_NAMES: PillarName[] = ["year", "month", "day", "hour"];

export function evaluateChartStructure(input: BirthInput): ChartStructureResult {
  if (input.calendar_type === "lunar") {
    return {
      status: "unsupported",
      input,
      reason: "lunar_calendar_not_supported",
    };
  }

  if (!isValidSolarInput(input)) {
    return {
      status: "unsupported",
      input,
      reason: "invalid_solar_input",
    };
  }

  const yearPillar = getYearPillar(input);
  const monthPillar = getMonthPillar(input, yearPillar.stem);
  const dayPillar = getDayPillar(input);
  const hourPillar = getHourPillar(input.hour, dayPillar.stem);
  const pillars: Record<PillarName, Pillar> = {
    year: yearPillar,
    month: monthPillar,
    day: dayPillar,
    hour: hourPillar,
  };
  const dayMaster = {
    stem: dayPillar.stem,
    element: dayPillar.stem_element,
    yin_yang: dayPillar.stem_yin_yang,
  };
  const fiveElementCounts = countFiveElements(pillars);
  const tenGodCounts = countTenGods(pillars, dayPillar.stem);
  const branchRelations = detectBranchRelations(PILLAR_NAMES.map((name) => ({ pillarName: name, branch: pillars[name].branch })));
  const simplifiedStrength = deriveSimplifiedStrength(pillars, dayPillar.stem);

  return {
    status: "ok",
    input,
    calendar_note: "solar_mvp_approximate_jie_boundaries",
    pillars,
    day_master: dayMaster,
    five_element_counts: fiveElementCounts,
    ten_god_counts: tenGodCounts,
    branch_relations: branchRelations,
    simplified_strength: simplifiedStrength,
    chart_structure_summary: buildChartStructureSummary({
      dayMasterStem: dayPillar.stem,
      dayMasterElement: dayPillar.stem_element,
      fiveElementCounts,
      branchRelations,
      simplifiedStrength,
    }),
  };
}

export function detectBranchRelations(
  branches: Array<{ pillarName: PillarName; branch: EarthlyBranch }>,
): BranchRelation[] {
  const relations: BranchRelation[] = [];

  for (let leftIndex = 0; leftIndex < branches.length; leftIndex += 1) {
    for (let rightIndex = leftIndex + 1; rightIndex < branches.length; rightIndex += 1) {
      const left = branches[leftIndex];
      const right = branches[rightIndex];
      const pair: [EarthlyBranch, EarthlyBranch] = [left.branch, right.branch];

      if (hasPair(SIX_COMBINATIONS, pair)) {
        relations.push({
          type: "six_combination",
          branches: pair,
          pillar_names: [left.pillarName, right.pillarName],
        });
      }

      if (hasPair(SIX_CLASHES, pair)) {
        relations.push({
          type: "six_clash",
          branches: pair,
          pillar_names: [left.pillarName, right.pillarName],
        });
      }
    }
  }

  for (const harmony of THREE_HARMONIES) {
    const hits = harmony.branches
      .map((branch) => branches.find((candidate) => candidate.branch === branch))
      .filter((candidate): candidate is { pillarName: PillarName; branch: EarthlyBranch } => Boolean(candidate));

    if (hits.length === 3) {
      relations.push({
        type: "three_harmony",
        branches: harmony.branches,
        pillar_names: hits.map((hit) => hit.pillarName),
        element: harmony.element,
      });
    }
  }

  return relations;
}

function isValidSolarInput(input: BirthInput): boolean {
  if (!Number.isInteger(input.year) || input.year < 1800 || input.year > 2200) {
    return false;
  }

  if (!Number.isInteger(input.month) || input.month < 1 || input.month > 12) {
    return false;
  }

  if (!Number.isInteger(input.day) || input.day < 1 || input.day > 31) {
    return false;
  }

  if (!Number.isInteger(input.hour) || input.hour < 0 || input.hour > 23) {
    return false;
  }

  const date = new Date(Date.UTC(input.year, input.month - 1, input.day));
  return (
    date.getUTCFullYear() === input.year &&
    date.getUTCMonth() === input.month - 1 &&
    date.getUTCDate() === input.day
  );
}

function getYearPillar(input: BirthInput): Pillar {
  const baziYear = input.month < 2 || (input.month === 2 && input.day < 4) ? input.year - 1 : input.year;
  const cycleIndex = mod(baziYear - 4, 60);
  return makePillar("year", HEAVENLY_STEMS[cycleIndex % 10], EARTHLY_BRANCHES[cycleIndex % 12]);
}

function getMonthPillar(input: BirthInput, yearStem: HeavenlyStem): Pillar {
  const monthOffset = getSolarMonthOffset(input.month, input.day);
  const startStem = MONTH_START_STEM_BY_YEAR_STEM[yearStem];
  const stem = HEAVENLY_STEMS[mod(HEAVENLY_STEMS.indexOf(startStem) + monthOffset, 10)];
  const branch = MONTH_BRANCH_SEQUENCE[monthOffset];
  return makePillar("month", stem, branch);
}

function getSolarMonthOffset(month: number, day: number): number {
  if (month === 1) {
    return day >= 6 ? 11 : 10;
  }

  if (month === 2) {
    return day >= 4 ? 0 : 11;
  }

  if (month === 3) {
    return day >= 6 ? 1 : 0;
  }

  if (month === 4) {
    return day >= 5 ? 2 : 1;
  }

  if (month === 5) {
    return day >= 6 ? 3 : 2;
  }

  if (month === 6) {
    return day >= 6 ? 4 : 3;
  }

  if (month === 7) {
    return day >= 7 ? 5 : 4;
  }

  if (month === 8) {
    return day >= 8 ? 6 : 5;
  }

  if (month === 9) {
    return day >= 8 ? 7 : 6;
  }

  if (month === 10) {
    return day >= 8 ? 8 : 7;
  }

  if (month === 11) {
    return day >= 7 ? 9 : 8;
  }

  return day >= 7 ? 10 : 9;
}

function getDayPillar(input: BirthInput): Pillar {
  const jdn = toJulianDayNumber(input.year, input.month, input.day);
  const cycleIndex = mod(jdn + 49, 60);
  return makePillar("day", HEAVENLY_STEMS[cycleIndex % 10], EARTHLY_BRANCHES[cycleIndex % 12]);
}

function getHourPillar(hour: number, dayStem: HeavenlyStem): Pillar {
  const branchIndex = Math.floor((hour + 1) / 2) % 12;
  const startStem = HOUR_START_STEM_BY_DAY_STEM[dayStem];
  const stem = HEAVENLY_STEMS[mod(HEAVENLY_STEMS.indexOf(startStem) + branchIndex, 10)];
  return makePillar("hour", stem, EARTHLY_BRANCHES[branchIndex]);
}

function makePillar(name: PillarName, stem: HeavenlyStem, branch: EarthlyBranch): Pillar {
  const stemMeta = STEM_META[stem];
  const branchMainStem = BRANCH_MAIN_STEM[branch];
  const branchMeta = STEM_META[branchMainStem];

  return {
    name,
    stem,
    branch,
    stem_element: stemMeta.element,
    stem_yin_yang: stemMeta.yinYang,
    branch_element: branchMeta.element,
    branch_yin_yang: branchMeta.yinYang,
    display: `${stem}${branch}`,
  };
}

function countFiveElements(pillars: Record<PillarName, Pillar>): FiveElementCounts {
  const counts = emptyFiveElementCounts();

  for (const name of PILLAR_NAMES) {
    counts[pillars[name].stem_element] += 1;
    counts[pillars[name].branch_element] += 1;
  }

  return counts;
}

function countTenGods(pillars: Record<PillarName, Pillar>, dayStem: HeavenlyStem): TenGodCounts {
  const counts = emptyTenGodCounts();
  const targets: HeavenlyStem[] = [];

  for (const name of PILLAR_NAMES) {
    if (name !== "day") {
      targets.push(pillars[name].stem);
    }

    targets.push(BRANCH_MAIN_STEM[pillars[name].branch]);
  }

  for (const target of targets) {
    counts[getTenGod(dayStem, target)] += 1;
  }

  return counts;
}

function deriveSimplifiedStrength(pillars: Record<PillarName, Pillar>, dayStem: HeavenlyStem): SimplifiedStrength {
  const dayMeta = STEM_META[dayStem];
  let sameKindCount = 0;
  let supportCount = 0;
  let pressureDrainExhaustCount = 0;
  const targetElements: FiveElement[] = [];

  for (const name of PILLAR_NAMES) {
    if (name !== "day") {
      targetElements.push(pillars[name].stem_element);
    }

    targetElements.push(pillars[name].branch_element);
  }

  for (const element of targetElements) {
    if (element === dayMeta.element) {
      sameKindCount += 1;
    } else if (GENERATES[element] === dayMeta.element) {
      supportCount += 1;
    } else {
      pressureDrainExhaustCount += 1;
    }
  }

  const supportiveTotal = sameKindCount + supportCount;
  const tendency =
    supportiveTotal >= pressureDrainExhaustCount + 2
      ? "strong"
      : pressureDrainExhaustCount >= supportiveTotal + 2
        ? "weak"
        : "balanced";

  return {
    same_kind_count: sameKindCount,
    support_count: supportCount,
    pressure_drain_exhaust_count: pressureDrainExhaustCount,
    tendency,
  };
}

function getTenGod(dayStem: HeavenlyStem, targetStem: HeavenlyStem): TenGod {
  const day = STEM_META[dayStem];
  const target = STEM_META[targetStem];
  const samePolarity = day.yinYang === target.yinYang;

  if (day.element === target.element) {
    return samePolarity ? "peer" : "rob_wealth";
  }

  if (GENERATES[day.element] === target.element) {
    return samePolarity ? "eating_god" : "hurting_officer";
  }

  if (CONTROLS[day.element] === target.element) {
    return samePolarity ? "indirect_wealth" : "direct_wealth";
  }

  if (CONTROLS[target.element] === day.element) {
    return samePolarity ? "seven_killings" : "direct_officer";
  }

  return samePolarity ? "indirect_resource" : "direct_resource";
}

function buildChartStructureSummary({
  dayMasterStem,
  dayMasterElement,
  fiveElementCounts,
  branchRelations,
  simplifiedStrength,
}: {
  dayMasterStem: HeavenlyStem;
  dayMasterElement: FiveElement;
  fiveElementCounts: FiveElementCounts;
  branchRelations: BranchRelation[];
  simplifiedStrength: SimplifiedStrength;
}): ChartStructureSignal[] {
  return [
    {
      key: "calendar_support",
      label: "Calendar Support",
      value: "solar_mvp",
      source: "calendar",
    },
    {
      key: "day_master",
      label: "Day Master",
      value: `${dayMasterStem}:${dayMasterElement}`,
      source: "day_master",
    },
    {
      key: "strength_tendency",
      label: "Simplified Strength",
      value: simplifiedStrength.tendency,
      source: "day_master",
    },
    {
      key: "dominant_element",
      label: "Dominant Element",
      value: getDominantElement(fiveElementCounts),
      source: "five_element_counts",
    },
    {
      key: "branch_relation_count",
      label: "Branch Relations",
      value: String(branchRelations.length),
      source: "branch_relations",
    },
  ];
}

function getDominantElement(counts: FiveElementCounts): FiveElement {
  return FIVE_ELEMENTS.reduce((current, candidate) => (counts[candidate] > counts[current] ? candidate : current), "wood");
}

function hasPair(pairs: Array<[EarthlyBranch, EarthlyBranch]>, pair: [EarthlyBranch, EarthlyBranch]): boolean {
  return pairs.some(([left, right]) => (left === pair[0] && right === pair[1]) || (left === pair[1] && right === pair[0]));
}

function emptyFiveElementCounts(): FiveElementCounts {
  return {
    wood: 0,
    fire: 0,
    earth: 0,
    metal: 0,
    water: 0,
  };
}

function emptyTenGodCounts(): TenGodCounts {
  return TEN_GODS.reduce<TenGodCounts>(
    (counts, tenGod) => ({
      ...counts,
      [tenGod]: 0,
    }),
    {
      peer: 0,
      rob_wealth: 0,
      eating_god: 0,
      hurting_officer: 0,
      indirect_wealth: 0,
      direct_wealth: 0,
      seven_killings: 0,
      direct_officer: 0,
      indirect_resource: 0,
      direct_resource: 0,
    },
  );
}

function toJulianDayNumber(year: number, month: number, day: number): number {
  const a = Math.floor((14 - month) / 12);
  const y = year + 4800 - a;
  const m = month + 12 * a - 3;

  return day + Math.floor((153 * m + 2) / 5) + 365 * y + Math.floor(y / 4) - Math.floor(y / 100) + Math.floor(y / 400) - 32045;
}

function mod(value: number, divisor: number): number {
  return ((value % divisor) + divisor) % divisor;
}

