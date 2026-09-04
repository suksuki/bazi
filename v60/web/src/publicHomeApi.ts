import { request } from "./http";

export type PillarSlot = "year" | "month" | "day" | "hour";

export interface PublicCaseOption {
  case_ref: string;
  profile_ref: string;
  display_name: string;
  gender: "male" | "female";
  calendar_type: "solar" | "lunar";
  birth_date: string;
  birth_time: string;
  birth_location: string;
  timezone: string;
  lunar_leap_month: boolean;
  status: "ACTIVE" | "INACTIVE";
  pillars: Record<PillarSlot, string>;
  active: boolean;
  stage_subject_id: string;
  subject_kind: "HUMAN_OWNER" | "HUMAN_REFERENCE";
  identity_badge: "私密真实档案" | "真实参考档案";
  birth_location_status: "RECORDED" | "HISTORICAL_MISSING";
}

export interface PublicHomeSnapshot {
  scope: "MINGLI_HOME";
  profile: {
    profile_ref: string;
    display_name: string;
  };
  case: {
    case_ref: string;
    subject_kind: "HUMAN_OWNER" | "HUMAN_REFERENCE";
    status: "ACTIVE";
    case_version: number;
  };
  case_options: PublicCaseOption[];
  chart: {
    chart_version_ref: string;
    version: number;
    pillars: Record<PillarSlot, string>;
    chart_hash: string;
  };
  life_case: {
    life_case_revision_ref: string;
    revision: number;
    status: string;
    revision_hash: string;
  };
  tree: {
    tree_ref: string;
    projection_version: number;
    scene_ref: string;
    phenotype: {
      profile_version: string;
      fact_basis: string;
      element_membership_ratios: Record<
        "wood" | "fire" | "earth" | "metal" | "water",
        number
      >;
      crown_spread: number;
      branch_lift: number;
      root_spread: number;
      bark_definition: number;
      surface_moisture: number;
      semantic_status: "VISUAL_METAPHOR_ONLY";
    };
    read_only: true;
    source_kind: "CANONICAL_SCENE_PROJECTION";
  };
  privacy: {
    private_to_account: true;
  };
}

export type PublicLifeTreeHomeSnapshot = Pick<
  PublicHomeSnapshot,
  "profile" | "case" | "case_options" | "chart" | "life_case" | "tree"
>;

export interface OwnerCaseInput {
  display_name: string;
  gender: "male" | "female";
  calendar_type: "solar" | "lunar";
  birth_date: string;
  birth_time: string;
  birth_location: string;
  timezone: string;
  lunar_leap_month: boolean;
  true_solar_time_policy: "not_applied";
}

export function loadPublicHome(): Promise<PublicHomeSnapshot> {
  return request("/api/v60/experience/home");
}

export function createOwnerCase(
  payload: OwnerCaseInput,
): Promise<{ case_ref: string; profile_ref: string; active: true }> {
  return request("/api/v60/cases", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function activateOwnerCase(
  caseRef: string,
): Promise<{ case_ref: string; active: true }> {
  return request(`/api/v60/cases/${encodeURIComponent(caseRef)}/activate`, {
    method: "POST",
  });
}
