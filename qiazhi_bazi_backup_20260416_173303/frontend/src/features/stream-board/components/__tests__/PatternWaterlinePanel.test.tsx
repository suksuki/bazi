import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PatternWaterlinePanel } from "@/features/stream-board/components/PatternWaterlinePanel";
import type { PatternThresholdRow } from "@/features/stream-board/models";

describe("PatternWaterlinePanel · V8.2 水位常态", () => {
  it("EMPTY_NO_DATA 且无行时不再展示 EMPTY 文案，与 OK 空行一致走待物理/图例", () => {
    render(
      <PatternWaterlinePanel
        committed={[]}
        preview={[]}
        shadowActive={false}
        patternThresholdsStatus="EMPTY_NO_DATA"
        t={(s) => s}
      />,
    );
    expect(screen.queryByTestId("pattern-waterline-empty-no-data")).not.toBeInTheDocument();
    expect(screen.queryByTestId("pattern-waterline-loader")).not.toBeInTheDocument();
    expect(screen.getByText("pattern.waterline.awaitingPhysics")).toBeInTheDocument();
  });

  it("指纹不合法时显示阻塞加载", () => {
    render(
      <PatternWaterlinePanel
        committed={
          [
            {
              name: "假行",
              progress: 0.5,
              stability: 0.5,
              engine_v: "LEGACY_CENTROID",
            },
          ] as PatternThresholdRow[]
        }
        preview={[]}
        shadowActive={false}
        patternThresholdsStatus="OK"
        t={(s) => s}
      />,
    );
    expect(screen.getByTestId("pattern-waterline-loader")).toBeInTheDocument();
  });

  it("OK 且无行时显示待物理（非法典错误态）", () => {
    render(
      <PatternWaterlinePanel
        committed={[]}
        preview={[]}
        shadowActive={false}
        patternThresholdsStatus="OK"
        t={(s) => s}
      />,
    );
    expect(screen.queryByTestId("pattern-waterline-loader")).not.toBeInTheDocument();
    expect(screen.getByText("pattern.waterline.awaitingPhysics")).toBeInTheDocument();
  });
});
