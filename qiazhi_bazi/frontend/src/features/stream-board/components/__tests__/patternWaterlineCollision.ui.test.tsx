import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PatternWaterlinePanel } from "@/features/stream-board/components/PatternWaterlinePanel";
import type { PatternThresholdRow } from "@/features/stream-board/models";

/** 假从儿 + 印星触线：对齐法典 FOLLOW_CHILD exclusions.Seal_Axis */
function zhT(key: string): string {
  const map: Record<string, string> = {
    格局引力水位线: "格局引力水位线",
    稳定性: "稳定性",
    "pattern.waterline.gapToCatastrophe": "距 {name} 还差 {pct}%",
    "pattern.waterline.awaitingPhysics": "待 physics",
    "pattern.waterline.emptyNoData": "EMPTY",
    "pattern.waterline.awaitingStrict": "等待 STRICT",
    "pattern.waterline.affinityLegend": "图例",
    "pattern.waterline.affinityMatch": "Affinity",
    "pattern.follow_child": "从儿格",
    "pattern.collision.intercepted": "INTERCEPTED (已拦截)",
    "pattern.collision.title": "碰撞报告",
    "pattern.collision.close": "关闭",
    "pattern.collision.gating": "门控",
    "pattern.collision.gatingUnset": "无",
    "pattern.collision.actual": "实际",
    "pattern.collision.gatePass": "通过",
    "pattern.collision.gateFail": "未过",
    "pattern.collision.redline": "红线",
    "pattern.collision.noSnapshots": "无快照",
    "pattern.collision.triggered": "触线",
    "pattern.collision.redlineActive": "已拦截",
  };
  return map[key] ?? key;
}

describe("PatternWaterlinePanel · V7 ui-collision", () => {
  it("假从格+印星：从儿格显示 INTERCEPTED、Affinity 0%、红线抖动条", () => {
    const followChild: PatternThresholdRow = {
      name: "从儿格",
      pattern_id: "FOLLOW_CHILD",
      progress: 0,
      stability: 0.42,
      affinity_score: 0,
      pre_exclusion_affinity: 0.58,
      exclusion_hit: true,
      engine_v: "MANIFEST_V5.8_STRICT",
      primary_axis: "Output_Axis",
      primary_axis_energy: 0.55,
      gating_min_energy: 0.52,
      gating_max_self_energy: 0.12,
      exclusion_axis_snapshots: [
        {
          axis: "Seal_Axis",
          label_zh: "印绶",
          energy: 0.15,
          threshold: 0.03,
          triggered: true,
        },
      ],
      trace_display_zh: ["[拦截] 印星破格：从儿见印，格局破损。"],
      i18n_key: "pattern.follow_child",
    };

    render(
      <PatternWaterlinePanel
        committed={[followChild]}
        preview={null}
        shadowActive={false}
        patternThresholdsStatus="OK"
        t={zhT}
      />,
    );

    expect(screen.getByTestId("pattern-waterline-row-FOLLOW_CHILD-intercepted")).toHaveTextContent(
      "INTERCEPTED (已拦截)",
    );

    const rowBtn = screen.getByTestId("pattern-waterline-row-FOLLOW_CHILD");
    const li = rowBtn.closest("li");
    expect(li).toBeTruthy();
    const shake = li?.querySelector(".animate-shake");
    expect(shake).toBeTruthy();

    expect(li?.querySelector('[style*="width: 0%"]')).toBeTruthy();
    expect(screen.getByText("0.0%")).toBeInTheDocument();
  });
});
