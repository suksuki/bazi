import { useEffect, useMemo, useRef, useState, type SyntheticEvent } from "react";

import {
  activateOwnerCase,
  createOwnerCase,
  type HomeSnapshot,
  type OwnerCaseInput,
} from "../homeApi";
import type { HomeWorldLight } from "../homeWorldLight";
import { HomeProfileCreateForm } from "./HomeProfileCreateForm";

type CaseOption = HomeSnapshot["case_options"][number];

const PILLAR_ORDER = ["year", "month", "day", "hour"] as const;
const ELEMENT_BY_STEM: Record<string, string> = {
  甲: "wood", 乙: "wood", 丙: "fire", 丁: "fire", 戊: "earth",
  己: "earth", 庚: "metal", 辛: "metal", 壬: "water", 癸: "water",
};

function CaseGlyph({ option }: { option: CaseOption }) {
  const dayMaster = option.pillars.day.slice(0, 1);
  return (
    <i className="profile-case-glyph" data-element={ELEMENT_BY_STEM[dayMaster] ?? "earth"}>
      {dayMaster}
    </i>
  );
}

function pillarsText(option: CaseOption) {
  return PILLAR_ORDER.map((slot) => option.pillars[slot]).join(" · ");
}

export function HomeProfileManager({
  home,
  light,
  onChanged,
  onClose,
  onOpenMingli,
}: {
  home: HomeSnapshot;
  light: HomeWorldLight;
  onChanged: () => Promise<void>;
  onClose: () => void;
  onOpenMingli: (option: CaseOption, anchor: HTMLElement) => void;
}) {
  const [query, setQuery] = useState("");
  const [selectedRef, setSelectedRef] = useState(home.case.case_ref);
  const [mode, setMode] = useState<"view" | "create">("view");
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshFailed, setRefreshFailed] = useState(false);
  const [pendingCaseRef, setPendingCaseRef] = useState<string | null>(null);
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (dialog && !dialog.open) dialog.showModal();
    return () => {
      if (dialog?.open) dialog.close();
    };
  }, []);

  useEffect(() => {
    if (
      !pendingCaseRef
      && !home.case_options.some((option) => option.case_ref === selectedRef)
    ) {
      setSelectedRef(home.case.case_ref);
    }
  }, [home.case.case_ref, home.case_options, pendingCaseRef, selectedRef]);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase("zh-CN");
    if (!normalized) return home.case_options;
    return home.case_options.filter((option) =>
      [option.display_name, option.birth_location, pillarsText(option)]
        .join(" ")
        .toLocaleLowerCase("zh-CN")
        .includes(normalized),
    );
  }, [home.case_options, query]);

  const selected =
    home.case_options.find((option) => option.case_ref === selectedRef) ??
    filtered[0] ??
    null;

  const activate = async (caseRef: string) => {
    setWorking(true);
    setError(null);
    setRefreshFailed(false);
    try {
      await activateOwnerCase(caseRef);
      setPendingCaseRef(caseRef);
      setSelectedRef(caseRef);
      try {
        await onChanged();
        setPendingCaseRef(null);
      } catch {
        setRefreshFailed(true);
        setError("档案已经切换成功，但页面没有读回最新生命树。请重新读取；不要重复切换。");
      }
    } catch (cause) {
      setPendingCaseRef(null);
      setError(`档案切换未提交：${cause instanceof Error ? cause.message : String(cause)}`);
    } finally {
      setWorking(false);
    }
  };

  const create = async (input: OwnerCaseInput) => {
    setWorking(true);
    setError(null);
    setRefreshFailed(false);
    try {
      const created = await createOwnerCase(input);
      setPendingCaseRef(created.case_ref);
      setSelectedRef(created.case_ref);
      try {
        await onChanged();
        setPendingCaseRef(null);
        setMode("view");
      } catch {
        setRefreshFailed(true);
        setError("新档案已经保存成功，但页面没有读回最新生命树。请重新读取；不要再次保存。");
      }
    } catch (cause) {
      setPendingCaseRef(null);
      setError(`档案保存未提交：${cause instanceof Error ? cause.message : String(cause)}`);
    } finally {
      setWorking(false);
    }
  };

  const refresh = async () => {
    setWorking(true);
    try {
      await onChanged();
      if (pendingCaseRef) setSelectedRef(pendingCaseRef);
      setPendingCaseRef(null);
      setError(null);
      setRefreshFailed(false);
      setMode("view");
    } catch {
      setError("档案已经提交，但仍未读回最新生命树。可以安全刷新页面，不要重复提交。");
    } finally {
      setWorking(false);
    }
  };

  return (
    <dialog
      aria-label="八字档案管理"
      className="profile-manager"
      data-light={light}
      onCancel={(event: SyntheticEvent<HTMLDialogElement>) => {
        event.preventDefault();
        if (working) return;
        if (mode === "create") setMode("view");
        else onClose();
      }}
      ref={dialogRef}
    >
      <div className="profile-manager-backdrop" aria-hidden="true" />
      <header className="profile-manager-header">
        <span>
          <small>BAZI PROFILES · LIFECASES</small>
          <strong>八字档案</strong>
        </span>
        <button aria-label="关闭八字档案" autoFocus disabled={working} onClick={onClose} type="button">
          回到生命树 <b aria-hidden="true">×</b>
        </button>
      </header>

      <div className="profile-manager-layout">
        <aside className="profile-manager-list">
          <div className="profile-manager-list-tools">
            <label>
              <span aria-hidden="true">⌕</span>
              <input
                aria-label="搜索八字档案"
                placeholder="搜索姓名、地点或四柱"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </label>
            <button disabled={working} onClick={() => setMode("create")} type="button">＋ 新增</button>
          </div>
          <div className="profile-manager-tabs">
            <strong>真实档案 · {home.case_options.length}</strong>
            <small>本人和参考档案各自绑定独立 Case</small>
          </div>
          <div className="profile-manager-cards">
            {filtered.map((option) => (
              <button
                className={`${selected?.case_ref === option.case_ref ? "is-selected" : ""} ${option.active ? "is-current" : ""}`}
                disabled={working}
                key={option.case_ref}
                onClick={() => {
                  setMode("view");
                  setSelectedRef(option.case_ref);
                }}
                type="button"
              >
                <CaseGlyph option={option} />
                <span>
                  <strong>{option.display_name}</strong>
                  <small>{option.gender === "male" ? "男" : "女"} · {option.birth_location} · {option.birth_date}</small>
                  <em>{pillarsText(option)}</em>
                </span>
                <b>
                  {option.subject_kind === "HUMAN_OWNER" ? "本人" : "参考"}
                  {option.active ? " · 当前" : ""}
                </b>
              </button>
            ))}
            {filtered.length === 0 && <p className="profile-manager-empty">没有找到匹配的档案。</p>}
          </div>
        </aside>

        <article className="profile-manager-detail">
          {error && (
            <div className="profile-manager-error" role="alert">
              <span>{error}</span>
              {refreshFailed && (
                <button disabled={working} onClick={() => void refresh()} type="button">
                  {working ? "正在读取…" : "重新读取档案"}
                </button>
              )}
            </div>
          )}
          {mode === "create" ? (
            <HomeProfileCreateForm
              saving={working}
              onCancel={() => setMode("view")}
              onSubmit={create}
            />
          ) : selected ? (
            <div className="profile-detail-card">
              <header>
                <div className="profile-detail-identity">
                  <CaseGlyph option={selected} />
                  <span>
                    <small>{selected.active ? "当前生命叶" : selected.identity_badge}</small>
                    <strong>{selected.display_name}</strong>
                    <em>{selected.gender === "male" ? "男" : "女"} · {selected.birth_location}</em>
                  </span>
                </div>
                <span className="profile-detail-leaf" aria-hidden="true">叶</span>
              </header>

              <dl className="profile-birth-facts">
                <div><dt>出生</dt><dd>{selected.birth_date} · {selected.birth_time}</dd></div>
                <div><dt>地点</dt><dd>{selected.birth_location} · {selected.timezone}</dd></div>
                <div><dt>历法</dt><dd>{selected.calendar_type === "solar" ? "公历" : `农历${selected.lunar_leap_month ? " · 闰月" : ""}`} · 民用钟表时间</dd></div>
                <div><dt>状态</dt><dd>真实 Case · 已绑定可恢复 Reading</dd></div>
                <div><dt>身份</dt><dd>{selected.identity_badge}{selected.birth_location_status === "HISTORICAL_MISSING" ? " · 出生地待补充" : ""}</dd></div>
              </dl>

              <section className="profile-chart-summary">
                <small>FOUR PILLARS</small>
                <strong>{pillarsText(selected)}</strong>
                <p>日主 {selected.pillars.day.slice(0, 1)} · 四柱由 canonical 排盘引擎生成</p>
              </section>

              <p className="profile-detail-boundary">
                出生事实与命盘版本保持不可变；需要修正资料时，请建立一份新档案，旧 Reading 不会被无声改写。
              </p>
              <div className="profile-detail-actions">
                <button
                  className="is-primary"
                  disabled={working}
                  onClick={(event) => {
                    const card = event.currentTarget.closest(".profile-detail-card");
                    const leaf = card?.querySelector<HTMLElement>(".profile-detail-leaf");
                    onOpenMingli(selected, leaf ?? event.currentTarget);
                  }}
                  type="button"
                >
                  打开这片命理枝
                </button>
                {!selected.active && selected.subject_kind === "HUMAN_OWNER" && (
                  <button disabled={working} onClick={() => void activate(selected.case_ref)} type="button">
                    {working ? "正在切换…" : "设为当前生命树"}
                  </button>
                )}
              </div>
            </div>
          ) : (
            <p className="profile-manager-empty">请选择一份八字档案。</p>
          )}
        </article>
      </div>
    </dialog>
  );
}
