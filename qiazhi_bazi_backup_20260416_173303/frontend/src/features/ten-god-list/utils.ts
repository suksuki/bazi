import { ALL_DEITIES } from "./constants";

export function extractHardRouteKeys(hardRouteLogs: string[]): string[] {
  const keys = new Set<string>();
  hardRouteLogs.forEach((line) => {
    const hit = String(line || "").match(/Param '([^']+)'/);
    if (hit?.[1]) keys.add(hit[1]);
  });
  return Array.from(keys);
}

export function buildLockedDeitySet(hardRouteLogs: string[]): Set<string> {
  const locked = new Set<string>();
  const keys = extractHardRouteKeys(hardRouteLogs);
  const joinedLogs = hardRouteLogs.join(" ");

  keys.forEach((key) => {
    if (key === "CF_FLOATING_DECAY") {
      locked.add("比肩");
      locked.add("劫财");
      return;
    }
    if (key === "A_PROTRUSION") {
      ALL_DEITIES.forEach((deity) => {
        if (joinedLogs.includes(deity)) locked.add(deity);
      });
      return;
    }
    if (key.startsWith("EFF_RESTRAINING")) {
      ["正官", "七杀", "比肩", "劫财"].forEach((deity) => locked.add(deity));
      return;
    }
    if (key.startsWith("EFF_EXHAUSTING")) {
      ["比肩", "劫财", "食神", "伤官"].forEach((deity) => locked.add(deity));
      return;
    }
    if (key.startsWith("EFF_CONSUMING")) {
      ["比肩", "劫财", "正财", "偏财"].forEach((deity) => locked.add(deity));
      return;
    }
    if (key.startsWith("EFF_GENERATING")) {
      ["正印", "偏印", "比肩", "劫财"].forEach((deity) => locked.add(deity));
    }
  });

  ALL_DEITIES.forEach((deity) => {
    if (joinedLogs.includes(deity)) locked.add(deity);
  });
  return locked;
}

export function buildConsensusText(
  consensusHistory: Array<{ decision_key: string; confirmed_value?: number; reasoning?: string }>
) {
  return consensusHistory
    .map((item) => `${item.decision_key}=${typeof item.confirmed_value === "number" ? item.confirmed_value.toFixed(2) : "?"}`)
    .join("; ");
}
