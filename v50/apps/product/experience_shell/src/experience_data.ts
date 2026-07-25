import { loadWorkspaceBootstrap } from "./api";
import type {
  CaseWorkspaceEnvelope,
  ExperienceCaseSummary,
  MingliExperienceEnvelope,
  WorkspaceCognitionState,
} from "./contracts";
import {
  initialUiState,
  reduceUi,
  type ProductArea,
  type UiState,
  type WorkspaceSurface,
} from "./state";


export interface LoadedExperienceCase {
  account: { display_name: string; role: string };
  cases: ExperienceCaseSummary[];
  selectedCaseId: string;
  selectedProfileId: string;
  workspace: CaseWorkspaceEnvelope | null;
  envelope: MingliExperienceEnvelope | null;
  cognition: WorkspaceCognitionState;
  availableSurfaces: WorkspaceSurface[];
  availableAreas: ProductArea[];
  ui: UiState;
  profileRequired: boolean;
}


export async function loadExperienceCase(
  selection: { caseId?: string; profileId?: string },
  params: URLSearchParams,
  previousUi?: UiState,
): Promise<LoadedExperienceCase> {
  const bootstrap = await loadWorkspaceBootstrap(selection);
  const role = bootstrap.account.role;
  const profileRequired = bootstrap.status === "workspace_profile_required";
  const availableSurfaces: WorkspaceSurface[] = profileRequired
    ? ["overview"]
    : ["overview", "onecanvas", "theater"];
  const researchAllowed = bootstrap.workspace?.allowed_surfaces.includes("mingli_lab")
    || ["admin", "research", "research_master", "practitioner"].includes(role);
  const availableAreas: ProductArea[] = researchAllowed
    ? ["world", "workbench", "lab"]
    : ["world", "workbench"];

  let ui = previousUi ? structuredClone(previousUi) : structuredClone(initialUiState);
  const requestedSurface = params.get("surface") as WorkspaceSurface | null;
  const preferredSurface = requestedSurface
    || bootstrap.workspace?.state.current_surface
    || ui.workspaceSurface;
  ui = reduceUi(ui, {
    type: "workspace-surface",
    surface: availableSurfaces.includes(preferredSurface) ? preferredSurface : "overview",
  });
  const requestedArea = params.get("area") as ProductArea | null;
  const preferredArea = requestedArea
    || (requestedSurface || ui.workspaceSurface !== "overview" ? "workbench" : ui.productArea);
  ui = reduceUi(ui, {
    type: "product-area",
    area: availableAreas.includes(preferredArea) ? preferredArea : "world",
  });

  return {
    account: bootstrap.account,
    cases: bootstrap.cases,
    selectedCaseId: bootstrap.selected_case_id,
    selectedProfileId: bootstrap.selected_profile_id,
    workspace: bootstrap.workspace,
    envelope: bootstrap.envelope,
    cognition: bootstrap.cognition,
    availableSurfaces,
    availableAreas,
    ui,
    profileRequired,
  };
}
