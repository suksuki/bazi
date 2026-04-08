import type { ConflictPoint, TimelineSnapshot } from "@/types/bazi";

import {
  BRANCH_MAIN_STEM,
  DAY_ROOT_BRANCHES,
  DEITY_ABBR,
  ELEMENT_CONTROLS,
  ELEMENT_GENERATES,
  STEM_ELEMENT,
  STEM_POLARITY,
} from "./constants";

export function branchInConflict(branch: string, points: ConflictPoint[]) {
  return points.some((point) => point.detail.includes(branch));
}

export function splitGanZhi(gz: string): { stem: string; branch: string } {
  if (gz && gz.length >= 2) return { stem: gz[0], branch: gz[1] };
  return { stem: "?", branch: gz || "?" };
}

export function clampEnergy(value: number) {
  return Math.max(0, Math.min(100, Math.round(value)));
}

export function deityByDayAndTarget(dayStem: string, targetStem: string): string {
  const selfEl = STEM_ELEMENT[dayStem];
  const tarEl = STEM_ELEMENT[targetStem];
  const dayPol = STEM_POLARITY[dayStem];
  const tarPol = STEM_POLARITY[targetStem];
  if (!selfEl || !tarEl || !dayPol || !tarPol) return "比肩";
  if (selfEl === tarEl) return tarPol === dayPol ? "比肩" : "劫财";
  if (ELEMENT_GENERATES[selfEl] === tarEl) return tarPol === dayPol ? "食神" : "伤官";
  if (ELEMENT_CONTROLS[selfEl] === tarEl) return tarPol === dayPol ? "偏财" : "正财";
  if (ELEMENT_CONTROLS[tarEl] === selfEl) return tarPol === dayPol ? "七杀" : "正官";
  return tarPol === dayPol ? "偏印" : "正印";
}

export function deityAbbr(dayStem: string, targetStem: string) {
  return DEITY_ABBR[deityByDayAndTarget(dayStem, targetStem)] || "比";
}

export function computeRootState(args: {
  dayStem: string;
  pillars: { year: { branch: string }; month: { branch: string }; day: { branch: string }; hour: { branch: string } };
  timeline?: TimelineSnapshot | null;
  confirmedConflictDetails: string[];
  deityScores: Record<string, number>;
  deityEnergyAxes: Record<string, { absolute_energy?: number }>;
}) {
  const roots = DAY_ROOT_BRANCHES[args.dayStem] ?? [];
  const hasRootInNatal = [
    args.pillars.year.branch,
    args.pillars.month.branch,
    args.pillars.day.branch,
    args.pillars.hour.branch,
  ].some((branch) => roots.includes(branch));
  const unstableRoot = args.confirmedConflictDetails.some((item) => item.includes("冲"));
  const hasGengLuck = (args.timeline?.dayun || "").includes("庚");
  const hasBingWuYear = (args.timeline?.liunian || "").includes("丙午");
  const selfEnergy =
    Math.max(0, Math.min(100, Number(args.deityScores["比肩"] ?? 0) + Number(args.deityScores["劫财"] ?? 0)));
  const selfAbs =
    Number(args.deityEnergyAxes["比肩"]?.absolute_energy ?? 0) +
    Number(args.deityEnergyAxes["劫财"]?.absolute_energy ?? 0);
  const extremeExhausted =
    !hasRootInNatal && (hasBingWuYear || unstableRoot || selfEnergy <= 16.0 || selfAbs < 0.5);
  const selfGlow = extremeExhausted ? 0.3 : 0.25 + selfEnergy / 130;
  return { roots, hasRootInNatal, unstableRoot, hasGengLuck, hasBingWuYear, selfEnergy, extremeExhausted, selfGlow };
}

export function computeBranchEnergy(args: {
  pillars: {
    year: { branch: string; energy_value?: number };
    month: { branch: string; energy_value?: number };
    day: { branch: string; energy_value?: number };
    hour: { branch: string; energy_value?: number };
  };
  points: ConflictPoint[];
  confirmedConflictDetails: string[];
}) {
  const branchEnergy: Record<string, number> = {
    year_branch: args.pillars.year.energy_value ?? 100,
    month_branch: args.pillars.month.energy_value ?? 100,
    day_branch: args.pillars.day.energy_value ?? 100,
    hour_branch: args.pillars.hour.energy_value ?? 100,
  };
  args.points.forEach((point) => {
    if (!args.confirmedConflictDetails.includes(point.detail)) return;
    if (point.kind === "clash") {
      if (point.detail.includes("子午冲") && point.positions.length === 2) {
        const [a, b] = point.positions;
        const aBranch = (args.pillars as Record<string, { branch: string }>)[a.replace("_branch", "")]?.branch;
        const bBranch = (args.pillars as Record<string, { branch: string }>)[b.replace("_branch", "")]?.branch;
        if (aBranch === "子") {
          branchEnergy[a] = clampEnergy(branchEnergy[a] - 30);
          branchEnergy[b] = clampEnergy(branchEnergy[b] - 60);
        } else if (bBranch === "子") {
          branchEnergy[a] = clampEnergy(branchEnergy[a] - 60);
          branchEnergy[b] = clampEnergy(branchEnergy[b] - 30);
        } else {
          branchEnergy[a] = clampEnergy(branchEnergy[a] - 45);
          branchEnergy[b] = clampEnergy(branchEnergy[b] - 45);
        }
      } else {
        point.positions.forEach((position) => {
          branchEnergy[position] = clampEnergy((branchEnergy[position] ?? 100) - 40);
        });
      }
    }
  });
  return branchEnergy;
}

export function resolveTimelineStem(branch: string, stem: string) {
  return BRANCH_MAIN_STEM[branch] || stem;
}
