import {
  loadCanvasContext,
  loadCognitiveJob,
  loadNarration,
  loadReadOnlyCanvas,
  startMissingBaseline,
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
  WorkspaceCognitionState,
} from "./contracts";
import { loadExperienceCase } from "./experience_data";
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
let activeProfileId = "";
let workspace: CaseWorkspaceEnvelope | null = null;
let cognition: WorkspaceCognitionState | null = null;
let availableSurfaces: WorkspaceSurface[] = ["overview"];
let availableAreas: ProductArea[] = ["world", "workbench"];
let envelope: MingliExperienceEnvelope | null = null;
let canvas: ReadOnlySixPillarCanvas | null = null;
let canvasContext: CanvasContextPack | null = null;
let narrationManifest: NarrationManifest | null = null;
let narrationAssets: Record<string, NarrationStatus> = {};
let timeline: NarrationTimeline | null = null;
let ui: UiState = structuredClone(initialUiState);
let canvasLoading = false;
let narrationLoading = false;
let cognitionEpoch = 0;
let openCaseEpoch = 0;
const localReconciliationAttempted = new Set<string>();

void boot();


async function boot(): Promise<void> {
  root.innerHTML = renderLoading("正在打开你的命局");
  try {
    const params = new URLSearchParams(location.search);
    await openCase({
      caseId: params.get("case") || "",
      profileId: params.get("profile") || "",
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    const unauthenticated = message.includes("authentication_required");
    root.innerHTML = renderUnavailable(
      unauthenticated ? "先和阿布打个招呼" : "这份命局暂时没有准备好",
      unauthenticated ? "登录后，阿布会继续你已经建立的档案。" : humanizeError(message),
      unauthenticated ? "登录或注册" : "返回阿布入口",
    );
  }
}


async function openCase(
  selection: { caseId?: string; profileId?: string },
  preserveUi = false,
): Promise<void> {
  const requestEpoch = ++openCaseEpoch;
  cognitionEpoch += 1;
  const previousCaseId = activeCaseId;
  const loaded = await loadExperienceCase(
    selection,
    new URLSearchParams(location.search),
    preserveUi ? ui : undefined,
  );
  if (requestEpoch !== openCaseEpoch) return;
  if (loaded.profileRequired || !loaded.envelope) {
    account = loaded.account;
    cases = loaded.cases;
    root.innerHTML = renderUnavailable(
      "先建立一份出生档案",
      "保存四柱后会直接进入命局，不需要再经过一次“开始测算”。",
      "建立档案",
    );
    return;
  }
  const caseChanged = Boolean(previousCaseId && previousCaseId !== loaded.selectedCaseId);
  timeline?.stop();
  if (caseChanged || preserveUi) {
    canvas = null;
    canvasContext = null;
    narrationManifest = null;
    narrationAssets = {};
    timeline = null;
  }
  account = loaded.account;
  cases = loaded.cases;
  activeCaseId = loaded.selectedCaseId;
  activeProfileId = loaded.selectedProfileId;
  workspace = loaded.workspace;
  envelope = loaded.envelope;
  cognition = loaded.cognition;
  availableSurfaces = loaded.availableSurfaces;
  availableAreas = loaded.availableAreas;
  ui = loaded.ui;
  updateExperienceLocation(activeCaseId, ui);
  render();
  void loadSelectedProjection();
  scheduleBackgroundCognition();
}


function render(): void {
  if (!envelope || !cognition) return;
  root.innerHTML = renderExperience({
    accountName: account.display_name,
    accountRole: account.role,
    cases,
    activeCaseId,
    activeProfileId,
    availableAreas,
    availableSurfaces,
    workspace,
    envelope,
    cognition,
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
      void playNarrationSegment(index);
    },
    selectCanvasStage,
    selectCanvasLayer,
    selectCanvasObject(selected) {
      void refreshCanvasContext(selected);
    },
    selectProfile(profileId) {
      root.innerHTML = renderLoading("正在切换命盘");
      void openCase({ profileId });
    },
  });
  requestAnimationFrame(() => applyActiveAnchor(ui.selectedAnchor));
}


function selectArea(area: ProductArea): void {
  if (!availableAreas.includes(area)) return;
  ui = reduceUi(ui, { type: "product-area", area });
  if (area === "lab") {
    selectLabLayer();
    void ensureCanvas();
  }
  updateExperienceLocation(activeCaseId, ui);
  render();
}


function selectSurface(surface: WorkspaceSurface): void {
  if (!availableSurfaces.includes(surface)) return;
  ui = reduceUi(ui, { type: "workspace-surface", surface });
  updateExperienceLocation(activeCaseId, ui);
  render();
  void loadSelectedProjection();
}


async function loadSelectedProjection(): Promise<void> {
  if (ui.productArea === "lab" || ui.workspaceSurface === "onecanvas") await ensureCanvas();
  if (ui.workspaceSurface === "theater") await ensureNarration();
}


async function ensureCanvas(): Promise<void> {
  if (canvas || canvasLoading || !activeCaseId) return;
  canvasLoading = true;
  try {
    canvas = await loadReadOnlyCanvas(activeCaseId);
    const projection = canvas.stages[canvas.default_stage];
    canvasContext = projection.context;
    ui = reduceUi(ui, {
      type: "canvas-stage",
      stage: canvas.default_stage,
      layer: projection.default_layer_id,
      selected: projection.context.selected_object_refs[0] || projection.spec.semantic_slots[0]?.slot_ref || "",
    });
    if (ui.productArea === "lab") selectLabLayer();
  } catch {
    canvas = null;
    canvasContext = null;
  } finally {
    canvasLoading = false;
    render();
  }
}


async function ensureNarration(): Promise<boolean> {
  if (narrationManifest && timeline) return true;
  if (narrationLoading || !activeCaseId) return false;
  narrationLoading = true;
  try {
    const loaded = await loadNarration(activeCaseId);
    narrationManifest = loaded.manifest;
    narrationAssets = loaded.speechAssets;
    timeline = createNarrationTimeline(
      activeCaseId,
      narrationManifest,
      narrationAssets,
      dispatch,
      focusAnchor,
      humanizeError,
    );
    return true;
  } catch {
    narrationManifest = null;
    narrationAssets = {};
    timeline = null;
    return false;
  } finally {
    narrationLoading = false;
    render();
  }
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


async function playNarrationSegment(index: number): Promise<void> {
  if (await ensureNarration()) await timeline?.playSegment(index);
}


async function handleCommand(command: string): Promise<void> {
  if (command === "toggle-abu") {
    dispatch({ type: "toggle-abu" });
    return;
  }
  if (command === "listen") {
    dispatch({ type: "toggle-abu", expanded: true });
    if (!(await ensureNarration()) || !timeline) {
      dispatch({ type: "narration", status: "error", message: "四柱已经就绪，语音暂时没有连接上。" });
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


function scheduleBackgroundCognition(): void {
  const epoch = ++cognitionEpoch;
  requestAnimationFrame(() => void continueBackgroundCognition(epoch));
}


async function continueBackgroundCognition(epoch: number): Promise<void> {
  if (epoch !== cognitionEpoch || !cognition || !activeCaseId) return;
  if (cognition.status === "ready") return;
  if (cognition.status === "preparing" && cognition.background_job_id) {
    await pollCognitiveJob(cognition.background_job_id, epoch);
    return;
  }
  const shouldReconcile = cognition.status === "partial"
    && !localReconciliationAttempted.has(activeCaseId);
  if (!cognition.background_start_allowed && !shouldReconcile) return;
  if (shouldReconcile) localReconciliationAttempted.add(activeCaseId);
  try {
    const started = await startMissingBaseline(activeCaseId);
    if (epoch !== cognitionEpoch) return;
    if (started.status === "baseline_preparing" && started.job_id) {
      cognition = {
        ...cognition,
        status: "preparing",
        message: "四柱已经就绪，阿布正在梳理整盘主线。",
        background_start_allowed: false,
        background_job_id: started.job_id,
      };
      render();
      await pollCognitiveJob(started.job_id, epoch);
      return;
    }
    if (started.status === "baseline_reconciled" || started.status === "baseline_cache_reused") {
      await refreshWorkspaceAfterCognition(epoch);
      return;
    }
    cognition = {
      ...cognition,
      status: "partial",
      message: "四柱与已确认内容都可以继续查看，其他部分暂时保留。",
      background_start_allowed: false,
    };
    render();
  } catch {
    cognition = {
      ...cognition,
      status: "partial",
      message: "四柱已经就绪，整盘主线稍后再继续整理。",
      background_start_allowed: false,
    };
    render();
  }
}


async function pollCognitiveJob(jobId: string, epoch: number): Promise<void> {
  for (let attempt = 0; attempt < 90 && epoch === cognitionEpoch; attempt += 1) {
    await delay(1500);
    let job;
    try {
      job = await loadCognitiveJob(jobId);
    } catch {
      return;
    }
    if (job.status === "completed" || job.status === "failed") {
      await refreshWorkspaceAfterCognition(epoch);
      return;
    }
  }
}


async function refreshWorkspaceAfterCognition(epoch: number): Promise<void> {
  if (epoch !== cognitionEpoch) return;
  await openCase({ caseId: activeCaseId, profileId: activeProfileId }, true);
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


function delay(milliseconds: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}
