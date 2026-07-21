import { loadCanvasContext } from "./api";
import { NarrationTimeline } from "./audio";
import { renderExperience, renderLoading, renderUnavailable } from "./components";
import type {
  CaseWorkspaceEnvelope,
  CanvasContextPack,
  CanvasLayer,
  CanvasStage,
  ExperienceCaseSummary,
  MingliExperienceEnvelope,
  NarrationManifest,
  NarrationStatus,
  ReadOnlySixPillarCanvas,
} from "./contracts";
import { loadExperienceBootstrap, loadExperienceCase } from "./experience_data";
import { applyActiveAnchor, humanizeError, updateExperienceLocation } from "./experience_dom";
import { bindExperienceInteractions } from "./experience_interactions";
import { createNarrationTimeline } from "./experience_timeline";
import {
  initialUiState,
  reduceUi,
  type ProductArea,
  type UiAction,
  type UiState,
  type WorkspaceSurface,
} from "./state";


const rootElement = document.querySelector<HTMLElement>("#experienceRoot");
if (!rootElement) throw new Error("experience_root_missing");
const root: HTMLElement = rootElement;

let account = { display_name: "", role: "member" };
let cases: ExperienceCaseSummary[] = [];
let activeCaseId = "";
let workspace: CaseWorkspaceEnvelope | null = null;
let availableSurfaces: WorkspaceSurface[] = ["overview"];
let availableAreas: ProductArea[] = ["world", "workbench"];
let envelope: MingliExperienceEnvelope | null = null;
let canvas: ReadOnlySixPillarCanvas | null = null;
let canvasContext: CanvasContextPack | null = null;
let narrationManifest: NarrationManifest | null = null;
let narrationAssets: Record<string, NarrationStatus> = {};
let timeline: NarrationTimeline | null = null;
let ui: UiState = structuredClone(initialUiState);

void boot();


async function boot(): Promise<void> {
  root.innerHTML = renderLoading("正在取回你的正式命局认知");
  try {
    ({ account, cases } = await loadExperienceBootstrap());
    if (!cases.length) {
      root.innerHTML = renderUnavailable(
        "还没有可以阅读的命局",
        "先让阿布帮你建立出生档案，并完成第一份整盘基线。",
        "去找阿布建档",
      );
      return;
    }
    const requested = new URLSearchParams(location.search).get("case") || "";
    const selected = cases.find((item) => item.case_id === requested)
      || cases.find((item) => item.baseline_available)
      || cases[0];
    await openCase(selected.case_id);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    const unauthenticated = message.includes("authentication_required");
    root.innerHTML = renderUnavailable(
      unauthenticated ? "先和阿布打个招呼" : "这份命局暂时没有准备好",
      unauthenticated ? "登录后，阿布会继续你已经建立的 LifeCase。" : humanizeError(message),
      unauthenticated ? "登录或注册" : "返回阿布入口",
    );
  }
}


async function openCase(caseId: string): Promise<void> {
  timeline?.stop();
  activeCaseId = caseId;
  const loaded = await loadExperienceCase(caseId, new URLSearchParams(location.search));
  workspace = loaded.workspace;
  envelope = loaded.envelope;
  canvas = loaded.canvas;
  canvasContext = loaded.canvasContext;
  narrationManifest = loaded.narrationManifest;
  narrationAssets = loaded.narrationAssets;
  availableSurfaces = loaded.availableSurfaces;
  availableAreas = loaded.availableAreas;
  ui = loaded.ui;
  timeline = narrationManifest
    ? createNarrationTimeline(caseId, narrationManifest, narrationAssets, dispatch, focusAnchor, humanizeError)
    : null;
  updateExperienceLocation(activeCaseId, ui);
  render();
}


