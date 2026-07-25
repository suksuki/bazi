import { renderDreamGameCanvas, renderDreamVerificationCanvas } from "./components";
import {
  checkpointDreamVisit,
  closeDreamMirror,
  commitDreamDeparture,
  createDreamVisit,
  currentDreamWorldProjectionRef,
  DreamApiError,
  enterDreamVisit,
  heartbeatDreamControl,
  loadDreamEncounter,
  loadDreamDepartureResult,
  loadDreamMirror,
  loadDreamTree,
  loadDreamVisit,
  openDreamMirror,
  prepareDreamReveal,
  recoverDreamVisit,
  selectDreamTree,
  setDreamDepartureIntent,
  suspendDreamVisit,
  takeoverDreamVisit,
  clearDreamControl,
  type DreamEncounterProjection,
  type DreamMirrorProjection,
  type DreamNavigationSample,
  type DreamRevealProjection,
  type DreamTreeCard,
  type DreamVisitView,
} from "./dream_api";
import {
  answerDreamLearningQuestion,
  beginDreamGameJudgment,
  castDreamGameDivination,
  closeDreamProblemFlower,
  completeDreamGameRound,
  DREAM_GAME_BANNER,
  loadDreamGameAttempt,
  loadDreamGameContentGate,
  loadDreamGameResult,
  loadDreamGameRounds,
  observeDreamGameLens,
  openDreamProblemFlower,
  revealDreamGameOutcome,
  sealDreamGameJudgment,
  startDreamGameRound,
  type DreamGameAttemptView,
  type DreamGameJudgmentPayload,
  type DreamGameLens,
  type DreamGameResult,
  type DreamGameRoundCard,
} from "./dream_game_api";
import { dreamText } from "./dream_i18n";
import {
  buildDreamTreeQuestions,
  renderDreamTreeQuestionMap,
  renderDreamTreePorch,
  treeQuestionForNode,
  type DreamTreeMediaCue,
  type DreamTreeQuestionNodeId,
  type DreamTreeRevealAct,
} from "./dream_tree_world";
import {
  DREAM_RUNTIME_ASSETS,
  preloadDreamPorchScenes,
} from "./dream_asset_registry";
import {
  DreamStoryRuntime,
  markDreamReturnedWithSeed,
} from "./dream_story_runtime";


type FirstVisitPhase =
  | "fog_wait"
  | "fog_crossing"
  | "self_recognition"
  | "free_roam"
  | "tree_contact"
  | "reveal_settling"
  | "mirror_ready"
  | "mirror_opening"
  | "mirror_open"
  | "mirror_closing"
  | "authorization_closed"
  | "local_mist_reentry"
  | "visit_suspended"
  | "departure_intent"
  | "departure_committing"
  | "departed"
  | "fail_closed";

type PointerMode = "ground" | "tree_touch" | "root_mirror" | "mirror_exit";

interface WorldPoint {
  x: number;
  y: number;
}

interface TreePlacement extends DreamTreeCard {
  x: number;
  y: number;
  scale: number;
  depth: number;
  own: boolean;
}

interface PointerSession {
  id: number;
  mode: PointerMode;
  startedAt: number;
  startClientX: number;
  startClientY: number;
  target: WorldPoint;
  sceneRef: string;
  moved: boolean;
  crossedMirrorBoundary: boolean;
  mirrorBoundaryClientY: number;
}

interface TapMotion {
  from: WorldPoint;
  to: WorldPoint;
  startedAt: number;
  durationMs: number;
}

interface AlphaMask {
  image: HTMLImageElement;
  canvas: HTMLCanvasElement;
  context: CanvasRenderingContext2D;
}

interface PorchPointerSession {
  id: number;
  startClientX: number;
  currentClientX: number;
  camera: HTMLElement;
  treeIndex: number | null;
}

const AMBIENT_AUDIO = DREAM_RUNTIME_ASSETS.openingTheme.source;
const ABU_WAIT = DREAM_RUNTIME_ASSETS.abuSeated.fallback || DREAM_RUNTIME_ASSETS.abuSeated.poster || "";
const ABU_WALK = DREAM_RUNTIME_ASSETS.abuWalk.fallback || DREAM_RUNTIME_ASSETS.abuWalk.poster || "";
const ABU_REST = DREAM_RUNTIME_ASSETS.abuSeated.poster || DREAM_RUNTIME_ASSETS.abuSeated.source;
const ENTER_HINT_DELAY_MS = 4200;
const FOLLOW_DELAY_MS = 620;
const TREE_TOUCH_DISTANCE = 13;
const MIRROR_POLL_MS = 5000;
const FOG_CROSSING_MS = 2300;
const SELF_RECOGNITION_END_MS = 5400;
const LOCAL_MIST_REENTRY_MS = 1500;
const HEARTBEAT_MS = 30000;
const CHECKPOINT_MS = 12000;
const PENDING_DEPARTURE_KEY = "deepbazi.dream.pending-departure.v1";
const PENDING_GAME_ACTION_KEY = "deepbazi.dream.pending-game-action.v1";
const TREE_QUESTION_STATE_KEY = "deepbazi.dream.tree-question-map.v1";


type DreamJudgmentStep = "outcome" | "hypothesis" | "counter" | "review";

interface DreamTreeQuestionState {
  attemptId: string;
  activeNode: DreamTreeQuestionNodeId | "";
  judgmentStep: DreamJudgmentStep;
  draft: DreamGameDraft;
}


interface DreamGameDraft {
  selectedOutcome: "yes" | "no" | "partial_or_unclear";
  confidence: number;
  nodeRefs: string[];
  relationRefs: string[];
  interpretation: string;
  strongestAlternative: string;
  disconfirmationCondition: string;
}


interface PendingDreamGameAction {
  visitId: string;
  attemptId: string;
  kind: "seal" | "close-flower" | "reveal";
  payload: DreamGameJudgmentPayload | { idempotencyKey: string };
}


export async function bootDreamExperience(root: HTMLElement): Promise<void> {
  const runtime = new DreamFirstVisitRuntime(root);
  await runtime.boot();
}


class DreamFirstVisitRuntime {
  private readonly story = new DreamStoryRuntime();
  private visit: DreamVisitView | null = null;
  private encounter: DreamEncounterProjection | null = null;
  private trees: TreePlacement[] = [];
  private reveal: DreamRevealProjection | null = null;
  private mirror: DreamMirrorProjection | null = null;
  private phase: FirstVisitPhase = "fog_wait";
  private user: WorldPoint = { x: 50, y: 88 };
  private abu: WorldPoint = { x: 47, y: 76 };
  private pointer: PointerSession | null = null;
  private masks = new Map<string, AlphaMask>();
  private trail: Array<{ at: number; point: WorldPoint }> = [];
  private movementFrame = 0;
  private previousFrameAt = 0;
  private tapMotion: TapMotion | null = null;
  private userMoving = false;
  private abuFollowing = false;
  private abuFacing: "left" | "right" = "right";
  private totalTravel = 0;
  private followNotBefore = Number.POSITIVE_INFINITY;
  private nearestResidentRef = "";
  private hintTimer = 0;
  private revealTimer = 0;
  private mirrorPollTimer = 0;
  private mirrorHistoryActive = false;
  private suppressNextPop = false;
  private ambient: HTMLAudioElement | null = null;
  private sceneStartedAt = Date.now();
  private canonicalAbu = false;
  private heartbeatTimer = 0;
  private checkpointTimer = 0;
  private recoverySequence = 0;
  private departureCommitSequence = 0;
  private departureIntentPending = false;
  private departureIntentActive = false;
  private departureCommitPending = false;
  private lastStableUser: WorldPoint = { x: 50, y: 88 };
  private visibilityRequestInFlight = false;
  private visibilityReconcilePending = false;
  private forestHistoryActive = false;
  private gameRounds: DreamGameRoundCard[] = [];
  private gameAttempt: DreamGameAttemptView | null = null;
  private gameResult: DreamGameResult | null = null;
  private gameLens: DreamGameLens = "overview";
  private gameDraft: DreamGameDraft = this.emptyGameDraft();
  private gameSealConfirmation = false;
  private gameCastConfirmation = false;
  private gameBusy = false;
  private gameStatusMessage = "";
  private gameHistoryActive = false;
  private gamePollTimer = 0;
  private gameShellOpen = false;
  private porchIndex = 0;
  private porchEntering = true;
  private porchIntroTimer = 0;
  private porchOrbitTimer = 0;
  private porchWhisperTimer = 0;
  private porchWhisper = "";
  private readonly spokenRoundIds = new Set<string>();
  private porchPointer: PorchPointerSession | null = null;
  private suppressNextPorchSelection = false;
  private gameLensOpen = false;
  private gameLensHistoryActive = false;
  private gameQuestionHistoryActive = false;
  private gameMediaCue: DreamTreeMediaCue = "none";
  private gameMediaTimer = 0;
  private gameTreeState: DreamTreeQuestionState = {
    attemptId: "",
    activeNode: "",
    judgmentStep: "outcome",
    draft: this.emptyGameDraft(),
  };
  private gameRevealAct: DreamTreeRevealAct = "user";

  constructor(private readonly root: HTMLElement) {
    this.root.addEventListener("pointerdown", (event) => this.handlePointerDown(event));
    this.root.addEventListener("pointermove", (event) => this.handlePointerMove(event));
    this.root.addEventListener("pointerup", (event) => void this.handlePointerUp(event));
    this.root.addEventListener("pointercancel", (event) => this.handlePointerCancel(event));
    this.root.addEventListener("click", (event) => void this.handleCommand(event));
    this.root.addEventListener("input", (event) => this.handleGameInput(event));
    this.root.addEventListener("change", (event) => this.handleGameInput(event));
    window.addEventListener("keydown", (event) => void this.handleKeyDown(event));
    window.addEventListener("popstate", () => void this.handleHistoryReturn());
    document.addEventListener("visibilitychange", () => void this.handleVisibilityChange());
    window.addEventListener("online", () => void this.resumePendingDeparture());
    window.addEventListener("online", () => void this.resumePendingGameAction());
    window.addEventListener("pagehide", () => void this.handlePageHide());
  }

  async boot(): Promise<void> {
    this.renderPreflight();
    try {
      if (await this.resolveCompletedDeparture()) return;
      const route = parseDreamRoute();
      this.visit = await this.acquireVisit(route.visitId);
      if (!this.visit) return;
      this.recoverySequence = this.visit.recovery_sequence;
      this.departureCommitSequence = this.visit.departure_commit_sequence;
      const pendingDeparture = this.readPendingDeparture();
      if (pendingDeparture?.visitId === this.visit.visit_id) {
        await this.resumePendingDeparture();
        if (this.phase === "departed" || this.departureCommitPending) return;
      }
      if (["HOME_GROVE", "PATH_OFFERED", "DREAM_ENTERING"].includes(this.visit.state)) {
        this.acceptVisit(await enterDreamVisit(this.visit.visit_id));
      }
      if (
        (this.visit.is_return_visit || this.visit.runtime_state === "LOCAL_MIST_REENTRY")
        && this.visit.runtime_state !== "FOREST_ACTIVE"
      ) {
        this.acceptVisit(await enterDreamVisit(this.visit.visit_id));
      }
      this.encounter = await loadDreamEncounter(this.visit.visit_id);
      this.trees = placeTrees(this.encounter.trees);
      await this.loadGameRounds();
      if (this.gameRounds.length) await preloadDreamPorchScenes();
      this.sceneStartedAt = readSceneAnchor(this.visit.visit_id);
      this.applyServerNavigationState();
      this.renderGrove();
      this.activateForestHistory();
      this.startControlLoops();

      if (this.gameRounds.length) {
        this.gameShellOpen = true;
        this.porchEntering = !this.visit.is_return_visit;
        this.playAmbient();
        if (this.visit.is_return_visit || this.visit.runtime_state === "LOCAL_MIST_REENTRY") {
          await this.beginReturnVisit();
        } else {
          this.phase = "free_roam";
          this.syncSceneDom();
        }
        await this.resumeGameFromRoute();
        if (!this.gameAttempt) this.renderGameLayer();
        await this.resumePendingGameAction();
        return;
      }

      if (this.visit.is_return_visit || this.visit.runtime_state === "LOCAL_MIST_REENTRY") {
        await this.beginReturnVisit();
        await this.resumeGameFromRoute();
        await this.resumePendingGameAction();
        return;
      }

      const routeMatchesVisit = !route.visitId || route.visitId === this.visit.visit_id;
      const sceneRef = (routeMatchesVisit ? route.sceneRef : "") || this.visit.selected_scene_ref;
      if (sceneRef) {
        await this.resumeSelectedTree(
          sceneRef,
          (routeMatchesVisit && route.mirror) || this.visit.state === "MIRROR_OPEN",
        );
      } else {
        this.startEntranceHint();
      }
      await this.resumeGameFromRoute();
      await this.resumePendingGameAction();
    } catch (error) {
      this.renderError(error);
    }
  }

  private async acquireVisit(routeVisitId: string): Promise<DreamVisitView | null> {
    try {
      // Workspace already acquired the exact Visit and handed its lease to this
      // navigation. Loading that Visit preserves its LifeCase namespace. A new
      // tab has no matching credential and therefore reaches the takeover gate.
      return routeVisitId
        ? await loadDreamVisit(routeVisitId)
        : await createDreamVisit("");
    } catch (error) {
      const code = this.errorCode(error);
      if ([
        "dream_control_takeover_required",
        "dream_control_lease_required",
        "dream_control_lease_superseded",
        "dream_control_lease_stale",
        "dream_control_lease_expired",
      ].includes(code)) {
        this.renderTakeover(routeVisitId);
        return null;
      }
      throw error;
    }
  }

  private renderTakeover(routeVisitId: string): void {
    this.root.innerHTML = `<main class="dream-state dream-control-choice" aria-labelledby="dream-control-title">
      <img src="${ABU_REST}" alt="阿布安静坐着">
      <h1 id="dream-control-title">梦境正在另一处继续</h1>
      <p>这里不会同时控制同一片林境。</p>
      <div class="dream-control-actions">
        <button class="dream-command" type="button" data-dream-takeover>从这里接管</button>
        <a class="dream-command is-quiet" href="/experience">暂不进入</a>
      </div>
    </main>`;
    this.root.querySelector<HTMLElement>("[data-dream-takeover]")?.addEventListener("click", async () => {
      try {
        const visit = routeVisitId
          ? await takeoverDreamVisit(routeVisitId)
          : await createDreamVisit("", true);
        location.replace(`/experience/dream/visits/${encodeURIComponent(visit.visit_id || routeVisitId)}`);
      } catch (error) {
        this.renderError(error);
      }
    });
  }

  private applyServerNavigationState(): void {
    if (!this.visit) return;
    const resolved = this.visit.anchor_resolution;
    if (resolved) {
      this.user = { ...resolved.position };
      this.lastStableUser = { ...resolved.position };
    }
    const abu = this.visit.canonical_abu;
    if (abu) {
      this.abu = { ...abu.public_position };
      this.canonicalAbu = true;
    }
  }

  private acceptVisit(visit: DreamVisitView): DreamVisitView {
    this.visit = visit;
    this.recoverySequence = Math.max(this.recoverySequence, visit.recovery_sequence);
    this.departureCommitSequence = Math.max(
      this.departureCommitSequence,
      visit.departure_commit_sequence,
    );
    return visit;
  }

  private async beginReturnVisit(): Promise<void> {
    if (!this.visit) return;
    this.reveal = null;
    this.mirror = null;
    this.nearestResidentRef = "";
    this.phase = "local_mist_reentry";
    this.syncSceneDom();
    this.announce("雾只在你身边轻轻散开。林中的时间一直在继续。");
    this.acceptVisit(await enterDreamVisit(this.visit.visit_id));
    await delay(window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 180 : LOCAL_MIST_REENTRY_MS);
    if (this.phase !== "local_mist_reentry") return;
    this.phase = "free_roam";
    this.syncSceneDom();
  }

  private activateForestHistory(): void {
    if (this.forestHistoryActive || !this.visit) return;
    history.replaceState(
      { dreamForest: true, visitId: this.visit.visit_id },
      "",
      location.href,
    );
    history.pushState(
      { dreamForestGuard: true, visitId: this.visit.visit_id },
      "",
      location.href,
    );
    this.forestHistoryActive = true;
  }

  private renderPreflight(): void {
    this.root.innerHTML = `<main class="dream-first-visit dream-preflight" aria-label="阿布梦境">
      <div class="dream-grove-background" aria-hidden="true"></div>
      <div class="dream-fog dream-fog-front" aria-hidden="true"></div>
      <img class="dream-abu dream-abu-preflight" src="${ABU_WAIT}" alt="阿布在雾中等待">
    </main>`;
  }

