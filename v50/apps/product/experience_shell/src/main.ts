import {
  authenticate,
  deleteProfile as deleteProductProfile,
  loadCanvasContext,
  loadCognitiveJob,
  loadNarration,
  loadProfiles,
  loadReadOnlyCanvas,
  logout,
  saveProfile,
  startMissingBaseline,
  type AuthMode,
  type BirthProfileInput,
  type ProductProfile,
} from "./api";
import { renderAuthSurface, renderProfileManager, type ProfileEditorMode } from "./account_components";
import { bindAccountInteractions } from "./account_interactions";
import { NarrationTimeline } from "./audio";
import { renderExperience, renderLoading, renderUnavailable } from "./components";
import type {
  CaseWorkspaceEnvelope,
  CanvasContextPack,
  CanvasLayer,
  CanvasStage,
  CanvasVisibilityLayer,
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
import { OpeningMusicController } from "./opening_music";
import {
  createDreamVisit,
  enterDreamVisit,
  grantDreamConsent,
  loadDreamStatus,
  markDreamNavigationHandoff,
  migrateGuestDreamAnchor,
  withdrawDreamConsent,
  type DreamFeatureStatus,
} from "./dream_api";
import { bootDreamExperience } from "./dream_runtime";
import {
  beginDreamEntryTransition,
  resumeDreamEntryTransition,
} from "./dream_entry_transition";
import { consumeDreamReturnedWithSeed } from "./dream_story_runtime";
import {
  answerRealLifeTreeQuestion,
  loadRealLifeTree,
  loadRealMingliLab,
  type LifeTreeQuestionCategory,
  type RealLifeTreeBootstrap,
  type RealMingliLabBootstrap,
} from "./relation_work_api";
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
const openingMusic = new OpeningMusicController(syncOpeningMusicControls);

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
let authMode: AuthMode = "login";
let accountProfiles: ProductProfile[] = [];
let profileEditorMode: ProfileEditorMode = "none";
let editingProfileId = "";
let accountBusy = false;
let accountError = "";
let dreamStatus: DreamFeatureStatus | null = null;
const dreamReturnedWithSeed = consumeDreamReturnedWithSeed();
let realLifeTree: RealLifeTreeBootstrap | null = null;
let realLifeTreeLoading = false;
let realLifeTreeError = "";
let selectedLifeTreeQuestionId = "";
let selectedLifeTreeCategory: LifeTreeQuestionCategory = "factual_observation";
let selectedLifeTreeOptionId = "";
let lifeTreeAnswerSaving = false;
let realMingliLab: RealMingliLabBootstrap | null = null;
let realMingliLabLoading = false;
let realMingliLabError = "";
let relationLabMode: "facts" | "candidates" | "professional" = "candidates";
let selectedRelationPathRef = "";
let selectedRelationFactRef = "";

if (location.pathname.startsWith("/experience/dream")) {
  const entryTransition = resumeDreamEntryTransition();
  void bootDreamExperience(root).finally(() => entryTransition?.markDestinationReady());
} else {
  void boot();
}


async function boot(): Promise<void> {
  root.innerHTML = renderLoading("正在打开你的命局");
  try {
    const params = new URLSearchParams(location.search);
    await openCase({
      caseId: params.get("case") || "",
      profileId: params.get("profile") || "",
    });
    if (params.get("manage") === "1" && envelope) await openProfileManager();
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    const unauthenticated = message.includes("authentication_required");
    if (unauthenticated) showAuth();
    else root.innerHTML = renderUnavailable(
      "这份命局暂时没有准备好",
      humanizeError(message),
      "管理档案",
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
    await openProfileManager("create");
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
    realLifeTree = null;
    realLifeTreeError = "";
    selectedLifeTreeQuestionId = "";
    selectedLifeTreeOptionId = "";
    realMingliLab = null;
    realMingliLabError = "";
    selectedRelationPathRef = "";
    selectedRelationFactRef = "";
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
  void ensureRealLifeTree();
  void loadSelectedProjection();
  void refreshDreamStatus();
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
    dreamStatus,
    dreamReturnedWithSeed,
    realLifeTree,
    realLifeTreeLoading,
    realLifeTreeError,
    selectedLifeTreeQuestionId,
    selectedLifeTreeCategory,
    selectedLifeTreeOptionId,
    lifeTreeAnswerSaving,
    realMingliLab,
    realMingliLabLoading,
    realMingliLabError,
    relationLabMode,
    selectedRelationPathRef,
    selectedRelationFactRef,
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
    selectCanvasVisibility,
    selectCanvasObject(selected) {
      selectRelationFactForNode(selected);
      void refreshCanvasContext(selected);
    },
    selectProfile(profileId) {
      root.innerHTML = renderLoading("正在切换命盘");
      void openCase({ profileId });
    },
    selectLifeTreeQuestion(questionId, category) {
      selectedLifeTreeQuestionId = questionId;
      selectedLifeTreeCategory = category;
      selectedLifeTreeOptionId = "";
      realLifeTreeError = "";
      render();
    },
    selectLifeTreeOption(optionId) {
      selectedLifeTreeOptionId = optionId;
      render();
    },
    submitLifeTreeAnswer() {
      void submitRealLifeTreeAnswer();
    },
    selectRelationLabMode(mode) {
      relationLabMode = mode;
      if (mode === "facts") {
        const visible = realMingliLab?.relation_work.factual_view.find(
          (item) => item.inventory_visible,
        );
        selectedRelationFactRef = visible?.fact_revision_ref || "";
      }
      render();
    },
    selectRelationPath(pathRef) {
      selectedRelationPathRef = pathRef;
      relationLabMode = "candidates";
      const path = realMingliLab?.relation_work.candidate_path_view.find(
        (item) => item.work_path_candidate_ref === pathRef,
      );
      selectedRelationFactRef = path?.ordered_fact_revision_refs[0] || "";
      render();
    },
    selectRelationFact(factRef) {
      selectedRelationFactRef = factRef;
      const path = realMingliLab?.relation_work.candidate_path_view.find(
        (item) => (
          realMingliLab?.path_focus.visible_path_refs.includes(
            item.work_path_candidate_ref,
          )
          && item.ordered_fact_revision_refs.includes(factRef)
        ),
      );
      if (path && relationLabMode === "candidates") {
        selectedRelationPathRef = path.work_path_candidate_ref;
      }
      render();
    },
    restoreRelationNatal() {
      selectCanvasStage("natal");
    },
  });
  syncOpeningMusicControls();
  openingMusic.arm();
  requestAnimationFrame(() => applyActiveAnchor(ui.selectedAnchor));
}


function syncOpeningMusicControls(): void {
  openingMusic.syncControls(root);
}


function selectArea(area: ProductArea): void {
  if (!availableAreas.includes(area)) return;
  ui = reduceUi(ui, { type: "product-area", area });
  if (area === "lab") {
    selectLabLayer();
    void ensureCanvas();
    void ensureRealMingliLab();
  } else {
    ui = reduceUi(ui, { type: "canvas-visibility", visibility: "formal" });
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
  if (ui.productArea === "lab" || ui.workspaceSurface === "onecanvas") {
    await ensureCanvas();
  }
  if (ui.productArea === "lab") await ensureRealMingliLab();
  if (ui.workspaceSurface === "theater") await ensureNarration();
}


async function ensureRealLifeTree(): Promise<void> {
  if (realLifeTree || realLifeTreeLoading || !activeCaseId) return;
  realLifeTreeLoading = true;
  realLifeTreeError = "";
  render();
  try {
    realLifeTree = await loadRealLifeTree(activeCaseId);
  } catch (error) {
    realLifeTree = null;
    realLifeTreeError = humanizeError(
      error instanceof Error ? error.message : String(error),
    );
  } finally {
    realLifeTreeLoading = false;
    render();
  }
}


async function submitRealLifeTreeAnswer(): Promise<void> {
  if (
    lifeTreeAnswerSaving
    || !activeCaseId
    || !selectedLifeTreeQuestionId
    || !selectedLifeTreeOptionId
  ) return;
  lifeTreeAnswerSaving = true;
  realLifeTreeError = "";
  render();
  try {
    await answerRealLifeTreeQuestion(
      activeCaseId,
      selectedLifeTreeQuestionId,
      selectedLifeTreeOptionId,
    );
    realLifeTree = await loadRealLifeTree(activeCaseId);
    selectedLifeTreeOptionId = "";
  } catch (error) {
    realLifeTreeError = humanizeError(
      error instanceof Error ? error.message : String(error),
    );
  } finally {
    lifeTreeAnswerSaving = false;
    render();
  }
}


async function ensureRealMingliLab(): Promise<void> {
  if (realMingliLab || realMingliLabLoading || !activeCaseId) return;
  realMingliLabLoading = true;
  realMingliLabError = "";
  render();
  try {
    realMingliLab = await loadRealMingliLab(activeCaseId);
    selectedRelationPathRef = (
      realMingliLab.path_focus.primary_path_ref
    );
    const primary = realMingliLab.relation_work.candidate_path_view.find(
      (item) => (
        item.work_path_candidate_ref
        === realMingliLab?.path_focus.primary_path_ref
      ),
    );
    selectedRelationFactRef = primary?.ordered_fact_revision_refs[0] || "";
  } catch (error) {
    realMingliLab = null;
    realMingliLabError = humanizeError(
      error instanceof Error ? error.message : String(error),
    );
  } finally {
    realMingliLabLoading = false;
    render();
  }
}


function selectRelationFactForNode(nodeRef: string): void {
  if (ui.productArea !== "lab" || !realMingliLab) return;
  const visiblePathRefs = new Set(realMingliLab.path_focus.visible_path_refs);
  const visiblePathFactRefs = new Set(
    realMingliLab.relation_work.candidate_path_view
      .filter((path) => visiblePathRefs.has(path.work_path_candidate_ref))
      .flatMap((path) => path.ordered_fact_revision_refs),
  );
  const connected = realMingliLab.relation_work.factual_view.find((fact) => (
    fact.participant_refs.includes(nodeRef)
    && (
      relationLabMode === "facts"
        ? fact.inventory_visible
        : visiblePathFactRefs.has(fact.fact_revision_ref)
    )
  ));
  if (connected) selectedRelationFactRef = connected.fact_revision_ref;
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


function selectCanvasVisibility(visibility: CanvasVisibilityLayer): void {
  if (!canvas || !canvas.renderer_policy.available_visibility_layers.includes(visibility)) return;
  ui = reduceUi(ui, { type: "canvas-visibility", visibility });
  render();
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
  openingMusic.pauseForNarration();
  if (await ensureNarration()) await timeline?.playSegment(index);
}


async function handleCommand(command: string): Promise<void> {
  if (command === "toggle-opening-music") {
    await openingMusic.toggle();
    return;
  }
  if (command === "manage-profiles") {
    await openProfileManager();
    return;
  }
  if (command === "toggle-abu") {
    dispatch({ type: "toggle-abu" });
    return;
  }
  if (command === "enter-dream") {
    let entryTransition: ReturnType<typeof beginDreamEntryTransition> | null = null;
    try {
      const guestCapability = sessionStorage.getItem("deepbazi.dream.guest-anchor-capability.v1");
      if (
        guestCapability
        && await confirmDreamAction(
          "只恢复这台设备上未登录时的梦境离开位置？不会迁移命理事实、授权或访问历史。",
          "恢复位置",
        )
      ) {
        await migrateGuestDreamAnchor(activeCaseId, guestCapability, true);
        sessionStorage.removeItem("deepbazi.dream.guest-anchor-capability.v1");
      }
      entryTransition = beginDreamEntryTransition();
      let visit = await createDreamVisit(activeCaseId);
      visit = await enterDreamVisit(visit.visit_id);
      entryTransition?.bindVisit(visit.visit_id);
      await entryTransition?.waitUntilVisible();
      markDreamNavigationHandoff();
      location.assign(`/experience/dream/visits/${encodeURIComponent(visit.visit_id)}`);
    } catch (error) {
      entryTransition?.cancel();
      const message = error instanceof Error ? error.message : String(error);
      root.innerHTML = renderUnavailable("这条梦路暂时没有开放", humanizeError(message), "回到生命世界");
    }
    return;
  }
  if (command === "grant-dream-consent") {
    const accepted = await confirmDreamAction(
      "授权当前档案以匿名生命树进入本地封闭梦境？仅展示确定性命盘与只读树象，你可以随时撤回。",
      "确认授权",
    );
    if (!accepted) return;
    try {
      await grantDreamConsent(activeCaseId);
      await refreshDreamStatus();
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      window.alert(`授权未完成：${humanizeError(message)}`);
    }
    return;
  }
  if (command === "withdraw-dream-consent") {
    const confirmed = await confirmDreamAction(
      "撤回当前档案的梦境展示授权？撤回后，这棵真人生命树会立即失去进入资格。",
      "确认撤回",
    );
    if (!confirmed) return;
    try {
      await withdrawDreamConsent(activeCaseId);
      await refreshDreamStatus();
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      window.alert(`撤回未完成：${humanizeError(message)}`);
    }
    return;
  }
  if (command === "listen") {
    openingMusic.pauseForNarration();
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


function confirmDreamAction(message: string, confirmLabel: string): Promise<boolean> {
  const dialog = document.createElement("dialog");
  dialog.className = "dream-consent-dialog";
  dialog.setAttribute("aria-labelledby", "dream-consent-dialog-title");
  dialog.innerHTML = `<form method="dialog">
    <p id="dream-consent-dialog-title"></p>
    <div>
      <button type="submit" value="cancel">暂不</button>
      <button class="is-primary" type="submit" value="confirm"></button>
    </div>
  </form>`;
  const copy = dialog.querySelector("p");
  const confirm = dialog.querySelector<HTMLButtonElement>('button[value="confirm"]');
  if (copy) copy.textContent = message;
  if (confirm) confirm.textContent = confirmLabel;
  document.body.append(dialog);
  return new Promise((resolve) => {
    const settle = (): void => {
      const accepted = dialog.returnValue === "confirm";
      dialog.remove();
      resolve(accepted);
    };
    dialog.addEventListener("close", settle, { once: true });
    dialog.showModal();
  });
}


async function refreshDreamStatus(): Promise<void> {
  try {
    dreamStatus = await loadDreamStatus(activeCaseId);
  } catch {
    dreamStatus = null;
  }
  render();
}


function selectLabLayer(): void {
  if (!canvas) return;
  const layer = canvas.stages[ui.canvasStage].layers.find((item) => (
    item.layer_id === "overview" && item.available
  ));
  if (layer) ui = reduceUi(ui, { type: "canvas-layer", layer: layer.layer_id });
  if (canvas.renderer_policy.available_visibility_layers.includes("lab_audit")) {
    ui = reduceUi(ui, { type: "canvas-visibility", visibility: "lab_audit" });
  }
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


function showAuth(error = ""): void {
  accountError = error;
  root.innerHTML = renderAuthSurface({ mode: authMode, busy: accountBusy, error: accountError });
  bindAccountInteractions(root, accountInteractionHandlers());
  history.replaceState({}, "", "/experience");
}


async function openProfileManager(preferredMode: ProfileEditorMode = "none"): Promise<void> {
  root.innerHTML = renderLoading("正在打开命理档案");
  try {
    accountProfiles = await loadProfiles();
    profileEditorMode = preferredMode === "none" && !accountProfiles.length ? "create" : preferredMode;
    editingProfileId = "";
    accountError = "";
    renderProfileManagement();
    history.replaceState({}, "", "/experience?manage=1");
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    if (message.includes("authentication_required")) showAuth();
    else {
      accountError = humanizeAccountError(message);
      accountProfiles = [];
      profileEditorMode = "create";
      renderProfileManagement();
    }
  }
}


function renderProfileManagement(): void {
  root.innerHTML = renderProfileManager({
    accountName: account.display_name,
    profiles: accountProfiles,
    activeProfileId,
    editorMode: profileEditorMode,
    editingProfileId,
    busy: accountBusy,
    error: accountError,
    canReturnToWorkspace: Boolean(envelope && cognition && activeCaseId),
  });
  bindAccountInteractions(root, accountInteractionHandlers());
}


function accountInteractionHandlers() {
  return {
    setAuthMode(mode: AuthMode) {
      authMode = mode;
      accountError = "";
      showAuth();
    },
    submitAuth(form: HTMLFormElement) {
      void submitAuthForm(form);
    },
    command(command: string) {
      void handleAccountCommand(command);
    },
    useProfile(profileId: string) {
      if (!profileId) return;
      root.innerHTML = renderLoading("正在进入命局");
      void openCase({ profileId });
    },
    editProfile(profileId: string) {
      profileEditorMode = "edit";
      editingProfileId = profileId;
      accountError = "";
      renderProfileManagement();
    },
    deleteProfile(profileId: string) {
      void removeProfile(profileId);
    },
    submitProfile(form: HTMLFormElement) {
      void submitProfileForm(form);
    },
  };
}


async function submitAuthForm(form: HTMLFormElement): Promise<void> {
  const data = new FormData(form);
  accountBusy = true;
  accountError = "";
  showAuth();
  try {
    const result = await authenticate({
      mode: authMode,
      email: String(data.get("email") || ""),
      password: String(data.get("password") || ""),
      displayName: String(data.get("display_name") || ""),
      role: String(data.get("role") || "member"),
    });
    account = {
      display_name: result.account.display_name,
      role: result.account.role || result.account.account_role || "member",
    };
    accountBusy = false;
    await openCase({});
  } catch (error) {
    accountBusy = false;
    accountError = humanizeAccountError(error instanceof Error ? error.message : String(error));
    showAuth(accountError);
  }
}


async function handleAccountCommand(command: string): Promise<void> {
  if (command === "create-profile") {
    profileEditorMode = "create";
    editingProfileId = "";
    accountError = "";
    renderProfileManagement();
    return;
  }
  if (command === "cancel-profile") {
    profileEditorMode = "none";
    editingProfileId = "";
    accountError = "";
    renderProfileManagement();
    return;
  }
  if (command === "return-workspace" && envelope && cognition) {
    updateExperienceLocation(activeCaseId, ui);
    render();
    void loadSelectedProjection();
    return;
  }
  if (command === "logout") {
    accountBusy = true;
    renderProfileManagement();
    try {
      await logout();
    } finally {
      timeline?.stop();
      accountBusy = false;
      account = { display_name: "", role: "member" };
      accountProfiles = [];
      activeCaseId = "";
      activeProfileId = "";
      workspace = null;
      envelope = null;
      cognition = null;
      canvas = null;
      narrationManifest = null;
      showAuth();
    }
  }
}


async function submitProfileForm(form: HTMLFormElement): Promise<void> {
  const data = new FormData(form);
  const profileId = form.dataset.profileId || "";
  const existing = accountProfiles.find((item) => item.profile_id === profileId);
  accountBusy = true;
  accountError = "";
  renderProfileManagement();
  try {
    const profile = await saveProfile(profileInputFromForm(data, existing), profileId);
    accountBusy = false;
    root.innerHTML = renderLoading("四柱已确认，正在进入命局");
    await openCase({ profileId: profile.profile_id });
  } catch (error) {
    accountBusy = false;
    accountError = humanizeAccountError(error instanceof Error ? error.message : String(error));
    renderProfileManagement();
  }
}


async function removeProfile(profileId: string): Promise<void> {
  const profile = accountProfiles.find((item) => item.profile_id === profileId);
  if (!profile || !window.confirm(`确定删除“${profile.display_name}”吗？历史探索不会同时删除。`)) return;
  accountBusy = true;
  accountError = "";
  renderProfileManagement();
  try {
    await deleteProductProfile(profileId);
    accountProfiles = accountProfiles.filter((item) => item.profile_id !== profileId);
    if (profileId === activeProfileId) {
      activeCaseId = "";
      activeProfileId = "";
      workspace = null;
      envelope = null;
      cognition = null;
      canvas = null;
      narrationManifest = null;
    }
    profileEditorMode = accountProfiles.length ? "none" : "create";
    editingProfileId = "";
  } catch (error) {
    accountError = humanizeAccountError(error instanceof Error ? error.message : String(error));
  } finally {
    accountBusy = false;
    renderProfileManagement();
  }
}


function profileInputFromForm(data: FormData, existing?: ProductProfile): BirthProfileInput {
  const approximate = String(data.get("time_precision") || "exact") === "approximate";
  return {
    birth_input_id: existing?.birth_input_id || `profile-${crypto.randomUUID()}`,
    name: String(data.get("name") || "我的命盘"),
    gender: String(data.get("gender") || "unknown") as ProductProfile["gender"],
    calendar_type: String(data.get("calendar_type") || "solar") as ProductProfile["calendar_type"],
    birth_date: String(data.get("birth_date") || ""),
    birth_time: String(data.get("birth_time") || ""),
    birth_location: String(data.get("birth_location") || ""),
    timezone: String(data.get("timezone") || "Asia/Seoul"),
    true_solar_time_policy: existing?.true_solar_time_policy || "not_applied",
    lunar_leap_month: data.get("lunar_leap_month") === "on",
    year_pillar: "",
    month_pillar: "",
    day_pillar: "",
    hour_pillar: "",
    input_quality: approximate ? "user_confirmed_approximate" : "user_confirmed",
    warnings: approximate ? ["birth_time_approximate"] : [],
  };
}


function humanizeAccountError(message: string): string {
  const messages: Record<string, string> = {
    invalid_email_or_password: "邮箱或密码不正确。",
    email_already_registered: "这个邮箱已经注册，可以直接登录。",
    invalid_email: "请填写有效邮箱。",
    password_too_short: "密码至少需要 8 位。",
    profile_not_found: "没有找到这份档案。",
    four_pillars_resolution_failed: "这组出生资料暂时无法排出完整四柱，请检查日期、时间与历法。",
  };
  return messages[message] || humanizeError(message);
}
