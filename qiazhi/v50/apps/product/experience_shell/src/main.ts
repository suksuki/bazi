import {
  loadCaseWorkspace,
  loadAccount,
  loadCanvasContext,
  loadCases,
  loadEnvelope,
  loadNarration,
  loadReadOnlyCanvas,
} from "./api";
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
import {
  initialUiState,
  reduceUi,
  type ProductArea,
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
    account = await loadAccount();
    cases = await loadCases();
    if (!cases.length) {
      root.innerHTML = renderUnavailable(
        "还没有可以阅读的命局",
        "先让阿布帮你建立出生档案，并完成第一份整盘基线。",
        "去找阿布建档",
      );
      return;
    }
    const requested = new URLSearchParams(location.search).get("case") || "";
    const selected = cases.find((item) => item.case_id === requested) || cases.find((item) => item.baseline_available) || cases[0];
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
  ui = structuredClone(initialUiState);
  const [envelopeResult, workspaceResult, canvasResult, narrationResult] = await Promise.allSettled([
    loadEnvelope(caseId),
    loadCaseWorkspace(caseId),
    loadReadOnlyCanvas(caseId),
    loadNarration(caseId),
  ]);
  if (envelopeResult.status === "rejected") throw envelopeResult.reason;
  if (workspaceResult.status === "rejected") throw workspaceResult.reason;
  envelope = envelopeResult.value;
  workspace = workspaceResult.value;

  if (canvasResult.status === "fulfilled") {
    canvas = canvasResult.value;
    const initialStage = canvas.default_stage;
    const initialProjection = canvas.stages[initialStage];
    canvasContext = initialProjection.context;
    ui = reduceUi(ui, {
      type: "canvas-stage",
      stage: initialStage,
      layer: initialProjection.default_layer_id,
      selected: initialProjection.context.selected_object_refs[0] || initialProjection.spec.semantic_slots[0]?.slot_ref || "",
    });
  } else {
    canvas = null;
    canvasContext = null;
  }
  if (narrationResult.status === "fulfilled") {
    const narration = narrationResult.value;
    narrationManifest = narration.manifest;
    narrationAssets = narration.speechAssets;
  } else {
    narrationManifest = null;
    narrationAssets = {};
  }
  availableSurfaces = workspace.allowed_surfaces.filter((surface) => (
    surface === "overview"
    || (surface === "onecanvas" && canvas !== null)
    || (surface === "theater" && narrationManifest !== null)
  ));
  availableAreas = workspace.allowed_surfaces.includes("mingli_lab")
    ? ["world", "workbench", "lab"]
    : ["world", "workbench"];
  const params = new URLSearchParams(location.search);
  const requestedSurface = params.get("surface") as WorkspaceSurface | null;
  const preferredSurface = requestedSurface || workspace.state.current_surface;
  ui = reduceUi(ui, {
    type: "workspace-surface",
    surface: supportedSurface(preferredSurface) ? preferredSurface : "overview",
  });
  const requestedArea = params.get("area") as ProductArea | null;
  const preferredArea = requestedArea
    || (requestedSurface || preferredSurface !== "overview" ? "workbench" : "world");
  ui = reduceUi(ui, {
    type: "product-area",
    area: supportedArea(preferredArea) ? preferredArea : "world",
  });
  if (ui.productArea === "lab") selectLabLayer();
  timeline = narrationManifest ? createTimeline(caseId, narrationManifest, narrationAssets) : null;
  updateLocation();
  render();
}

function createTimeline(
  caseId: string,
  manifest: NarrationManifest,
  statuses: Record<string, NarrationStatus>,
): NarrationTimeline {
  return new NarrationTimeline(caseId, manifest, statuses, {
    onPreparing(segment, index) {
      dispatch({ type: "narration", status: "preparing", index, message: `我正在准备“${segment.title}”。页面可以先看，不用等我。` });
    },
    onPlaying(segment, index) {
      dispatch({ type: "narration", status: "playing", index, message: segment.text });
      focusAnchor(segment.visual_anchor_ids[0] || "baseline-summary", false);
    },
    onPaused(segment, index) {
      dispatch({ type: "narration", status: "paused", index, message: `停在“${segment.title}”。你可以先看页面，也可以继续听。` });
    },
    onComplete() {
      dispatch({ type: "narration", status: "complete", index: -1, message: "这次先讲到这里。你可以点四柱、路径或未决项继续问。" });
    },
    onError(error) {
      dispatch({ type: "narration", status: "error", message: `声音暂时没有准备好：${humanizeError(error.message)}。文字内容仍然完整可读。` });
    },
    onCue(anchor) {
      focusAnchor(anchor, false);
    },
  });
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
  bindInteractions();
  requestAnimationFrame(() => applyActiveAnchor(ui.selectedAnchor));
}