  private renderGrove(): void {
    if (!this.visit) return;
    this.root.innerHTML = `<main class="dream-first-visit" data-phase="${this.phase}" aria-label="阿布梦境中的三树林境">
      <audio class="dream-ambient-audio" preload="metadata" loop src="${AMBIENT_AUDIO}"></audio>
      <div class="dream-grove-background" aria-hidden="true"></div>
      <div class="dream-grove-parallax" aria-hidden="true"></div>
      <section class="dream-grove" data-dream-ground tabindex="0" aria-label="可自由行走的林地">
        <div class="dream-canopy-shadow" aria-hidden="true"></div>
        <div class="dream-departure-path" aria-hidden="true">
          <span class="dream-departure-mist"></span>
          <span class="dream-departure-ground"></span>
        </div>
        <span class="dream-user-presence" aria-hidden="true"></span>
        <span class="dream-abu-shadow" aria-hidden="true"></span>
        <img class="dream-abu" src="${ABU_WAIT}" alt="阿布" draggable="false">
        <div class="dream-paw-hint" aria-live="polite"><i aria-hidden="true"></i><span>轻触，跟上阿布</span></div>
        <p class="dream-abu-line" aria-live="polite">慢一点。先听。</p>
        <div class="dream-fog dream-fog-back" aria-hidden="true"></div>
        <div class="dream-fog dream-fog-front" aria-hidden="true"></div>
      </section>
      <section class="dream-mirror-layer" aria-label="根镜中的命盘" aria-hidden="true"></section>
      <section class="dream-game-layer" aria-label="阿布问果三树局" aria-hidden="true"></section>
      <div class="dream-runtime-veil" aria-hidden="true"><span></span></div>
      <nav class="sr-only dream-a11y-actions" aria-label="梦境无障碍动作">
        <button type="button" data-dream-a11y="follow">跟上阿布</button>
        <button type="button" data-dream-a11y="open-mirror">触碰根镜</button>
        <button type="button" data-dream-a11y="leave-mirror">返回林地</button>
        <button type="button" data-dream-a11y="leave-dream">离开梦境</button>
      </nav>
      <p class="sr-only" data-dream-announcer aria-live="polite"></p>
    </main>`;
    this.ambient = this.root.querySelector<HTMLAudioElement>(".dream-ambient-audio");
    this.syncSceneDom();
  }

  private async resumeSelectedTree(sceneRef: string, resumeMirror: boolean): Promise<void> {
    if (!this.visit) return;
    await loadDreamTree(this.visit.visit_id, sceneRef);
    this.nearestResidentRef = sceneRef;
    const placement = this.treeByRef(sceneRef);
    if (placement) {
      const point = this.treeWorldPoint(placement);
      this.user = { x: point.x - 5, y: Math.min(88, point.y + 3) };
      this.abu = { x: this.user.x - 5, y: this.user.y + 4 };
    }
    if (resumeMirror && this.visit.active_onecanvas_view_ref) {
      this.phase = "mirror_ready";
      this.syncSceneDom();
      await this.openMirror(this.visit.active_onecanvas_view_ref, false);
      return;
    }
    if (this.visit.state === "MIRROR_OPEN") {
      this.acceptVisit(await closeDreamMirror(this.visit.visit_id));
    }
    this.reveal = await prepareDreamReveal(this.visit.visit_id, sceneRef);
    this.phase = "mirror_ready";
    this.syncSceneDom();
  }

  private startEntranceHint(): void {
    window.clearTimeout(this.hintTimer);
    this.hintTimer = window.setTimeout(() => {
      if (this.phase === "fog_wait") {
        this.root.querySelector(".dream-first-visit")?.classList.add("show-paw-hint");
      }
    }, ENTER_HINT_DELAY_MS);
  }

  private beginFogEntrance(): void {
    if (this.phase !== "fog_wait") return;
    window.clearTimeout(this.hintTimer);
    this.playAmbient();
    this.phase = "fog_crossing";
    this.tapMotion = null;
    this.userMoving = false;
    this.abuFollowing = false;
    this.user = { x: 50, y: 74 };
    this.abu = { x: 48, y: 62 };
    this.syncSceneDom();
    this.announce("你跟着阿布穿过雾界。慢一点，先听。");
    window.setTimeout(() => {
      if (this.phase !== "fog_crossing") return;
      this.phase = "self_recognition";
      this.user = { x: 42, y: 68 };
      const own = this.trees.find((tree) => tree.own);
      if (own) {
        const root = this.treeWorldPoint(own);
        this.abu = { x: root.x + 4, y: root.y };
      }
      this.syncSceneDom();
      this.announce("一条树根接住了你脚边的微光。那棵树先认出了你。");
    }, FOG_CROSSING_MS);
    window.setTimeout(() => {
      if (this.phase !== "self_recognition") return;
      this.phase = "free_roam";
      const own = this.trees.find((tree) => tree.own);
      if (own) {
        const root = this.treeWorldPoint(own);
        this.abu = { x: root.x + 3, y: root.y };
      }
      this.trail = [{ at: performance.now(), point: { ...this.user } }];
      this.totalTravel = 0;
      this.followNotBefore = Number.POSITIVE_INFINITY;
      this.syncSceneDom();
      this.announce("林地已经让开。你可以自己决定往哪里走。");
    }, SELF_RECOGNITION_END_MS);
  }

  private handlePointerDown(event: PointerEvent): void {
    const commandTarget = event.target instanceof Element ? event.target : null;
    const porchCamera = commandTarget?.closest<HTMLElement>("[data-dream-tree-porch]");
    const porchTree = commandTarget?.closest<HTMLElement>(".dream-tree-porch-tree");
    const porchControl = commandTarget?.closest(
      "button, a, input, textarea, select",
    );
    if (
      porchCamera
      && (!porchControl || porchTree)
      && !this.porchPointer
      && !this.gameAttempt
    ) {
      event.preventDefault();
      porchCamera.setPointerCapture(event.pointerId);
      this.porchPointer = {
        id: event.pointerId,
        startClientX: event.clientX,
        currentClientX: event.clientX,
        camera: porchCamera,
        treeIndex: porchTree?.dataset.porchIndex
          ? Number(porchTree.dataset.porchIndex)
          : null,
      };
      return;
    }
    const scene = this.root.querySelector<HTMLElement>(".dream-grove");
    if (!scene || !this.visit || this.pointer) return;
    const target = commandTarget;
    if (target?.closest(
      "button, a, input, textarea, select, [role='button'], [data-dream-game-round], [data-dream-game-command], [data-dream-a11y]",
    )) return;
    if (this.gameAttempt) return;
    if (this.phase === "fog_wait") {
      event.preventDefault();
      this.beginFogEntrance();
      return;
    }
    if (this.phase === "mirror_open") {
      const exitGeometry = this.mirrorExitGeometry(event);
      if (!exitGeometry) return;
      event.preventDefault();
      exitGeometry.layer.setPointerCapture(event.pointerId);
      exitGeometry.layer.classList.add("is-pulling-mirror");
      this.pointer = {
        id: event.pointerId,
        mode: "mirror_exit",
        startedAt: performance.now(),
        startClientX: event.clientX,
        startClientY: event.clientY,
        target: { x: event.clientX, y: event.clientY },
        sceneRef: this.visit.selected_scene_ref,
        moved: false,
        crossedMirrorBoundary: false,
        mirrorBoundaryClientY: exitGeometry.boundaryClientY,
      };
      return;
    }
    if (!["free_roam", "mirror_ready", "departure_intent"].includes(this.phase)) return;

    let point = this.worldPointFromClient(event.clientX, event.clientY);
    const touchedTree = this.hitTreeAt(event.clientX, event.clientY);
    const mirror = event.target instanceof Element
      ? event.target.closest<HTMLElement>(".dream-root-mirror")
      : null;
    let mode: PointerMode = "ground";
    let sceneRef = "";
    if (
      mirror
      && this.phase === "mirror_ready"
      && mirror.dataset.rootMirror === this.visit.selected_scene_ref
    ) {
      mode = "root_mirror";
      sceneRef = this.visit.selected_scene_ref;
    } else if (touchedTree && this.isWithinTouchDistance(touchedTree)) {
      mode = "tree_touch";
      sceneRef = touchedTree.scene_ref;
    } else if (touchedTree && !touchedTree.own) {
      // A visible resident tree is a real navigation target. The first touch
      // approaches it; selection still happens only after a second, nearby touch.
      point = this.treeApproachPoint(touchedTree);
      sceneRef = touchedTree.scene_ref;
    }
    event.preventDefault();
    scene.setPointerCapture(event.pointerId);
    this.pointer = {
      id: event.pointerId,
      mode,
      startedAt: performance.now(),
      startClientX: event.clientX,
      startClientY: event.clientY,
      target: point,
      sceneRef,
      moved: false,
      crossedMirrorBoundary: false,
      mirrorBoundaryClientY: 0,
    };
    if (mode === "ground") this.startMovementLoop();
  }

  private handlePointerMove(event: PointerEvent): void {
    if (this.porchPointer?.id === event.pointerId) {
      this.porchPointer.currentClientX = event.clientX;
      const drag = clamp(
        (event.clientX - this.porchPointer.startClientX) / Math.max(1, this.porchPointer.camera.clientWidth),
        -0.32,
        0.32,
      );
      this.porchPointer.camera.style.setProperty(
        "--porch-drag-x",
        `${drag * this.porchPointer.camera.clientWidth}px`,
      );
      this.porchPointer.camera.style.setProperty(
        "--porch-drag-sky",
        `${drag * this.porchPointer.camera.clientWidth * 0.18}px`,
      );
      this.porchPointer.camera.style.setProperty(
        "--porch-drag-far",
        `${drag * this.porchPointer.camera.clientWidth * 0.42}px`,
      );
      this.porchPointer.camera.style.setProperty(
        "--porch-drag-ground",
        `${drag * this.porchPointer.camera.clientWidth * 0.7}px`,
      );
      return;
    }
    if (!this.pointer || this.pointer.id !== event.pointerId) return;
    const distance = Math.hypot(
      event.clientX - this.pointer.startClientX,
      event.clientY - this.pointer.startClientY,
    );
    if (distance > 8) this.pointer.moved = true;
    if (this.pointer.mode === "ground") {
      this.pointer.target = this.worldPointFromClient(event.clientX, event.clientY);
      return;
    }
    if (this.pointer.mode === "mirror_exit") {
      const pull = Math.max(0, event.clientY - this.pointer.startClientY);
      this.pointer.crossedMirrorBoundary = (
        event.clientY >= this.pointer.mirrorBoundaryClientY
        && pull >= 28
      );
      const layer = this.root.querySelector<HTMLElement>(".dream-mirror-layer");
      const distanceToBoundary = Math.max(
        48,
        this.pointer.mirrorBoundaryClientY - this.pointer.startClientY,
      );
      layer?.style.setProperty(
        "--mirror-pull",
        String(Math.min(1, pull / (distanceToBoundary + 42))),
      );
    }
  }

  private async handlePointerUp(event: PointerEvent): Promise<void> {
    if (this.porchPointer?.id === event.pointerId) {
      const pointer = this.porchPointer;
      this.porchPointer = null;
      this.resetPorchDrag(pointer.camera);
      const travel = pointer.currentClientX - pointer.startClientX;
      if (Math.abs(travel) >= Math.min(72, pointer.camera.clientWidth * 0.16)) {
        this.suppressNextPorchSelection = true;
        window.setTimeout(() => {
          this.suppressNextPorchSelection = false;
        }, 250);
        this.shiftPorch(travel < 0 ? 1 : -1);
      } else if (
        pointer.treeIndex !== null
        && Number.isInteger(pointer.treeIndex)
        && pointer.treeIndex >= 0
        && pointer.treeIndex < this.gameRounds.length
      ) {
        this.suppressNextPorchSelection = true;
        window.setTimeout(() => {
          this.suppressNextPorchSelection = false;
        }, 250);
        if (pointer.treeIndex === this.porchIndex) {
          await this.commitFocusedTree();
        } else {
          this.focusPorchIndex(pointer.treeIndex);
        }
      }
      return;
    }
    if (!this.pointer || this.pointer.id !== event.pointerId) return;
    const session = this.pointer;
    this.pointer = null;
    if (session.mode === "ground") {
      if (performance.now() - session.startedAt < 180) {
        this.startTapMotion(session.target, session.sceneRef ? 100 : 5.5);
      } else {
        this.startMovementLoop();
      }
      return;
    }
    this.stopMovementLoopIfIdle();
    if (session.mode === "tree_touch" && !session.moved) {
      await this.touchTree(session.sceneRef);
      return;
    }
    if (session.mode === "root_mirror" && !session.moved && this.reveal) {
      await this.openMirror(this.reveal.onecanvas_view_ref, true);
      return;
    }
    if (session.mode === "mirror_exit") {
      const layer = this.root.querySelector<HTMLElement>(".dream-mirror-layer");
      layer?.classList.remove("is-pulling-mirror");
      layer?.style.removeProperty("--mirror-pull");
      if (session.crossedMirrorBoundary) await this.closeMirror("gesture");
    }
  }

  private handlePointerCancel(event: PointerEvent): void {
    if (this.porchPointer?.id === event.pointerId) {
      this.resetPorchDrag(this.porchPointer.camera);
      this.porchPointer = null;
      return;
    }
    if (!this.pointer || this.pointer.id !== event.pointerId) return;
    this.pointer = null;
    this.tapMotion = null;
    this.stopMovementLoopIfIdle();
    const layer = this.root.querySelector<HTMLElement>(".dream-mirror-layer");
    layer?.classList.remove("is-pulling-mirror");
    layer?.style.removeProperty("--mirror-pull");
  }

  private mirrorExitGeometry(
    event: PointerEvent,
  ): { layer: HTMLElement; boundaryClientY: number } | null {
    const target = event.target instanceof Element ? event.target : null;
    const layer = this.root.querySelector<HTMLElement>(".dream-mirror-layer");
    const optics = layer?.querySelector<HTMLElement>(".dream-mirror-optics");
    const boundary = layer?.querySelector<HTMLElement>(".dream-mirror-root-boundary");
    if (!target || !layer || !optics || !boundary || !layer.contains(target)) return null;
    if (target.closest(
      ".canvas-scene-node, .canvas-slot-label, .canvas-relation, .canvas-work-path, button, a",
    )) return null;

    const opticsRect = optics.getBoundingClientRect();
    const boundaryRect = boundary.getBoundingClientRect();
    const boundaryClientY = boundaryRect.top + (boundaryRect.height / 2);
    if (
      event.clientX < opticsRect.left
      || event.clientX > opticsRect.right
      || event.clientY < opticsRect.top
      || event.clientY >= boundaryClientY
    ) return null;
    return { layer, boundaryClientY };
  }

  private async handleCommand(event: Event): Promise<void> {
    const gameRound = event.target instanceof Element
      ? event.target.closest<HTMLElement>("[data-dream-game-round]")
      : null;
    if (gameRound?.dataset.dreamGameRound) {
      event.preventDefault();
      await this.openProblemRound(gameRound.dataset.dreamGameRound);
      return;
    }
    const gameCommand = event.target instanceof Element
      ? event.target.closest<HTMLElement>("[data-dream-game-command]")
      : null;
    if (gameCommand) {
      event.preventDefault();
      await this.handleGameCommand(gameCommand);
      return;
    }
    const target = event.target instanceof Element
      ? event.target.closest<HTMLElement>("[data-dream-a11y]")
      : null;
    if (!target) return;
    const command = target.dataset.dreamA11y;
    if (command === "follow") {
      this.beginFogEntrance();
      return;
    }
    if (command === "approach") {
      const tree = this.treeByRef(target.dataset.sceneRef || "");
      if (!tree || tree.own) return;
      const point = this.treeWorldPoint(tree);
      this.user = { x: point.x - 5, y: Math.min(88, point.y + 3) };
      this.nearestResidentRef = tree.scene_ref;
      this.syncSceneDom();
      this.announce(`你已经走到${tree.resident_label}的生命树前。`);
      return;
    }
    if (command === "touch" && this.nearestResidentRef) {
      await this.touchTree(this.nearestResidentRef);
      return;
    }
    if (command === "open-mirror" && this.reveal) {
      await this.openMirror(this.reveal.onecanvas_view_ref, true);
      return;
    }
    if (command === "leave-mirror" && this.phase === "mirror_open") {
      await this.closeMirror("accessibility");
      return;
    }
    if (command === "leave-dream" && ["free_roam", "mirror_ready", "departure_intent"].includes(this.phase)) {
      await this.departDream("SEMANTIC_EXIT");
      return;
    }
    if (command === "open-problem-flower") {
      await this.openProblemRound(target.dataset.roundId || "");
    }
  }

  private async handleKeyDown(event: KeyboardEvent): Promise<void> {
    if (!this.gameAttempt && this.gameShellOpen && (event.key === "ArrowLeft" || event.key === "ArrowRight")) {
      event.preventDefault();
      this.shiftPorch(event.key === "ArrowRight" ? 1 : -1);
      return;
    }
    if (event.key !== "Escape" && event.key !== "BrowserBack") return;
    if (this.gameAttempt) {
      event.preventDefault();
      if (this.gameLensOpen) {
        this.closeGameLens("accessibility");
      } else if (this.gameTreeState.activeNode) {
        this.closeTreeQuestion("accessibility");
      } else if (
        this.gameAttempt.state === "JUDGMENT_DRAFTING"
        && this.gameTreeState.judgmentStep !== "outcome"
      ) {
        this.stepJudgmentBack();
      } else {
        await this.returnToTreePorch("accessibility");
      }
      return;
    }
    if (this.gameShellOpen) {
      event.preventDefault();
      await this.departDream("SEMANTIC_EXIT");
      return;
    }
    if (this.phase === "mirror_open" || this.phase === "mirror_opening") {
      event.preventDefault();
      await this.closeMirror("accessibility");
      return;
    }
    if (!["free_roam", "mirror_ready", "departure_intent"].includes(this.phase)) return;
    event.preventDefault();
    await this.departDream("SEMANTIC_EXIT");
  }

