import { describe, expect, it } from "vitest";
import { extractLlmRoundDiagnosisText } from "./logicEvolutionAxisExtract";

describe("extractLlmRoundDiagnosisText", () => {
  it("parses physics_audit JSON diagnosis", () => {
    const rt = JSON.stringify({ logic_proposal: { diagnosis: "官杀混杂" }, param_key: "X" });
    expect(extractLlmRoundDiagnosisText({ scenario: "physics_audit", response_text: rt })).toBe("官杀混杂");
  });

  it("coerces final_verdict JSON body", () => {
    const rt = JSON.stringify({ verdict_body: "### A\n判词" });
    expect(extractLlmRoundDiagnosisText({ scenario: "final_verdict_mandatory_synthesis", response_text: rt })).toBe(
      "### A\n判词",
    );
  });
});
