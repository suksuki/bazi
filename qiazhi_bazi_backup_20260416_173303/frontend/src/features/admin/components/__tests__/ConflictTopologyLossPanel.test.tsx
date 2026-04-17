import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ConflictTopologyLossPanel } from "@/features/admin/components/ConflictTopologyLossPanel";

describe("ConflictTopologyLossPanel", () => {
  it("renders entries and aggregate", () => {
    render(
      <ConflictTopologyLossPanel
        physicsTensor={{
          meta: {
            conflict_topology_v1: {
              aggregate_conflict_linear_factor: 0.8,
              entries: [
                {
                  detail: "子午冲",
                  kind: "clash",
                  linear_multiplier: 0.8,
                  pct_change_display: -20,
                  source: "Manifest_Entry_04",
                  manifest_entry_id: "Entry_04",
                },
              ],
            },
          },
        }}
      />,
    );
    expect(screen.getByTestId("conflict-topology-loss")).toBeInTheDocument();
    expect(screen.getByText(/子午冲/)).toBeInTheDocument();
    expect(screen.getByText(/aggregate ×0\.8000/)).toBeInTheDocument();
  });

  it("renders PAIR_DECAYS element_loss_display when present", () => {
    render(
      <ConflictTopologyLossPanel
        physicsTensor={{
          meta: {
            conflict_topology_v1: {
              aggregate_conflict_linear_factor: 0.8,
              entries: [
                {
                  detail: "子午冲",
                  kind: "clash",
                  source: "Manifest_PAIR_DECAYS",
                  manifest_entry_id: "Manifest_Entry_09",
                  element_loss_display: "木能量 -10%、火能量 -25%",
                },
              ],
            },
          },
        }}
      />,
    );
    expect(screen.getByText(/木能量 -10%/)).toBeInTheDocument();
    expect(screen.getByText(/火能量 -25%/)).toBeInTheDocument();
  });
});
