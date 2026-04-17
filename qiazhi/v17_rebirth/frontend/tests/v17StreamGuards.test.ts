import { describe, expect, it } from "vitest";
import {
  isCanonPhysicsSnapshot,
  mergeV17LlmMetaForUi,
  type V17Frame,
} from "../hooks/useV17WebStream";

describe("isCanonPhysicsSnapshot", () => {
  it("accepts physics SNAPSHOT with four pillars", () => {
    const f: V17Frame = {
      layer: "SNAPSHOT",
      payload: {
        snapshot_kind: "physics",
        four_pillars: { year: "甲子", month: "乙丑", day: "丙寅", hour: "丁卯" },
      },
    };
    expect(isCanonPhysicsSnapshot(f)).toBe(true);
  });

  it("rejects non-physics snapshot_kind", () => {
    const f: V17Frame = {
      layer: "SNAPSHOT",
      payload: { snapshot_kind: "audit", four_pillars: { year: "甲", month: "乙", day: "丙", hour: "丁" } },
    };
    expect(isCanonPhysicsSnapshot(f)).toBe(false);
  });
});

describe("mergeV17LlmMetaForUi", () => {
  it("fills full_prompt_trace from audit snapshot when narrator omits it", () => {
    const auditSnap = {
      payload: {
        llm_meta: { model: "m1" },
        full_prompt_trace: { system_role: "S" },
        llm_system_prompt: "sys-audit",
      },
    };
    const latestNarr = { payload: { llm_meta: { ok: true, stream_partial: true } } };
    const merged = mergeV17LlmMetaForUi(undefined, latestNarr, auditSnap);
    expect(merged.full_prompt_trace).toEqual({ system_role: "S" });
    expect(merged.llm_system_prompt).toBe("sys-audit");
    expect(merged.ok).toBe(true);
  });
});
