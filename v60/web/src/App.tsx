import { useCallback, useEffect, useMemo, useState } from "react";

import { HomeLifeTreeScene } from "./components/HomeLifeTreeScene";
import { LoginScene } from "./components/LoginScene";
import { MingliBranchSceneHost } from "./components/MingliBranchSceneHost";
import { MingliSceneHost } from "./components/MingliSceneHost";
import { RuntimeBoundaryScene } from "./components/RuntimeBoundaryScene";
import {
  readMingliStageExperience,
  writeMingliStageExperience,
} from "./mingliStageNavigation";
import { enforcePublicExperienceLocation } from "./productExposure";
import {
  loadPublicHome,
  type PublicHomeSnapshot,
} from "./publicHomeApi";
import type {
  Bootstrap,
  PublicRuntimeMediaManifest,
  Session,
} from "./publicRuntimeTypes";
import { loadBootstrap, loadSession, login, logout } from "./runtimeApi";

type PublicView = "HOME" | "BRANCH" | "STAGE";

export function App() {
  const [bootstrap, setBootstrap] = useState<Bootstrap | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [home, setHome] = useState<PublicHomeSnapshot | null>(null);
  const [view, setView] = useState<PublicView>(readPublicView);
  const [booting, setBooting] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshHome = useCallback(async () => {
    const nextHome = await loadPublicHome();
    setHome(nextHome);
  }, []);

  const boot = useCallback(async () => {
    setBooting(true);
    setError(null);
    try {
      enforcePublicExperienceLocation();
      const nextBootstrap = await loadBootstrap();
      setBootstrap(nextBootstrap);
      try {
        const nextSession = await loadSession();
        const nextHome = await loadPublicHome();
        setSession(nextSession);
        setHome(nextHome);
        setView(readPublicView());
      } catch (caught) {
        if (!errorMessage(caught).includes("authentication_required")) throw caught;
        setSession(null);
        setHome(null);
      }
    } catch (caught) {
      setError(friendlyError(caught));
    } finally {
      setBooting(false);
    }
  }, []);

  useEffect(() => {
    void boot();
  }, [boot]);

  useEffect(() => {
    const restore = () => {
      enforcePublicExperienceLocation();
      setView(readPublicView());
    };
    window.addEventListener("popstate", restore);
    return () => window.removeEventListener("popstate", restore);
  }, []);

  const handleLogin = async (email: string, password: string) => {
    setBusy(true);
    setError(null);
    try {
      const nextSession = await login(email, password);
      const nextHome = await loadPublicHome();
      setSession(nextSession);
      setHome(nextHome);
      goHome("replace");
      setView("HOME");
    } catch (caught) {
      setError(
        errorMessage(caught).includes("invalid_credentials")
          ? "邮箱或密码不正确。"
          : friendlyError(caught),
      );
    } finally {
      setBusy(false);
    }
  };

  const handleLogout = async () => {
    setBusy(true);
    try {
      await logout();
    } finally {
      goHome("replace");
      setSession(null);
      setHome(null);
      setView("HOME");
      setBusy(false);
    }
  };

  const homeLineageKey = useMemo(
    () => home
      ? [
          home.case.case_ref,
          home.chart.chart_version_ref,
          home.life_case.life_case_revision_ref,
        ].join("|")
      : "public-home-pending",
    [home],
  );
  const ignoreContext = useCallback(() => undefined, []);

  if (booting && bootstrap === null) {
    return <RuntimeBoundaryScene message="生命树正在醒来" />;
  }
  if (bootstrap === null) {
    return (
      <RuntimeBoundaryScene
        message={error ?? "暂时无法连接到 V60"}
        status="error"
      />
    );
  }
  if (session === null || home === null) {
    return (
      <LoginScene
        busy={busy}
        error={error}
        media={bootstrap.media}
        onLogin={handleLogin}
      />
    );
  }

  const mingliMedia: PublicRuntimeMediaManifest = bootstrap.media;
  return (
    <main
      className="v60-root v60-shell"
      data-experience-scope="home"
      data-scene-id={view === "HOME" ? "private-home-tree" : "mingli-shared-scene"}
      data-scene-version={
        view === "HOME" ? home.tree.projection_version : "mingli-stage"
      }
      data-layout-key="picture_book_private_home"
    >
      <div
        className="experience-layout"
        data-mingli-stage-wide={view !== "HOME"}
      >
        <section className="story-canvas" aria-label="生命树与命理枝">
          {view === "HOME" ? (
            <HomeLifeTreeScene
              busy={busy}
              home={home}
              media={bootstrap.media}
              onHomeRefresh={refreshHome}
              onLogout={() => void handleLogout()}
              onOpenMingli={() => setView("BRANCH")}
            />
          ) : view === "BRANCH" ? (
            <div className="mingli-growth-composition">
              <div aria-hidden="true" className="mingli-growth-home-underlay" inert>
                <HomeLifeTreeScene
                  busy
                  home={home}
                  media={bootstrap.media}
                  onHomeRefresh={refreshHome}
                  onLogout={() => undefined}
                  onOpenMingli={() => undefined}
                />
              </div>
              <MingliBranchSceneHost
                media={mingliMedia}
                onContextChange={ignoreContext}
                onExit={() => {
                  goHome("push");
                  setView("HOME");
                }}
                onOpenStage={() => setView("STAGE")}
                publicMode
              />
            </div>
          ) : (
            <MingliSceneHost
              homeLineageKey={homeLineageKey}
              media={mingliMedia}
              onContextChange={ignoreContext}
              onExit={() => {
                goHome("push");
                setView("HOME");
              }}
              onReturnToBranch={() => {
                writeMingliStageExperience("branch", "observe", "replace");
                setView("BRANCH");
              }}
              onSurfaceChange={() => undefined}
              publicMode
              surface="READING"
            />
          )}
        </section>
      </div>
    </main>
  );
}

const MINGLI_ROUTE_KEYS = [
  "view",
  "mingli_subject",
  "mingli_mode",
  "mingli_year",
  "mingli_layer",
  "mingli_entry",
  "mingli_entry_x",
  "mingli_entry_y",
  "mingli_entry_scene_x",
  "mingli_entry_scene_y",
  "mingli_light",
  "mingli_stage",
  "mingli_rehearsal",
] as const;

function readPublicView(): PublicView {
  const url = new URL(window.location.href);
  if (url.searchParams.get("view") !== "mingli") return "HOME";
  return readMingliStageExperience() === "stage" ? "STAGE" : "BRANCH";
}

function goHome(mode: "push" | "replace") {
  const url = new URL(window.location.href);
  MINGLI_ROUTE_KEYS.forEach((key) => url.searchParams.delete(key));
  window.history[mode === "push" ? "pushState" : "replaceState"](
    null,
    "",
    url,
  );
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function friendlyError(error: unknown): string {
  const reason = errorMessage(error);
  if (reason.includes("Failed to fetch") || reason.includes("request_failed:5")) {
    return "服务暂时没有响应，请稍后重试。";
  }
  if (reason.includes("home_case_not_found")) {
    return "还没有可读取的命盘，请先建立八字档案。";
  }
  return "这一步暂时没有完成，请稍后重试。";
}
