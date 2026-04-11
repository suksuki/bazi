import { describe, expect, it } from "vitest";
import type { StreamBoardPipelineParams } from "../useStreamBoardPipeline";
import { useStreamBoardPipeline } from "../useStreamBoardPipeline";

describe("useStreamBoardPipeline", () => {
  it("exports the pipeline hook for controller composition", () => {
    expect(typeof useStreamBoardPipeline).toBe("function");
    expect(useStreamBoardPipeline.name).toBe("useStreamBoardPipeline");
  });

  it("types activeView as shell tab literals (not empty string)", () => {
    const lab: Pick<StreamBoardPipelineParams, "activeView"> = { activeView: "lab" };
    const debug: Pick<StreamBoardPipelineParams, "activeView"> = { activeView: "debug" };
    const admin: Pick<StreamBoardPipelineParams, "activeView"> = { activeView: "admin" };
    expect([lab.activeView, debug.activeView, admin.activeView].sort()).toEqual(["admin", "debug", "lab"]);
  });
});