  private async handleHistoryReturn(): Promise<void> {
    if (this.suppressNextPop) {
      this.suppressNextPop = false;
      return;
    }
    if (this.gameAttempt) {
      if (this.gameLensOpen) {
        this.closeGameLens("history");
      } else if (this.gameTreeState.activeNode) {
        this.closeTreeQuestion("history");
      } else if (
        this.gameAttempt.state === "JUDGMENT_DRAFTING"
        && this.gameTreeState.judgmentStep !== "outcome"
      ) {
        this.stepJudgmentBack();
        this.restoreGameHistoryGuard();
      } else {
        this.gameHistoryActive = false;
        await this.returnToTreePorch("history");
      }
      return;
    }
    if (this.phase === "mirror_open" || this.phase === "mirror_opening") {
      this.mirrorHistoryActive = false;
      await this.closeMirror("history");
      return;
    }
    if (["free_roam", "mirror_ready", "departure_intent"].includes(this.phase)) {
      history.pushState(
        { dreamForestGuard: true, visitId: this.visit?.visit_id || "" },
        "",
        location.href,
      );
      await this.departDream("SEMANTIC_EXIT");
    }
  }

  private async handleVisibilityChange(): Promise<void> {
    this.resyncSceneClock();
    if (!this.visit) return;
    if (this.visibilityRequestInFlight) {
      this.visibilityReconcilePending = true;
      return;
    }
    const requestedVisibility = document.visibilityState;
    this.visibilityRequestInFlight = true;
    try {
      if (requestedVisibility === "hidden") {
        this.clearSensitiveProjection();
        this.phase = "visit_suspended";
        this.syncSceneDom();
        this.acceptVisit(await suspendDreamVisit(
          this.visit.visit_id,
          this.navigationSample(this.lastStableUser),
          ++this.recoverySequence,
          true,
        ));
        return;
      }
      if (this.phase === "visit_suspended" || this.visit.runtime_state === "VISIT_SUSPENDED") {
        this.acceptVisit(await recoverDreamVisit(this.visit.visit_id));
        this.applyServerNavigationState();
        this.phase = "local_mist_reentry";
        this.syncSceneDom();
        await delay(window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 120 : 780);
        this.acceptVisit(await enterDreamVisit(this.visit.visit_id));
        this.phase = "free_roam";
        this.syncSceneDom();
        if (this.gameAttempt) {
          this.gameAttempt = await loadDreamGameAttempt(
            this.visit.visit_id,
            this.gameAttempt.attempt_id,
          );
          if (["KNOWLEDGE_SEED_ISSUED", "ROUND_COMPLETE"].includes(this.gameAttempt.state)) {
            this.gameResult = await loadDreamGameResult(
              this.visit.visit_id,
              this.gameAttempt.attempt_id,
            );
          }
          this.renderGameLayer();
          this.startGamePolling();
        } else if (this.gameShellOpen) {
          this.renderGameLayer();
        }
      } else if (this.phase === "mirror_open") {
        await this.validateOpenMirror();
      } else if (this.gameAttempt) {
        await this.validateOpenGame();
        this.renderGameLayer();
        this.startGamePolling();
      }
    } catch (error) {
      this.handleRuntimeFailure(error);
    } finally {
      this.visibilityRequestInFlight = false;
      const shouldReconcile = this.visibilityReconcilePending
        || document.visibilityState !== requestedVisibility;
      this.visibilityReconcilePending = false;
      if (
        shouldReconcile
        && this.visit
        && !["departure_committing", "departed"].includes(this.phase)
      ) {
        queueMicrotask(() => void this.handleVisibilityChange());
      }
    }
  }

  private handlePageHide(): void {
    if (
      !this.visit
      || this.phase === "departed"
      || this.departureCommitPending
      || this.visibilityRequestInFlight
    ) return;
    this.clearSensitiveProjection();
    void suspendDreamVisit(
      this.visit.visit_id,
      this.navigationSample(this.lastStableUser),
      ++this.recoverySequence,
      true,
    ).catch(() => undefined);
  }

  private startMovementLoop(): void {
    if (this.movementFrame) return;
    this.previousFrameAt = performance.now();
    const tick = (now: number) => {
      const deltaSeconds = Math.min(0.05, (now - this.previousFrameAt) / 1000);
      this.previousFrameAt = now;
      const groundPointer = this.pointer?.mode === "ground" ? this.pointer : null;
      let userMoved = false;
      if (groundPointer) {
        const elapsed = now - groundPointer.startedAt;
        if (elapsed > 180) {
          const remaining = pointDistance(this.user, groundPointer.target);
          const acceleration = clamp((elapsed - 180) / 360, 0.18, 1);
          const braking = clamp(remaining / 7, 0.28, 1);
          userMoved = this.moveToward(
            groundPointer.target,
            15 * acceleration * braking * deltaSeconds,
            now,
          );
        }
      }
      if (this.tapMotion) userMoved = this.advanceTapMotion(now) || userMoved;
      const abuMoved = this.advanceAbuFollower(now, deltaSeconds);
      const motionStateChanged = (
        this.userMoving !== userMoved
        || this.abuFollowing !== abuMoved
      );
      this.userMoving = userMoved;
      this.abuFollowing = abuMoved;
      if (userMoved || abuMoved || motionStateChanged) this.syncSceneDom();

      if (groundPointer || this.tapMotion || this.shouldContinueAbuFollower(now)) {
        this.movementFrame = requestAnimationFrame(tick);
        return;
      }
      this.movementFrame = 0;
      this.userMoving = false;
      this.abuFollowing = false;
      this.followNotBefore = Number.POSITIVE_INFINITY;
      this.syncSceneDom();
    };
    this.movementFrame = requestAnimationFrame(tick);
  }

  private stopMovementLoop(): void {
    if (this.movementFrame) cancelAnimationFrame(this.movementFrame);
    this.movementFrame = 0;
    this.tapMotion = null;
    this.userMoving = false;
    this.abuFollowing = false;
    this.followNotBefore = Number.POSITIVE_INFINITY;
  }

  private stopMovementLoopIfIdle(): void {
    if (
      this.pointer?.mode === "ground"
      || this.tapMotion
      || this.shouldContinueAbuFollower(performance.now())
    ) {
      this.startMovementLoop();
      return;
    }
    this.stopMovementLoop();
    this.syncSceneDom();
  }

  private startTapMotion(target: WorldPoint, maximumDistance: number): void {
    const dx = target.x - this.user.x;
    const dy = target.y - this.user.y;
    const length = Math.hypot(dx, dy);
    if (length < 0.05) return;
    const distance = Math.min(length, maximumDistance);
    const now = performance.now();
    this.tapMotion = {
      from: { ...this.user },
      to: {
        x: clamp(this.user.x + ((dx / length) * distance), 7, 97),
        y: clamp(this.user.y + ((dy / length) * distance), 24, 91),
      },
      startedAt: now,
      durationMs: clamp(
        500 + (distance * (maximumDistance > 20 ? 76 : 54)),
        620,
        maximumDistance > 20 ? 4200 : 880,
      ),
    };
    this.startMovementLoop();
  }

  private advanceTapMotion(now: number): boolean {
    if (!this.tapMotion) return false;
    const motion = this.tapMotion;
    const progress = clamp((now - motion.startedAt) / motion.durationMs, 0, 1);
    const eased = progress < 0.5
      ? 2 * progress * progress
      : 1 - (Math.pow(-2 * progress + 2, 2) / 2);
    const previous = { ...this.user };
    this.user = {
      x: motion.from.x + ((motion.to.x - motion.from.x) * eased),
      y: motion.from.y + ((motion.to.y - motion.from.y) * eased),
    };
    this.recordUserMotion(previous, now);
    if (progress >= 1) this.tapMotion = null;
    return pointDistance(previous, this.user) > 0.01;
  }

  private moveToward(target: WorldPoint, maximumDistance: number, now: number): boolean {
    const dx = target.x - this.user.x;
    const dy = target.y - this.user.y;
    const length = Math.hypot(dx, dy);
    if (length < 0.05 || maximumDistance <= 0) return false;
    const distance = Math.min(length, maximumDistance);
    const previous = { ...this.user };
    this.user = {
      x: clamp(this.user.x + ((dx / length) * distance), 7, 97),
      y: clamp(this.user.y + ((dy / length) * distance), 24, 91),
    };
    this.recordUserMotion(previous, now);
    return true;
  }

  private recordUserMotion(previous: WorldPoint, now: number): void {
    const distance = pointDistance(previous, this.user);
    if (distance <= 0.001) return;
    if (!Number.isFinite(this.followNotBefore)) {
      this.followNotBefore = now + FOLLOW_DELAY_MS;
    }
    this.totalTravel += distance;
    if (this.user.x <= 93 && this.user.y <= 91 && !(this.user.x >= 88 && this.user.y >= 80)) {
      this.lastStableUser = { ...this.user };
    }
    this.trail.push({ at: now, point: { ...this.user } });
    while (this.trail.length > 2 && this.trail[1].at < now - 2600) this.trail.shift();
    this.updateNearestResident();
    void this.updateDepartureState();
  }

  private advanceAbuFollower(now: number, deltaSeconds: number): boolean {
    if (this.totalTravel < 2.4) return false;
    if (now < this.followNotBefore) return false;
    const delayed = [...this.trail].reverse().find((item) => item.at <= now - FOLLOW_DELAY_MS);
    if (!delayed) return false;
    const dx = delayed.point.x - this.abu.x;
    const dy = delayed.point.y - this.abu.y;
    const distance = Math.hypot(dx, dy);
    if (distance <= 2.2) return false;
    if (Math.abs(dx) > 0.08) this.abuFacing = dx < 0 ? "left" : "right";
    const speed = clamp(distance * 1.28, 4.4, 10.6);
    const step = Math.min(distance, speed * deltaSeconds);
    this.abu = {
      x: clamp(this.abu.x + ((dx / distance) * step), 7, 93),
      y: clamp(this.abu.y + ((dy / distance) * step), 24, 91),
    };
    return true;
  }

  private shouldContinueAbuFollower(now: number): boolean {
    if (this.totalTravel < 2.4 || this.trail.length === 0) return false;
    if (now < this.followNotBefore) return true;
    const latest = this.trail[this.trail.length - 1];
    if (now - latest.at < FOLLOW_DELAY_MS + 40) return true;
    const delayed = [...this.trail].reverse().find((item) => item.at <= now - FOLLOW_DELAY_MS);
    return Boolean(delayed && pointDistance(this.abu, delayed.point) > 2.2);
  }

  private updateNearestResident(): void {
    const residents = this.trees.filter((tree) => !tree.own);
    const nearest = residents
      .map((tree) => ({ tree, distance: pointDistance(this.user, this.treeWorldPoint(tree)) }))
      .sort((left, right) => left.distance - right.distance)[0];
    this.nearestResidentRef = nearest && nearest.distance < 22 ? nearest.tree.scene_ref : "";
  }

  private async updateDepartureState(): Promise<void> {
    if (
      !this.visit
      || this.departureIntentPending
      || this.departureCommitPending
      || !["free_roam", "mirror_ready", "departure_intent"].includes(this.phase)
    ) return;
    if (this.user.x >= 95 && this.user.y >= 86) {
      await this.departDream("SPATIAL_BOUNDARY", { ...this.user });
      return;
    }
    const insideMist = this.user.x >= 88 && this.user.y >= 80;
    if (insideMist === this.departureIntentActive) return;
    this.departureIntentPending = true;
    try {
      this.acceptVisit(await setDreamDepartureIntent(this.visit.visit_id, insideMist));
      this.departureIntentActive = insideMist;
      this.phase = insideMist ? "departure_intent" : (this.reveal ? "mirror_ready" : "free_roam");
      if (this.ambient) this.ambient.volume = insideMist ? 0.045 : 0.12;
      this.syncSceneDom();
    } catch (error) {
      this.handleRuntimeFailure(error);
    } finally {
      this.departureIntentPending = false;
    }
  }

  private async departDream(
    trigger: "SPATIAL_BOUNDARY" | "SEMANTIC_EXIT",
    boundaryPosition?: WorldPoint,
  ): Promise<void> {
    if (!this.visit || this.departureCommitPending || this.phase === "departed") return;
    if (this.phase === "mirror_open" || this.phase === "mirror_opening") {
      await this.closeMirror("accessibility");
      return;
    }
    this.departureCommitPending = true;
    this.stopControlLoops();
    this.stopMovementLoop();
    this.stopMirrorPolling();
    this.clearSensitiveProjection();
    this.phase = "departure_committing";
    this.syncSceneDom();
    if (this.ambient) this.ambient.volume = 0.025;
    const commitSequence = ++this.departureCommitSequence;
    const navigation = this.navigationSample(this.lastStableUser);
    const pending = {
      visitId: this.visit.visit_id,
      trigger,
      navigation,
      boundaryPosition: boundaryPosition || null,
      commitSequence,
      hasKnowledgeSeed: Boolean(this.gameResult?.knowledge_seed),
    };
    sessionStorage.setItem(PENDING_DEPARTURE_KEY, JSON.stringify(pending));
    try {
      const result = await commitDreamDeparture(
        pending.visitId,
        trigger,
        navigation,
        commitSequence,
        boundaryPosition,
      );
      await this.finishDeparture(result.waking_route, pending.hasKnowledgeSeed);
    } catch (error) {
      this.departureCommitPending = false;
      if (!navigator.onLine || !(error instanceof DreamApiError)) {
        this.announce("雾在原地停住了。连接恢复后，会继续完成这次离开。");
        return;
      }
      this.handleRuntimeFailure(error);
    }
  }

  private async resumePendingDeparture(): Promise<void> {
    const pending = this.readPendingDeparture();
    if (!pending || this.departureCommitPending) return;
    try {
      const result = await loadDreamDepartureResult(pending.visitId, pending.commitSequence);
      await this.finishDeparture(result.waking_route, pending.hasKnowledgeSeed);
      return;
    } catch (error) {
      if (!(error instanceof DreamApiError) || error.status !== 404) return;
    }
    if (!this.visit || this.visit.visit_id !== pending.visitId) return;
    this.departureCommitPending = true;
    try {
      const result = await commitDreamDeparture(
        pending.visitId,
        pending.trigger,
        pending.navigation,
        pending.commitSequence,
        pending.boundaryPosition || undefined,
      );
      await this.finishDeparture(result.waking_route, pending.hasKnowledgeSeed);
    } catch (error) {
      this.departureCommitPending = false;
      if (navigator.onLine) this.handleRuntimeFailure(error);
    }
  }

  private async resolveCompletedDeparture(): Promise<boolean> {
    const pending = this.readPendingDeparture();
    if (!pending) return false;
    try {
      const result = await loadDreamDepartureResult(pending.visitId, pending.commitSequence);
      sessionStorage.removeItem(PENDING_DEPARTURE_KEY);
      clearDreamControl();
      markDreamReturnedWithSeed(pending.hasKnowledgeSeed);
      location.replace(result.waking_route);
      return true;
    } catch {
      return false;
    }
  }

