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
  kind: string;
  positions: string[];
  detail: string;
};

export type BaziMetadata = {
  version: string;
  pillars: FourPillars | null;
  conflict_matrix: { points: ConflictPoint[] };
  flow_state: string;
  notes: string;
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
