import {
  loadAccount,
  loadCaseWorkspace,
  loadCases,
  loadEnvelope,
  loadNarration,
  loadReadOnlyCanvas,
} from "./api";
import type {
  CaseWorkspaceEnvelope,
  CanvasContextPack,
  ExperienceCaseSummary,
  MingliExperienceEnvelope,
  NarrationManifest,
  NarrationStatus,
  ReadOnlySixPillarCanvas,
} from "./contracts";
import {
  initialUiState,
  reduceUi,
  type ProductArea,
  type UiState,
  type WorkspaceSurface,
} from "./state";

export interface ExperienceBootstrap {
  account: { display_name: string; role: string };
  cases: ExperienceCaseSummary[];
}

export interface LoadedExperienceCase {
  workspace: CaseWorkspaceEnvelope;
  envelope: MingliExperienceEnvelope;
  canvas: ReadOnlySixPillarCanvas | null;
  canvasContext: CanvasContextPack | null;
  narrationManifest: NarrationManifest | null;
  narrationAssets: Record<string, NarrationStatus>;
  availableSurfaces: WorkspaceSurface[];
  availableAreas: ProductArea[];
  ui: UiState;
}

export async function loadExperienceBootstrap(): Promise<ExperienceBootstrap> {
  const account = await loadAccount();
  const cases = await loadCases();
  return { account, cases };
}

export async function loadExperienceCase(
  caseId: string,
  params: URLSearchParams,
): Promise<LoadedExperienceCase> {
  const [envelopeResult, workspaceResult, canvasResult, narrationResult] = await Promise.allSettled([
    loadEnvelope(caseId),
    loadCaseWorkspace(caseId),
    loadReadOnlyCanvas(caseId),
    loadNarration(caseId),
  ]);
  if (envelopeResult.status === "rejected") throw envelopeResult.reason;
  if (workspaceResult.status === "rejected") throw workspaceResult.reason;

  const envelope = envelopeResult.value;
  const workspace = workspaceResult.value;
  const canvas = canvasResult.status === "fulfilled" ? canvasResult.value : null;
  const canvasContext = canvas ? canvas.stages[canvas.default_stage].context : null;
  const narrationManifest = narrationResult.status === "fulfilled" ? narrationResult.value.manifest : null;
  const narrationAssets = narrationResult.status === "fulfilled" ? narrationResult.value.speechAssets : {};
  const availableSurfaces = workspace.allowed_surfaces.filter((surface) => (
    surface === "overview"
    || (surface === "onecanvas" && canvas !== null)
    || (surface === "theater" && narrationManifest !== null)
  ));
  const availableAreas: ProductArea[] = workspace.allowed_surfaces.includes("mingli_lab")
    ? ["world", "workbench", "lab"]
    : ["world", "workbench"];

  let ui = structuredClone(initialUiState);
  if (canvas) {
    const initialProjection = canvas.stages[canvas.default_stage];
    ui = reduceUi(ui, {
      type: "canvas-stage",
      stage: canvas.default_stage,
      layer: initialProjection.default_layer_id,
      selected: initialProjection.context.selected_object_refs[0] || initialProjection.spec.semantic_slots[0]?.slot_ref || "",
    });
  }
  const requestedSurface = params.get("surface") as WorkspaceSurface | null;
  const preferredSurface = requestedSurface || workspace.state.current_surface;
  ui = reduceUi(ui, {
    type: "workspace-surface",
    surface: availableSurfaces.includes(preferredSurface) ? preferredSurface : "overview",
  });
  const requestedArea = params.get("area") as ProductArea | null;
  const preferredArea = requestedArea
    || (requestedSurface || preferredSurface !== "overview" ? "workbench" : "world");
  ui = reduceUi(ui, {
    type: "product-area",
    area: availableAreas.includes(preferredArea) ? preferredArea : "world",
  });
  if (ui.productArea === "lab" && canvas) {
    const layer = canvas.stages[ui.canvasStage].layers.find((item) => (
      item.layer_id === "generation_control" && item.available
    ));
    if (layer) ui = reduceUi(ui, { type: "canvas-layer", layer: layer.layer_id });
  }

  return {
    workspace,
    envelope,
    canvas,
    canvasContext,
    narrationManifest,
    narrationAssets,
    availableSurfaces,
    availableAreas,
    ui,
  };
}