  private readPendingDeparture(): {
    visitId: string;
    trigger: "SPATIAL_BOUNDARY" | "SEMANTIC_EXIT";
    navigation: DreamNavigationSample;
    boundaryPosition: WorldPoint | null;
    commitSequence: number;
    hasKnowledgeSeed: boolean;
  } | null {
    try {
      const raw = sessionStorage.getItem(PENDING_DEPARTURE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      sessionStorage.removeItem(PENDING_DEPARTURE_KEY);
      return null;
    }
  }

  private async finishDeparture(
    wakingRoute: "/experience",
    hasKnowledgeSeed: boolean,
  ): Promise<void> {
    this.departureCommitPending = false;
    this.departureIntentActive = false;
    this.phase = "departed";
    this.stopControlLoops();
    this.syncSceneDom();
    sessionStorage.removeItem(PENDING_DEPARTURE_KEY);
    clearDreamControl();
    markDreamReturnedWithSeed(hasKnowledgeSeed);
    this.announce("你离开了梦境。林中的时间仍会继续。");
    await delay(window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 80 : 680);
    location.replace(wakingRoute);
  }

  private navigationSample(position: WorldPoint): DreamNavigationSample {
    if (!this.visit) throw new DreamApiError("dream_visit_not_ready", 409);
    const ref = this.visit.world_projection_ref
      || currentDreamWorldProjectionRef(this.visit.visit_id);
    return {
      world_projection_ref: ref,
      world_space_ref: "dream-world:canonical-grove:v1",
      position: { x: position.x, y: position.y },
      camera_heading: 0,
      geometry_version: "dream-grove-geometry.v1",
    };
  }

  private startControlLoops(): void {
    this.stopControlLoops();
    void this.heartbeat();
    this.heartbeatTimer = window.setInterval(() => void this.heartbeat(), HEARTBEAT_MS);
    this.checkpointTimer = window.setInterval(() => void this.checkpoint(), CHECKPOINT_MS);
  }

  private stopControlLoops(): void {
    if (this.heartbeatTimer) window.clearInterval(this.heartbeatTimer);
    if (this.checkpointTimer) window.clearInterval(this.checkpointTimer);
    this.heartbeatTimer = 0;
    this.checkpointTimer = 0;
  }

  private async heartbeat(): Promise<void> {
    if (!this.visit || document.visibilityState !== "visible" || this.departureCommitPending) return;
    try {
      this.acceptVisit(await heartbeatDreamControl(this.visit.visit_id));
    } catch (error) {
      if (this.departureCommitPending || ["departure_committing", "departed"].includes(this.phase)) return;
      this.handleRuntimeFailure(error);
    }
  }

  private async checkpoint(): Promise<void> {
    if (
      !this.visit
      || document.visibilityState !== "visible"
      || this.departureCommitPending
      || !["free_roam", "mirror_ready", "departure_intent"].includes(this.phase)
    ) return;
    try {
      this.acceptVisit(await checkpointDreamVisit(
        this.visit.visit_id,
        this.navigationSample(this.lastStableUser),
        ++this.recoverySequence,
      ));
    } catch (error) {
      if (this.departureCommitPending || ["departure_committing", "departed"].includes(this.phase)) return;
      this.handleRuntimeFailure(error);
    }
  }

  private async touchTree(sceneRef: string): Promise<void> {
    if (!this.visit || !["free_roam", "mirror_ready"].includes(this.phase)) return;
    const tree = this.treeByRef(sceneRef);
    if (!tree || tree.own || !this.isWithinTouchDistance(tree)) return;
    this.playAmbient();
    this.phase = "tree_contact";
    this.nearestResidentRef = sceneRef;
    this.syncSceneDom();
    try {
      if (this.visit.selected_scene_ref !== sceneRef) {
        this.acceptVisit(await selectDreamTree(this.visit.visit_id, sceneRef));
        history.replaceState(
          {},
          "",
          `/experience/dream/visits/${encodeURIComponent(this.visit.visit_id)}/trees/${encodeURIComponent(sceneRef)}`,
        );
      }
      await loadDreamTree(this.visit.visit_id, sceneRef);
      this.reveal = await prepareDreamReveal(this.visit.visit_id, sceneRef);
      this.phase = "reveal_settling";
      this.syncSceneDom();
      this.playRevealTone(this.reveal.reveal_kind !== "none");
      this.announce(
        this.reveal.reveal_kind === "none"
          ? "树皮轻轻回应了触碰，没有生成新的命理含义。"
          : this.reveal.authorized_statement,
      );
      window.clearTimeout(this.revealTimer);
      this.revealTimer = window.setTimeout(() => {
        if (this.phase !== "reveal_settling") return;
        this.phase = "mirror_ready";
        this.syncSceneDom();
        this.announce("树根间的倒影现在可以被触碰。");
      }, this.reveal.reveal_kind === "none" ? 2100 : 3200);
    } catch (error) {
      this.handleAuthorizationOrError(error);
    }
  }

  private async openMirror(viewRef: string, pushHistory: boolean): Promise<void> {
    if (!this.visit || !this.visit.selected_scene_ref) return;
    this.phase = "mirror_opening";
    this.syncSceneDom();
    try {
      this.acceptVisit(await openDreamMirror(
        this.visit.visit_id,
        viewRef,
        this.navigationSample(this.lastStableUser),
      ));
      this.mirror = await loadDreamMirror(
        this.visit.visit_id,
        this.visit.selected_scene_ref,
        viewRef,
      );
      this.renderMirrorLayer();
      this.phase = "mirror_open";
      this.syncSceneDom();
      if (pushHistory) {
        history.pushState(
          { dreamMirror: true, visitId: this.visit.visit_id },
          "",
          `/experience/dream/visits/${encodeURIComponent(this.visit.visit_id)}/trees/${encodeURIComponent(this.visit.selected_scene_ref)}/mirror`,
        );
        this.mirrorHistoryActive = true;
      }
      this.startMirrorPolling();
      this.announce(
        this.mirror.verification.state === "focused"
          ? `${this.mirror.verification.verification_copy}${this.mirror.verification.authorized_statement}`
          : "当前暂无已确认主路径。",
      );
    } catch (error) {
      this.handleAuthorizationOrError(error);
    }
  }

  private renderMirrorLayer(): void {
    if (!this.mirror) return;
    const layer = this.root.querySelector<HTMLElement>(".dream-mirror-layer");
    if (!layer) return;
    layer.innerHTML = `<div class="dream-mirror-optics" aria-hidden="true"></div>
      <div class="dream-mirror-canvas-shell">
        ${renderDreamVerificationCanvas(this.mirror.canvas, this.mirror.verification)}
      </div>
      <div class="dream-mirror-water" data-mirror-exit-start aria-hidden="true">
        <span class="dream-mirror-root-boundary"></span>
        <span class="dream-mirror-forest-edge"></span>
      </div>`;
    layer.setAttribute("aria-hidden", "false");
    requestAnimationFrame(() => this.focusMirrorTarget());
  }

  private async closeMirror(origin: "gesture" | "history" | "accessibility" | "revoked"): Promise<void> {
    if (!this.visit || !["mirror_open", "mirror_opening", "authorization_closed"].includes(this.phase)) return;
    this.stopMirrorPolling();
    this.phase = origin === "revoked" ? "authorization_closed" : "mirror_closing";
    const layer = this.root.querySelector<HTMLElement>(".dream-mirror-layer");
    if (origin === "revoked") layer?.classList.add("is-masked");
    this.syncSceneDom();
    try {
      if (this.visit.state === "MIRROR_OPEN") {
        this.acceptVisit(await closeDreamMirror(this.visit.visit_id));
      }
    } catch (error) {
      if (origin !== "revoked") this.handleAuthorizationOrError(error);
    }
    window.setTimeout(() => {
      if (layer) {
        layer.innerHTML = "";
        layer.setAttribute("aria-hidden", "true");
        layer.classList.remove("is-masked");
      }
      this.mirror = null;
      this.reveal = null;
      this.phase = "free_roam";
      this.syncSceneDom();
      this.announce("你把手从镜中带回林地。林中的时间仍在继续。");
    }, window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 720);

    if (origin !== "history" && this.mirrorHistoryActive) {
      this.mirrorHistoryActive = false;
      this.suppressNextPop = true;
      history.back();
    } else if (this.visit) {
      history.replaceState(
        {},
        "",
        `/experience/dream/visits/${encodeURIComponent(this.visit.visit_id)}/trees/${encodeURIComponent(this.visit.selected_scene_ref)}`,
      );
    }
  }

  private startMirrorPolling(): void {
    this.stopMirrorPolling();
    this.mirrorPollTimer = window.setInterval(
      () => void this.validateOpenMirror(),
      MIRROR_POLL_MS,
    );
  }

  private stopMirrorPolling(): void {
    if (this.mirrorPollTimer) window.clearInterval(this.mirrorPollTimer);
    this.mirrorPollTimer = 0;
  }

  private async validateOpenMirror(): Promise<void> {
    if (!this.visit || this.phase !== "mirror_open" || !this.visit.active_onecanvas_view_ref) return;
    try {
      const next = await loadDreamMirror(
        this.visit.visit_id,
        this.visit.selected_scene_ref,
        this.visit.active_onecanvas_view_ref,
      );
      if (next.verification.state !== this.mirror?.verification.state) {
        this.mirror = next;
        this.renderMirrorLayer();
      }
    } catch (error) {
      await this.closeMirror("revoked");
      this.announce("这棵树的展示授权已经失效，命盘内容已被收起。");
    }
  }

  private async loadGameRounds(): Promise<void> {
    if (!this.visit) return;
    const load = async (): Promise<DreamGameRoundCard[]> => {
      if (!this.visit) return [];
      const gate = await loadDreamGameContentGate(this.visit.visit_id);
      if (
        gate.development_content !== "V50_CANONICAL_ONLY"
        || gate.simulated_round_count !== 0
        || gate.v50_canonical_round_count !== 3
        || gate.verified_real_content_gate !== "0/3"
      ) {
        throw new Error("dream_game_development_gate_invalid");
      }
      return loadDreamGameRounds(this.visit.visit_id);
    };
    try {
      this.gameRounds = await load();
    } catch {
      try {
        this.acceptVisit(await enterDreamVisit(this.visit.visit_id));
        this.gameRounds = await load();
      } catch {
        this.gameRounds = [];
      }
    }
  }

  private async openProblemRound(roundId: string): Promise<void> {
    if (!this.visit || this.gameBusy || !roundId) return;
    const round = this.gameRounds.find((item) => item.round_id === roundId);
    if (!round) return;
    this.porchIndex = Math.max(0, this.gameRounds.findIndex((item) => item.round_id === roundId));
    this.gameBusy = true;
    this.gameStatusMessage = "正在冻结问题发生前的观察面。";
    try {
      if (this.visit.selected_scene_ref !== round.resident_scene_ref) {
        this.acceptVisit(await selectDreamTree(this.visit.visit_id, round.resident_scene_ref));
      }
      this.nearestResidentRef = round.resident_scene_ref;
      const tree = this.treeByRef(round.resident_scene_ref);
      if (tree) {
        const point = this.treeApproachPoint(tree);
        this.user = point;
      }
      this.gameAttempt = await startDreamGameRound(this.visit.visit_id, roundId);
      this.gameLens = "overview";
      if (["KNOWLEDGE_SEED_ISSUED", "ROUND_COMPLETE"].includes(this.gameAttempt.state)) {
        this.gameResult = await loadDreamGameResult(
          this.visit.visit_id,
          this.gameAttempt.attempt_id,
        );
      } else {
        this.gameResult = null;
        if (
          this.gameAttempt.state === "ROUND_OBSERVING"
          && !this.gameAttempt.observed_lenses.includes(this.gameLens)
        ) {
          this.gameAttempt = await observeDreamGameLens(
            this.visit.visit_id,
            this.gameAttempt.attempt_id,
            this.gameLens,
          );
        }
      }
      this.gameShellOpen = true;
      this.gameLensOpen = false;
      this.gameLensHistoryActive = false;
      this.gameRevealAct = "user";
      this.gameDraft = this.emptyGameDraft();
      this.gameSealConfirmation = false;
      this.gameCastConfirmation = false;
      this.gameStatusMessage = "";
      this.restoreTreeQuestionState();
      this.openGameHistory(this.gameAttempt.attempt_id);
      this.renderGameLayer();
      this.startGamePolling();
      this.announce(
        `${this.gameResidentDisplayLabel(round.resident_scene_ref, round.resident_label)}的生命树已经可以观察。当前题组来自正式命盘冻结快照。`,
      );
    } catch (error) {
      this.handleGameError(error);
    } finally {
      this.gameBusy = false;
    }
  }

  private async resumeGameFromRoute(): Promise<void> {
    if (!this.visit) return;
    const attemptId = new URL(location.href).searchParams.get("dreamGameAttempt") || "";
    if (!attemptId) return;
    try {
      this.gameAttempt = await loadDreamGameAttempt(this.visit.visit_id, attemptId);
      this.gameShellOpen = true;
      this.gameLensOpen = false;
      this.porchIndex = Math.max(
        0,
        this.gameRounds.findIndex((item) => item.round_id === this.gameAttempt?.round_id),
      );
      this.restoreTreeQuestionState();
      if (["KNOWLEDGE_SEED_ISSUED", "ROUND_COMPLETE"].includes(this.gameAttempt.state)) {
        this.gameResult = await loadDreamGameResult(this.visit.visit_id, attemptId);
        this.gameRevealAct = "user";
      }
      this.gameHistoryActive = true;
      this.renderGameLayer();
      this.startGamePolling();
    } catch (error) {
      this.handleGameError(error);
    }
  }

  private renderGameLayer(): void {
    const layer = this.root.querySelector<HTMLElement>(".dream-game-layer");
    if (!layer) return;
    this.syncStoryRuntime();
    layer.classList.toggle("is-tree-world", this.gameShellOpen);
    if (!this.gameAttempt) {
      if (!this.gameShellOpen || !this.gameRounds.length) {
        layer.innerHTML = "";
        layer.setAttribute("aria-hidden", "true");
        this.syncSceneDom();
        return;
      }
      layer.innerHTML = renderDreamTreePorch({
        rounds: this.displayGameRounds(),
        activeIndex: this.porchIndex,
        banner: DREAM_GAME_BANNER,
        entering: this.porchEntering,
        mediaCue: this.gameMediaCue,
        focusedWhisper: this.porchWhisper,
        scene: this.story.scene,
      });
      layer.setAttribute("aria-hidden", "false");
      this.syncSceneDom();
      layer.querySelector<HTMLElement>("[data-dream-tree-porch]")?.focus({ preventScroll: true });
      this.schedulePorchIntroCompletion();
      return;
    }
    layer.innerHTML = this.renderDeferredQuestionLayer();
    layer.setAttribute("aria-hidden", "false");
    this.syncSceneDom();
  }

  private renderDeferredQuestionLayer(): string {
    if (!this.gameAttempt) return "";
    const attempt = this.gameAttempt;
    const projection = attempt.projection;
    const selectedRelations = projection.allowed_relations.filter(
      (item) => this.gameDraft.relationRefs.includes(item.relation_ref),
    );
    const canvas = renderDreamGameCanvas(
      projection.canvas,
      this.gameLens,
      this.gameDraft.nodeRefs,
      selectedRelations,
    );
    const passedNodes = this.passedTreeQuestionNodes();
    const flowerUnlocked = attempt.question_progress.flower_unlocked;
    return renderDreamTreeQuestionMap({
      attempt,
      residentDisplayLabel: this.gameResidentDisplayLabel(
        projection.resident_scene_ref,
        projection.resident_label,
      ),
      banner: projection.banner,
      activeLens: this.gameLens,
      lensOpen: this.gameLensOpen,
      canvasMarkup: canvas,
      questionBandMarkup: this.renderGameStage(),
      resultMarkup: this.gameResult ? this.renderGameResult() : "",
      activeNode: this.gameTreeState.activeNode,
      passedNodes,
      flowerUnlocked,
      flowerOpened: flowerUnlocked,
      fruitVisible: Boolean(attempt.flower?.shared_fruit_visible || this.gameResult),
      mediaCue: this.gameMediaCue,
      statusMessage: this.gameStatusMessage,
      scene: this.story.scene,
    });
  }

  private renderGameStage(): string {
    if (!this.gameAttempt) return "";
    const attempt = this.gameAttempt;
    if (attempt.state === "ROUND_OBSERVING") {
      if (!this.gameTreeState.activeNode) return "";
      if (this.gameTreeState.activeNode === "problem_flower") {
        return `<section class="dream-tree-node-question is-problem-flower">
          <button type="button" class="dream-question-close" data-dream-game-command="tree-question-close" aria-label="收起问题">×</button>
          <small>问题花 · 已解锁</small>
          <h2>这朵花承载着一个已经封存结果窗口的问题。</h2>
          <p>摘下花朵只会打开正式问题，不会自动起卦，也不会提前生成果实。</p>
          <div class="dream-game-actions">
            <button type="button" data-dream-game-command="open-flower">摘下问题花</button>
          </div>
        </section>`;
      }
      return this.renderTreeQuestion(this.gameTreeState.activeNode);
    }
    if (["QUESTION_FLOWER_OPEN", "OPTIONAL_DIVINATION"].includes(attempt.state)) {
      const question = attempt.flower_question;
      if (!question) {
        return `<section class="dream-game-question-stage" role="alert">
          <h2>问题花未能通过服务端核验</h2>
          <p>本轮已停止披露，不会寻找或替换另一个问题。</p>
        </section>`;
      }
      return `<section class="dream-game-question-stage">
        <button type="button" class="dream-question-close" data-dream-game-command="tree-question-close" aria-label="收起问题">×</button>
        <div class="dream-game-question-copy">
          <small>问题发生前冻结于 ${escapeHtml(formatDreamDate(question.knowledge_cutoff))}</small>
          <h2>${escapeHtml(question.neutral_question_text)}</h2>
          <p>结果窗口：${escapeHtml(formatDreamDate(question.outcome_window_start))} 至 ${escapeHtml(formatDreamDate(question.outcome_window_end))}</p>
        </div>
        ${attempt.divination ? this.renderDivination(attempt.divination.line_values_bottom_up, attempt.divination.moving_line_indexes) : ""}
        <div class="dream-game-actions">
          ${question.liuyao_permitted && !attempt.divination
            ? this.gameCastConfirmation
              ? `<span class="dream-game-inline-confirm">六爻将在你明确确认后才起卦，不生成解释。
                  <button type="button" data-dream-game-command="cast-confirm">确认发起</button>
                  <button type="button" data-dream-game-command="cast-cancel">取消</button>
                </span>`
              : `<button type="button" class="secondary" data-dream-game-command="cast-review">明确发起六爻</button>`
            : ""}
          <button type="button" data-dream-game-command="start-judgment">${attempt.divination ? "带着卦象作出判断" : "不占，直接判断"}</button>
        </div>
      </section>`;
    }
    if (attempt.state === "JUDGMENT_DRAFTING") {
      return this.renderJudgmentForm();
    }
    if (attempt.flower) {
      const flower = attempt.flower;
      if (flower.state === "OPEN" && attempt.sealed) {
        return `<section class="dream-game-sealed-fruit">
          <small>独立判断已封存</small>
          <h2>你的判断已经封入花心</h2>
          <p>${escapeHtml(flower.neutral_message)}</p>
          ${flower.answer_count_visible
            ? `<p>当前已有 ${flower.answer_count ?? 0} 份回应。开放期间不会显示答案或方向。</p>
              <button type="button" class="secondary" data-dream-game-command="close-flower">结束收集</button>`
            : ""}
        </section>`;
      }
      if (flower.state === "OPEN" && flower.answer_count_visible) {
        return `<section class="dream-game-sealed-fruit">
          <small>问题花仍在开放</small>
          <h2>只显示回应数量，不显示答案方向</h2>
          <p>当前已有 ${flower.answer_count ?? 0} 份回应。</p>
          <button type="button" class="secondary" data-dream-game-command="close-flower">结束收集</button>
        </section>`;
      }
      if (flower.state === "CLOSED_NO_RESPONSE") {
        return `<section class="dream-game-sealed-fruit">
          <small>答案集合已关闭</small>
          <h2>这朵花没有形成共同果实</h2>
          <p>${escapeHtml(flower.neutral_message)}</p>
        </section>`;
      }
      if (flower.state === "SHARED_FRUIT_FORMED" && !flower.revealable) {
        return `<section class="dream-game-sealed-fruit">
          <small>答案集合已经封存</small>
          <h2>共同雾白果实正在等待现实反馈</h2>
          <p>${escapeHtml(flower.neutral_message)}</p>
        </section>`;
      }
      if (flower.revealable && attempt.sealed) {
        return `<section class="dream-game-sealed-fruit">
          <small>共同果实已经到达揭盲时刻</small>
          <h2>雾白果实可以打开</h2>
          <p>揭盲只会追加你的私人对账记录，不会修改任何事前判断。</p>
          <button type="button" data-dream-game-command="reveal">揭开果实</button>
        </section>`;
      }
    }
    if (attempt.state === "OUTCOME_REVEALABLE") {
      return `<section class="dream-game-sealed-fruit">
        <small>玩家判断与独立系统判断已经分别封存</small>
        <h2>雾白果实第一次显形</h2>
        <p>揭盲只会追加结果记录，不会修改任何一份事前判断。</p>
        <button type="button" data-dream-game-command="reveal">揭开果实</button>
      </section>`;
    }
    return `<section class="dream-game-sealed-fruit"><p>这一局正在恢复。</p></section>`;
  }

  private renderTreeQuestion(nodeId: DreamTreeQuestionNodeId): string {
    if (!this.gameAttempt || nodeId === "problem_flower") return "";
    const definition = treeQuestionForNode(this.gameAttempt, nodeId);
    if (!definition) return "";
    const progress = this.questionProgressForNode(nodeId);
    const answer = progress?.last_selected_option_id || "";
    return `<section class="dream-tree-node-question" data-tree-question="${nodeId}">
      <button type="button" class="dream-question-close" data-dream-game-command="tree-question-close" aria-label="收起问题">×</button>
      <small>${escapeHtml(definition.title)}</small>
      <h2>${escapeHtml(definition.prompt)}</h2>
      <div class="dream-tree-question-options">
        ${definition.options.map((option) => `<button
          type="button"
          class="${answer === option.optionId ? "is-selected" : ""}"
          data-dream-game-command="tree-answer"
          data-tree-node="${nodeId}"
          data-answer-id="${escapeAttr(option.optionId)}"
          ${progress?.status === "COMPLETED" ? " disabled" : ""}
        >${escapeHtml(option.label)}</button>`).join("")}
      </div>
      ${progress?.feedback ? `<p class="dream-tree-question-feedback">${escapeHtml(progress.feedback)}</p>` : ""}
      <button
        type="button"
        class="dream-tree-observe-lens"
        data-dream-game-command="tree-open-lens"
        data-lens="${definition.lens}"
      >回到同源命盘镜观察</button>
    </section>`;
  }

  private renderJudgmentForm(): string {
    if (!this.gameAttempt) return "";
    const question = this.gameAttempt.flower_question;
    if (!question) return this.renderMissingFlowerQuestion();
    const options = Object.entries(question.outcome_options) as Array<["yes" | "no" | "partial_or_unclear", string]>;
    if (this.gameTreeState.judgmentStep === "outcome") {
      return `<form class="dream-game-judgment is-outcome" data-dream-game-form>
        <header><small>正式判断 · 1 / 4</small><h2>${escapeHtml(question.neutral_question_text)}</h2></header>
        <fieldset><legend>选择你认为最可能发生的结果</legend>
          ${options.map(([value, label]) => `<label><input type="radio" name="dream-outcome" data-dream-game-field="selectedOutcome" value="${value}"${this.gameDraft.selectedOutcome === value ? " checked" : ""}><span>${escapeHtml(label)}</span></label>`).join("")}
        </fieldset>
        <div class="dream-game-actions"><button type="button" data-dream-game-command="judgment-next">继续</button></div>
      </form>`;
    }
    if (this.gameTreeState.judgmentStep === "hypothesis") {
      const evidence = [
        ...this.gameDraft.nodeRefs.map((ref) => this.gameEvidenceDisplayLabel(ref)),
        ...this.gameDraft.relationRefs.map((ref) => this.gameEvidenceDisplayLabel(ref)),
      ];
      return `<form class="dream-game-judgment is-hypothesis" data-dream-game-form>
        <header><small>主要依据 · 2 / 4</small><h2>你怎样把刚才读过的叶与枝连成判断？</h2></header>
        <div class="dream-game-hypothesis-summary">
          <strong>已读结构</strong>
          ${evidence.length ? evidence.map((item) => `<i>${escapeHtml(item)}</i>`).join("") : "<span>当前暂不确认主要作用路径</span>"}
        </div>
        <label><span>你的候选路径假说</span><textarea data-dream-game-field="interpretation" maxlength="1200" placeholder="这是玩家假说，不会写成正式 PathAssertion。">${escapeHtml(this.gameDraft.interpretation)}</textarea></label>
        <div class="dream-game-actions"><button type="button" class="secondary" data-dream-game-command="judgment-back">返回</button><button type="button" data-dream-game-command="judgment-next">继续</button></div>
      </form>`;
    }
    if (this.gameTreeState.judgmentStep === "counter") {
      return `<form class="dream-game-judgment is-counter" data-dream-game-form>
        <header><small>反证与信心 · 3 / 4</small><h2>如果你的判断错了，最可能是哪条证据推翻它？</h2></header>
        <label class="dream-game-confidence"><span>信心程度 <b data-confidence-value>${Math.round(this.gameDraft.confidence / 100)}%</b></span><input type="range" min="0" max="10000" step="100" value="${this.gameDraft.confidence}" data-dream-game-field="confidence"></label>
        <label><span>最强的另一种解释</span><textarea data-dream-game-field="strongestAlternative" maxlength="1000" required>${escapeHtml(this.gameDraft.strongestAlternative)}</textarea></label>
        <label><span>什么事实会让你改变判断？</span><textarea data-dream-game-field="disconfirmationCondition" maxlength="1000" required>${escapeHtml(this.gameDraft.disconfirmationCondition)}</textarea></label>
        <div class="dream-game-actions"><button type="button" class="secondary" data-dream-game-command="judgment-back">返回</button><button type="button" data-dream-game-command="review-seal">花心回顾</button></div>
      </form>`;
    }
    return this.renderSealConfirmation();
  }

  private renderSealConfirmation(): string {
    if (!this.gameAttempt) return "";
    const question = this.gameAttempt.flower_question;
    if (!question) return this.renderMissingFlowerQuestion();
    const relationOptions = this.gameAttempt.projection.allowed_relations.filter(
      (item) => this.gameDraft.relationRefs.includes(item.relation_ref),
    );
    return `<section class="dream-game-seal-confirmation">
      <small>花心回顾 · 4 / 4</small>
      <h2>${escapeHtml(question.outcome_options[this.gameDraft.selectedOutcome])}</h2>
      <p>信心 ${Math.round(this.gameDraft.confidence / 100)}%</p>
      <div class="dream-game-hypothesis-summary">
        <strong>玩家候选路径 · 非正式</strong>
        <span>${escapeHtml(this.gameDraft.interpretation || "未填写路径说明")}</span>
        ${relationOptions.map((item) => `<i>${escapeHtml(item.label)}</i>`).join("")}
      </div>
      <dl><dt>最强替代</dt><dd>${escapeHtml(this.gameDraft.strongestAlternative)}</dd><dt>反证条件</dt><dd>${escapeHtml(this.gameDraft.disconfirmationCondition)}</dd></dl>
      <div class="dream-game-review-petals">
        <button type="button" data-dream-game-command="edit-step" data-step="outcome">正式选择</button>
        <button type="button" data-dream-game-command="edit-step" data-step="hypothesis">主要依据</button>
        <button type="button" data-dream-game-command="edit-step" data-step="counter">反证与信心</button>
      </div>
      <div class="dream-game-actions"><button type="button" class="secondary" data-dream-game-command="judgment-back">返回</button><button type="button" data-dream-game-command="seal">封存这次判断</button></div>
    </section>`;
  }

  private renderDivination(lines: number[], moving: number[]): string {
    return `<section class="dream-game-divination" aria-label="本次明确发起的六爻原始记录">
      <header><strong>六爻原始记录</strong><small>没有自动解释</small></header>
      <ol>${[...lines].reverse().map((value, reverseIndex) => {
        const lineIndex = 6 - reverseIndex;
        const yang = value === 7 || value === 9;
        return `<li class="${yang ? "is-yang" : "is-yin"}${moving.includes(lineIndex) ? " is-moving" : ""}"><span>${yang ? "━━━━━━" : "━━  ━━"}</span><small>${lineIndex}${moving.includes(lineIndex) ? " · 动" : ""}</small></li>`;
      }).join("")}</ol>
    </section>`;
  }

  private renderGameResult(): string {
    if (!this.gameResult || !this.gameAttempt) return "";
    const result = this.gameResult;
    const question = this.gameAttempt.flower_question;
    if (!question) return this.renderMissingFlowerQuestion();
    const labels = question.outcome_options;
    const acts: Record<DreamTreeRevealAct, string> = {
      user: `<article class="dream-tree-reveal-act is-user">
        <small>第一幕 · 我的判断</small>
        <strong>${escapeHtml(labels[result.submission.selected_outcome_option_id])}</strong>
        <span>封存信心 ${Math.round(result.submission.confidence_basis_points / 100)}%</span>
        <p>${escapeHtml(result.submission.user_path_hypothesis.interpretation || "未填写路径说明")}</p>
        <dl><dt>最强替代</dt><dd>${escapeHtml(result.submission.strongest_alternative)}</dd><dt>推翻条件</dt><dd>${escapeHtml(result.submission.disconfirmation_condition)}</dd></dl>
      </article>`,
      system: `<article class="dream-tree-reveal-act is-system">
        <small>第二幕 · 系统判断</small>
        <strong>${escapeHtml(labels[result.system_seal.selected_outcome_option_id])}</strong>
        <span>封存信心 ${Math.round(result.system_seal.confidence_basis_points / 100)}%</span>
        <p>${escapeHtml(result.system_seal.reasoning_summary)}</p>
        <dl><dt>最强替代</dt><dd>${escapeHtml(result.system_seal.strongest_alternative)}</dd><dt>推翻条件</dt><dd>${escapeHtml(result.system_seal.disconfirmation_condition)}</dd></dl>
      </article>`,
      evidence: `<article class="dream-tree-reveal-act is-evidence">
        <small>第三幕 · 事实证据</small>
        <strong>${escapeHtml(labels[result.outcome_evidence.resolved_option_id])}</strong>
        <p>${escapeHtml(result.outcome_evidence.outcome_summary)}</p>
        <ul>${result.outcome_evidence.evidence_items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
      </article>`,
      seed: `<article class="dream-tree-reveal-act is-seed">
        <small>知识种子 · 私人复盘记录</small>
        <strong>${escapeHtml(result.knowledge_seed.issued_calibration_summary)}</strong>
        <p>${escapeHtml(result.knowledge_seed.applicable_boundary)}</p>
        ${result.knowledge_seed.observation_kept.length
          ? `<div><b>保留的观察</b>${result.knowledge_seed.observation_kept.map((item) => `<span>${escapeHtml(this.gameEvidenceDisplayLabel(item))}</span>`).join("")}</div>`
          : ""}
        ${result.knowledge_seed.missed_or_overweighted.length
          ? `<div><b>遗漏或过度强调</b>${result.knowledge_seed.missed_or_overweighted.map((item) => `<span>${escapeHtml(this.gameEvidenceDisplayLabel(item))}</span>`).join("")}</div>`
          : ""}
      </article>`,
    };
    const sequence: DreamTreeRevealAct[] = ["user", "system", "evidence", "seed"];
    const index = sequence.indexOf(this.gameRevealAct);
    const previous = index > 0;
    const next = index < sequence.length - 1;
    return `<section class="dream-tree-reveal" data-reveal-act="${this.gameRevealAct}">
      <header><small>V50 结构果实已揭盲</small><h2>${escapeHtml(question.neutral_question_text)}</h2></header>
      <div class="dream-tree-reveal-stage">${acts[this.gameRevealAct]}</div>
      <nav class="dream-tree-reveal-progress" aria-label="揭盲进度">
        ${sequence.map((act, itemIndex) => `<span aria-current="${act === this.gameRevealAct ? "step" : "false"}">${itemIndex + 1}</span>`).join("")}
      </nav>
      <div class="dream-game-actions">
        ${previous ? `<button type="button" class="secondary" data-dream-game-command="reveal-prev">上一幕</button>` : ""}
        ${next
          ? `<button type="button" data-dream-game-command="reveal-next">继续</button>`
          : `<button type="button" data-dream-game-command="return-porch">回到梦树门廊</button>
             <button type="button" class="secondary" data-dream-game-command="depart">正式离梦</button>`}
      </div>
    </section>`;
  }

  private renderMissingFlowerQuestion(): string {
    return `<section class="dream-game-question-stage" role="alert">
      <h2>问题花未能通过服务端核验</h2>
      <p>本轮已停止披露，不会寻找或替换另一个问题。</p>
    </section>`;
  }

  private gameEvidenceDisplayLabel(ref: string): string {
    const projection = this.gameAttempt?.projection;
    const node = projection?.allowed_nodes.find((item) => item.node_ref === ref);
    if (node) return `${node.pillar_label} · ${node.label}`;
    const relation = projection?.allowed_relations.find((item) => item.relation_ref === ref);
    if (relation) return relation.label;
    if (ref.startsWith("node:")) return "未展示的命盘节点";
    return "本局中的一项观察";
  }

  private async handleGameCommand(target: HTMLElement): Promise<void> {
    if (!this.visit || this.gameBusy) return;
    const command = target.dataset.dreamGameCommand;
    this.gameStatusMessage = "";
    if (command === "porch-select") {
      if (this.suppressNextPorchSelection) {
        this.suppressNextPorchSelection = false;
        return;
      }
      const next = Number(target.dataset.porchIndex);
      if (Number.isInteger(next) && next >= 0 && next < this.gameRounds.length) {
        if (next === this.porchIndex) await this.commitFocusedTree();
        else this.focusPorchIndex(next);
      }
      return;
    }
    if (command === "porch-shift") {
      this.shiftPorch(Number(target.dataset.direction) || 0);
      return;
    }
    if (command === "depart" && !this.gameAttempt) {
      await this.departDream("SEMANTIC_EXIT");
      return;
    }
    if (!this.gameAttempt) return;
    if (command === "tree-node") {
      const nodeId = target.dataset.treeNode as DreamTreeQuestionNodeId;
      const definition = nodeId === "problem_flower"
        ? null
        : treeQuestionForNode(this.gameAttempt, nodeId);
      const locked = nodeId === "problem_flower"
        ? !this.gameAttempt.question_progress.flower_unlocked
        : !definition?.available;
      if (locked) {
        this.gameStatusMessage = nodeId === "problem_flower"
          ? "先读懂这棵树的叶与枝，花才会开放。"
          : "先读懂两片特殊树叶，再沿枝路继续观察。";
        this.persistTreeQuestionState();
        this.renderGameLayer();
        return;
      }
      this.gameTreeState.activeNode = nodeId;
      this.pushTreeQuestionHistory(nodeId);
      this.persistTreeQuestionState();
      this.renderGameLayer();
      return;
    }
    if (command === "tree-question-close") {
      this.closeTreeQuestion("command");
      return;
    }
    if (command === "tree-answer") {
      const nodeId = target.dataset.treeNode as DreamTreeQuestionNodeId;
      const answerId = target.dataset.answerId || "";
      await this.answerTreeQuestion(nodeId, answerId);
      return;
    }
    if (command === "tree-open-lens") {
      const lens = target.dataset.lens as DreamGameLens;
      await this.openGameLens(lens);
      return;
    }
    if (command === "close-lens") {
      this.closeGameLens("command");
      return;
    }
    if (command === "return-porch" || command === "return-forest") {
      if (this.gameResult && this.gameAttempt.state !== "ROUND_COMPLETE") {
        await this.runGameAction(async () => {
          this.gameAttempt = await completeDreamGameRound(
            this.visit!.visit_id,
            this.gameAttempt!.attempt_id,
          );
        }, false);
      }
      await this.returnToTreePorch("command");
      return;
    }
    if (command === "reveal-next" || command === "reveal-prev") {
      this.shiftRevealAct(command === "reveal-next" ? 1 : -1);
      return;
    }
    if (command === "lens") {
      const lens = target.dataset.lens as DreamGameLens;
      await this.openGameLens(lens);
      return;
    }
    if (command === "open-flower") {
      if (!this.gameAttempt.question_progress.flower_unlocked) {
        this.gameStatusMessage = "先读懂这棵树的叶与枝，花才会开放。";
        this.persistTreeQuestionState();
        this.renderGameLayer();
        return;
      }
      await this.runGameAction(async () => {
        this.gameAttempt = await openDreamProblemFlower(
          this.visit!.visit_id,
          this.gameAttempt!.attempt_id,
        );
        this.gameTreeState.activeNode = "problem_flower";
        this.persistTreeQuestionState();
      });
      this.playGameMediaCue("flower_open", 2250);
      return;
    }
    if (command === "cast-review") {
      this.gameCastConfirmation = true;
      this.renderGameLayer();
      return;
    }
    if (command === "cast-cancel") {
      this.gameCastConfirmation = false;
      this.renderGameLayer();
      return;
    }
    if (command === "cast-confirm") {
      const key = actionId("dream-cast");
      await this.runGameAction(async () => {
        this.gameAttempt = await castDreamGameDivination(
          this.visit!.visit_id,
          this.gameAttempt!.attempt_id,
          key,
        );
        this.gameCastConfirmation = false;
      });
      return;
    }
    if (command === "start-judgment") {
      await this.runGameAction(async () => {
        this.gameAttempt = await beginDreamGameJudgment(
          this.visit!.visit_id,
          this.gameAttempt!.attempt_id,
        );
        this.gameTreeState.judgmentStep = "outcome";
        this.persistTreeQuestionState();
      });
      return;
    }
    if (command === "judgment-next") {
      if (this.gameTreeState.judgmentStep === "outcome") {
        this.gameTreeState.judgmentStep = "hypothesis";
      } else if (this.gameTreeState.judgmentStep === "hypothesis") {
        this.gameTreeState.judgmentStep = "counter";
      }
      this.persistTreeQuestionState();
      this.renderGameLayer();
      return;
    }
    if (command === "judgment-back") {
      this.stepJudgmentBack();
      return;
    }
    if (command === "edit-step") {
      const step = target.dataset.step as DreamJudgmentStep;
      if (["outcome", "hypothesis", "counter"].includes(step)) {
        this.gameTreeState.judgmentStep = step;
        this.persistTreeQuestionState();
        this.renderGameLayer();
      }
      return;
    }
    if (command === "review-seal") {
      if (!this.gameDraft.strongestAlternative.trim() || !this.gameDraft.disconfirmationCondition.trim()) {
        this.gameStatusMessage = "请先写下最强替代解释和可推翻判断的事实。";
        this.renderGameLayer();
        return;
      }
      this.gameTreeState.judgmentStep = "review";
      this.persistTreeQuestionState();
      this.renderGameLayer();
      return;
    }
    if (command === "edit-judgment") {
      this.gameTreeState.judgmentStep = "outcome";
      this.persistTreeQuestionState();
      this.renderGameLayer();
      return;
    }
    if (command === "seal") {
      await this.sealCurrentGameJudgment();
      return;
    }
    if (command === "close-flower") {
      await this.closeCurrentProblemFlower();
      return;
    }
    if (command === "reveal") {
      await this.revealCurrentGameOutcome();
      return;
    }
    if (command === "depart") {
      if (this.gameResult && this.gameAttempt.state !== "ROUND_COMPLETE") {
        await this.runGameAction(async () => {
          this.gameAttempt = await completeDreamGameRound(
            this.visit!.visit_id,
            this.gameAttempt!.attempt_id,
          );
        }, false);
      }
      await this.closeGameLayer("command");
      await this.departDream("SEMANTIC_EXIT");
    }
  }

  private handleGameInput(event: Event): void {
    if (!this.gameAttempt || this.gameAttempt.state !== "JUDGMENT_DRAFTING") return;
    const input = (
      event.target instanceof HTMLInputElement
      || event.target instanceof HTMLTextAreaElement
      || event.target instanceof HTMLSelectElement
    )
      ? event.target
      : null;
    if (!input) return;
    const field = input.dataset.dreamGameField;
    if (field === "selectedOutcome" && input instanceof HTMLInputElement && input.checked) {
      this.gameDraft.selectedOutcome = input.value as DreamGameDraft["selectedOutcome"];
      this.persistTreeQuestionState();
      return;
    }
    if (field === "confidence" && input instanceof HTMLInputElement) {
      this.gameDraft.confidence = Number(input.value);
      const label = this.root.querySelector<HTMLElement>("[data-confidence-value]");
      if (label) label.textContent = `${Math.round(this.gameDraft.confidence / 100)}%`;
      this.persistTreeQuestionState();
      return;
    }
    if (field === "interpretation") this.gameDraft.interpretation = input.value;
    if (field === "strongestAlternative") this.gameDraft.strongestAlternative = input.value;
    if (field === "disconfirmationCondition") this.gameDraft.disconfirmationCondition = input.value;
    const kind = input.dataset.dreamGameKind;
    const reference = input.dataset.dreamGameRef || "";
    if (input instanceof HTMLInputElement && reference && kind) {
      const target = kind === "node" ? this.gameDraft.nodeRefs : this.gameDraft.relationRefs;
      const next = input.checked
        ? [...new Set([...target, reference])]
        : target.filter((item) => item !== reference);
      if (kind === "node") this.gameDraft.nodeRefs = next;
      if (kind === "relation") this.gameDraft.relationRefs = next;
      input.closest("label")?.classList.toggle("is-selected", input.checked);
    }
    this.persistTreeQuestionState();
  }

  private async sealCurrentGameJudgment(): Promise<void> {
    if (!this.visit || !this.gameAttempt) return;
    const payload: DreamGameJudgmentPayload = {
      selected_outcome_option_id: this.gameDraft.selectedOutcome,
      confidence_basis_points: this.gameDraft.confidence,
      node_refs: this.gameDraft.nodeRefs,
      relation_refs: this.gameDraft.relationRefs,
      interpretation: this.gameDraft.interpretation,
      evidence_refs: [...new Set([...this.gameDraft.nodeRefs, ...this.gameDraft.relationRefs])],
      strongest_alternative: this.gameDraft.strongestAlternative,
      disconfirmation_condition: this.gameDraft.disconfirmationCondition,
      idempotency_key: actionId("dream-seal"),
      confirmed: true,
    };
    this.rememberPendingGameAction({
      visitId: this.visit.visit_id,
      attemptId: this.gameAttempt.attempt_id,
      kind: "seal",
      payload,
    });
    await this.runGameAction(async () => {
      this.gameAttempt = await sealDreamGameJudgment(
        this.visit!.visit_id,
        this.gameAttempt!.attempt_id,
        payload,
      );
      sessionStorage.removeItem(PENDING_GAME_ACTION_KEY);
      this.gameSealConfirmation = false;
    });
    if (this.gameAttempt.flower?.shared_fruit_visible) {
      this.playGameMediaCue("fruit_forming", 1800);
    } else if (this.gameAttempt.flower?.own_answer_sealed) {
      this.gameStatusMessage = this.gameAttempt.flower.neutral_message;
    }
  }

  private async closeCurrentProblemFlower(): Promise<void> {
    if (!this.visit || !this.gameAttempt || !this.gameAttempt.flower?.answer_count_visible) return;
    const payload = { idempotencyKey: actionId("dream-flower-close") };
    this.rememberPendingGameAction({
      visitId: this.visit.visit_id,
      attemptId: this.gameAttempt.attempt_id,
      kind: "close-flower",
      payload,
    });
    await this.runGameAction(async () => {
      this.gameAttempt = await closeDreamProblemFlower(
        this.visit!.visit_id,
        this.gameAttempt!.attempt_id,
        payload.idempotencyKey,
      );
      sessionStorage.removeItem(PENDING_GAME_ACTION_KEY);
    });
    if (this.gameAttempt.flower?.shared_fruit_visible) {
      this.playGameMediaCue("fruit_forming", 1800);
    }
  }

  private async revealCurrentGameOutcome(): Promise<void> {
    if (!this.visit || !this.gameAttempt) return;
    const payload = { idempotencyKey: actionId("dream-reveal") };
    this.rememberPendingGameAction({
      visitId: this.visit.visit_id,
      attemptId: this.gameAttempt.attempt_id,
      kind: "reveal",
      payload,
    });
    await this.runGameAction(async () => {
      this.gameResult = await revealDreamGameOutcome(
        this.visit!.visit_id,
        this.gameAttempt!.attempt_id,
        payload.idempotencyKey,
      );
      this.gameAttempt = await loadDreamGameAttempt(
        this.visit!.visit_id,
        this.gameAttempt!.attempt_id,
      );
      this.gameLensOpen = false;
      this.gameRevealAct = "user";
      sessionStorage.removeItem(PENDING_GAME_ACTION_KEY);
    });
  }

  private async runGameAction(action: () => Promise<void>, render = true): Promise<void> {
    if (this.gameBusy) return;
    this.gameBusy = true;
    this.gameStatusMessage = "";
    try {
      await action();
    } catch (error) {
      const networkFailure = !(error instanceof DreamApiError);
      this.gameStatusMessage = networkFailure
        ? "连接暂时中断。恢复后会使用同一幂等请求继续，不会重复封存。"
        : "当前动作没有写入，请重新确认梦境状态。";
      this.handleGameError(error, false);
    } finally {
      this.gameBusy = false;
      if (render) this.renderGameLayer();
    }
  }

  private async resumePendingGameAction(): Promise<void> {
    if (!this.visit || this.gameBusy || !navigator.onLine) return;
    const pending = this.readPendingGameAction();
    if (!pending || pending.visitId !== this.visit.visit_id) return;
    try {
      this.gameAttempt = await loadDreamGameAttempt(this.visit.visit_id, pending.attemptId);
      if (pending.kind === "seal" && !this.gameAttempt.sealed) {
        this.gameAttempt = await sealDreamGameJudgment(
          pending.visitId,
          pending.attemptId,
          pending.payload as DreamGameJudgmentPayload,
        );
      }
      if (
        pending.kind === "close-flower"
        && this.gameAttempt.flower?.state === "OPEN"
      ) {
        const close = pending.payload as { idempotencyKey: string };
        this.gameAttempt = await closeDreamProblemFlower(
          pending.visitId,
          pending.attemptId,
          close.idempotencyKey,
        );
      }
      if (pending.kind === "reveal" && !["KNOWLEDGE_SEED_ISSUED", "ROUND_COMPLETE"].includes(this.gameAttempt.state)) {
        const reveal = pending.payload as { idempotencyKey: string };
        this.gameResult = await revealDreamGameOutcome(
          pending.visitId,
          pending.attemptId,
          reveal.idempotencyKey,
        );
        this.gameAttempt = await loadDreamGameAttempt(this.visit.visit_id, pending.attemptId);
      } else if (pending.kind === "reveal") {
        this.gameResult = await loadDreamGameResult(this.visit.visit_id, pending.attemptId);
      }
      sessionStorage.removeItem(PENDING_GAME_ACTION_KEY);
      this.renderGameLayer();
    } catch (error) {
      if (error instanceof DreamApiError) {
        sessionStorage.removeItem(PENDING_GAME_ACTION_KEY);
        this.handleGameError(error);
      }
    }
  }

  private rememberPendingGameAction(value: PendingDreamGameAction): void {
    sessionStorage.setItem(PENDING_GAME_ACTION_KEY, JSON.stringify(value));
  }

  private readPendingGameAction(): PendingDreamGameAction | null {
    try {
      const raw = sessionStorage.getItem(PENDING_GAME_ACTION_KEY);
      return raw ? JSON.parse(raw) as PendingDreamGameAction : null;
    } catch {
      sessionStorage.removeItem(PENDING_GAME_ACTION_KEY);
      return null;
    }
  }

  private startGamePolling(): void {
    this.stopGamePolling();
    this.gamePollTimer = window.setInterval(() => void this.validateOpenGame(), 10000);
  }

  private stopGamePolling(): void {
    if (this.gamePollTimer) window.clearInterval(this.gamePollTimer);
    this.gamePollTimer = 0;
  }

  private async validateOpenGame(): Promise<void> {
    if (!this.visit || !this.gameAttempt || document.visibilityState !== "visible") return;
    try {
      const next = await loadDreamGameAttempt(this.visit.visit_id, this.gameAttempt.attempt_id);
      const flowerChanged = flowerLifecycleKey(next) !== flowerLifecycleKey(this.gameAttempt);
      if (
        next.state !== this.gameAttempt.state
        || next.updated_at !== this.gameAttempt.updated_at
        || flowerChanged
      ) {
        this.gameAttempt = next;
        if (flowerChanged) {
          this.gameStatusMessage = next.flower?.neutral_message || "";
        }
        if (["KNOWLEDGE_SEED_ISSUED", "ROUND_COMPLETE"].includes(next.state)) {
          this.gameResult = await loadDreamGameResult(this.visit.visit_id, next.attempt_id);
        }
        this.renderGameLayer();
      }
    } catch (error) {
      this.handleGameError(error);
    }
  }

  private shiftPorch(delta: number): void {
    if (!this.gameRounds.length || this.gameAttempt || this.porchOrbitTimer) return;
    const next = (
      (this.porchIndex + delta) % this.gameRounds.length
      + this.gameRounds.length
    ) % this.gameRounds.length;
    this.focusPorchIndex(next);
  }

  private focusPorchIndex(index: number): void {
    if (!Number.isInteger(index) || index < 0 || index >= this.gameRounds.length) return;
    const porchCamera = this.root.querySelector<HTMLElement>("[data-dream-tree-porch]");
    if (porchCamera?.dataset.orbitLocked === "true") return;
    const previousIndex = this.porchIndex;
    if (index === previousIndex || this.porchOrbitTimer) return;
    if (porchCamera) porchCamera.dataset.orbitLocked = "true";
    this.porchIndex = index;
    this.porchEntering = false;
    this.porchWhisper = "";
    this.story.dispatch({
      type: "FOCUS_CANDIDATE",
      index: this.porchIndex,
      candidateCount: this.gameRounds.length,
    });
    if (!this.updatePorchFocus(previousIndex)) {
      if (porchCamera) delete porchCamera.dataset.orbitLocked;
      this.renderGameLayer();
    }
    this.scheduleFocusedTreeWhisper(780);
  }

  private updatePorchFocus(previousIndex: number): boolean {
    const layer = this.root.querySelector<HTMLElement>(".dream-game-layer");
    const camera = layer?.querySelector<HTMLElement>("[data-dream-tree-porch]");
    if (!layer || !camera || this.gameAttempt) return false;
    const count = this.gameRounds.length;
    const forward = (this.porchIndex - previousIndex + count) % count;
    const direction = forward === 1 ? "next" : "previous";
    camera.classList.remove("is-orbiting-next", "is-orbiting-previous");
    camera.classList.add(`is-orbiting-${direction}`);
    window.clearTimeout(this.porchOrbitTimer);
    this.porchOrbitTimer = window.setTimeout(() => {
      this.porchOrbitTimer = 0;
      camera.classList.remove("is-orbiting-next", "is-orbiting-previous");
      delete camera.dataset.orbitLocked;
      for (const tree of camera.querySelectorAll<HTMLElement>("[data-orbit-from-slot]")) {
        delete tree.dataset.orbitFromSlot;
      }
    }, window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 220 : 1260);

    const rounds = this.displayGameRounds();
    for (const tree of layer.querySelectorAll<HTMLElement>(
      ".dream-tree-porch-tree.is-porch-actor[data-porch-index]",
    )) {
      const itemIndex = Number(tree.dataset.porchIndex);
      if (!Number.isInteger(itemIndex) || itemIndex < 0 || itemIndex >= count) continue;
      const active = itemIndex === this.porchIndex;
      const itemForward = (itemIndex - this.porchIndex + count) % count;
      tree.dataset.orbitFromSlot = tree.dataset.orbitSlot || "0";
      tree.dataset.orbitSlot = String(itemForward === 0 ? 0 : itemForward === 1 ? 1 : -1);
      tree.classList.toggle("is-active", active);
      tree.classList.toggle("is-dream-heart", active);
      tree.classList.toggle("is-ghost", !active);
      tree.setAttribute("aria-current", active ? "true" : "false");
      tree.setAttribute(
        "aria-label",
        active
          ? `${rounds[itemIndex].anonymous_label}位于梦心，轻触进入`
          : `让${rounds[itemIndex].anonymous_label}来到梦心`,
      );
    }
    const currentLabel = layer.querySelector<HTMLElement>("[data-porch-current-label]");
    if (currentLabel) {
      currentLabel.textContent = `当前梦心位：${rounds[this.porchIndex].anonymous_label}`;
    }
    this.updatePorchWhisper();
    return true;
  }

  private async commitFocusedTree(): Promise<void> {
    const round = this.gameRounds[this.porchIndex];
    if (!round || this.gameAttempt || this.gameBusy) return;
    this.gameBusy = true;
    this.story.dispatch({ type: "COMMIT_CANDIDATE", roundId: round.round_id });
    this.gameMediaCue = "tree_enter";
    this.renderGameLayer();
    await delay(window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 180 : 2300);
    this.story.dispatch({ type: "TREE_ENTRY_COMPLETED" });
    this.gameMediaCue = "none";
    this.gameBusy = false;
    await this.openProblemRound(round.round_id);
  }

  private scheduleFocusedTreeWhisper(delayMs: number): void {
    if (this.porchWhisperTimer) window.clearTimeout(this.porchWhisperTimer);
    const round = this.gameRounds[this.porchIndex];
    if (!round || this.spokenRoundIds.has(round.round_id)) return;
    this.porchWhisperTimer = window.setTimeout(() => {
      this.porchWhisperTimer = 0;
      const focused = this.gameRounds[this.porchIndex];
      if (!focused || focused.round_id !== round.round_id || this.gameAttempt) return;
      this.spokenRoundIds.add(round.round_id);
      this.porchWhisper = round.selection_whisper;
      this.updatePorchWhisper();
      this.announce(round.selection_whisper);
      this.porchWhisperTimer = window.setTimeout(() => {
        this.porchWhisperTimer = 0;
        if (this.porchWhisper !== round.selection_whisper) return;
        this.porchWhisper = "";
        this.updatePorchWhisper();
      }, 3000);
    }, delayMs);
  }

  private updatePorchWhisper(): void {
    const whisper = this.root.querySelector<HTMLElement>(".dream-ghost-orbit-whisper");
    if (!whisper) return;
    whisper.textContent = this.porchWhisper;
    if (this.porchWhisper) {
      whisper.removeAttribute("aria-hidden");
      whisper.setAttribute("aria-live", "polite");
    } else {
      whisper.setAttribute("aria-hidden", "true");
      whisper.removeAttribute("aria-live");
    }
  }

  private displayGameRounds(): DreamGameRoundCard[] {
    return this.gameRounds.map((round) => ({
      ...round,
      resident_label: this.gameResidentDisplayLabel(
        round.resident_scene_ref,
        round.resident_label,
      ),
    }));
  }

  private syncStoryRuntime(): void {
    const foundationComplete = Boolean(
      this.gameAttempt?.question_progress.flower_unlocked,
    );
    this.story.sync({
      visit: this.visit,
      gameState: this.gameAttempt?.state || "",
      hasAttempt: Boolean(this.gameAttempt),
      hasResult: Boolean(this.gameResult),
      foundationComplete,
    });
    const main = this.root.querySelector<HTMLElement>(".dream-first-visit");
    if (!main) return;
    main.dataset.dreamStoryState = this.story.snapshot.businessState;
    main.dataset.dreamStoryPresentation = this.story.snapshot.presentationState;
    main.dataset.dreamSceneId = this.story.scene.sceneId;
  }

  private gameResidentDisplayLabel(sceneRef: string, fallback: string): string {
    const source = this.trees.find((tree) => tree.scene_ref === sceneRef);
    if (source?.source_kind !== "authorized_human") return fallback;
    const index = Math.max(
      0,
      this.gameRounds.findIndex((round) => round.resident_scene_ref === sceneRef),
    );
    return `匿名梦境居民${["一", "二", "三"][index] || ""}`;
  }

  private resetPorchDrag(camera: HTMLElement): void {
    camera.style.setProperty("--porch-drag-x", "0px");
    camera.style.setProperty("--porch-drag-sky", "0px");
    camera.style.setProperty("--porch-drag-far", "0px");
    camera.style.setProperty("--porch-drag-ground", "0px");
  }

  private schedulePorchIntroCompletion(): void {
    if (!this.porchEntering || this.porchIntroTimer) return;
    const duration = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 220 : 5200;
    this.porchIntroTimer = window.setTimeout(() => {
      this.porchIntroTimer = 0;
      if (!this.porchEntering || this.gameAttempt) return;
      this.porchEntering = false;
      this.renderGameLayer();
      this.scheduleFocusedTreeWhisper(620);
    }, duration);
  }

  private playGameMediaCue(cue: DreamTreeMediaCue, durationMs: number): void {
    if (this.gameMediaTimer) window.clearTimeout(this.gameMediaTimer);
    this.gameMediaCue = cue;
    this.renderGameLayer();
    this.gameMediaTimer = window.setTimeout(() => {
      this.gameMediaTimer = 0;
      if (this.gameMediaCue !== cue) return;
      this.gameMediaCue = "none";
      this.renderGameLayer();
    }, window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 180 : durationMs);
  }

  private treeQuestionStorageKey(attemptId: string): string {
    return `${TREE_QUESTION_STATE_KEY}:${attemptId}`;
  }

  private resetTreeQuestionState(attemptId: string): void {
    this.gameDraft = this.emptyGameDraft();
    this.gameTreeState = {
      attemptId,
      activeNode: "",
      judgmentStep: "outcome",
      draft: { ...this.gameDraft },
    };
    this.persistTreeQuestionState();
  }

  private restoreTreeQuestionState(): void {
    if (!this.gameAttempt) return;
    const attemptId = this.gameAttempt.attempt_id;
    let restored: Partial<DreamTreeQuestionState> | null = null;
    try {
      const raw = sessionStorage.getItem(this.treeQuestionStorageKey(attemptId));
      restored = raw ? JSON.parse(raw) as Partial<DreamTreeQuestionState> : null;
    } catch {
      sessionStorage.removeItem(this.treeQuestionStorageKey(attemptId));
    }
    const allowedNodes: DreamTreeQuestionNodeId[] = [
      "leaf_structure",
      "leaf_support",
      "branch_path",
      "problem_flower",
    ];
    if (restored?.attemptId === attemptId) {
      const activeNode = (
        restored.activeNode && allowedNodes.includes(restored.activeNode)
      ) ? restored.activeNode : "";
      const judgmentStep = restored.judgmentStep
        && ["outcome", "hypothesis", "counter", "review"].includes(restored.judgmentStep)
        ? restored.judgmentStep
        : "outcome";
      this.gameDraft = {
        ...this.emptyGameDraft(),
        ...restored.draft,
      };
      this.gameTreeState = {
        attemptId,
        activeNode,
        judgmentStep,
        draft: { ...this.gameDraft },
      };
    } else {
      this.resetTreeQuestionState(attemptId);
    }
    if (this.gameAttempt.state !== "ROUND_OBSERVING") {
      this.gameTreeState.activeNode = "problem_flower";
    }
    const routeNode = new URLSearchParams(location.hash.replace(/^#/, "")).get(
      "tree-question",
    ) as DreamTreeQuestionNodeId | null;
    if (routeNode) {
      const routeNodeUnlocked = this.treeQuestionNodeAvailable(routeNode);
      if (allowedNodes.includes(routeNode) && routeNodeUnlocked) {
        this.gameTreeState.activeNode = routeNode;
        this.gameQuestionHistoryActive = true;
      }
    }
    this.persistTreeQuestionState();
  }

  private persistTreeQuestionState(): void {
    const attemptId = this.gameAttempt?.attempt_id || this.gameTreeState.attemptId;
    if (!attemptId) return;
    this.gameTreeState.attemptId = attemptId;
    this.gameTreeState.draft = {
      ...this.gameDraft,
      nodeRefs: [...this.gameDraft.nodeRefs],
      relationRefs: [...this.gameDraft.relationRefs],
    };
    try {
      sessionStorage.setItem(
        this.treeQuestionStorageKey(attemptId),
        JSON.stringify(this.gameTreeState),
      );
    } catch {
      // Visit recovery remains server-authoritative; storage can fail closed.
    }
  }

  private async answerTreeQuestion(
    nodeId: DreamTreeQuestionNodeId,
    answerId: string,
  ): Promise<void> {
    if (!this.visit || !this.gameAttempt || nodeId === "problem_flower") return;
    const definition = treeQuestionForNode(this.gameAttempt, nodeId);
    const answer = definition?.options.find((item) => item.optionId === answerId);
    if (!definition || !answer || !definition.available) return;
    const wasUnlocked = this.gameAttempt.question_progress.flower_unlocked;
    await this.runGameAction(async () => {
      this.gameAttempt = await answerDreamLearningQuestion(
        this.visit!.visit_id,
        this.gameAttempt!.attempt_id,
        definition.questionId,
        answer.optionId,
        actionId("dream-learning-answer"),
      );
      const progress = this.questionProgressForNode(nodeId);
      this.gameStatusMessage = progress?.feedback || "";
      if (progress?.status === "COMPLETED") {
        this.gameTreeState.activeNode = "";
        this.closeTreeQuestion("answer");
      }
      this.persistTreeQuestionState();
    });
    if (!wasUnlocked && this.gameAttempt.question_progress.flower_unlocked) {
      this.gameStatusMessage = "叶与枝已经读懂，能量沿树体抵达花骨朵。";
      this.playGameMediaCue("flower_open", 2250);
    }
  }

  private passedTreeQuestionNodes(): DreamTreeQuestionNodeId[] {
    if (!this.gameAttempt) return [];
    return this.gameAttempt.question_progress.items
      .filter((item) => item.status === "COMPLETED")
      .map((item) => {
        if (item.kind === "LEAF_BASIC_01") return "leaf_structure";
        if (item.kind === "LEAF_BASIC_02") return "leaf_support";
        return "branch_path";
      });
  }

  private questionProgressForNode(
    nodeId: DreamTreeQuestionNodeId,
  ): DreamGameAttemptView["question_progress"]["items"][number] | undefined {
    if (!this.gameAttempt || nodeId === "problem_flower") return undefined;
    const definition = treeQuestionForNode(this.gameAttempt, nodeId);
    if (!definition) return undefined;
    return this.gameAttempt.question_progress.items.find(
      (item) => item.question_id === definition.questionId,
    );
  }

  private treeQuestionNodeAvailable(nodeId: DreamTreeQuestionNodeId): boolean {
    if (!this.gameAttempt) return false;
    if (nodeId === "problem_flower") {
      return this.gameAttempt.question_progress.flower_unlocked;
    }
    return Boolean(treeQuestionForNode(this.gameAttempt, nodeId)?.available);
  }

  private async openGameLens(lens: DreamGameLens): Promise<void> {
    if (
      !this.visit
      || !this.gameAttempt
      || this.gameBusy
      || !this.gameAttempt.projection.available_lenses.includes(lens)
    ) return;
    this.gameBusy = true;
    try {
      this.gameAttempt = await observeDreamGameLens(
        this.visit.visit_id,
        this.gameAttempt.attempt_id,
        lens,
      );
      this.gameLens = lens;
      this.gameLensOpen = true;
      this.openGameLensHistory(lens);
      this.renderGameLayer();
    } catch (error) {
      this.handleGameError(error);
    } finally {
      this.gameBusy = false;
    }
  }

  private pushTreeQuestionHistory(nodeId: DreamTreeQuestionNodeId): void {
    if (this.gameQuestionHistoryActive) return;
    const url = new URL(location.href);
    url.hash = `tree-question=${nodeId}`;
    history.pushState(
      {
        dreamTreeQuestion: true,
        visitId: this.visit?.visit_id || "",
        attemptId: this.gameAttempt?.attempt_id || "",
        nodeId,
      },
      "",
      url,
    );
    this.gameQuestionHistoryActive = true;
  }

  private closeTreeQuestion(
    origin: "command" | "history" | "accessibility" | "answer",
  ): void {
    this.gameTreeState.activeNode = "";
    this.persistTreeQuestionState();
    if (origin !== "history" && this.gameQuestionHistoryActive) {
      this.gameQuestionHistoryActive = false;
      if (origin !== "answer") this.renderGameLayer();
      this.suppressNextPop = true;
      history.back();
      return;
    }
    this.gameQuestionHistoryActive = false;
    if (origin === "history") {
      const url = new URL(location.href);
      if (url.hash.startsWith("#tree-question=")) {
        url.hash = "";
        history.replaceState(
          {
            dreamGame: true,
            visitId: this.visit?.visit_id || "",
            attemptId: this.gameAttempt?.attempt_id || "",
          },
          "",
          url,
        );
      }
    }
    if (origin !== "answer") this.renderGameLayer();
  }

  private stepJudgmentBack(): void {
    if (this.gameTreeState.judgmentStep === "review") {
      this.gameTreeState.judgmentStep = "counter";
    } else if (this.gameTreeState.judgmentStep === "counter") {
      this.gameTreeState.judgmentStep = "hypothesis";
    } else if (this.gameTreeState.judgmentStep === "hypothesis") {
      this.gameTreeState.judgmentStep = "outcome";
    }
    this.persistTreeQuestionState();
    this.renderGameLayer();
  }

  private restoreGameHistoryGuard(): void {
    if (!this.gameAttempt) return;
    const url = new URL(location.href);
    url.searchParams.set("dreamGameAttempt", this.gameAttempt.attempt_id);
    history.pushState(
      {
        dreamGame: true,
        visitId: this.visit?.visit_id || "",
        attemptId: this.gameAttempt.attempt_id,
      },
      "",
      url,
    );
    this.gameHistoryActive = true;
  }

  private openGameLensHistory(lens: DreamGameLens): void {
    if (this.gameLensHistoryActive) return;
    const url = new URL(location.href);
    url.hash = `lens=${lens}`;
    history.pushState(
      {
        dreamTreeLens: true,
        visitId: this.visit?.visit_id || "",
        attemptId: this.gameAttempt?.attempt_id || "",
        lens,
      },
      "",
      url,
    );
    this.gameLensHistoryActive = true;
  }

  private closeGameLens(
    origin: "command" | "history" | "accessibility",
  ): void {
    if (!this.gameLensOpen) return;
    this.gameLensOpen = false;
    this.renderGameLayer();
    this.announce("你回到刚才的树中位置。");
    if (origin !== "history" && this.gameLensHistoryActive) {
      this.gameLensHistoryActive = false;
      this.suppressNextPop = true;
      history.back();
      return;
    }
    this.gameLensHistoryActive = false;
    const url = new URL(location.href);
    url.hash = "";
    history.replaceState(
      {
        dreamGame: true,
        visitId: this.visit?.visit_id || "",
        attemptId: this.gameAttempt?.attempt_id || "",
      },
      "",
      url,
    );
  }

  private shiftRevealAct(delta: number): void {
    const sequence: DreamTreeRevealAct[] = ["user", "system", "evidence", "seed"];
    const current = sequence.indexOf(this.gameRevealAct);
    const next = clamp(current + delta, 0, sequence.length - 1);
    if (next === current) return;
    this.gameRevealAct = sequence[next];
    this.renderGameLayer();
  }

  private async returnToTreePorch(
    origin: "command" | "history" | "accessibility",
  ): Promise<void> {
    this.stopGamePolling();
    this.gameAttempt = null;
    this.gameResult = null;
    this.gameLensOpen = false;
    this.gameLensHistoryActive = false;
    this.gameQuestionHistoryActive = false;
    this.gameTreeState.activeNode = "";
    this.gameMediaCue = "none";
    if (this.gameMediaTimer) window.clearTimeout(this.gameMediaTimer);
    this.gameMediaTimer = 0;
    this.gameRevealAct = "user";
    this.gameSealConfirmation = false;
    this.gameCastConfirmation = false;
    this.gameStatusMessage = "";
    sessionStorage.removeItem(PENDING_GAME_ACTION_KEY);
    this.renderGameLayer();
    this.gameHistoryActive = false;
    const url = new URL(location.href);
    url.searchParams.delete("dreamGameAttempt");
    url.hash = "";
    history.replaceState(
      { dreamForest: true, visitId: this.visit?.visit_id || "", origin },
      "",
      url,
    );
    this.announce("你回到三棵梦树之间。");
  }

  private async closeGameLayer(origin: "command" | "history" | "accessibility"): Promise<void> {
    this.stopGamePolling();
    this.gameShellOpen = false;
    this.gameAttempt = null;
    this.gameResult = null;
    this.gameLensOpen = false;
    this.gameLensHistoryActive = false;
    this.gameQuestionHistoryActive = false;
    this.gameTreeState.activeNode = "";
    this.gameMediaCue = "none";
    if (this.gameMediaTimer) window.clearTimeout(this.gameMediaTimer);
    this.gameMediaTimer = 0;
    this.gameSealConfirmation = false;
    this.gameCastConfirmation = false;
    this.gameStatusMessage = "";
    sessionStorage.removeItem(PENDING_GAME_ACTION_KEY);
    const layer = this.root.querySelector<HTMLElement>(".dream-game-layer");
    if (layer) {
      layer.innerHTML = "";
      layer.setAttribute("aria-hidden", "true");
    }
    this.gameHistoryActive = false;
    const url = new URL(location.href);
    url.searchParams.delete("dreamGameAttempt");
    url.hash = "";
    history.replaceState(
      { dreamForest: true, visitId: this.visit?.visit_id || "", origin },
      "",
      url,
    );
    this.announce("你回到了持续运行的三树林境。");
  }

  private openGameHistory(attemptId: string): void {
    const url = new URL(location.href);
    url.searchParams.set("dreamGameAttempt", attemptId);
    history.pushState(
      { dreamGame: true, visitId: this.visit?.visit_id || "", attemptId },
      "",
      url,
    );
    this.gameHistoryActive = true;
  }

  private handleGameError(error: unknown, closeOnAuthorityFailure = true): void {
    const code = this.errorCode(error);
    if (
      code.includes("control_lease")
      || code.includes("content_revoked")
      || code.includes("authorization")
      || code.includes("source_changed")
      || code.includes("projection_invalid")
    ) {
      this.stopGamePolling();
      sessionStorage.removeItem(PENDING_GAME_ACTION_KEY);
      if (closeOnAuthorityFailure) {
        const layer = this.root.querySelector<HTMLElement>(".dream-game-layer");
        if (layer) {
          layer.innerHTML = `<div class="dream-game-fail-closed" role="alert">当前内容授权或梦境控制已失效，盲局内容已经收起。</div>`;
        }
        this.gameAttempt = null;
        this.gameResult = null;
      }
      if (code.includes("control_lease")) this.handleRuntimeFailure(error);
      return;
    }
    if (closeOnAuthorityFailure) this.gameStatusMessage = "暂时无法确认盲局状态。没有结果被推断或写入。";
    this.renderGameLayer();
  }

  private emptyGameDraft(): DreamGameDraft {
    return {
      selectedOutcome: "partial_or_unclear",
      confidence: 5000,
      nodeRefs: [],
      relationRefs: [],
      interpretation: "",
      strongestAlternative: "",
      disconfirmationCondition: "",
    };
  }

  private syncSceneDom(): void {
    const main = this.root.querySelector<HTMLElement>(".dream-first-visit");
    if (!main) return;
    main.dataset.phase = this.phase;
    main.style.setProperty("--user-x", String(this.user.x));
    main.style.setProperty("--user-y", String(this.user.y));
    main.style.setProperty("--abu-x", String(this.abu.x));
    main.style.setProperty("--abu-y", String(this.abu.y));
    main.style.setProperty("--abu-facing", this.abuFacing === "left" ? "-1" : "1");
    main.style.setProperty("--camera-x", String((50 - this.user.x) * 0.12));
    main.style.setProperty("--camera-y", String((66 - this.user.y) * 0.08));
    main.dataset.nearScene = this.nearestResidentRef;
    main.dataset.selectedScene = this.visit?.selected_scene_ref || "";
    main.dataset.revealMode = this.reveal?.visual_mode || "none";
    main.dataset.runtimeState = this.visit?.runtime_state || "";
    main.dataset.abuMotion = this.abuFollowing ? "walking" : "resting";
    main.classList.toggle("is-canonical-abu", this.canonicalAbu);
    main.classList.toggle("is-departure-intent", this.departureIntentActive);
    main.classList.toggle("is-moving", this.userMoving || this.abuFollowing);
    main.classList.toggle("is-user-moving", this.userMoving);
    main.classList.toggle("is-abu-following", this.abuFollowing);
    main.classList.toggle("is-tree-world-active", this.gameShellOpen);
    main.classList.remove("show-paw-hint");
    if (this.gameShellOpen && main.scrollTop) main.scrollTop = 0;
    const grove = main.querySelector<HTMLElement>(".dream-grove");
    const legacyA11y = main.querySelector<HTMLElement>(".dream-a11y-actions");
    if (grove) {
      grove.toggleAttribute("inert", this.gameShellOpen);
      grove.setAttribute("aria-hidden", this.gameShellOpen ? "true" : "false");
    }
    if (legacyA11y) {
      legacyA11y.toggleAttribute("inert", this.gameShellOpen);
      legacyA11y.setAttribute("aria-hidden", this.gameShellOpen ? "true" : "false");
    }

    const abu = main.querySelector<HTMLImageElement>(".dream-abu");
    if (abu) {
      const abuElsewhere = this.visit?.canonical_abu?.public_action === "elsewhere";
      abu.hidden = Boolean(abuElsewhere);
      main.querySelector<HTMLElement>(".dream-abu-shadow")?.toggleAttribute("hidden", Boolean(abuElsewhere));
      const next = this.gameShellOpen
        ? ABU_REST
        : this.phase === "fog_wait" || this.phase === "fog_crossing"
          ? ABU_WALK
          : this.abuFollowing
            ? ABU_WALK
            : this.phase === "free_roam" || this.phase === "mirror_ready"
              ? ABU_REST
              : ABU_WAIT;
      if (!abu.src.endsWith(next)) abu.src = next;
    }
    for (const tree of this.trees) {
      const element = main.querySelector<HTMLElement>(`[data-dream-tree="${cssEscape(tree.scene_ref)}"]`);
      element?.classList.toggle("is-near", tree.scene_ref === this.nearestResidentRef);
      element?.classList.toggle("is-selected", tree.scene_ref === this.visit?.selected_scene_ref);
    }
    this.resyncSceneClock();
  }

  private resyncSceneClock(): void {
    const elapsed = Math.max(0, Date.now() - this.sceneStartedAt);
    for (const tree of this.trees) {
      const element = this.root.querySelector<HTMLElement>(`[data-dream-tree="${cssEscape(tree.scene_ref)}"]`);
      element?.style.setProperty("--life-delay", `${-((elapsed + tree.autonomous_phase_ms) % 60000)}ms`);
    }
  }

  private async preloadTreeMasks(): Promise<void> {
    const entries = this.trees.map(async (tree) => {
      const image = this.root.querySelector<HTMLImageElement>(`[data-dream-tree-image="${cssEscape(tree.scene_ref)}"]`);
      if (!image) return;
      try {
        await image.decode();
      } catch {
        await new Promise<void>((resolve) => image.addEventListener("load", () => resolve(), { once: true }));
      }
      const canvas = document.createElement("canvas");
      canvas.width = image.naturalWidth;
      canvas.height = image.naturalHeight;
      const context = canvas.getContext("2d", { willReadFrequently: true });
      if (!context) return;
      context.drawImage(image, 0, 0);
      this.masks.set(tree.scene_ref, { image, canvas, context });
    });
    await Promise.all(entries);
  }

  private hitTreeAt(clientX: number, clientY: number): TreePlacement | null {
    const ordered = [...this.trees].sort((left, right) => right.depth - left.depth);
    for (const tree of ordered) {
      const mask = this.masks.get(tree.scene_ref);
      if (!mask) continue;
      const rect = mask.image.getBoundingClientRect();
      if (clientX < rect.left || clientX > rect.right || clientY < rect.top || clientY > rect.bottom) continue;
      const x = Math.floor(((clientX - rect.left) / rect.width) * mask.canvas.width);
      const y = Math.floor(((clientY - rect.top) / rect.height) * mask.canvas.height);
      const alpha = mask.context.getImageData(
        clamp(x, 0, mask.canvas.width - 1),
        clamp(y, 0, mask.canvas.height - 1),
        1,
        1,
      ).data[3];
      if (alpha > 28) return tree;
    }
    return null;
  }

  private isWithinTouchDistance(tree: TreePlacement): boolean {
    return pointDistance(this.user, this.treeWorldPoint(tree)) <= TREE_TOUCH_DISTANCE;
  }

  private treeWorldPoint(tree: TreePlacement): WorldPoint {
    const scene = this.root.querySelector<HTMLElement>(".dream-grove");
    const image = this.root.querySelector<HTMLImageElement>(
      `[data-dream-tree-image="${cssEscape(tree.scene_ref)}"]`,
    );
    if (!scene || !image) return { x: tree.x, y: tree.y + 24 };
    const sceneRect = scene.getBoundingClientRect();
    const imageRect = image.getBoundingClientRect();
    return {
      x: clamp(
        (((imageRect.left + (imageRect.width * 0.5)) - sceneRect.left) / sceneRect.width) * 100,
        7,
        93,
      ),
      y: clamp(
        (((imageRect.top + (imageRect.height * 0.86)) - sceneRect.top) / sceneRect.height) * 100,
        24,
        91,
      ),
    };
  }

  private treeApproachPoint(tree: TreePlacement): WorldPoint {
    const root = this.treeWorldPoint(tree);
    return {
      x: clamp(root.x - 6, 7, 93),
      y: clamp(root.y + 4, 24, 91),
    };
  }

  private focusMirrorTarget(): void {
    if (!this.mirror?.verification.target_object_ref) return;
    const container = this.root.querySelector<HTMLElement>(".dream-verification-geometry");
    const target = this.root.querySelector<SVGGraphicsElement>(
      `[data-canvas-object="${cssEscape(this.mirror.verification.target_object_ref)}"]`,
    );
    if (!container || !target) return;
    const containerRect = container.getBoundingClientRect();
    const targetRect = target.getBoundingClientRect();
    container.scrollLeft += (
      targetRect.left + (targetRect.width / 2)
      - containerRect.left - (containerRect.width / 2)
    );
  }

  private worldPointFromClient(clientX: number, clientY: number): WorldPoint {
    const scene = this.root.querySelector<HTMLElement>(".dream-grove");
    if (!scene) return { ...this.user };
    const rect = scene.getBoundingClientRect();
    return {
      x: clamp(((clientX - rect.left) / rect.width) * 100, 7, 97),
      y: clamp(((clientY - rect.top) / rect.height) * 100, 24, 91),
    };
  }

  private treeByRef(sceneRef: string): TreePlacement | null {
    return this.trees.find((tree) => tree.scene_ref === sceneRef) || null;
  }

  private playAmbient(): void {
    if (!this.ambient) return;
    this.ambient.volume = 0.12;
    void this.ambient.play().catch(() => undefined);
  }

  private playRevealTone(hasFact: boolean): void {
    if (!hasFact) return;
    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      const context = new AudioContextClass();
      const oscillator = context.createOscillator();
      const gain = context.createGain();
      oscillator.type = "sine";
      oscillator.frequency.setValueAtTime(196, context.currentTime);
      oscillator.frequency.exponentialRampToValueAtTime(247, context.currentTime + 0.45);
      gain.gain.setValueAtTime(0.0001, context.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.055, context.currentTime + 0.08);
      gain.gain.exponentialRampToValueAtTime(0.0001, context.currentTime + 0.7);
      oscillator.connect(gain).connect(context.destination);
      oscillator.start();
      oscillator.stop(context.currentTime + 0.75);
    } catch {
      // The visual response is complete without audio.
    }
  }

  private handleAuthorizationOrError(error: unknown): void {
    const detail = this.errorCode(error);
    if (detail.includes("control_lease") || detail.includes("world_projection")) {
      this.handleRuntimeFailure(error);
      return;
    }
    if (
      detail.includes("authorization")
      || detail.includes("source_version_changed")
      || detail.includes("reference_invalid")
    ) {
      this.phase = "authorization_closed";
      this.syncSceneDom();
      this.announce("这棵树当前不能继续披露内容。");
      if (this.mirror || this.visit?.state === "MIRROR_OPEN") void this.closeMirror("revoked");
      return;
    }
    this.renderError(error);
  }

  private handleRuntimeFailure(error: unknown): void {
    const code = this.errorCode(error);
    if (
      code === "dream_control_lease_superseded"
      || code === "dream_control_lease_stale"
      || code === "dream_control_lease_expired"
      || code === "dream_control_lease_required"
    ) {
      this.stopControlLoops();
      this.clearSensitiveProjection();
      this.gameAttempt = null;
      this.gameResult = null;
      sessionStorage.removeItem(PENDING_GAME_ACTION_KEY);
      clearDreamControl();
      this.phase = "visit_suspended";
      this.syncSceneDom();
      this.setRuntimeVeil("梦境已在另一处继续。", false);
      this.announce("这个页面已经失去梦境控制权，私人内容已收起。");
      return;
    }
    if (
      code.includes("authorization")
      || code.includes("source_version_changed")
      || code.includes("world_projection_invalid")
    ) {
      this.clearSensitiveProjection();
      this.gameAttempt = null;
      this.gameResult = null;
      sessionStorage.removeItem(PENDING_GAME_ACTION_KEY);
      this.phase = "authorization_closed";
      this.syncSceneDom();
      this.setRuntimeVeil("当前授权已变化，内容已经收起。", true);
      return;
    }
    this.stopControlLoops();
    this.clearSensitiveProjection();
    this.gameAttempt = null;
    this.gameResult = null;
    this.phase = "fail_closed";
    this.syncSceneDom();
    this.setRuntimeVeil("暂时无法确认梦境状态。连接恢复后再继续。", true);
  }

  private clearSensitiveProjection(): void {
    this.stopMirrorPolling();
    this.stopGamePolling();
    this.mirror = null;
    this.reveal = null;
    const layer = this.root.querySelector<HTMLElement>(".dream-mirror-layer");
    if (layer) {
      layer.classList.add("is-masked");
      layer.innerHTML = "";
      layer.setAttribute("aria-hidden", "true");
    }
    const gameLayer = this.root.querySelector<HTMLElement>(".dream-game-layer");
    if (gameLayer) {
      gameLayer.innerHTML = "";
      gameLayer.setAttribute("aria-hidden", "true");
    }
  }

  private setRuntimeVeil(message: string, recoverable: boolean): void {
    const veil = this.root.querySelector<HTMLElement>(".dream-runtime-veil");
    if (!veil) return;
    veil.setAttribute("aria-hidden", "false");
    veil.innerHTML = `<span role="status">${escapeHtml(message)}</span>${recoverable
      ? `<button type="button" data-dream-retry>重新确认</button>`
      : ""}`;
    veil.querySelector<HTMLElement>("[data-dream-retry]")?.addEventListener("click", () => {
      location.reload();
    });
  }

  private errorCode(error: unknown): string {
    return error instanceof DreamApiError
      ? error.code
      : error instanceof Error
        ? error.message
        : String(error);
  }

  private announce(message: string): void {
    const announcer = this.root.querySelector<HTMLElement>("[data-dream-announcer]");
    if (announcer) announcer.textContent = message;
  }

  private renderError(error: unknown): void {
    this.stopMovementLoop();
    this.stopMirrorPolling();
    this.stopControlLoops();
    const detail = error instanceof Error ? error.message : String(error);
    const unavailable = detail.includes("DREAM_ENCOUNTER_UNAVAILABLE") || detail.includes("dream_feature_disabled");
    this.root.innerHTML = `<main class="dream-state dream-error">
      <img src="${ABU_WAIT}" alt="阿布">
      <h1>${escapeHtml(dreamText(unavailable ? "dream.unavailable.title" : "dream.error.title"))}</h1>
      <span>${escapeHtml(unavailable ? dreamText("dream.unavailable.detail") : detail)}</span>
      <a class="dream-command" href="/experience">${escapeHtml(dreamText("dream.workspace.back"))}</a>
    </main>`;
  }
}


function placeTrees(trees: DreamTreeCard[]): TreePlacement[] {
  const human = trees.find((tree) => tree.source_kind === "authorized_human");
  const residents = trees
    .filter((tree) => tree.source_kind === "canonical_npc")
    .sort((left, right) => left.resident_label.localeCompare(right.resident_label, "zh-CN"));
  const placements = [
    human ? { tree: human, x: 3, y: 58, scale: 1.48, depth: 3, own: true } : null,
    residents[0] ? { tree: residents[0], x: 56, y: 48, scale: 0.88, depth: 2, own: false } : null,
    residents[1] ? { tree: residents[1], x: 81, y: 27, scale: 0.78, depth: 1, own: false } : null,
  ].filter((item): item is NonNullable<typeof item> => Boolean(item));
  return placements.map((item) => ({ ...item.tree, ...item }));
}


function pointDistance(left: WorldPoint, right: WorldPoint): number {
  return Math.hypot(left.x - right.x, (left.y - right.y) * 0.82);
}


function readSceneAnchor(visitId: string): number {
  const key = `deepbazi:dream:first-visit:clock:${visitId}`;
  const stored = Number(sessionStorage.getItem(key));
  if (Number.isFinite(stored) && stored > 0) return stored;
  const value = Date.now();
  sessionStorage.setItem(key, String(value));
  return value;
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


function clamp(value: number, minimum: number, maximum: number): number {
  return Math.min(maximum, Math.max(minimum, value));
}


function delay(milliseconds: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}


function actionId(prefix: string): string {
  const value = globalThis.crypto?.randomUUID?.()
    || `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
  return `${prefix}-${value}`;
}

function flowerLifecycleKey(attempt: DreamGameAttemptView): string {
  const flower = attempt.flower;
  if (!flower) return "";
  return [
    flower.state,
    flower.answer_count_visible ? flower.answer_count ?? 0 : "private",
    flower.own_answer_sealed,
    flower.shared_fruit_visible,
    flower.revealable,
    flower.close_reason || "",
  ].join("|");
}


function formatDreamDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    timeZone: "UTC",
  }).format(date);
}


function cssEscape(value: string): string {
  return CSS.escape(value);
}


function escapeHtml(value: string): string {
  return value.replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  }[character] || character));
}


function escapeAttr(value: string): string {
  return escapeHtml(value);
}


declare global {
  interface Window {
    webkitAudioContext: typeof AudioContext;
  }
}
