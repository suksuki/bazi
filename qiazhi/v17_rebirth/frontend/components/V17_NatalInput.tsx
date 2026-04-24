"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { FolderOpen, Play, Save, Trash2 } from "lucide-react";
import { findCityGroup, findCityOption, getCityCatalogGroups } from "@/types/cityCatalog";

export type V17NatalInputValue = {
  birthTimeISO: string;
  gender: "male" | "female";
  calendarType: "solar" | "lunar";
  profileId?: number | null;
  profileName?: string;
  cityName?: string;
  cityCode?: string;
  cityGroup?: string;
  cityLongitude?: number | null;
};

type BaziProfile = {
  id: number;
  profile_name: string;
  birth_time_iso: string;
  gender: "male" | "female";
  calendar_type: "solar" | "lunar";
  city_name?: string;
  city_code?: string;
  city_group?: string;
  city_longitude?: number | null;
  created_at?: string;
  updated_at?: string;
  last_used_at?: string;
};

const DEFAULT_FORM = {
  year: "1990",
  month: "01",
  day: "01",
  hour: "00",
  minute: "00",
  gender: "male" as const,
  calendarType: "solar" as const,
};

function parseBirthTimeLocal(raw: string | undefined) {
  const source = String(raw || "").trim();
  const match = source.match(
    /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2}))?$/,
  );
  if (!match) return DEFAULT_FORM;
  return {
    year: match[1],
    month: match[2],
    day: match[3],
    hour: match[4],
    minute: match[5],
    gender: DEFAULT_FORM.gender,
    calendarType: DEFAULT_FORM.calendarType,
  };
}

function buildBirthTimeLocal(year: string, month: string, day: string, hour: string, minute: string) {
  const y = year.padStart(4, "0");
  const m = month.padStart(2, "0");
  const d = day.padStart(2, "0");
  const h = hour.padStart(2, "0");
  const mm = minute.padStart(2, "0");
  return `${y}-${m}-${d}T${h}:${mm}:00`;
}

function profileLabel(profile: BaziProfile): string {
  const birth = profile.birth_time_iso.replace("T", " ").slice(0, 16);
  const city = String(profile.city_name || "").trim();
  return city ? `${profile.profile_name} · ${city} · ${birth}` : `${profile.profile_name} · ${birth}`;
}

const cityGroups = getCityCatalogGroups();

