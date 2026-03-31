"use client";

import { useCallback, useMemo, useState } from "react";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8001";

const STRINGS: Record<string, Record<string, string>> = {
  zh: {
    title: "墓库裁决（原型）",
    clash: "地支逢冲",
    punishment: "有效刑",
    energy: "储能标量",
    evaluate: "检测相位",
    narrative: "系统叙述",
    need_you: "需要裁决人确认",
    sealed: "闭库",
    open: "开库",
    collapse: "坍塌",
    submit: "提交裁决",
    locale: "语言",
  },
  en: {
    title: "Storehouse (prototype)",
    clash: "Branch clash",
    punishment: "Effective punishment",
    energy: "Storage scalar",
    evaluate: "Evaluate",
    narrative: "System narrative",
    need_you: "Arbiter confirmation required",
    sealed: "Sealed",
    open: "Open vault",
    collapse: "Collapse",
    submit: "Submit",
    locale: "Locale",
  },
  ko: {
    title: "묘고（프로토타입）",
    clash: "지지 충",
    punishment: "유효 형",
    energy: "저장 스칼라",
    evaluate: "평가",
    narrative: "시스템 서술",
    need_you: "재판인 확인 필요",
    sealed: "폐고",
    open: "개고",
    collapse: "붕괴",
    submit: "제출",
    locale: "언어",
  },
};

type LocaleKey = "zh" | "en" | "ko";

export default function QiazhiPage() {
  const [locale, setLocale] = useState<LocaleKey>("zh");
  const t = useMemo(() => STRINGS[locale] || STRINGS.zh, [locale]);

  const [energy, setEnergy] = useState(22);
  const [clash, setClash] = useState(true);
  const [punishment, setPunishment] = useState(false);
  const [phase, setPhase] = useState<string | null>(null);
  const [narrative, setNarrative] = useState("");
  const [needsArb, setNeedsArb] = useState(false);
  const [arbChoice, setArbChoice] = useState<"sealed" | "open" | "collapse">(
    "open",
  );
  const [log, setLog] = useState<string>("");

  const evaluate = useCallback(async () => {
    const res = await fetch(`${API_BASE}/api/qiazhi/storehouse/evaluate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        energy_storage: energy,
        branch_has_clash: clash,
        branch_has_effective_punishment: punishment,
        earth_branch_code: "辰",
      }),
    });
    if (!res.ok) {
      setLog(`HTTP ${res.status}`);
      return;
    }
    const data = await res.json();
    setPhase(data.system_phase);
    setNarrative(data.narrative_zh);
    setNeedsArb(data.needs_arbitration);
    setLog("");
  }, [energy, clash, punishment]);

  const submitDecision = useCallback(async () => {
    const sid = `sess-${Date.now()}`;
    const res = await fetch(`${API_BASE}/api/qiazhi/storehouse/decision`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sid,
        system_suggested: phase,
        arbiter_choice: arbChoice,
        note: "next.js prototype",
      }),
    });
    if (!res.ok) {
      setLog(`decision HTTP ${res.status}`);
      return;
    }
    const data = await res.json();
    setLog(JSON.stringify(data.recorded, null, 2));
  }, [phase, arbChoice]);

  return (
    <main className="mx-auto max-w-lg px-4 py-10">
      <div className="mb-6 flex items-center justify-between gap-4">
        <h1 className="text-xl font-medium text-mist">{t.title}</h1>
        <label className="flex items-center gap-2 text-sm text-mist/70">
          <span>{t.locale}</span>
          <select
            value={locale}
            onChange={(e) => setLocale(e.target.value as LocaleKey)}
            className="rounded border border-mist/20 bg-ink px-2 py-1 text-mist"
          >
            <option value="zh">中文</option>
            <option value="en">English</option>
            <option value="ko">한국어</option>
          </select>
        </label>
      </div>

      <div className="space-y-4 rounded-lg border border-mist/10 bg-mist/5 p-4">
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-mist/70">{t.energy}</span>
          <input
            type="number"
            value={energy}
            onChange={(e) => setEnergy(Number(e.target.value))}
            className="rounded border border-mist/20 bg-ink px-3 py-2 text-mist"
          />
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={clash}
            onChange={(e) => setClash(e.target.checked)}
          />
          {t.clash}
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={punishment}
            onChange={(e) => setPunishment(e.target.checked)}
          />
          {t.punishment}
        </label>
        <button
          type="button"
          onClick={() => void evaluate()}
          className="w-full rounded bg-jade py-3 text-sm font-medium text-white hover:bg-jade/90"
        >
          {t.evaluate}
        </button>
      </div>

      {phase && (
        <section className="mt-8 space-y-3 rounded-lg border border-jade/30 p-4">
          <p className="text-sm text-mist/80">
            <span className="text-mist/50">phase: </span>
            {phase}
          </p>
          <p className="text-sm leading-relaxed text-mist/90">{t.narrative}</p>
          <p className="text-mist/80">{narrative}</p>
          {needsArb && (
            <div className="mt-4 space-y-3 border-t border-mist/10 pt-4">
              <p className="text-amber-200/90 text-sm">{t.need_you}</p>
              <div className="flex flex-wrap gap-2">
                {(
                  [
                    ["sealed", t.sealed],
                    ["open", t.open],
                    ["collapse", t.collapse],
                  ] as const
                ).map(([v, label]) => (
                  <button
                    key={v}
                    type="button"
                    onClick={() => setArbChoice(v)}
                    className={`rounded px-4 py-2 text-sm ${
                      arbChoice === v
                        ? "bg-jade text-white"
                        : "border border-mist/20 text-mist/80"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
              <button
                type="button"
                onClick={() => void submitDecision()}
                className="w-full rounded border border-mist/30 py-2 text-sm text-mist hover:bg-mist/5"
              >
                {t.submit}
              </button>
            </div>
          )}
        </section>
      )}

      {log && (
        <pre className="mt-6 overflow-x-auto rounded bg-black/30 p-3 text-xs text-mist/70">
          {log}
        </pre>
      )}

      <p className="mt-10 text-center text-xs text-mist/40">
        API: {API_BASE}
      </p>
    </main>
  );
}
