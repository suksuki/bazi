import { describe, expect, it } from "vitest";
import {
  deriveV17LlmLifecycle,
  isCanonPhysicsSnapshot,
  mergeV17LlmMetaForUi,
  shouldReleaseDecisionInboxLock,
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

describe("shouldReleaseDecisionInboxLock", () => {
  it("keeps the inbox locked until a newer LLM cycle reaches terminal state", () => {
    const lockStartedAtMs = Date.parse("2026-04-18T09:00:00.000Z");
    expect(
      shouldReleaseDecisionInboxLock({
        lockStartedAtMs,
        latestFrameTimestamp: "2026-04-18T08:59:56.000Z",
        hasFinalLlmMeta: true,
      }),
    ).toBe(false);
    expect(
      shouldReleaseDecisionInboxLock({
        lockStartedAtMs,
        latestFrameTimestamp: "2026-04-18T09:00:02.000Z",
        hasFinalLlmMeta: false,
        llmOk: true,
      }),
    ).toBe(false);
    expect(
      shouldReleaseDecisionInboxLock({
        lockStartedAtMs,
        latestFrameTimestamp: "2026-04-18T09:00:03.000Z",
        hasFinalLlmMeta: true,
      }),
    ).toBe(true);
  });

  it("releases the lock on a newer terminal error frame too", () => {
    const lockStartedAtMs = Date.parse("2026-04-18T09:00:00.000Z");
    expect(
      shouldReleaseDecisionInboxLock({
        lockStartedAtMs,
        latestFrameTimestamp: "2026-04-18T09:00:01.000Z",
        hasFinalLlmMeta: false,
        llmOk: false,
      }),
    ).toBe(true);
  });
});

describe("deriveV17LlmLifecycle", () => {
  it("marks audit-preview without narrator body as awaiting_first_token", () => {
    const out = deriveV17LlmLifecycle({
      running: true,
      llmMeta: {},
      latestNarrator: undefined,
      hasAuditPreview: true,
      streamState: {
        closed: false,
        closeReason: "idle",
        lastHeartbeat: { stepPosition: "SNAPSHOT:llm_audit_preview", idleSec: 2 },
        heartbeatHistory: [],
      },
    });
    expect(out.phase).toBe("awaiting_first_token");
  });

  it("marks closed stream without final llm meta as closed_without_output", () => {
    const out = deriveV17LlmLifecycle({
      running: true,
      llmMeta: {},
      latestNarrator: undefined,
      hasAuditPreview: true,
      streamState: {
        closed: true,
        closeReason: "stream_eof",
        lastHeartbeat: { stepPosition: "NARRATOR:已联通", idleSec: 2 },
        heartbeatHistory: [],
      },
    });
    expect(out.phase).toBe("closed_without_output");
    expect(out.statusText).toContain("流已结束");
  });

  it("marks terminal error as failed even without narrator text", () => {
    const out = deriveV17LlmLifecycle({
      running: true,
      llmMeta: { ok: false, error: "boom" },
      latestNarrator: undefined,
      hasAuditPreview: true,
      streamState: { closed: true, closeReason: "runtime_error", heartbeatHistory: [] },
    });
    expect(out.phase).toBe("failed");
  });
});
