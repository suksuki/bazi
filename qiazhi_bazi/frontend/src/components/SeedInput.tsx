"use client";

import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";

type Props = {
  onSubmit: (payload: {
    date: string;
    time: string;
    calendar: "solar" | "lunar";
    gender: "male" | "female";
  }) => Promise<void>;
  busy: boolean;
  t?: (s: string) => string;
};

export function SeedInput({ onSubmit, busy, t = (s) => s }: Props) {
  const [year, setYear] = useState("1990");
  const [month, setMonth] = useState("01");
  const [day, setDay] = useState("01");
  const [hour, setHour] = useState("00");
  const [minute, setMinute] = useState("00");
  const [calendar, setCalendar] = useState<"solar" | "lunar">("solar");
  const [gender, setGender] = useState<"male" | "female">("male");

  async function submit() {
    const date = `${year}-${month}-${day}`;
    const time = `${hour}:${minute}`;
    await onSubmit({ date, time, calendar, gender });
  }

  const years = Array.from({ length: 81 }, (_, i) => String(1950 + i));
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

  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-3"
    >
      <h2 className="text-sm font-medium text-zinc-300">{t("The Seed")}</h2>
      <p className="mt-0.5 text-xs text-zinc-500">{t("输入生日后，系统将进入流式推演。")}</p>
      <div className="mt-2 flex gap-2">
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
      <label className="mt-2 block text-xs text-zinc-500">{t("日期时刻")}</label>
      <div className="mt-2 flex gap-2">
        <button
          type="button"
          onClick={() => setGender("male")}
          className={`rounded-lg px-3 py-1.5 text-xs ${gender === "male" ? "bg-cyan-500 text-zinc-950" : "bg-zinc-800 text-zinc-300"}`}
        >
          乾造（男）
        </button>
        <button
          type="button"
          onClick={() => setGender("female")}
          className={`rounded-lg px-3 py-1.5 text-xs ${gender === "female" ? "bg-fuchsia-500 text-zinc-950" : "bg-zinc-800 text-zinc-300"}`}
        >
          坤造（女）
        </button>
      </div>
      <div className="mt-1 grid grid-cols-2 gap-2 md:grid-cols-5">
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
      <button
        type="button"
        disabled={busy}
        onClick={submit}
        className="mt-3 w-full rounded-xl bg-amber-500 py-2.5 text-sm font-medium text-zinc-950 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {busy ? t("推演中…") : t("掐指一算")}
      </button>
    </motion.section>
  );
}