export function V17_NatalInput({ onStart }: { onStart: (value: V17NatalInputValue) => void }) {
  const current = new Date();
  const currentYear = current.getFullYear();
  const [year, setYear] = useState(DEFAULT_FORM.year);
  const [month, setMonth] = useState(DEFAULT_FORM.month);
  const [day, setDay] = useState(DEFAULT_FORM.day);
  const [hour, setHour] = useState(DEFAULT_FORM.hour);
  const [minute, setMinute] = useState(DEFAULT_FORM.minute);
  const [gender, setGender] = useState<"male" | "female">(DEFAULT_FORM.gender);
  const [calendarType, setCalendarType] = useState<"solar" | "lunar">(DEFAULT_FORM.calendarType);

  const [profiles, setProfiles] = useState<BaziProfile[]>([]);
  const [profilesLoading, setProfilesLoading] = useState(false);
  const [profileBusy, setProfileBusy] = useState(false);
  const [selectedProfileId, setSelectedProfileId] = useState<number | null>(null);
  const [profileName, setProfileName] = useState("");
  const [cityGroup, setCityGroup] = useState("");
  const [cityName, setCityName] = useState("");
  const [profileError, setProfileError] = useState("");
  const [profileMessage, setProfileMessage] = useState("");

  const years = useMemo(
    () => Array.from({ length: currentYear - 1949 }, (_, i) => String(currentYear - i)),
    [currentYear],
  );
  const months = useMemo(() => Array.from({ length: 12 }, (_, i) => String(i + 1).padStart(2, "0")), []);
  const days = useMemo(() => Array.from({ length: 31 }, (_, i) => String(i + 1).padStart(2, "0")), []);
  const hours = useMemo(() => Array.from({ length: 24 }, (_, i) => String(i).padStart(2, "0")), []);
  const minutes = useMemo(() => Array.from({ length: 60 }, (_, i) => String(i).padStart(2, "0")), []);

  const birthTimeLocal = buildBirthTimeLocal(year, month, day, hour, minute);
  const selectedCityGroup = useMemo(() => findCityGroup(cityGroup), [cityGroup]);
  const visibleCities = selectedCityGroup?.items || [];
  const selectedCity = useMemo(() => findCityOption(cityName), [cityName]);

  const selectedProfile =
    selectedProfileId != null ? profiles.find((item) => item.id === selectedProfileId) || null : null;

  const loadProfiles = useCallback(async () => {
    setProfilesLoading(true);
    try {
      const resp = await fetch("/api/auth/profiles", { cache: "no-store" });
      const data = (await resp.json().catch(() => ({}))) as { profiles?: BaziProfile[]; detail?: string };
      if (!resp.ok) {
        throw new Error(String(data.detail || "档案列表加载失败。"));
      }
      const nextProfiles = Array.isArray(data.profiles) ? data.profiles : [];
      setProfiles(nextProfiles);
      setProfileError("");
      if (selectedProfileId != null && !nextProfiles.some((item) => item.id === selectedProfileId)) {
        setSelectedProfileId(null);
      }
    } catch (error) {
      setProfileError(error instanceof Error ? error.message : "档案列表加载失败。");
    } finally {
      setProfilesLoading(false);
    }
  }, [selectedProfileId]);

  useEffect(() => {
    void loadProfiles();
  }, [loadProfiles]);

  function applyProfile(profile: BaziProfile) {
    const parsed = parseBirthTimeLocal(profile.birth_time_iso);
    setSelectedProfileId(profile.id);
    setProfileName(profile.profile_name);
    setYear(parsed.year);
    setMonth(parsed.month);
    setDay(parsed.day);
    setHour(parsed.hour);
    setMinute(parsed.minute);
    setGender(profile.gender);
    setCalendarType(profile.calendar_type);
    const resolvedCity = findCityOption(profile.city_name);
    setCityGroup(String(profile.city_group || resolvedCity?.group.id || ""));
    setCityName(String(profile.city_name || resolvedCity?.item.name || "").trim());
    setProfileError("");
    setProfileMessage(`已载入档案「${profile.profile_name}」。`);
  }

  function resetDraft() {
    setSelectedProfileId(null);
    setProfileName("");
    setYear(DEFAULT_FORM.year);
    setMonth(DEFAULT_FORM.month);
    setDay(DEFAULT_FORM.day);
    setHour(DEFAULT_FORM.hour);
    setMinute(DEFAULT_FORM.minute);
    setGender(DEFAULT_FORM.gender);
    setCalendarType(DEFAULT_FORM.calendarType);
    setCityGroup("");
    setCityName("");
    setProfileError("");
    setProfileMessage("已切换为新建草稿。");
  }

  async function saveProfile() {
    const nextName = profileName.trim();
    if (!nextName) {
      setProfileError("请先填写八字姓名/档案名。");
      return;
    }
    setProfileBusy(true);
    setProfileError("");
    setProfileMessage("");
    try {
      const target = selectedProfileId == null ? "/api/auth/profiles" : `/api/auth/profiles/${selectedProfileId}`;
      const resp = await fetch(target, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          profile_name: nextName,
          birth_time_iso: birthTimeLocal,
          gender,
          calendar_type: calendarType,
          city_name: selectedCity?.item.name || cityName.trim(),
          city_code: selectedCity?.item.code || "",
          city_group: selectedCity?.group.id || cityGroup,
          city_longitude: selectedCity?.item.longitude ?? null,
        }),
      });
      const data = (await resp.json().catch(() => ({}))) as {
        ok?: boolean;
        detail?: string;
        profile?: BaziProfile;
      };
      if (!resp.ok || data.ok === false || !data.profile) {
        throw new Error(String(data.detail || "档案保存失败。"));
      }
      const saved = data.profile;
      setSelectedProfileId(saved.id);
      setProfileName(saved.profile_name);
      setProfiles((prev) => {
        const next = prev.filter((item) => item.id !== saved.id);
        next.unshift(saved);
        return next;
      });
      setProfileMessage(selectedProfileId == null ? `已创建档案「${saved.profile_name}」。` : `已更新档案「${saved.profile_name}」。`);
    } catch (error) {
      setProfileError(error instanceof Error ? error.message : "档案保存失败。");
    } finally {
      setProfileBusy(false);
    }
  }

  async function removeProfile() {
    if (selectedProfileId == null) {
      setProfileError("当前没有可删除的档案。");
      return;
    }
    const currentProfile = selectedProfile;
    if (!window.confirm(`确认删除档案「${currentProfile?.profile_name || profileName || "当前档案"}」吗？`)) {
      return;
    }
    setProfileBusy(true);
    setProfileError("");
    setProfileMessage("");
    try {
      const resp = await fetch(`/api/auth/profiles/${selectedProfileId}/delete`, {
        method: "POST",
      });
      const data = (await resp.json().catch(() => ({}))) as { ok?: boolean; detail?: string };
      if (!resp.ok || data.ok === false) {
        throw new Error(String(data.detail || "档案删除失败。"));
      }
      const deletedId = selectedProfileId;
      setProfiles((prev) => prev.filter((item) => item.id !== deletedId));
      setSelectedProfileId(null);
      setProfileMessage(`已删除档案「${currentProfile?.profile_name || profileName || "当前档案"}」，当前保留为未保存草稿。`);
    } catch (error) {
      setProfileError(error instanceof Error ? error.message : "档案删除失败。");
    } finally {
      setProfileBusy(false);
    }
  }

  async function touchProfile(profileId: number | null) {
    if (profileId == null) return;
    try {
      const resp = await fetch(`/api/auth/profiles/${profileId}/touch`, {
        method: "POST",
      });
      const data = (await resp.json().catch(() => ({}))) as { profile?: BaziProfile };
      if (!resp.ok || !data.profile) return;
      const touched = data.profile;
      setProfiles((prev) => {
        const next = prev.filter((item) => item.id !== touched.id);
        next.unshift(touched);
        return next;
      });
    } catch {
      // 档案触达失败不影响排盘主流程
    }
  }

  function start() {
    void touchProfile(selectedProfileId);
    onStart({
      birthTimeISO: birthTimeLocal,
      gender,
      calendarType,
      profileId: selectedProfileId,
      profileName: profileName.trim() || undefined,
      cityName: selectedCity?.item.name || cityName.trim() || undefined,
      cityCode: selectedCity?.item.code || undefined,
      cityGroup: selectedCity?.group.id || cityGroup || undefined,
      cityLongitude: selectedCity?.item.longitude ?? null,
    });
  }

  return (
    <section className="w-full rounded-2xl border border-violet-400/30 bg-violet-900/20 p-5 shadow-[0_10px_40px_rgba(76,29,149,0.35)] backdrop-blur-xl">
      <header className="mb-4">
        <h2 className="text-base font-semibold text-violet-100">掐指一算 · 排盘输入</h2>
        <p className="mt-1 text-xs text-violet-200/80">当前账号可管理自己的八字档案，保存后可随时载入继续测算。</p>
      </header>

      <div className="mb-5 rounded-2xl border border-violet-300/20 bg-black/20 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-violet-100">
            <FolderOpen className="h-4 w-4" />
            <h3 className="text-sm font-semibold">八字档案管理</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={resetDraft}
              className="rounded-md border border-zinc-700 bg-zinc-900/60 px-3 py-2 text-xs text-zinc-200 transition hover:border-zinc-600 hover:bg-zinc-900"
            >
              新建草稿
            </button>
            <button
              type="button"
              onClick={() => void saveProfile()}
              disabled={profileBusy}
              className="inline-flex items-center gap-2 rounded-md border border-emerald-400/30 bg-emerald-400 px-3 py-2 text-xs font-semibold text-black transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <Save className="h-3.5 w-3.5" />
              {selectedProfileId == null ? "保存档案" : "更新档案"}
            </button>
            <button
              type="button"
              onClick={() => void removeProfile()}
              disabled={profileBusy || selectedProfileId == null}
              className="inline-flex items-center gap-2 rounded-md border border-rose-400/30 bg-rose-400 px-3 py-2 text-xs font-semibold text-black transition hover:bg-rose-300 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <Trash2 className="h-3.5 w-3.5" />
              删除档案
            </button>
          </div>
        </div>

        <div className="mt-4 grid gap-3 md:grid-cols-[1.2fr_1fr]">
          <label className="flex flex-col gap-1 text-xs text-violet-100">
            已有档案
            <select
              className="rounded-md border border-violet-300/30 bg-black/30 px-2 py-2 text-sm"
              value={selectedProfileId == null ? "" : String(selectedProfileId)}
              onChange={(event) => {
                const raw = event.target.value;
                if (!raw) {
                  resetDraft();
                  return;
                }
                const next = profiles.find((item) => item.id === Number(raw));
                if (next) applyProfile(next);
              }}
            >
              <option value="">未选择档案（当前草稿）</option>
              {profiles.map((item) => (
                <option key={item.id} value={item.id}>
                  {profileLabel(item)}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-xs text-violet-100">
            八字姓名 / 档案名
            <input
              value={profileName}
              onChange={(event) => setProfileName(event.target.value)}
              className="rounded-md border border-violet-300/30 bg-black/30 px-2 py-2 text-sm text-violet-50 outline-none transition focus:border-violet-200/50"
              placeholder="例如：本人命盘 / 父亲 / 案例 A"
            />
          </label>
        </div>

        <div className="mt-3 grid gap-3 md:grid-cols-[0.9fr_1.1fr]">
          <label className="flex flex-col gap-1 text-xs text-violet-100">
            城市分组
            <select
              className="rounded-md border border-violet-300/30 bg-black/30 px-2 py-2 text-sm"
              value={cityGroup}
              onChange={(event) => {
                const nextGroup = event.target.value;
                setCityGroup(nextGroup);
                const nextGroupInfo = findCityGroup(nextGroup);
                if (!nextGroupInfo) {
                  setCityName("");
                  return;
                }
                if (!nextGroupInfo.items.some((item) => item.name === cityName)) {
                  setCityName("");
                }
              }}
            >
              <option value="">未选择城市</option>
              {cityGroups.map((group) => (
                <option key={group.id} value={group.id}>
                  {group.label}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-xs text-violet-100">
            所属城市
            <select
              className="rounded-md border border-violet-300/30 bg-black/30 px-2 py-2 text-sm"
              value={cityName}
              onChange={(event) => setCityName(event.target.value)}
              disabled={!cityGroup}
            >
              <option value="">{cityGroup ? "请选择城市" : "请先选择城市分组"}</option>
              {cityName && !visibleCities.some((item) => item.name === cityName) ? (
                <option value={cityName}>{cityName}（当前档案保留值）</option>
              ) : null}
              {visibleCities.map((item) => (
                <option key={item.code || item.name} value={item.name}>
                  {item.display_name}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="mt-3 flex flex-wrap gap-3 text-[11px] text-violet-200/70">
          <span>{profilesLoading ? "档案加载中..." : `当前档案数：${profiles.length}`}</span>
          <span>{selectedProfileId == null ? "当前状态：未保存草稿" : `当前档案 ID：${selectedProfileId}`}</span>
          <span>{cityName ? `当前城市：${cityName}` : "当前城市：未设置"}</span>
        </div>

        {profileError ? (
          <p className="mt-3 rounded-xl border border-rose-500/25 bg-rose-950/25 px-3 py-2 text-xs text-rose-200">{profileError}</p>
        ) : null}
        {profileMessage ? (
          <p className="mt-3 rounded-xl border border-emerald-500/25 bg-emerald-950/25 px-3 py-2 text-xs text-emerald-200">{profileMessage}</p>
        ) : null}
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-7">
        <label className="flex flex-col gap-1 text-xs text-violet-100">
          历法
          <select
            className="rounded-md border border-violet-300/30 bg-black/30 px-2 py-2 text-sm"
            value={calendarType}
            onChange={(e) => setCalendarType(e.target.value as "solar" | "lunar")}
          >
            <option value="solar">阳历</option>
            <option value="lunar">阴历</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-violet-100">
          年
          <select className="rounded-md border border-violet-300/30 bg-black/30 px-2 py-2 text-sm" value={year} onChange={(e) => setYear(e.target.value)}>
            {years.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-violet-100">
          月
          <select className="rounded-md border border-violet-300/30 bg-black/30 px-2 py-2 text-sm" value={month} onChange={(e) => setMonth(e.target.value)}>
            {months.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-violet-100">
          日
          <select className="rounded-md border border-violet-300/30 bg-black/30 px-2 py-2 text-sm" value={day} onChange={(e) => setDay(e.target.value)}>
            {days.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-violet-100">
          时
          <select className="rounded-md border border-violet-300/30 bg-black/30 px-2 py-2 text-sm" value={hour} onChange={(e) => setHour(e.target.value)}>
            {hours.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-violet-100">
          分
          <select className="rounded-md border border-violet-300/30 bg-black/30 px-2 py-2 text-sm" value={minute} onChange={(e) => setMinute(e.target.value)}>
            {minutes.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-violet-100">
          性别
          <select className="rounded-md border border-violet-300/30 bg-black/30 px-2 py-2 text-sm" value={gender} onChange={(e) => setGender(e.target.value as "male" | "female")}>
            <option value="female">女</option>
            <option value="male">男</option>
          </select>
        </label>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-violet-200/75">当前出生时刻：{birthTimeLocal.replace("T", " ").slice(0, 16)}</p>
        <button
          type="button"
          onClick={start}
          className="inline-flex items-center gap-2 rounded-md bg-violet-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-violet-400"
        >
          <Play className="h-4 w-4" />
          启动测算
        </button>
      </div>
    </section>
  );
}
