import { renderReadOnlyCanvas } from "./components";
import type { CanvasContextPack, CanvasLayer, CanvasStage } from "./contracts";
import {
  closeDreamMirror,
  createDreamVisit,
  enterDreamVisit,
  loadDreamEncounter,
  loadDreamMirror,
  loadDreamMirrorContext,
  loadDreamTree,
  loadDreamVisit,
  openDreamMirror,
  selectDreamTree,
  type DreamEncounterProjection,
  type DreamMirrorProjection,
  type DreamTreeProjection,
  type DreamVisitView,
} from "./dream_api";
import { dreamText } from "./dream_i18n";
import { initialUiState, reduceUi, type UiState } from "./state";


export async function bootDreamExperience(root: HTMLElement): Promise<void> {
  const runtime = new DreamRuntime(root);
  await runtime.boot();
}


class DreamRuntime {
  private visit: DreamVisitView | null = null;
  private encounter: DreamEncounterProjection | null = null;
  private tree: DreamTreeProjection | null = null;
  private mirror: DreamMirrorProjection | null = null;
  private context: CanvasContextPack | null = null;
  private ui: UiState = structuredClone(initialUiState);

  constructor(private readonly root: HTMLElement) {
    root.addEventListener("click", (event) => void this.handleClick(event));
  }

  async boot(): Promise<void> {
    this.renderLoading();
    try {
      const route = parseDreamRoute();
      this.visit = route.visitId
        ? await loadDreamVisit(route.visitId)
        : await createDreamVisit("");
      if (["HOME_GROVE", "PATH_OFFERED", "DREAM_ENTERING"].includes(this.visit.state)) {
        this.visit = await enterDreamVisit(this.visit.visit_id);
      }
      const sceneRef = route.sceneRef || this.visit.selected_scene_ref;
      if (sceneRef) {
        await this.showTree(sceneRef, route.mirror || this.visit.state === "MIRROR_OPEN");
      } else {
        await this.showEncounter();
      }
    } catch (error) {
      this.renderError(error);
    }
  }

  private async showEncounter(): Promise<void> {
    if (!this.visit) return;
    this.encounter = await loadDreamEncounter(this.visit.visit_id);
    this.tree = null;
    this.mirror = null;
    this.context = null;
    history.replaceState({}, "", `/experience/dream/visits/${encodeURIComponent(this.visit.visit_id)}`);
    this.root.innerHTML = renderEncounter(this.encounter);
  }

  private async showTree(sceneRef: string, showMirror = false): Promise<void> {
    if (!this.visit) return;
    this.tree = await loadDreamTree(this.visit.visit_id, sceneRef);
    this.mirror = null;
    this.context = null;
    history.replaceState(
      {},
      "",
      `/experience/dream/visits/${encodeURIComponent(this.visit.visit_id)}/trees/${encodeURIComponent(sceneRef)}`,
    );
    if (showMirror) {
      await this.showMirror(sceneRef);
      return;
    }
    this.root.innerHTML = renderTree(this.tree);
  }

  private async showMirror(sceneRef: string): Promise<void> {
    if (!this.visit) return;
    this.visit = await openDreamMirror(this.visit.visit_id);
    this.mirror = await loadDreamMirror(this.visit.visit_id, sceneRef);
    const canvas = this.mirror.canvas;
    const stage = canvas.stages[canvas.default_stage];
    this.ui = {
      ...structuredClone(initialUiState),
      workspaceSurface: "onecanvas",
      canvasStage: canvas.default_stage,
      canvasLayer: stage.default_layer_id,
      canvasVisibilityLayer: "formal",
      selectedCanvasObject: stage.context.selected_object_refs[0] || stage.spec.semantic_slots[0]?.slot_ref || "",
      canvasContextStatus: "ready",
    };
    this.context = stage.context;
    history.replaceState(
      {},
      "",
      `/experience/dream/visits/${encodeURIComponent(this.visit.visit_id)}/trees/${encodeURIComponent(sceneRef)}/mirror`,
    );
    this.renderMirror();
  }

  private renderMirror(): void {
    if (!this.mirror) return;
    this.root.innerHTML = renderMirror(
      renderReadOnlyCanvas(this.mirror.canvas, this.ui, this.context, false),
      dreamText(this.mirror.source_label_key),
    );
  }

