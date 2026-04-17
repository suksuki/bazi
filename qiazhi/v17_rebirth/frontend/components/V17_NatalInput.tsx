"use client";

import { useMemo, useState } from "react";
import { Play } from "lucide-react";

export type V17NatalInputValue = {
  birthTimeISO: string;
  gender: "male" | "female";
  calendarType: "solar" | "lunar";
};

export function V17_NatalInput({ onStart }: { onStart: (value: V17NatalInputValue) => void }) {
  const current = new Date();
  const currentYear = current.getFullYear();
  const [year, setYear] = useState(String(currentYear));
  const [month, setMonth] = useState(String(current.getMonth() + 1).padStart(2, "0"));
  const [day, setDay] = useState(String(current.getDate()).padStart(2, "0"));
  const [hour, setHour] = useState(String(current.getHours()).padStart(2, "0"));
  const [gender, setGender] = useState<"male" | "female">("female");
  const [calendarType, setCalendarType] = useState<"solar" | "lunar">("solar");

  const years = useMemo(() => Array.from({ length: currentYear - 1949 }, (_, i) => String(currentYear - i)), [currentYear]);

  const months = useMemo(() => Array.from({ length: 12 }, (_, i) => String(i + 1).padStart(2, "0")), []);
  const days = useMemo(() => Array.from({ length: 31 }, (_, i) => String(i + 1).padStart(2, "0")), []);
  const hours = useMemo(() => Array.from({ length: 24 }, (_, i) => String(i).padStart(2, "0")), []);

  function start() {
    const localDate = new Date(Number(year), Number(month) - 1, Number(day), Number(hour), 0, 0);
    onStart({
      birthTimeISO: localDate.toISOString(),
      gender,
      calendarType,
    });
  }

  return (
    <section className="w-full rounded-2xl border border-violet-400/30 bg-violet-900/20 p-5 shadow-[0_10px_40px_rgba(76,29,149,0.35)] backdrop-blur-xl">
      <header className="mb-4">
        <h2 className="text-base font-semibold text-violet-100">V17 Natal Input</h2>
        <p className="mt-1 text-xs text-violet-200/80">输入出生时刻，触发 8017 专属链路测算。</p>
      </header>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
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
          性别
          <select className="rounded-md border border-violet-300/30 bg-black/30 px-2 py-2 text-sm" value={gender} onChange={(e) => setGender(e.target.value as "male" | "female")}>
            <option value="female">女</option>
            <option value="male">男</option>
          </select>
        </label>
      </div>

      <button
        type="button"
        onClick={start}
        className="mt-5 inline-flex items-center gap-2 rounded-md bg-violet-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-violet-400"
      >
        <Play className="h-4 w-4" />
        启动测算
      </button>
    </section>
  );
}
