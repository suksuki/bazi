import type { AuthRole, AuthUser } from "@/hooks/useAuthSession";

export const ORACLE_SURFACES = ["core", "auxiliary", "trace"] as const;

export type OracleSurface = (typeof ORACLE_SURFACES)[number];

export type V17AccessPolicy = {
  role: AuthRole | "guest";
  oracleSurfaces: OracleSurface[];
  canAccessOracleSurface: (surface: OracleSurface) => boolean;
  canAccessAdmin: boolean;
  canManageUsers: boolean;
  canUseSimpleOracle: boolean;
  canUseProfessionalOracle: boolean;
  canReadEvidence: boolean;
  canSubmitPractitionerFeedback: boolean;
  hasCapability: (capability: string) => boolean;
};

function isOracleSurface(value: string): value is OracleSurface {
  return (ORACLE_SURFACES as readonly string[]).includes(value);
}

export function getOracleSurfaces(user: AuthUser | null | undefined): OracleSurface[] {
  if (!user) return [];

  const rawSurfaces = Array.isArray(user.surface_access?.oracle) ? user.surface_access?.oracle : ["core"];
  const normalized = (rawSurfaces || [])
    .map((surface) => String(surface || "").trim())
    .filter(isOracleSurface);
  const withCore = normalized.includes("core") ? normalized : ["core", ...normalized];

  return ORACLE_SURFACES.filter((surface) => withCore.includes(surface));
}

export function createAccessPolicy(user: AuthUser | null | undefined): V17AccessPolicy {
  const oracleSurfaces = getOracleSurfaces(user);
  const capabilitySet = new Set((user?.capabilities || []).map((capability) => String(capability || "").trim()).filter(Boolean));
  const hasCapability = (capability: string) => capabilitySet.has(capability);

  return {
    role: user?.role || "guest",
    oracleSurfaces,
    canAccessOracleSurface: (surface) => oracleSurfaces.includes(surface),
    canAccessAdmin: Boolean(user?.surface_access?.admin),
    canManageUsers: Boolean(user?.surface_access?.user_management),
    canUseSimpleOracle: hasCapability("oracle.simple"),
    canUseProfessionalOracle: hasCapability("oracle.professional"),
    canReadEvidence: hasCapability("evidence.read"),
    canSubmitPractitionerFeedback: hasCapability("evidence.feedback.practitioner"),
    hasCapability,
  };
}