  private async handleClick(event: Event): Promise<void> {
    const target = event.target instanceof Element ? event.target.closest<HTMLElement>("button, a") : null;
    if (!target || !this.visit) return;

    const sceneRef = target.dataset.dreamSelect;
    if (sceneRef) {
      this.renderLoading();
      try {
        this.visit = await selectDreamTree(this.visit.visit_id, sceneRef);
        await this.showTree(sceneRef);
      } catch (error) {
        this.renderError(error);
      }
      return;
    }

    if (target.dataset.dreamCommand === "open-mirror" && this.visit.selected_scene_ref) {
      this.renderLoading();
      try {
        await this.showMirror(this.visit.selected_scene_ref);
      } catch (error) {
        this.renderError(error);
      }
      return;
    }

    if (target.dataset.dreamCommand === "close-mirror" && this.visit.selected_scene_ref) {
      this.renderLoading();
      try {
        this.visit = await closeDreamMirror(this.visit.visit_id);
        await this.showTree(this.visit.selected_scene_ref);
      } catch (error) {
        this.renderError(error);
      }
      return;
    }

    const stage = target.dataset.canvasStage as CanvasStage | undefined;
    if (stage && this.mirror?.canvas.stages[stage]) {
      const projection = this.mirror.canvas.stages[stage];
      this.ui = reduceUi(this.ui, {
        type: "canvas-stage",
        stage,
        layer: projection.default_layer_id,
        selected: projection.context.selected_object_refs[0] || projection.spec.semantic_slots[0]?.slot_ref || "",
      });
      this.context = projection.context;
      this.renderMirror();
      return;
    }

    const layer = target.dataset.canvasLayer as CanvasLayer | undefined;
    if (layer) {
      this.ui = reduceUi(this.ui, { type: "canvas-layer", layer });
      this.renderMirror();
      return;
    }

    const visibility = target.dataset.canvasVisibility;
    if (visibility === "formal" || visibility === "focus") {
      this.ui = reduceUi(this.ui, { type: "canvas-visibility", visibility });
      this.renderMirror();
      return;
    }

    const selected = target.dataset.canvasObject;
    if (selected && this.visit.selected_scene_ref) await this.refreshContext(selected);
  }

  private async refreshContext(selected: string): Promise<void> {
    if (!this.mirror || !this.visit) return;
    this.ui = reduceUi(this.ui, { type: "canvas-select", selected, status: "loading" });
    this.renderMirror();
    try {
      this.context = await loadDreamMirrorContext(
        this.visit.visit_id,
        this.visit.selected_scene_ref,
        this.ui.canvasStage,
        selected,
        this.ui.canvasLayer,
      );
      this.ui = reduceUi(this.ui, { type: "canvas-context-status", status: "ready" });
    } catch {
      this.context = null;
      this.ui = reduceUi(this.ui, { type: "canvas-context-status", status: "error" });
    }
    this.renderMirror();
  }

  private renderLoading(): void {
    this.root.innerHTML = `<main class="dream-state"><div class="dream-mist-mark" aria-hidden="true"></div><p>ABU DREAM</p><h1>${escapeHtml(dreamText("dream.loading"))}</h1></main>`;
  }

  private renderError(error: unknown): void {
    const detail = error instanceof Error ? error.message : String(error);
    const unavailable = detail.includes("DREAM_ENCOUNTER_UNAVAILABLE") || detail.includes("dream_feature_disabled");
    this.root.innerHTML = `<main class="dream-state dream-error">
      <img src="/assets/abu/v5-designer-welcome/web/abu_welcome_wave_v5.webp" alt="Abu">
      <p>ABU DREAM</p>
      <h1>${escapeHtml(dreamText(unavailable ? "dream.unavailable.title" : "dream.error.title"))}</h1>
      <span>${escapeHtml(unavailable ? dreamText("dream.unavailable.detail") : detail)}</span>
      <a class="dream-command" href="/experience">${escapeHtml(dreamText("dream.workspace.back"))}</a>
    </main>`;
  }
}


