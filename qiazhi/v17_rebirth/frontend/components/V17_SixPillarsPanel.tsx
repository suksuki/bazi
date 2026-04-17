"use client";

type Pillar = { stem: string; branch: string };

type FourPillars = {
  year?: string;
  month?: string;
  day?: string;
  hour?: string;
};

/** 解析后端/表单传来的出生时刻：无时区后缀时按本地墙钟理解，与 NatalInput 一致。 */
export function parseBirthTimeLocal(iso: string | undefined): Date | null {
  const raw = String(iso || "").trim();
  if (!raw) return null;
  if (raw.endsWith("Z") || /[+-]\d{2}:?\d{2}$/.test(raw)) {
    return new Date(raw);
  }
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2}))?/.exec(raw);
  if (!m) return new Date(raw);
  return new Date(
    Number(m[1]),
    Number(m[2]) - 1,
    Number(m[3]),
    Number(m[4]),
    Number(m[5]),
    m[6] ? Number(m[6]) : 0,
    0,
  );
}

const STEM_META: Record<string, { element: string; yinYang: "阳" | "阴" }> = {
  甲: { element: "木", yinYang: "阳" },
  乙: { element: "木", yinYang: "阴" },
  丙: { element: "火", yinYang: "阳" },
  丁: { element: "火", yinYang: "阴" },
  戊: { element: "土", yinYang: "阳" },
  己: { element: "土", yinYang: "阴" },
  庚: { element: "金", yinYang: "阳" },
  辛: { element: "金", yinYang: "阴" },
  壬: { element: "水", yinYang: "阳" },
  癸: { element: "水", yinYang: "阴" },
};

const BRANCH_META: Record<string, { element: string; yinYang: "阳" | "阴" }> = {
  子: { element: "水", yinYang: "阳" },
  丑: { element: "土", yinYang: "阴" },
  寅: { element: "木", yinYang: "阳" },
  卯: { element: "木", yinYang: "阴" },
  辰: { element: "土", yinYang: "阳" },
  巳: { element: "火", yinYang: "阴" },
  午: { element: "火", yinYang: "阳" },
  未: { element: "土", yinYang: "阴" },
  申: { element: "金", yinYang: "阳" },
  酉: { element: "金", yinYang: "阴" },
  戌: { element: "土", yinYang: "阳" },
  亥: { element: "水", yinYang: "阴" },
};

function colorForElement(el: string, yinYang: "阳" | "阴") {
  const palette: Record<string, string> = {
    木:
      yinYang === "阳"
        ? "text-lime-100 bg-lime-500/40 border-lime-300/80 shadow-[0_0_16px_rgba(132,204,22,0.45)]"
        : "text-emerald-100 bg-emerald-900/55 border-emerald-400/55 shadow-[0_0_10px_rgba(16,185,129,0.25)]",
    火:
      yinYang === "阳"
        ? "text-orange-50 bg-orange-500/45 border-orange-200/85 shadow-[0_0_18px_rgba(249,115,22,0.5)]"
        : "text-rose-100 bg-rose-900/55 border-rose-400/60 shadow-[0_0_10px_rgba(225,29,72,0.28)]",
    土:
      yinYang === "阳"
        ? "text-yellow-50 bg-yellow-500/45 border-yellow-200/80 shadow-[0_0_16px_rgba(234,179,8,0.45)]"
        : "text-amber-100 bg-amber-900/55 border-amber-400/60 shadow-[0_0_10px_rgba(245,158,11,0.28)]",
    金:
      yinYang === "阳"
        ? "text-white bg-slate-300/45 border-slate-100/85 shadow-[0_0_18px_rgba(226,232,240,0.45)]"
        : "text-zinc-100 bg-zinc-700/60 border-zinc-300/55 shadow-[0_0_10px_rgba(161,161,170,0.28)]",
    水:
      yinYang === "阳"
        ? "text-sky-50 bg-sky-500/45 border-sky-200/85 shadow-[0_0_18px_rgba(14,165,233,0.48)]"
        : "text-cyan-100 bg-cyan-900/60 border-cyan-400/60 shadow-[0_0_10px_rgba(6,182,212,0.3)]",
  };
  return palette[el] || "text-zinc-200 bg-zinc-700/20 border-zinc-500/50";
}

