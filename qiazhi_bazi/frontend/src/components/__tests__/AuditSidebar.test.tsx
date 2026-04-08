import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AuditSidebar, type AuditItem } from "@/components/AuditSidebar";

describe("AuditSidebar", () => {
  it("renders physics and final verdict audit summary", () => {
    const items: AuditItem[] = [
      {
        id: "auditor-1",
        step: "05",
        role: "Auditor",
        action: "终判审计链路已生成",
        timestamp: "2026-04-08T00:00:00.000Z",
        payload: {
          model_name: "gpt-5",
          physics_confidence: 0.88,
          final_verdict_version_id: "v2.04080000",
          skill_id: "final_verdict_skill",
          rule_version: "final_verdict_rules.v1",
        },
      },
    ];

    render(
      <AuditSidebar
        items={items}
        dbOk
        llmOk
      />,
    );

    expect(screen.getByText(/physics confidence: 88%/)).toBeInTheDocument();
    expect(screen.getByText(/final verdict: v2.04080000/)).toBeInTheDocument();
    expect(screen.getByText(/final_verdict_skill/)).toBeInTheDocument();
  });
});
