import { useState } from "react";

import type { HomeWorldLight } from "../homeWorldLight";
import type { PublicLifeTreeHomeSnapshot } from "../publicHomeApi";
import type { PublicRuntimeMediaManifest } from "../publicRuntimeTypes";

const PILLAR_ORDER = ["year", "month", "day", "hour"] as const;

export function HomeWorldHeader({
  busyCaseRef,
  home,
  light,
  media,
  onOpenCase,
  onLogout,
  onOpenSettings,
  onToggleLight,
}: {
  busyCaseRef: string | null;
  home: PublicLifeTreeHomeSnapshot;
  light: HomeWorldLight;
  media: PublicRuntimeMediaManifest;
  onOpenCase: (option: PublicLifeTreeHomeSnapshot["case_options"][number], anchor: HTMLElement) => void;
  onLogout: () => void;
  onOpenSettings: () => void;
  onToggleLight: () => void;
}) {
  const [profileOpen, setProfileOpen] = useState(false);
  const logo = light === "day" ? media.assets.home_day_logo : media.assets.home_night_logo;

  return (
    <header className="v108-home-header">
      <div className="v108-home-brand" aria-label="AbuKnows 阿布知命">
        <span>
          <img data-asset-ref={logo.asset_ref} src={logo.url} alt="" />
        </span>
        <span>
          <strong>AbuKnows</strong>
          <small>阿布知命</small>
        </span>
      </div>

      <nav className="v108-home-controls" aria-label="生命世界控制">
        <div className="v108-profile-control">
          <button
            aria-expanded={profileOpen}
            className="v108-profile-chip"
            onClick={() => setProfileOpen((current) => !current)}
            type="button"
          >
            <i aria-hidden="true">{home.profile.display_name.slice(0, 1)}</i>
            <span>
              <small>当前档案</small>
              <strong>{home.profile.display_name}</strong>
            </span>
            <b aria-hidden="true">⌄</b>
          </button>
          {profileOpen && (
            <div className="v108-profile-popover">
              <header>
                <span>
                  <small>我的八字档案</small>
                  <strong>选择一片生命叶</strong>
                </span>
                <button
                  aria-label="关闭档案选择"
                  onClick={() => setProfileOpen(false)}
                  type="button"
                >
                  ×
                </button>
              </header>
              <div>
                {home.case_options.map((option) => (
                  <button
                    data-active={option.active}
                    disabled={busyCaseRef !== null}
                    key={option.case_ref}
                    onClick={(event) => {
                      onOpenCase(option, event.currentTarget);
                      setProfileOpen(false);
                    }}
                    type="button"
                  >
                    <i aria-hidden="true">{option.display_name.slice(0, 1)}</i>
                    <span>
                      <strong>{option.display_name}</strong>
                      <small>{PILLAR_ORDER.map((slot) => option.pillars[slot]).join(" · ")}</small>
                    </span>
                    <b>{option.active ? "当前" : busyCaseRef === option.case_ref ? "…" : "测算"}</b>
                  </button>
                ))}
              </div>
              <button
                className="v108-profile-manage"
                onClick={() => {
                  setProfileOpen(false);
                  onOpenSettings();
                }}
                type="button"
              >
                管理八字档案
              </button>
            </div>
          )}
        </div>
        <button
          className="v108-round-control"
          onClick={onToggleLight}
          title={light === "day" ? "切换到月夜" : "切换到白昼"}
          type="button"
        >
          <span aria-hidden="true">{light === "day" ? "☾" : "☀"}</span>
        </button>
        <button className="v108-round-control" disabled title="环境声音将在声音正本接入后开放" type="button">
          <span aria-hidden="true">♪</span>
        </button>
        <button className="v108-locale-control" disabled title="本轮以中文为正式体验" type="button">
          中
        </button>
        <button
          aria-label="退出账号"
          className="v108-round-control"
          onClick={onLogout}
          title="退出账号"
          type="button"
        >
          <span aria-hidden="true">退</span>
        </button>
      </nav>
    </header>
  );
}
