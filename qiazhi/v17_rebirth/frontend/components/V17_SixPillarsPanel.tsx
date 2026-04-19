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
        ? "text-lime-200 bg-gradient-to-br from-lime-500/45 to-lime-300/25 shadow-[0_0_14px_rgba(163,230,53,0.4)]"
        : "text-emerald-100 bg-gradient-to-br from-emerald-800/50 to-emerald-500/20 shadow-[0_0_12px_rgba(16,185,129,0.28)]",
    火:
      yinYang === "阳"
        ? "text-orange-50 bg-gradient-to-br from-orange-500/50 to-red-400/25 shadow-[0_0_14px_rgba(249,115,22,0.45)]"
        : "text-pink-100 bg-gradient-to-br from-rose-800/45 to-rose-500/20 shadow-[0_0_12px_rgba(244,63,94,0.28)]",
    土:
      yinYang === "阳"
        ? "text-amber-50 bg-gradient-to-br from-amber-500/45 to-yellow-300/25 shadow-[0_0_14px_rgba(245,158,11,0.4)]"
        : "text-orange-100 bg-gradient-to-br from-amber-800/45 to-amber-500/20 shadow-[0_0_12px_rgba(251,191,36,0.25)]",
    金:
      yinYang === "阳"
        ? "text-slate-100 bg-gradient-to-br from-slate-200/35 to-zinc-300/15 shadow-[0_0_14px_rgba(226,232,240,0.42)]"
        : "text-zinc-200 bg-gradient-to-br from-zinc-700/45 to-zinc-500/20 shadow-[0_0_12px_rgba(212,212,216,0.28)]",
    水:
      yinYang === "阳"
        ? "text-sky-50 bg-gradient-to-br from-sky-500/45 to-cyan-300/20 shadow-[0_0_14px_rgba(56,189,248,0.42)]"
        : "text-cyan-100 bg-gradient-to-br from-cyan-800/45 to-cyan-500/20 shadow-[0_0_12px_rgba(34,211,238,0.26)]",
  };
  return palette[el] || "text-zinc-200 bg-zinc-700/20";
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
    <section className="relative overflow-hidden rounded-2xl border border-violet-500/35 bg-gradient-to-br from-violet-900/20 via-zinc-950/90 to-zinc-900/80 p-4 shadow-[0_0_24px_rgba(124,58,237,0.25)]">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-violet-400/70 to-transparent" />
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-violet-600/30 bg-zinc-900/60 px-2.5 py-2 text-[11px] text-zinc-300">
        <span className="text-zinc-500">出生 </span>
        <span className="text-violet-100">{birthLabel}</span>
        <span className="mx-1.5 text-zinc-600">·</span>
        <span className="text-zinc-500">性别 </span>
        <span className="text-violet-100">{genderLabel}</span>
        <span className="mx-1.5 text-zinc-600">·</span>
        <span className="text-zinc-500">历法 </span>
        <span className="text-violet-100">{calendarLabel}</span>
      </div>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-semibold tracking-wide text-violet-100">命局六柱</p>
        <p className="text-[11px] text-violet-200/80">仅展示 NDJSON 快照中的服务端结果</p>
        <label className="inline-flex items-center gap-2 text-xs text-zinc-300">
          <span>年份</span>
          <select
            value={selectedYear}
            onChange={(e) => onYearChange(Number(e.target.value))}
            className="rounded border border-violet-500/40 bg-zinc-900 px-2 py-1.5 text-xs text-zinc-100 transition-colors hover:border-violet-300/60"
          >
            {yearChoices.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-6">
        {rows.map((row) => {
          const stemMeta = STEM_META[row.pillar.stem] || { element: "土", yinYang: "阳" as const };
          const branchMeta = BRANCH_META[row.pillar.branch] || { element: "土", yinYang: "阳" as const };
          const stemColor = colorForElement(stemMeta.element, stemMeta.yinYang);
          const branchColor = colorForElement(branchMeta.element, branchMeta.yinYang);
          return (
            <div
              key={row.label}
              className="group rounded-xl border border-zinc-700/35 bg-zinc-900/45 p-2.5 text-center transition duration-150 hover:border-violet-400/70"
            >
              <p className="mb-2 text-[10px] font-semibold tracking-wide text-zinc-300">{row.label}</p>
              <div className="flex flex-col items-stretch gap-1.5">
                <div className={`rounded-md px-2 py-1.5 text-center text-lg font-bold ${stemColor}`}>
                  <span className="block text-[10px] font-semibold tracking-wide text-zinc-200/85">天干</span>
                  <span className="leading-none">{row.pillar.stem || "—"}</span>
                </div>
                <div className={`rounded-md px-2 py-1.5 text-center text-lg font-bold ${branchColor}`}>
                  <span className="block text-[10px] font-semibold tracking-wide text-zinc-200/85">地支</span>
                  <span className="leading-none">{row.pillar.branch || "—"}</span>
                </div>
              </div>
              <div className="mt-2 text-[10px] text-zinc-400">
                {row.pillar.stem && row.pillar.branch ? (
                  <>
                    <span className="font-medium text-zinc-200">{row.pillar.stem + row.pillar.branch}</span>
                    <span className="ml-1 text-zinc-500">·</span>
                    <span className="ml-1 text-violet-200">
                      {stemMeta.element}-{branchMeta.element}
                    </span>
                  </>
                ) : (
                  <span>待重算</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-3 rounded-lg border border-violet-500/30 bg-zinc-950/55 p-2 text-xs text-zinc-400">
        <p className="text-violet-200/90">提示</p>
        <p className="mt-1 text-zinc-400">六柱在切换流年后会同步重算大运和流年柱，以保证命盘时态一致。</p>
      </div>
    </section>
  );
}
