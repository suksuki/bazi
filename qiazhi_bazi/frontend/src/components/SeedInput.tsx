"use client";

import { motion } from "framer-motion";
import { useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import { SEED_YEAR_STRINGS } from "@/components/seedYearRange";

export type SeedFormPayload = {
  date: string;
  time: string;
  calendar: "solar" | "lunar";
  gender: "male" | "female";
};

type Props = {
  onSubmit: (payload: SeedFormPayload) => Promise<void>;
  busy: boolean;
  rightSummarySlot?: ReactNode;
  hideSubmitButton?: boolean;
  /** 入口页主按钮：选定生辰后进入主界面（与 splitActions 二选一展示） */
  entryCommitAction?: {
    label: string;
    busy?: boolean;
    onClick: (payload: SeedFormPayload) => void | Promise<void>;
  };
  /** 仅拉预览；正式「测算八字」由主栏 UnifiedActionBar 触发 onSeedSubmit */
  splitActions?: {
    onPreview: (payload: SeedFormPayload) => void | Promise<void>;
    previewBusy?: boolean;
  };
  onPayloadChange?: (payload: SeedFormPayload) => void;
  /** 返回入口页时回填上次生辰（不随每次 render 反复覆盖） */
  hydrateFrom?: SeedFormPayload | null;
  t?: (s: string) => string;
};

export function SeedInput({
  onSubmit,
  busy,
  rightSummarySlot,
  hideSubmitButton = false,
  entryCommitAction,
  splitActions,
  onPayloadChange,
  hydrateFrom = null,
  t = (s) => s,
}: Props) {
  const [year, setYear] = useState("1990");
  const [month, setMonth] = useState("01");
  const [day, setDay] = useState("01");
  const [hour, setHour] = useState("00");
  const [minute, setMinute] = useState("00");
  const [calendar, setCalendar] = useState<"solar" | "lunar">("solar");
  const [gender, setGender] = useState<"male" | "female">("male");

  const buildPayload = (): SeedFormPayload => ({
    date: `${year}-${month}-${day}`,
    time: `${hour}:${minute}`,
    calendar,
    gender,
  });

  async function submit() {
    await onSubmit(buildPayload());
  }

  useEffect(() => {
    onPayloadChange?.({
      date: `${year}-${month}-${day}`,
      time: `${hour}:${minute}`,
      calendar,
      gender,
    });
  }, [year, month, day, hour, minute, calendar, gender, onPayloadChange]);

  const years = SEED_YEAR_STRINGS;
  const months = Array.from({ length: 12 }, (_, i) => String(i + 1).padStart(2, "0"));
  const daysInMonth = useMemo(() => {
    if (calendar === "lunar") return 30;
    const y = Number(year);
    const m = Number(month);
    return new Date(y, m, 0).getDate();
  }, [calendar, year, month]);
  const days = Array.from({ length: daysInMonth }, (_, i) => String(i + 1).padStart(2, "0"));
  const hours = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, "0"));
  const minutes = Array.from({ length: 60 }, (_, i) => String(i).padStart(2, "0"));

  useEffect(() => {
    if (Number(day) > daysInMonth) {
      setDay(String(daysInMonth).padStart(2, "0"));
    }
  }, [day, daysInMonth]);

  const hydratedSigRef = useRef("");
  useEffect(() => {
    if (!hydrateFrom) return;
    const sig = `${hydrateFrom.date}|${hydrateFrom.time}|${hydrateFrom.calendar}|${hydrateFrom.gender}`;
    if (hydratedSigRef.current === sig) return;
    hydratedSigRef.current = sig;
    const [y, m, d] = hydrateFrom.date.split("-").map((x) => x.trim());
    const [hh, mm] = hydrateFrom.time.split(":").map((x) => x.trim());
    if (y) setYear(y.padStart(4, "0").slice(0, 4));
    if (m) setMonth(m.padStart(2, "0").slice(0, 2));
    if (d) setDay(d.padStart(2, "0").slice(0, 2));
    if (hh) setHour(hh.padStart(2, "0").slice(0, 2));
    if (mm) setMinute(mm.padStart(2, "0").slice(0, 2));
    setCalendar(hydrateFrom.calendar);
    setGender(hydrateFrom.gender);
  }, [hydrateFrom]);

  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-3"
    >
      {rightSummarySlot ? (
        <div className="mb-3 rounded-xl border border-zinc-800/80 bg-zinc-950/35 p-2">
          {rightSummarySlot}
        </div>
      ) : null}

      <div>
          <div className="flex flex-wrap items-center gap-3">
            <div className="min-w-[13rem]">
              <h2 className="text-sm font-medium text-zinc-300">{t("The Seed")}</h2>
              <p className="mt-0.5 text-xs text-zinc-500">{t("输入生日后，系统将进入流式推演。")}</p>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setCalendar("solar")}
                className={`rounded-lg px-3 py-1.5 text-xs ${calendar === "solar" ? "bg-amber-500 text-zinc-950" : "bg-zinc-800 text-zinc-300"}`}
              >
                {t("公历")}
              </button>
              <button
                type="button"
                onClick={() => setCalendar("lunar")}
                className={`rounded-lg px-3 py-1.5 text-xs ${calendar === "lunar" ? "bg-amber-500 text-zinc-950" : "bg-zinc-800 text-zinc-300"}`}
              >
                {t("农历")}
              </button>
            </div>
            <span className="text-xs text-zinc-500">{t("日期时刻")}</span>
            <button
              type="button"
              onClick={() => setGender("male")}
              className={`rounded-lg px-3 py-1.5 text-xs ${gender === "male" ? "bg-cyan-500 text-zinc-950" : "bg-zinc-800 text-zinc-300"}`}
            >
              {t("乾造（男）")}
            </button>
            <button
              type="button"
              onClick={() => setGender("female")}
              className={`rounded-lg px-3 py-1.5 text-xs ${gender === "female" ? "bg-fuchsia-500 text-zinc-950" : "bg-zinc-800 text-zinc-300"}`}
            >
              {t("坤造（女）")}
            </button>
          </div>
          <div className="mt-2 grid grid-cols-2 gap-2 md:grid-cols-5">
            <select
              value={year}
              onChange={(e) => setYear(e.target.value)}
              className="rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm outline-none focus:border-amber-500/80"
            >
              {years.map((y) => (
                <option key={y} value={y}>
                  {y}{t("年")}
                </option>
              ))}
            </select>
            <select
              value={month}
              onChange={(e) => setMonth(e.target.value)}
              className="rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm outline-none focus:border-amber-500/80"
            >
              {months.map((m) => (
                <option key={m} value={m}>
                  {m}{t("月")}
                </option>
              ))}
            </select>
            <select
              value={day}
              onChange={(e) => setDay(e.target.value)}
              className="rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm outline-none focus:border-amber-500/80"
            >
              {days.map((d) => (
                <option key={d} value={d}>
                  {d}{t("日")}
                </option>
              ))}
            </select>
            <select
              value={hour}
              onChange={(e) => setHour(e.target.value)}
              className="rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm outline-none focus:border-amber-500/80"
            >
              {hours.map((h) => (
                <option key={h} value={h}>
                  {h}{t("时")}
                </option>
              ))}
            </select>
            <select
              value={minute}
              onChange={(e) => setMinute(e.target.value)}
              className="rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm outline-none focus:border-amber-500/80"
            >
              {minutes.map((m) => (
                <option key={m} value={m}>
                  {m}{t("分")}
                </option>
              ))}
            </select>
          </div>
          {entryCommitAction && hideSubmitButton ? (
            <div className="mt-3">
              <button
                type="button"
                disabled={Boolean(busy || entryCommitAction.busy)}
                onClick={() => void entryCommitAction.onClick(buildPayload())}
                className="w-full rounded-xl border border-amber-500/50 bg-gradient-to-r from-amber-500/90 to-amber-600/85 py-2.5 text-sm font-semibold text-zinc-950 shadow-md shadow-amber-900/30 hover:from-amber-400 hover:to-amber-500 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {entryCommitAction.busy ? t("推演中…") : entryCommitAction.label}
              </button>
            </div>
          ) : splitActions && hideSubmitButton ? (
            <div className="mt-3">
              <button
                type="button"
                disabled={Boolean(splitActions.previewBusy)}
                onClick={() => void splitActions.onPreview(buildPayload())}
                className="w-full rounded-xl border border-zinc-600 bg-zinc-800/90 py-2.5 text-sm font-medium text-zinc-100 hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {splitActions.previewBusy ? t("预览更新中…") : t("选择出生日期")}
              </button>
            </div>
          ) : !hideSubmitButton ? (
            <button
              type="button"
              disabled={busy}
              onClick={submit}
              className="mt-3 w-full rounded-xl bg-amber-500 py-2.5 text-sm font-medium text-zinc-950 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {busy ? t("推演中…") : t("掐指一算")}
            </button>
          ) : null}
      </div>
    </motion.section>
  );
}