function renderEncounter(encounter: DreamEncounterProjection): string {
  return `<main class="dream-world dream-encounter">
    ${dreamHeader()}
    <section class="dream-copy">
      <p>${escapeHtml(dreamText("dream.encounter.eyebrow"))}</p>
      <h1>${escapeHtml(dreamText("dream.encounter.title"))}</h1>
      <span>${escapeHtml(dreamText("dream.encounter.lede"))}</span>
    </section>
    <section class="dream-tree-grove" aria-label="Three anonymous life trees">
      ${encounter.trees.map((tree, index) => `<button type="button" class="dream-tree-card is-${tree.art_variant} element-${tree.primary_element}" data-dream-select="${escapeAttr(tree.scene_ref)}" aria-label="${escapeAttr(dreamText("dream.tree.choose"))}">
        <em class="dream-source-badge">${escapeHtml(dreamText(tree.source_label_key))}</em>
        <span class="dream-tree-crown"><i></i><i></i><i></i><i></i></span>
        <span class="dream-tree-trunk"><i></i></span>
        <strong>0${index + 1}</strong>
        <small>${escapeHtml(dreamText("dream.tree.choose"))}</small>
      </button>`).join("")}
    </section>
    <img class="dream-abu-guide" src="/assets/abu/v5-designer-welcome/web/abu_welcome_wave_v5.webp" alt="Abu guides the way">
  </main>`;
}


function renderTree(tree: DreamTreeProjection): string {
  const variant = String(tree.visual_tokens.art_variant || "mist");
  const element = String(tree.visual_tokens.primary_element || "unknown");
  return `<main class="dream-world dream-tree-observation is-${escapeAttr(variant)} element-${escapeAttr(element)}">
    ${dreamHeader()}
    <section class="dream-copy compact">
      <p>${escapeHtml(dreamText("dream.tree.eyebrow"))}</p>
      <h1>${escapeHtml(dreamText("dream.tree.title"))}</h1>
      <span>${escapeHtml(dreamText(tree.source_label_key))} · ${escapeHtml(dreamText("dream.tree.lede"))}</span>
    </section>
    <section class="dream-single-tree" aria-label="Anonymous life tree">
      <div class="dream-tree-crown"><i></i><i></i><i></i><i></i><i></i></div>
      <div class="dream-tree-trunk"><i></i><i></i></div>
      <div class="dream-tree-roots"><i></i><i></i><i></i></div>
      <p>${escapeHtml(dreamText(tree.work_path_message_key))}</p>
    </section>
    <div class="dream-tree-actions">
      <button class="dream-command" type="button" data-dream-command="open-mirror">${escapeHtml(dreamText("dream.mirror.open"))}</button>
      <a href="/experience">${escapeHtml(dreamText("dream.workspace.back"))}</a>
    </div>
    <img class="dream-abu-observer" src="/assets/abu/v12-actor-pass/turn-and-point/web/abu_turn_and_point_v1.webp" alt="Abu observes the tree">
  </main>`;
}


function renderMirror(canvasMarkup: string, sourceLabel: string): string {
  return `<main class="dream-world dream-mirror-world">
    ${dreamHeader()}
    <section class="dream-mirror-heading"><div><p>ONECANVAS · DREAM MIRROR</p><h1>${escapeHtml(dreamText("dream.mirror.open"))}</h1><span>${escapeHtml(sourceLabel)}</span></div><button type="button" data-dream-command="close-mirror">${escapeHtml(dreamText("dream.mirror.close"))}</button></section>
    <section class="dream-mirror-surface">${canvasMarkup}</section>
  </main>`;
}


function dreamHeader(): string {
  return `<header class="dream-header"><a href="/experience"><img src="/assets/deepbazi_logo_horizontal.png" alt="DeepBazi"></a><span>ABU DREAM · READ ONLY</span></header>`;
}


function parseDreamRoute(): { visitId: string; sceneRef: string; mirror: boolean } {
  const parts = location.pathname.split("/").filter(Boolean);
  const visitIndex = parts.indexOf("visits");
  const treeIndex = parts.indexOf("trees");
  return {
    visitId: visitIndex >= 0 ? decodeURIComponent(parts[visitIndex + 1] || "") : "",
    sceneRef: treeIndex >= 0 ? decodeURIComponent(parts[treeIndex + 1] || "") : "",
    mirror: parts.includes("mirror"),
  };
}


function escapeHtml(value: string): string {
  return value.replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  }[character] || character));
}


function escapeAttr(value: string): string {
  return escapeHtml(value);
}
