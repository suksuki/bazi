"use client";

import { useState } from "react";

import { resolveQiazhiApiBase } from "@/lib/qiazhiApiBase";

const API_BASE = resolveQiazhiApiBase();

export function MobileBaziInput() {
  const [date, setDate] = useState("");
  const [time, setTime] = useState("12:00");
  const [tz, setTz] = useState("Asia/Shanghai");
  const [status, setStatus] = useState<string | null>(null);

  async function submit() {
    setStatus("提交中…");
    try {
      const r = await fetch(`${API_BASE}/api/consultations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subject_ref: null,
          input_meta: { date, time, timezone: tz, source: "mobile_form" },
        }),
      });
      if (!r.ok) throw new Error(await r.text());
      const j = await r.json();
      setStatus(`已建立测算记录 id=${j.id}`);
    } catch (e) {
      setStatus(`失败：${e instanceof Error ? e.message : String(e)}`);
    }
  }

  return (
    <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4 shadow-lg backdrop-blur">
      <label className="block text-sm text-zinc-400">公历日期</label>
      <input
        type="date"
        value={date}
        onChange={(e) => setDate(e.target.value)}
        className="mt-1 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-3 text-base outline-none ring-0 focus:border-amber-500/80"
      />
      <label className="mt-4 block text-sm text-zinc-400">时刻</label>
      <input
        type="time"
        value={time}
        onChange={(e) => setTime(e.target.value)}
        className="mt-1 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-3 text-base outline-none focus:border-amber-500/80"
      />
      <label className="mt-4 block text-sm text-zinc-400">时区</label>
      <input
        type="text"
        value={tz}
        onChange={(e) => setTz(e.target.value)}
        placeholder="Asia/Shanghai"
        className="mt-1 w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-3 text-base outline-none focus:border-amber-500/80"
      />
      <button
        type="button"
        onClick={submit}
        className="mt-6 w-full rounded-xl bg-amber-500 py-3 text-center text-base font-medium text-zinc-950 active:scale-[0.99]"
      >
        开始测算
      </button>
      {status ? <p className="mt-3 text-sm text-zinc-400">{status}</p> : null}
    </section>
  );
}
