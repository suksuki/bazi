import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ClimateFieldStrengthCompare } from "@/features/admin/components/ClimateFieldStrengthCompare";

describe("ClimateFieldStrengthCompare", () => {
  it("renders five rows when meta block present", () => {
    render(
      <ClimateFieldStrengthCompare
        physicsTensor={{
          meta: {
            climate_field_correction_v1: { month_branch: "午" },
            climate_manifest_field_compare_v1: {
              normalized_pre_manifest: { wood: 0.2, fire: 0.2, earth: 0.2, metal: 0.2, water: 0.2 },
              normalized_post_manifest_pre_hard_climate: {
                wood: 0.19,
                fire: 0.22,
                earth: 0.2,
                metal: 0.2,
                water: 0.19,
              },
            },
          },
        }}
      />,
    );
    expect(screen.getByTestId("climate-field-compare")).toBeInTheDocument();
    expect(screen.getByText(/火 Fire/i)).toBeInTheDocument();
  });

  it("shows empty hint without compare block", () => {
    render(<ClimateFieldStrengthCompare physicsTensor={{ meta: {} }} />);
    expect(screen.getByTestId("climate-field-compare-empty")).toBeInTheDocument();
  });
});
