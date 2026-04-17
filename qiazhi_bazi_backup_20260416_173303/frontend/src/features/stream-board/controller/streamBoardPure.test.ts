import { describe, expect, it } from "vitest";

import {
  buildStreamBoardEnabledPlugins,
  hoistPhysicsAuditDiagnosis,
  isFinalVerdictPhysicsFallbackBody,
  isPhysicsAuditFallbackUi,
  isTrustworthyPhysicsAuditDiagnosis,
  PHYSICS_AUDIT_LOGIC_PROPOSAL_PARAM_KEYS,
  RESIDENT_PATTERN_PLUGIN_ID,
} from "./streamBoardPure";

describe("hoistPhysicsAuditDiagnosis", () => {
  it("pulls diagnosis from nested logic_proposal", () => {
    expect(
      hoistPhysicsAuditDiagnosis({
        logic_proposal: { diagnosis: "  官杀混杂  ", param_key: "X" },
      }),
    ).toBe("官杀混杂");
    expect(
      hoistPhysicsAuditDiagnosis({
        logic_proposal: { reason: "根气偏枯", param_key: "Y" },
      }),
    ).toBe("根气偏枯");
  });

  it("prefers top-level diagnosis over proposal", () => {
    expect(
      hoistPhysicsAuditDiagnosis({
        diagnosis: "顶层",
        logic_proposal: { diagnosis: "内层" },
      }),
    ).toBe("顶层");
  });
});

describe("streamBoardPure audit guard", () => {
  it("includes expanded param keys in whitelist", () => {
    expect(PHYSICS_AUDIT_LOGIC_PROPOSAL_PARAM_KEYS.has("OFFICER_RESTRAINT_ALPHA")).toBe(true);
    expect(PHYSICS_AUDIT_LOGIC_PROPOSAL_PARAM_KEYS.has("POWER_DISTRIBUTION_GAMMA")).toBe(true);
  });

  it("isTrustworthyPhysicsAuditDiagnosis rejects empty and diagnosis-only sentinel", () => {
    expect(isTrustworthyPhysicsAuditDiagnosis("", "x")).toBe(false);
    expect(isTrustworthyPhysicsAuditDiagnosis("未拿到结构化审计结论", "ok")).toBe(false);
    expect(isTrustworthyPhysicsAuditDiagnosis("结构化审计回退：LLM 未返回可解析 JSON", "未拿到结构化审计结论")).toBe(true);
    expect(isTrustworthyPhysicsAuditDiagnosis("官杀独强，印星受制", "根气偏枯")).toBe(true);
  });

  it("isPhysicsAuditFallbackUi detects API / state fallback", () => {
    expect(isPhysicsAuditFallbackUi(null)).toBe(false);
    expect(isPhysicsAuditFallbackUi({ structured_hit: true, diagnosis: "官杀独强" })).toBe(false);
    expect(isPhysicsAuditFallbackUi({ structured_hit: false, diagnosis: "x" })).toBe(true);
    expect(isPhysicsAuditFallbackUi({ diagnosis: "结构化审计回退：LLM 未返回可解析 JSON" })).toBe(true);
  });

  it("isFinalVerdictPhysicsFallbackBody detects physics rescue template", () => {
    expect(isFinalVerdictPhysicsFallbackBody("")).toBe(false);
    expect(isFinalVerdictPhysicsFallbackBody("### 核心气象\n日主从财")).toBe(false);
    const fb =
      "### 核心气象 盘局物理层已收敛；干支张力与芯片证据链已登记。 ### 裁决共识 据 `sys.core.physics` 已登记之结论与芯片证据链，与四柱气机相互参证。 ### 行为指引 宜据 VF 与柱位锚点重写语气与分疏；可再次发起终审以润色辞章。";
    expect(isFinalVerdictPhysicsFallbackBody(fb)).toBe(true);
  });
});

describe("buildStreamBoardEnabledPlugins", () => {
  const sw = {
    blindSchool: true,
    wangshuai: false,
    wealthRisk: false,
    blindSchoolPierceHarm: true,
    blindSchoolTombVault: true,
    blindSchoolHostGuest: true,
  };

  it("always appends pattern detector unless purePhysicsAudit", () => {
    const ids = buildStreamBoardEnabledPlugins(sw);
    expect(ids[0]).toBe(RESIDENT_PATTERN_PLUGIN_ID);
    expect(ids).toContain(RESIDENT_PATTERN_PLUGIN_ID);
    expect(ids).toContain("classical.blind_school.v1");
  });

  it("omits pattern detector when purePhysicsAudit", () => {
    const ids = buildStreamBoardEnabledPlugins(sw, { purePhysicsAudit: true });
    expect(ids).not.toContain(RESIDENT_PATTERN_PLUGIN_ID);
  });
});
