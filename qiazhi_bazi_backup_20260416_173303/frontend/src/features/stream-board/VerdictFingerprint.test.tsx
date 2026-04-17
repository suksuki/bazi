import React from "react";
import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { LiveVerdictDisplay } from "@/features/stream-board/components/LiveVerdictDisplay";
import { LabStoreProvider } from "@/features/stream-board/stores/LabSessionContext";

describe("VerdictFingerprint visibility", () => {
  it("moves sha256 fingerprint into audit drawer", () => {
    const fp = "<!--qiazhi-fingerprint:v1 abcdef sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef-->";
    render(
      <LabStoreProvider>
        <LiveVerdictDisplay
          verdictSkeleton={null}
          verdictBody={`【裁断】此命先守后攻。\n\n${fp}`}
          calculationNonce={1}
          t={(s) => s}
        />
      </LabStoreProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "查看审计抽屉" }));
    const panels = screen.getAllByText(/sha256:[0-9a-f]{64}/i);
    expect(panels.length).toBeGreaterThan(0);
    expect(panels[0].textContent).toMatch(/sha256:[0-9a-f]{64}/i);
  });
});

