import { useEffect, useMemo, useState } from "react";

import {
  type DreamSnapshot,
  executeDreamCommand,
  loadBootstrap,
  loadDreamEntry,
  loadEncounter,
  loadSession,
  login,
  logout,
  returnToDreamGrove,
  selectDreamTree,
} from "./api";
import {
  dreamEntryState,
  failedRuntimeAction,
  initialRuntimeState,
  loggedOutState,
  type RuntimeState,
} from "./appRuntime";
import { CompanionRail } from "./components/CompanionRail";
import { ExperienceHeader } from "./components/ExperienceHeader";
import { ExperienceRuntimeOverlay } from "./components/ExperienceRuntimeOverlay";
import { createDreamNextAttentionHandler } from "./dreamNextAttentionAction";
import { startDreamPersonalJourney } from "./dreamPersonalJourneyApi";
import type { DreamLifeDomain } from "./dreamPersonalJourneyTypes";
import { ExperienceStoryCanvas } from "./components/ExperienceStoryCanvas";
import { HomeSceneCompanion } from "./components/HomeSceneCompanion";
import { LoginScene } from "./components/LoginScene";
import { RuntimeBoundaryScene } from "./components/RuntimeBoundaryScene";
import { commandForOrgan } from "./dreamCommands";
import {
  type ExperienceScope,
  readFocusRef,
  readScope,
  readUnit,
  writeNavigation,
} from "./experienceNavigation";
import type { ExperienceUnit } from "./experienceUnits";
import { compareHomeMechanisms, loadHomeExperience } from "./homeApi";
import { initialMingliStageContext } from "./mingliStageContext";
import type { MingliStageViewContext } from "./mingliStageTypes";
import {
  deriveSemanticFocus,
  findOrganForSources,
  type OrganRole,
} from "./semanticFocus";
export function App() {
  const [runtime, setRuntime] = useState<RuntimeState>(initialRuntimeState);
  const [scope, setScope] = useState<ExperienceScope>(readScope);
  const [activeUnit, setActiveUnit] = useState<ExperienceUnit>(readUnit);
  const [focusRef, setFocusRef] = useState<string | null>(readFocusRef);
  const [mingliContext, setMingliContext] = useState<MingliStageViewContext>(initialMingliStageContext);

  useEffect(() => {
    let active = true;
    void loadBootstrap()
      .then(async (bootstrap) => {
        try {
          const session = await loadSession();
          const home = await loadHomeExperience();
          const entry =
            readScope() === "dream" ? await loadDreamEntry() : null;
          if (active) {
            setRuntime({
              bootstrap,
              session,
              home,
              grove: entry?.kind === "GROVE" ? entry.grove : null,
              snapshot: entry?.kind === "ENCOUNTER" ? entry.snapshot : null,
              loading: false,
              busy: false,
              error: null,
            });
          }
        } catch {
          if (active) {
            setRuntime({
              bootstrap,
              session: null,
              home: null,
              grove: null,
              snapshot: null,
              loading: false,
              busy: false,
              error: null,
            });
          }
        }
      })
      .catch((error: unknown) => {
        if (active) {
          setRuntime((current) => ({
            ...current,
            loading: false,
            error: error instanceof Error ? error.message : String(error),
          }));
        }
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const restoreNavigation = () => {
      const restoredScope = readScope();
      setScope(restoredScope);
      setActiveUnit(readUnit());
      setFocusRef(readFocusRef());
      if (restoredScope === "home") {
        void loadHomeExperience().then((home) =>
          setRuntime((current) => ({ ...current, home })),
        );
      } else {
        void loadDreamEntry().then((entry) =>
          setRuntime((current) => ({ ...current, ...dreamEntryState(entry) })),
        );
      }
    };
    window.addEventListener("popstate", restoreNavigation);
    return () => window.removeEventListener("popstate", restoreNavigation);
  }, []);

  useEffect(() => {
    if (
      scope === "dream" &&
      runtime.snapshot &&
      focusRef &&
      !runtime.snapshot.tree.organs.some(
        (organ) => organ.visible && organ.organ_ref === focusRef,
      )
    ) {
      setFocusRef(null);
      writeNavigation(scope, activeUnit, null, "replace");
    }
  }, [
    activeUnit,
    focusRef,
    scope,
    runtime.snapshot?.encounter.encounter_ref,
    runtime.snapshot?.tree.projection_version,
  ]);

  useEffect(() => {
    const encounter = runtime.snapshot?.encounter;
    const question = runtime.snapshot?.question;
    const watchingOpenQuestion =
      encounter?.status === "QUESTION_OPEN" &&
      question?.answer_window_status === "OPEN";
    if (
      !runtime.session ||
      scope !== "dream" ||
      !encounter ||
      (encounter.status !== "WAITING_FOR_WORLD" &&
        !watchingOpenQuestion)
    ) {
      return;
    }

    let active = true;
    const refreshFromWorld = async () => {
      try {
        const snapshot = await loadEncounter();
        if (active) {
          setRuntime((current) => ({
            ...current,
            snapshot,
          }));
        }
      } catch {
        // A transient read failure does not replace the last committed snapshot.
      }
    };
    const timer = window.setInterval(() => {
      void refreshFromWorld();
    }, 2000);
    void refreshFromWorld();
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [
    runtime.session?.account.account_ref,
    scope,
    runtime.snapshot?.encounter.encounter_ref,
    runtime.snapshot?.encounter.status,
    runtime.snapshot?.question?.answer_window_status,
  ]);

  const runAction = async (action: () => Promise<DreamSnapshot>) => {
    setRuntime((current) => ({ ...current, busy: true, error: null }));
    try {
      const snapshot = await action();
      setRuntime((current) => ({ ...current, snapshot, busy: false }));
    } catch (error) {
      setRuntime((current) => failedRuntimeAction(current, error));
    }
  };

  const semanticFocus = useMemo(
    () =>
      scope === "dream" && runtime.snapshot
        ? deriveSemanticFocus(runtime.snapshot, focusRef)
        : null,
    [focusRef, runtime.snapshot, scope],
  );

  const focusFromSources = (
    sourceRefs: readonly string[],
    preferredRoles: readonly OrganRole[],
  ) => {
    if (!runtime.snapshot) return;
    const organ = findOrganForSources(
      runtime.snapshot,
      sourceRefs,
      preferredRoles,
    );
    if (!organ) return;
    setFocusRef(organ.organ_ref);
    writeNavigation("dream", activeUnit, organ.organ_ref, "replace");
  };

  const handleLogin = async (email: string, password: string) => {
    setRuntime((current) => ({ ...current, busy: true, error: null }));
    try {
      const session = await login(email, password);
      const home = await loadHomeExperience();
      setRuntime((current) => ({
        ...current,
        session,
        home,
        grove: null,
        snapshot: null,
        busy: false,
      }));
      setScope("home");
      setActiveUnit("dream");
      setFocusRef(null);
      writeNavigation("home", "dream", null, "replace");
    } catch (error) {
      setRuntime((current) => failedRuntimeAction(current, error));
    }
  };

  const enterDream = async () => {
    setRuntime((current) => ({ ...current, busy: true, error: null }));
    try {
      const entry = await loadDreamEntry();
      setRuntime((current) => ({
        ...current,
        ...dreamEntryState(entry),
        busy: false,
      }));
      setScope("dream");
      setActiveUnit("dream");
      setFocusRef(null);
      writeNavigation("dream", "dream", null, "push");
    } catch (error) {
      setRuntime((current) => failedRuntimeAction(current, error));
    }
  };

  const selectGroveTree = async (
    candidateRef: string,
    personal?: { domain: DreamLifeDomain; question: string },
  ) => {
    setRuntime((current) => ({ ...current, busy: true, error: null }));
    try {
      const snapshot = personal
        ? await startDreamPersonalJourney(
            candidateRef,
            personal.domain,
            personal.question,
          )
        : await selectDreamTree(candidateRef);
      setRuntime((current) => ({
        ...current,
        grove: null,
        snapshot,
        busy: false,
      }));
    } catch (error) {
      setRuntime((current) => failedRuntimeAction(current, error));
    }
  };

  const returnHome = async () => {
    setRuntime((current) => ({ ...current, busy: true, error: null }));
    try {
      const home = await loadHomeExperience();
      setRuntime((current) => ({
        ...current,
        home,
        grove: null,
        busy: false,
      }));
      setScope("home");
      setActiveUnit("dream");
      setFocusRef(null);
      writeNavigation("home", "dream", null, "push");
    } catch (error) {
      setRuntime((current) => failedRuntimeAction(current, error));
    }
  };

  const returnToGrove = async () => {
    if (!runtime.snapshot) return;
    setRuntime((current) => ({ ...current, busy: true, error: null }));
    try {
      const entry = await returnToDreamGrove(runtime.snapshot);
      setRuntime((current) => ({
        ...current,
        ...dreamEntryState(entry),
        busy: false,
      }));
      setFocusRef(null);
      writeNavigation("dream", "dream", null, "replace");
    } catch (error) {
      setRuntime((current) => failedRuntimeAction(current, error));
    }
  };

  const compareMechanisms = async () => {
    setRuntime((current) => ({ ...current, busy: true, error: null }));
    try {
      await compareHomeMechanisms();
      const home = await loadHomeExperience();
      setRuntime((current) => ({ ...current, home, busy: false }));
    } catch (error) {
      setRuntime((current) => failedRuntimeAction(current, error));
    }
  };

  const refreshHome = async () => {
    const home = await loadHomeExperience();
    setRuntime((current) => ({ ...current, home }));
  };
  const selectUnit = (unit: ExperienceUnit, mode?: "push" | "replace") => {
    setActiveUnit(unit);
    const currentView = new URL(window.location.href).searchParams.get("view");
    writeNavigation(scope, unit, scope === "dream" ? focusRef : null, mode ?? (currentView === unit ? "replace" : "push"));
  };

  const handleLogout = () => {
    void logout().then(() => setRuntime(loggedOutState));
    setScope("home");
    setFocusRef(null);
    setActiveUnit("dream");
    writeNavigation("home", "dream", null, "replace");
  };

  if (runtime.loading) {
    return <RuntimeBoundaryScene message="雾正在辨认这次来访" />;
  }

  if (!runtime.bootstrap) {
    return (
      <RuntimeBoundaryScene
        message={`梦境素材注册表未能加载：${
          runtime.error ?? "DREAM_MEDIA_UNAVAILABLE"
        }`}
        status="error"
      />
    );
  }

  if (!runtime.session || !runtime.home) {
    return (
      <LoginScene
        media={runtime.bootstrap.media}
        busy={runtime.busy}
        error={runtime.error}
        onLogin={handleLogin}
      />
    );
  }

  if (scope === "dream" && !runtime.snapshot && !runtime.grove) {
    return (
      <RuntimeBoundaryScene
        brand={runtime.bootstrap.media.assets.brand_logo}
        message="正在回到持续运行的梦境"
      />
    );
  }

  const home = runtime.home;
  const snapshot = runtime.snapshot;
  const media = runtime.bootstrap.media;
  const mingliSceneActive =
    scope === "home" && (activeUnit === "mingli" || activeUnit === "lab");
  return (
    <main
      className="dream-root v60-shell"
      data-experience-scope={scope}
      data-scene-id={
        scope === "home"
          ? mingliSceneActive
            ? "mingli-shared-scene"
            : "private-home-tree"
          : snapshot?.game.scene_id
      }
      data-scene-version={
        mingliSceneActive
          ? (mingliContext.projection?.projection_version ?? "mingli-stage-pending")
          : scope === "home"
            ? home.tree.projection_version
            : snapshot?.game.scene_version
      }
      data-layout-key={
        scope === "home" ? "picture_book_private_home" : snapshot?.game.layout_key
      }
    >
      <ExperienceHeader
        accountName={runtime.session.account.display_name}
        brand={scope === "dream" ? media.assets.home_night_logo : media.assets.brand_logo}
        home={home}
        mingliContext={mingliSceneActive ? mingliContext : null}
        onLogout={handleLogout}
        onReturnHome={() => void returnHome()}
        scope={scope}
        snapshot={snapshot}
        inGrove={runtime.grove !== null}
      />

      <div
        className="experience-layout"
        data-grove={scope === "dream" && runtime.grove !== null}
        data-mingli-stage-wide={mingliSceneActive}
      >
        <ExperienceStoryCanvas
          activeUnit={activeUnit}
          scope={scope}
          home={home}
          grove={runtime.grove}
          snapshot={snapshot}
          media={media}
          busy={runtime.busy}
          focusedOrganRef={semanticFocus?.organ.organ_ref ?? null}
          onEnterDream={() => void enterDream()}
          onHomeRefresh={refreshHome}
          onMingliContext={setMingliContext}
          onSelectUnit={selectUnit}
          onSelectTree={(candidateRef) => void selectGroveTree(candidateRef)}
          onStartPersonalJourney={(candidateRef, domain, question) => void selectGroveTree(candidateRef, { domain, question })}
          onSelectDreamAttention={createDreamNextAttentionHandler(runtime, setRuntime)}
          onFocus={(organ) => {
            setFocusRef(organ.organ_ref);
            writeNavigation("dream", activeUnit, organ.organ_ref, "replace");
          }}
          onOrgan={(organ) => void runAction(() => executeDreamCommand(
            snapshot!, commandForOrgan(organ), { targetRef: organ.organ_ref },
          ))}
          onAnswer={(choiceId) => void runAction(() =>
            executeDreamCommand(snapshot!, "SEAL_ANSWER", { choiceId }))}
          onReveal={() => void runAction(() => executeDreamCommand(snapshot!, "REVEAL"))}
          onReconcile={() => void runAction(() => executeDreamCommand(snapshot!, "RECONCILE"))}
          onContinue={() =>
            void runAction(() =>
              executeDreamCommand(snapshot!, "CONTINUE_ENCOUNTER"),
            )
          }
          onReturnToGrove={() => void returnToGrove()}
        />

        {scope === "home" ? (
          <HomeSceneCompanion
            activeUnit={activeUnit}
            busy={runtime.busy}
            home={home}
            mingliContext={mingliContext}
            mingliSceneActive={mingliSceneActive}
            onCompareMechanisms={() => void compareMechanisms()}
            onHomeRefresh={refreshHome}
            onEnterDream={() => void enterDream()}
          />
        ) : runtime.grove ? null : (
          snapshot && (
            <CompanionRail
              focus={semanticFocus}
              activeUnit={activeUnit}
              media={media}
              onFocusSources={focusFromSources}
              snapshot={snapshot}
            />
          )
        )}
      </div>

      <ExperienceRuntimeOverlay
        activeUnit={activeUnit}
        error={runtime.error}
        hideDock={mingliSceneActive || scope === "dream"}
        onSelect={selectUnit}
      />
    </main>
  );
}