function render(): void {
  if (!envelope || !workspace) return;
  root.innerHTML = renderExperience({
    accountName: account.display_name,
    accountRole: account.role,
    cases,
    activeCaseId,
    availableAreas,
    availableSurfaces,
    workspace,
    envelope,
    narrationManifest,
    canvas,
    canvasContext,
    ui,
  });
  bindExperienceInteractions(root, {
    selectArea,
    selectSurface,
    selectAnchor(anchor, message) {
      dispatch({ type: "select", anchor, message });
      focusAnchor(anchor);
    },
    toggleSection(section) {
      dispatch({ type: "toggle-section", section });
    },
    command(command) {
      void handleCommand(command);
    },
    playSegment(index) {
      void timeline?.playSegment(index);
    },
    selectCanvasStage,
    selectCanvasLayer,
    selectCanvasObject(selected) {
      void refreshCanvasContext(selected);
    },
    selectCase(caseId) {
      root.innerHTML = renderLoading("正在切换命盘");
      void openCase(caseId);
    },
  });
  requestAnimationFrame(() => applyActiveAnchor(ui.selectedAnchor));
}


function selectArea(area: ProductArea): void {
  if (!availableAreas.includes(area)) return;
  ui = reduceUi(ui, { type: "product-area", area });
  if (area === "lab") selectLabLayer();
  updateExperienceLocation(activeCaseId, ui);
  render();
}


function selectSurface(surface: WorkspaceSurface): void {
  if (!availableSurfaces.includes(surface)) return;
  ui = reduceUi(ui, { type: "workspace-surface", surface });
  updateExperienceLocation(activeCaseId, ui);
  render();
}


function selectCanvasStage(stage: CanvasStage): void {
  if (!canvas) return;
  const projection = canvas.stages[stage];
  canvasContext = projection.context;
  ui = reduceUi(ui, {
    type: "canvas-stage",
    stage,
    layer: projection.default_layer_id,
    selected: projection.context.selected_object_refs[0] || projection.spec.semantic_slots[0]?.slot_ref || "",
  });
  render();
}


function selectCanvasLayer(layer: CanvasLayer): void {
  if (!canvas) return;
  ui = reduceUi(ui, { type: "canvas-layer", layer });
  render();
  if (ui.selectedCanvasObject) void refreshCanvasContext(ui.selectedCanvasObject);
}


async function refreshCanvasContext(selected: string): Promise<void> {
  if (!canvas) return;
  ui = reduceUi(ui, { type: "canvas-select", selected, status: "loading" });
  render();
  try {
    canvasContext = await loadCanvasContext(activeCaseId, ui.canvasStage, selected, ui.canvasLayer);
    ui = reduceUi(ui, { type: "canvas-context-status", status: "ready" });
  } catch {
    canvasContext = null;
    ui = reduceUi(ui, { type: "canvas-context-status", status: "error" });
  }
  render();
}


async function handleCommand(command: string): Promise<void> {
  if (command === "toggle-abu") {
    dispatch({ type: "toggle-abu" });
    return;
  }
  if (command === "listen") {
    dispatch({ type: "toggle-abu", expanded: true });
    if (!timeline) {
      dispatch({ type: "narration", status: "error", message: "这份案例暂时没有可播放的正式讲解。" });
    } else if (ui.narrationStatus === "playing") {
      timeline.pause();
    } else {
      await timeline.play();
    }
    return;
  }
  if (command === "stop") {
    timeline?.stop();
    dispatch({ type: "narration", status: "idle", index: -1, message: "已停止。你可以点任意命理对象，让我从那里继续。" });
    return;
  }
  if (command === "focus-pillars") focusAnchor("four-pillars");
}


function selectLabLayer(): void {
  if (!canvas) return;
  const layer = canvas.stages[ui.canvasStage].layers.find((item) => (
    item.layer_id === "generation_control" && item.available
  ));
  if (layer) ui = reduceUi(ui, { type: "canvas-layer", layer: layer.layer_id });
}


function dispatch(action: UiAction): void {
  ui = reduceUi(ui, action);
  render();
}


function focusAnchor(anchor: string, scroll = true): void {
  ui = reduceUi(ui, { type: "select", anchor, message: ui.abuMessage });
  applyActiveAnchor(anchor);
  if (scroll) {
    document.querySelector<HTMLElement>(`[data-anchor="${CSS.escape(anchor)}"]`)?.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
  }
}
