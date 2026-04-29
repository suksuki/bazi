export type CalendarType = "solar" | "lunar";

export type Gender = "male" | "female";

export type HeavenlyStem =
  | "甲"
  | "乙"
  | "丙"
  | "丁"
  | "戊"
  | "己"
  | "庚"
  | "辛"
  | "壬"
  | "癸";

export type EarthlyBranch =
  | "子"
  | "丑"
  | "寅"
  | "卯"
  | "辰"
  | "巳"
  | "午"
  | "未"
  | "申"
  | "酉"
  | "戌"
  | "亥";

export type FiveElement = "wood" | "fire" | "earth" | "metal" | "water";

export type YinYang = "yang" | "yin";

export type PillarName = "year" | "month" | "day" | "hour";

export type TenGod =
  | "peer"
  | "rob_wealth"
  | "eating_god"
  | "hurting_officer"
  | "indirect_wealth"
  | "direct_wealth"
  | "seven_killings"
  | "direct_officer"
  | "indirect_resource"
  | "direct_resource";

export type BranchRelationType = "six_combination" | "six_clash" | "three_harmony";

export type StrengthTendency = "weak" | "balanced" | "strong";

export type ChartStructureUnsupportedReason = "lunar_calendar_not_supported" | "invalid_solar_input";

export type BirthInput = {
  year: number;
  month: number;
  day: number;
  hour: number;
  calendar_type: CalendarType;
  gender: Gender;
  flow_year?: number;
};

export type Pillar = {
  name: PillarName;
  stem: HeavenlyStem;
  branch: EarthlyBranch;
  stem_element: FiveElement;
  stem_yin_yang: YinYang;
  branch_element: FiveElement;
  branch_yin_yang: YinYang;
  display: string;
};

export type DayMaster = {
  stem: HeavenlyStem;
  element: FiveElement;
  yin_yang: YinYang;
};

export type FiveElementCounts = Record<FiveElement, number>;

export type TenGodCounts = Record<TenGod, number>;

export type BranchRelation = {
  type: BranchRelationType;
  branches: EarthlyBranch[];
  pillar_names: PillarName[];
  element?: FiveElement;
};

export type SimplifiedStrength = {
  same_kind_count: number;
  support_count: number;
  pressure_drain_exhaust_count: number;
  tendency: StrengthTendency;
};

export type ChartStructureSignal = {
  key:
    | "day_master"
    | "strength_tendency"
    | "dominant_element"
    | "branch_relation_count"
    | "calendar_support";
  label: string;
  value: string;
  source: "pillars" | "day_master" | "five_element_counts" | "branch_relations" | "calendar";
};

export type ChartStructureOk = {
  status: "ok";
  input: BirthInput;
  calendar_note: "solar_mvp_approximate_jie_boundaries";
  pillars: Record<PillarName, Pillar>;
  day_master: DayMaster;
  five_element_counts: FiveElementCounts;
  ten_god_counts: TenGodCounts;
  branch_relations: BranchRelation[];
  simplified_strength: SimplifiedStrength;
  chart_structure_summary: ChartStructureSignal[];
};

export type ChartStructureUnsupported = {
  status: "unsupported";
  input: BirthInput;
  reason: ChartStructureUnsupportedReason;
};

export type ChartStructureResult = ChartStructureOk | ChartStructureUnsupported;