function parsePillar(raw: string | undefined): Pillar {
  const text = String(raw || "").trim();
  if (text.length < 2) return { stem: "—", branch: "" };
  return { stem: text.slice(0, 1), branch: text.slice(1, 2) };
}

export function V17_SixPillarsPanel({
  fourPillars,
  luckPillarFromServer,
  flowPillarFromServer,
  birthTimeISO,
  gender,
  calendarType,
  selectedYear,
  onYearChange,
}: {
  fourPillars?: FourPillars;
  /** 后端 lunar_python 大运（与所选流年对应） */
  luckPillarFromServer?: string;
  flowPillarFromServer?: string;
  birthTimeISO?: string;
  gender?: "male" | "female";
  calendarType?: "solar" | "lunar";
  selectedYear: number;
  onYearChange: (year: number) => void;
}) {
  const birth = parseBirthTimeLocal(birthTimeISO);

  const yearP = parsePillar(fourPillars?.year);
  const monthP = parsePillar(fourPillars?.month);
  const dayP = parsePillar(fourPillars?.day);
  const hourP = parsePillar(fourPillars?.hour);
  const luckP = parsePillar(luckPillarFromServer);
  const flowP = parsePillar(flowPillarFromServer);

  const rows: Array<{ label: string; pillar: Pillar }> = [
    { label: "年柱", pillar: yearP },
    { label: "月柱", pillar: monthP },
    { label: "日柱", pillar: dayP },
    { label: "时柱", pillar: hourP },
    { label: "大运", pillar: luckP },
    { label: "流年", pillar: flowP },
  ];

  const yearChoices = Array.from({ length: 111 }, (_, i) => selectedYear - 80 + i);

  const birthLabel =
    birth != null
      ? `${birth.getFullYear()}-${String(birth.getMonth() + 1).padStart(2, "0")}-${String(birth.getDate()).padStart(2, "0")} ${String(birth.getHours()).padStart(2, "0")}:00`
      : "—";
  const genderLabel = gender === "male" ? "男" : gender === "female" ? "女" : "—";
  const calendarLabel = calendarType === "lunar" ? "阴历" : calendarType === "solar" ? "阳历" : "—";

  return (
    <section className="rounded-xl border border-violet-700/40 bg-zinc-950/70 p-3">
      <div className="mb-2 rounded-lg border border-violet-600/25 bg-zinc-900/50 px-2 py-1.5 text-[11px] text-zinc-300">
        <span className="text-zinc-500">出生 </span>
        <span className="text-violet-100">{birthLabel}</span>
        <span className="mx-1.5 text-zinc-600">·</span>
        <span className="text-zinc-500">性别 </span>
        <span className="text-violet-100">{genderLabel}</span>
        <span className="mx-1.5 text-zinc-600">·</span>
        <span className="text-zinc-500">历法 </span>
        <span className="text-violet-100">{calendarLabel}</span>
      </div>
      <div className="mb-3 flex items-center justify-between gap-2">
        <p className="text-xs text-violet-200/80">命局六柱（仅展示 NDJSON 快照中的服务端结果）</p>
        <label className="inline-flex items-center gap-2 text-xs text-zinc-300">
          <span>年份</span>
          <select
            value={selectedYear}
            onChange={(e) => onYearChange(Number(e.target.value))}
            className="rounded border border-violet-500/40 bg-zinc-900 px-2 py-1 text-xs text-zinc-100"
          >
            {yearChoices.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="grid grid-cols-3 gap-2 md:grid-cols-6">
        {rows.map((row) => {
          const stemMeta = STEM_META[row.pillar.stem] || { element: "土", yinYang: "阳" as const };
          const branchMeta = BRANCH_META[row.pillar.branch] || { element: "土", yinYang: "阳" as const };
          return (
            <div key={row.label} className="rounded-lg border border-violet-600/30 bg-zinc-900/60 p-2 text-center">
              <p className="mb-1 text-[11px] text-zinc-400">{row.label}</p>
              <div className={`rounded border px-2 py-1 text-base font-semibold ${colorForElement(stemMeta.element, stemMeta.yinYang)}`}>
                {row.pillar.stem || "—"}
              </div>
              <div className={`mt-1 rounded border px-2 py-1 text-base font-semibold ${colorForElement(branchMeta.element, branchMeta.yinYang)}`}>
                {row.pillar.branch || "—"}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
