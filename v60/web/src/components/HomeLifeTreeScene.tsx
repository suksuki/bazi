import { useEffect, useRef, useState, type CSSProperties } from "react";

import type { RuntimeMediaManifest } from "../api";
import type { HomeSnapshot } from "../homeApi";
import { writeMingliLeafRoute } from "../mingliStageNavigation";
import {
  rememberHomeWorldLight,
  resolveHomeWorldLight,
  type HomeWorldLight,
} from "../homeWorldLight";
import { HomeWorldHeader } from "./HomeWorldHeader";
import { HomeWorldHotspots } from "./HomeWorldHotspots";
import { HomeProfileManager } from "./HomeProfileManager";
import { TransparentCharacterMedia } from "./TransparentCharacterMedia";

type HomePassage = "lab" | "dream";

export function HomeLifeTreeScene({
  busy,
  home,
  media,
  onEnterDream,
  onHomeRefresh,
  onOpenLab,
  onOpenMingli,
}: {
  busy: boolean;
  home: HomeSnapshot;
  media: RuntimeMediaManifest;
  onEnterDream: () => void;
  onHomeRefresh: () => Promise<void>;
  onOpenLab: () => void;
  onOpenMingli: () => void;
}) {
  const [light, setLight] = useState<HomeWorldLight>(resolveHomeWorldLight);
  const [profileManagerOpen, setProfileManagerOpen] = useState(false);
  const [passage, setPassage] = useState<HomePassage | null>(null);
  const timers = useRef<number[]>([]);
  const worldRef = useRef<HTMLDivElement>(null);
  const planeRef = useRef<HTMLDivElement>(null);
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

  const openMingliCase = (
    option: HomeSnapshot["case_options"][number],
    anchor: HTMLElement,
  ) => {
    if (passage || busy) return;
    const stableAnchor = anchor.closest(".profile-manager")
      ? worldRef.current?.querySelector<HTMLElement>(".v108-profile-more")
        ?? worldRef.current?.querySelector<HTMLElement>(".v108-settings-fruit")
        ?? anchor
      : anchor.closest(".v108-profile-popover")
        ? worldRef.current?.querySelector<HTMLElement>(".v108-profile-chip") ?? anchor
        : anchor;
    const rect = stableAnchor.getBoundingClientRect();
    const planeRect = planeRef.current?.getBoundingClientRect() ?? {
      left: 0,
      top: 0,
      width: window.innerWidth,
      height: window.innerHeight,
    };
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    writeMingliLeafRoute(option.stage_subject_id, {
      light,
      viewportX: centerX / window.innerWidth * 100,
      viewportY: centerY / window.innerHeight * 100,
      sceneX: (centerX - planeRect.left) / planeRect.width * 100,
      sceneY: (centerY - planeRect.top) / planeRect.height * 100,
    });
    setProfileManagerOpen(false);
    onOpenMingli();
  };

  const openLab = () => {
    setProfileManagerOpen(false);
    enterThrough("lab", onOpenLab);
  };
  const enterDream = () => {
    setProfileManagerOpen(false);
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
      ref={worldRef}
      style={style}
    >
      <HomeWorldHeader
        busyCaseRef={null}
        home={home}
        light={light}
        media={media}
        onOpenCase={openMingliCase}
        onOpenSettings={() => setProfileManagerOpen(true)}
        onToggleLight={toggleLight}
      />

      <div className="v108-home-viewport">
        <div className="v108-home-plane" ref={planeRef}>
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
            busyCaseRef={null}
            home={home}
            media={media}
            onEnterDream={enterDream}
            onOpenLab={openLab}
            onOpenMingli={openMingliCase}
            onOpenSettings={() => setProfileManagerOpen(true)}
          />
        </div>
      </div>

      <button
        className="v108-profile-identity"
        onClick={() => setProfileManagerOpen(true)}
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

      {profileManagerOpen && (
        <HomeProfileManager
          home={home}
          light={light}
          onChanged={onHomeRefresh}
          onClose={() => setProfileManagerOpen(false)}
          onOpenMingli={openMingliCase}
        />
      )}
      {passage && (
        <div className={`v108-world-passage to-${passage}`} aria-live="polite">
          <i aria-hidden="true" /><b aria-hidden="true" />
          <p>
            <small>{passage === "dream" ? "阿布梦境 · 账号旅程" : passage === "lab" ? "命理 Lab" : "命理测算"}</small>
            <strong>{passage === "dream" ? "穿过树洞，进入阿布梦境" : "循着水光，进入阿布 LAB"}</strong>
          </p>
        </div>
      )}
    </div>
  );
}
