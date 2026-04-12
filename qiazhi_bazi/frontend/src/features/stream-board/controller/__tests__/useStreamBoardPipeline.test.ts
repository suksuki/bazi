import { describe, expect, it } from "vitest";
import type { StreamBoardPipelineParams } from "../useStreamBoardPipeline";
import { reducePipelinePhase, useStreamBoardPipeline } from "../useStreamBoardPipeline";

describe("useStreamBoardPipeline", () => {
  it("exports the pipeline hook for controller composition", () => {
    expect(typeof useStreamBoardPipeline).toBe("function");
    expect(useStreamBoardPipeline.name).toBe("useStreamBoardPipeline");
  });

  it("reducePipelinePhase maps hub work to THINKING / POLISHING / READY", () => {
    let p = reducePipelinePhase("READY", "SCAN_STARTED");
    expect(p).toBe("THINKING");
    p = reducePipelinePhase(p, "SCAN_COMPLETED");
    expect(p).toBe("READY");
    p = reducePipelinePhase(p, "AUDIT_COMPLETED");
    expect(p).toBe("READY");
    p = reducePipelinePhase(p, "RECALC_STARTED");
    expect(p).toBe("THINKING");
    p = reducePipelinePhase(p, "RECALC_COMPLETED");
    expect(p).toBe("READY");
    p = reducePipelinePhase(p, "FINAL_SYNTHESIS_STARTED");
    expect(p).toBe("POLISHING");
    p = reducePipelinePhase(p, "FINAL_SYNTHESIS_COMPLETED");
    expect(p).toBe("READY");
    p = reducePipelinePhase(p, "NARRATIVE_REFRESH_STARTED");
    expect(p).toBe("THINKING");
  });

  it("types activeView as shell tab literals (not empty string)", () => {
    const lab: Pick<StreamBoardPipelineParams, "activeView"> = { activeView: "lab" };
    const debug: Pick<StreamBoardPipelineParams, "activeView"> = { activeView: "debug" };
    const admin: Pick<StreamBoardPipelineParams, "activeView"> = { activeView: "admin" };
    expect([lab.activeView, debug.activeView, admin.activeView].sort()).toEqual(["admin", "debug", "lab"]);
  });
});