function bindInteractions(): void {
  root.querySelectorAll<HTMLButtonElement>("[data-product-area]").forEach((button) => {
    button.addEventListener("click", () => {
      const area = button.dataset.productArea as ProductArea;
      if (!supportedArea(area)) return;
      ui = reduceUi(ui, { type: "product-area", area });
      if (area === "lab") selectLabLayer();
      updateLocation();
      render();
    });
  });
  root.querySelectorAll<HTMLButtonElement>("[data-workspace-surface]").forEach((button) => {
    button.addEventListener("click", () => {
      const surface = button.dataset.workspaceSurface as WorkspaceSurface;
      if (!supportedSurface(surface)) return;
      ui = reduceUi(ui, { type: "workspace-surface", surface });
      updateLocation();
      render();
    });
  });
  root.querySelectorAll<HTMLElement>("[data-select-anchor]").forEach((element) => {
    element.addEventListener("click", () => {
      const anchor = element.dataset.selectAnchor || "baseline-summary";
      const message = element.dataset.message || "这一处来自正式命局认知。";
      dispatch({ type: "select", anchor, message });
      focusAnchor(anchor);
    });
  });
  root.querySelectorAll<HTMLButtonElement>("[data-toggle-section]").forEach((button) => {
    button.addEventListener("click", () => dispatch({ type: "toggle-section", section: button.dataset.toggleSection || "baseline" }));
  });
  root.querySelectorAll<HTMLButtonElement>("[data-command]").forEach((button) => {
    button.addEventListener("click", () => void handleCommand(button.dataset.command || ""));
  });
  root.querySelectorAll<HTMLButtonElement>("[data-play-segment]").forEach((button) => {
    button.addEventListener("click", () => void timeline?.playSegment(Number(button.dataset.playSegment || 0)));
  });
  root.querySelectorAll<HTMLButtonElement>("[data-canvas-stage]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!canvas) return;
      const stage = (button.dataset.canvasStage || "natal") as CanvasStage;
      const projection = canvas.stages[stage];
      canvasContext = projection.context;
      ui = reduceUi(ui, {
        type: "canvas-stage",
        stage,
        layer: projection.default_layer_id,
        selected: projection.context.selected_object_refs[0] || projection.spec.semantic_slots[0]?.slot_ref || "",
      });
      render();
    });
  });
  root.querySelectorAll<HTMLButtonElement>("[data-canvas-layer]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!canvas || button.disabled) return;
      const layer = (button.dataset.canvasLayer || "generation_control") as CanvasLayer;
      ui = reduceUi(ui, { type: "canvas-layer", layer });
      render();
      if (ui.selectedCanvasObject) void refreshCanvasContext(ui.selectedCanvasObject);
    });
  });
  root.querySelectorAll<Element>("[data-canvas-object]").forEach((element) => {
    element.addEventListener("click", () => {
      const selected = element.getAttribute("data-canvas-object") || "";
      if (selected) void refreshCanvasContext(selected);
    });
    element.addEventListener("keydown", (event) => {
      if (event instanceof KeyboardEvent && (event.key === "Enter" || event.key === " ")) {
        event.preventDefault();
        const selected = element.getAttribute("data-canvas-object") || "";
        if (selected) void refreshCanvasContext(selected);
      }
    });
  });
  root.querySelector<HTMLSelectElement>("[data-case-select]")?.addEventListener("change", (event) => {
    const select = event.currentTarget as HTMLSelectElement;
    root.innerHTML = renderLoading("正在切换命盘");
    void openCase(select.value);
  });
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

function supportedSurface(surface: WorkspaceSurface): boolean {
  return availableSurfaces.includes(surface);
}

function supportedArea(area: ProductArea): boolean {
  return availableAreas.includes(area);
}

function selectLabLayer(): void {
  if (!canvas) return;
  const projection = canvas.stages[ui.canvasStage];
  const layer = projection.layers.find((item) => (
    item.layer_id === "generation_control" && item.available
  ));
  if (layer) ui = reduceUi(ui, { type: "canvas-layer", layer: layer.layer_id });
}

function updateLocation(): void {
  const params = new URLSearchParams({ case: activeCaseId });
  if (ui.productArea !== "world") params.set("area", ui.productArea);
  if (ui.productArea === "workbench" && ui.workspaceSurface !== "overview") {
    params.set("surface", ui.workspaceSurface);
  }
  history.replaceState({}, "", `/experience?${params.toString()}`);
}

function dispatch(action: Parameters<typeof reduceUi>[1]): void {
  ui = reduceUi(ui, action);
  render();
}

function focusAnchor(anchor: string, scroll = true): void {
  ui = reduceUi(ui, { type: "select", anchor, message: ui.abuMessage });
  applyActiveAnchor(anchor);
  if (scroll) document.querySelector<HTMLElement>(`[data-anchor="${CSS.escape(anchor)}"]`)?.scrollIntoView({ behavior: "smooth", block: "center" });
}

function applyActiveAnchor(anchor: string): void {
  document.querySelectorAll(".narration-active").forEach((element) => element.classList.remove("narration-active"));
  document.querySelectorAll<HTMLElement>(`[data-anchor="${CSS.escape(anchor)}"], [data-select-anchor="${CSS.escape(anchor)}"]`).forEach((element) => element.classList.add("narration-active"));
}

function humanizeError(message: string): string {
  return message
    .replace(/^formal_life_case_not_available$/, "正式整盘认知尚未通过可靠性门禁。")
    .replace(/^experience_case_not_found$/, "没有找到这份案例，或它不属于当前账户。")
    .replace(/^canvas_official_timing_required$/, "这份案例还没有完整的大运与流年计算。")
    .replace(/_/g, " ");
}
