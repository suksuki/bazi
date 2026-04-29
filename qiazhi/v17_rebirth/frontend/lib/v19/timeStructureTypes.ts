import type { ChartStructureOk, EarthlyBranch, HeavenlyStem } from "./chartStructureTypes";

export type TimePillar = {
  stem: HeavenlyStem;
  branch: EarthlyBranch;
};

export type TimeRelations = {
  clashes: string[];
  combinations: string[];
};

export type LuckCycle = {
  start_age: number;
  end_age: number;
  pillar: TimePillar;
  relations_with_natal: TimeRelations;
};

export type LuckCycleDirection = "forward" | "reverse";

export type FlowYear = {
  year: number;
  pillar: TimePillar;
  relations_with_natal: TimeRelations;
  relations_with_luck_cycle?: TimeRelations;
};

export type TimeContext = {
  natal: ChartStructureOk;
  luck_cycle?: LuckCycle;
  flow_year?: FlowYear;
};
