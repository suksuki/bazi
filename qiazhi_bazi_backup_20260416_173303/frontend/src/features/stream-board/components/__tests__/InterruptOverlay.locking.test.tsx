import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";

import { InterruptOverlay } from "../InterruptOverlay";

describe("InterruptOverlay", () => {
  it("does not disable buttons when locked=false", async () => {
    const onResume = vi.fn().mockResolvedValue(undefined);
    render(
      <InterruptOverlay
        interruptRequest={{ reason_code: "TEST", state: "pending" }}
        locked={false}
        onResume={onResume}
      />,
    );
    const btn = screen.getByRole("button", { name: "确认冲突" });
    expect(btn).not.toBeDisabled();
    fireEvent.click(btn);
    expect(onResume).toHaveBeenCalledTimes(1);
  });

  it("disables interactions when locked=true", () => {
    render(
      <InterruptOverlay
        interruptRequest={{ reason_code: "TEST", state: "pending" }}
        locked={true}
        onResume={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: "确认冲突" })).toBeDisabled();
  });

  it("disables interactions when submitCooldown=true", () => {
    render(
      <InterruptOverlay
        interruptRequest={{ reason_code: "TEST", state: "pending" }}
        locked={false}
        submitCooldown
        onResume={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: "确认冲突" })).toBeDisabled();
  });
});
