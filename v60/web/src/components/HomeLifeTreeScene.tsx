import { useEffect, useRef, useState, type CSSProperties } from "react";

import type { RuntimeMediaManifest } from "../api";
import { activateOwnerCase } from "../homeApi";
import type { HomeSnapshot } from "../homeApi";
import {
  rememberHomeWorldLight,
  resolveHomeWorldLight,
  type HomeWorldLight,
} from "../homeWorldLight";
import { HomeWorldHeader } from "./HomeWorldHeader";
import { HomeWorldHotspots } from "./HomeWorldHotspots";
import { HomeWorldSettings } from "./HomeWorldSettings";
import { TransparentCharacterMedia } from "./TransparentCharacterMedia";

type HomePassage = "mingli" | "lab" | "dream";

export function HomeLifeTreeScene({
  busy,
  home,
  media,
  onEnterDream,
  onOpenLab,
  onOpenMingli,
}: {
  busy: boolean;
  home: HomeSnapshot;
  media: RuntimeMediaManifest;
  onEnterDream: () => void;
  onOpenLab: () => void;
  onOpenMingli: () => void;
}) {
  const [light, setLight] = useState<HomeWorldLight>(resolveHomeWorldLight);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [busyCaseRef, setBusyCaseRef] = useState<string | null>(null);
  const [caseError, setCaseError] = useState<string | null>(null);
  const [passage, setPassage] = useState<HomePassage | null>(null);
  const timers = useRef<number[]>([]);
  const phenotype = home.tree.phenotype;
  const guideCue = light === "day" ? media.cues.dodo_idle : media.cues.abu_idle;
  const style = {
    "--v108-home-moisture": phenotype.surface_moisture,
    "--v108-home-bark": phenotype.bark_definition,
    "--v108-home-lift": phenotype.branch_lift,
  } as CSSProperties;

  useEffect(
    () => () => timers.current.forEach((timer) => window.clearTimeout(timer)),
    [],
  );

  const toggleLight = () => {
    const next = light === "day" ? "night" : "day";
    setLight(next);
    rememberHomeWorldLight(next);
  };

  const enterThrough = (next: HomePassage, action: () => void) => {
    if (passage || busy) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    setPassage(next);
    timers.current.push(window.setTimeout(action, reduced ? 0 : 520));
    timers.current.push(window.setTimeout(() => setPassage(null), reduced ? 80 : 1500));
  };

  const activateCase = async (caseRef: string, destination: "home" | "mingli") => {
    setBusyCaseRef(caseRef);
    setCaseError(null);
    try {
      await activateOwnerCase(caseRef);
      if (destination === "mingli") {
        const url = new URL(window.location.href);
        url.searchParams.set("view", "mingli");
        window.location.assign(url.toString());
        return;
      }
      window.location.reload();
    } catch (error) {
      setCaseError(error instanceof Error ? error.message : String(error));
      setBusyCaseRef(null);
    }
  };

  const openLab = () => {
    setSettingsOpen(false);
    enterThrough("lab", onOpenLab);
  };
  const enterDream = () => {
    setSettingsOpen(false);
    enterThrough("dream", onEnterDream);
  };

  return (
    <div
      className="v108-home-world"
      data-case-ref={home.case.case_ref}
      data-chart-version-ref={home.chart.chart_version_ref}
      data-life-case-ref={home.life_case.life_case_revision_ref}
      data-tree-ref={home.tree.tree_ref}
      data-world-light={light}
      style={style}
    >
      <HomeWorldHeader
        busyCaseRef={busyCaseRef}
        home={home}
        light={light}
        media={media}
        onActivateCase={(caseRef) => void activateCase(caseRef, "home")}
        onOpenSettings={() => setSettingsOpen(true)}
        onToggleLight={toggleLight}
      />

      <div className="v108-home-viewport">
        <div className="v108-home-plane">
          <img
            alt=""
            className="v108-home-art v108-home-art-day"
            data-asset-ref={media.assets.home_day_background.asset_ref}
            src={media.assets.home_day_background.url}
          />
          <img
            alt=""
            className="v108-home-art v108-home-art-night"
            data-asset-ref={media.assets.home_night_background.asset_ref}
            src={media.assets.home_night_background.url}
          />
          <div className="v108-home-scene-wash" aria-hidden="true" />
          <div className="v108-life-current" aria-hidden="true"><i /><b /><span /></div>
          <HomeWorldHotspots
            busy={busy || passage !== null}
            busyCaseRef={busyCaseRef}
            home={home}
            media={media}
            onActivateCase={(caseRef) => void activateCase(caseRef, "mingli")}
            onEnterDream={enterDream}
            onOpenLab={openLab}
            onOpenMingli={() => enterThrough("mingli", onOpenMingli)}
            onOpenSettings={() => setSettingsOpen(true)}
          />
        </div>
      </div>

      <button
        className="v108-profile-identity"
        onClick={() => setSettingsOpen(true)}
        type="button"
      >
        <i aria-hidden="true">{home.profile.display_name.slice(0, 1)}</i>
        <span>
          <small>当前档案</small>
          <strong>{home.profile.display_name} · 生命树</strong>
        </span>
      </button>

      <div className="v108-home-context">
        <h1>跟着光，看见自己的生命树。</h1>
        <span><i aria-hidden="true" />档案叶、Lab 花与梦境树洞都在原位</span>
      </div>

      <TransparentCharacterMedia
        active
        alt={`${light === "day" ? "多多" : "阿布"}在生命树旁陪伴`}
        className="v108-home-guide"
        cueRef={guideCue.cue_ref}
        key={guideCue.cue_ref}
        poster={guideCue.deliveries.REDUCED_MOTION_POSTER}
        video={guideCue.deliveries.VP9_ALPHA_WEBM}
        webp={guideCue.deliveries.ANIMATED_WEBP}
      />

      {caseError && <p className="v108-home-error" role="alert">档案没有切换成功：{caseError}</p>}
      {settingsOpen && (
        <HomeWorldSettings
          home={home}
          onClose={() => setSettingsOpen(false)}
          onEnterDream={enterDream}
          onOpenLab={openLab}
        />
      )}
      {passage && (
        <div className={`v108-world-passage to-${passage}`} aria-live="polite">
          <i aria-hidden="true" /><b aria-hidden="true" />
          <p>
            <small>{passage === "dream" ? "阿布梦境 · 账号旅程" : passage === "lab" ? "命理 Lab" : "命理测算"}</small>
            <strong>{passage === "dream" ? "穿过树洞，进入阿布梦境" : "沿着生命光，进入命理枝"}</strong>
          </p>
        </div>
      )}
    </div>
  );
}
