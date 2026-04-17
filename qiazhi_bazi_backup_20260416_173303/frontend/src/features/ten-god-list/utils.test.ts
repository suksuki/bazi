import { describe, expect, it } from "vitest";

import { buildConsensusText, buildLockedDeitySet, extractHardRouteKeys } from "./utils";

describe("ten god list utils", () => {
  it("extracts hard route keys", () => {
    expect(extractHardRouteKeys(["Param 'CF_FLOATING_DECAY' applied", "Param 'A_PROTRUSION' applied"])).toEqual([
      "CF_FLOATING_DECAY",
      "A_PROTRUSION",
    ]);
  });

  it("builds locked deity set from param logs", () => {
    const locked = buildLockedDeitySet(["Param 'CF_FLOATING_DECAY' applied", "比肩 path updated"]);
    expect(locked.has("比肩")).toBe(true);
    expect(locked.has("劫财")).toBe(true);
  });

  it("formats consensus text", () => {
    expect(buildConsensusText([{ decision_key: "root_factor", confirmed_value: 0.25 }])).toBe("root_factor=0.25");
  });
});
