import type {
  MingliFocus,
  MingliFocusedPassRecord,
  MingliFocusedPassResult,
  MingliReadingSummaryProjection,
} from "./mingliStageTypes";

export const PUBLIC_READING_TOPICS = [
  { focus: "STRUCTURE", label: "总纲", hint: "先看命局主线" },
  { focus: "LIFE_IMAGE_PERSONALITY", label: "性情", hint: "气质与行事方式" },
  { focus: "CAREER_WEALTH", label: "事业财富", hint: "发力与交换方式" },
  { focus: "RELATIONSHIP_FAMILY", label: "感情家庭", hint: "关系中的互动主题" },
  { focus: "TIMING", label: "近年趋势", hint: "当前大运与流年" },
] as const satisfies ReadonlyArray<{
  focus: MingliFocus;
  label: string;
  hint: string;
}>;

export interface PublicReadingCopy {
  lead: string;
  paragraphs: string[];
  evidence: string[];
  source: "FOCUSED_MODEL" | "DETERMINISTIC_BASE";
}

const PUBLIC_SAFE_NORMALIZATION_CODES = new Set([
  "ABSOLUTE_TONE_SOFTENED",
  "EVIDENCE_TOKEN_REMOVED",
  "MARKDOWN_FENCE_REMOVED",
  "MARKDOWN_PRESENTATION_REMOVED",
  "TIMING_SCOPE_PHRASE_REMOVED",
  "VISIBLE_TEN_GOD_COORDINATE_REPAIRED",
]);

export function focusedPass(
  summary: MingliReadingSummaryProjection,
  focus: MingliFocus,
): MingliFocusedPassResult | null {
  const record = focusedPassRecord(summary, focus);
  if (record) return record.pass_result;
  return summary.focused_reading?.passes.find((item) => item.focus === focus) ?? null;
}

export function focusedPassRecord(
  summary: MingliReadingSummaryProjection,
  focus: MingliFocus,
): MingliFocusedPassRecord | null {
  return summary.focused_pass_records.find((item) => item.focus === focus) ?? null;
}

export function publicFocusedPassRecord(
  summary: MingliReadingSummaryProjection,
  focus: MingliFocus,
): MingliFocusedPassRecord | null {
  const record = focusedPassRecord(summary, focus);
  return record && isPublicPassSafe(record.pass_result) ? record : null;
}

export function isPublicPassSafe(pass: MingliFocusedPassResult): boolean {
  return pass.normalization_codes.every((code) => PUBLIC_SAFE_NORMALIZATION_CODES.has(code));
}

export function publicReadingCopy(
  summary: MingliReadingSummaryProjection,
  focus: MingliFocus,
): PublicReadingCopy {
  const record = publicFocusedPassRecord(summary, focus);
  const legacyPass = summary.focused_reading?.passes.find((item) => item.focus === focus) ?? null;
  const pass = record?.pass_result ?? (
    legacyPass && isPublicPassSafe(legacyPass) ? legacyPass : null
  );
  if (pass) {
    const blocks = readableBlocks(pass.normalized_text);
    return {
      lead: blocks[0] ?? "阿布还在整理这部分的判断。",
      paragraphs: blocks.slice(1),
      evidence: deterministicEvidence(summary, focus),
      source: "FOCUSED_MODEL",
    };
  }

  const fallback = deterministicFallback(summary, focus);
  return {
    lead: fallback[0] ?? summary.reading_brief.headline,
    paragraphs: fallback.slice(1),
    evidence: deterministicEvidence(summary, focus),
    source: "DETERMINISTIC_BASE",
  };
}

export function readableBlocks(value: string): string[] {
  const cleaned = value
    .replace(/^\s{0,3}#{1,6}\s*/gm, "")
    .replace(/\*\*|__|`/g, "")
    .replace(/^\s*[-*+]\s+/gm, "")
    .replace(/^\s*\d+[.)、]\s+/gm, "")
    .replace(/[ \t]+/g, " ")
    .trim();
  if (!cleaned) return [];

  const explicit = cleaned
    .split(/\n{2,}/)
    .map((item) => item.replace(/\n+/g, " ").trim())
    .filter(Boolean);
  const sentences = explicit.flatMap((block) => {
    if (block.length <= 150) return [block];
    return block.match(/[^。！？；]+[。！？；]?/g)?.map((item) => item.trim()) ?? [block];
  });

  const grouped: string[] = [];
  for (const sentence of sentences) {
    const previous = grouped.at(-1);
    if (previous && previous.length + sentence.length <= 150) {
      grouped[grouped.length - 1] = `${previous}${sentence}`;
    } else {
      grouped.push(sentence);
    }
  }
  return grouped;
}

function deterministicFallback(
  summary: MingliReadingSummaryProjection,
  focus: MingliFocus,
): string[] {
  const brief = summary.reading_brief;
  if (focus === "STRUCTURE") {
    return [
      brief.headline,
      "四柱已经由本地历法确定。总纲会同时比较月令、根气、印比、泄耗与财官压力，不会拿一个符号代替整盘。",
      "当前先给出命盘底稿；这一项细断完成后会自动替换，不需要反复点击。",
    ];
  }
  if (focus === "LIFE_IMAGE_PERSONALITY") {
    const dayMaster = dayMasterFromBrief(brief.headline);
    const image = dayMaster ? DAY_MASTER_IMAGES[dayMaster] : null;
    return image
      ? [
          `${dayMaster}日主的基础意象，更接近${image.title}。`,
          image.copy,
          "性情细断还会回到整盘承载与制化条件；这里先不凭日主一个字给人贴标签。",
        ]
      : [
          "性情不是由一个符号决定的。",
          "当前先保留日主意象，等这一项细断把月令、根气与整盘承载合在一起再下判断。",
        ];
  }
  if (focus === "CAREER_WEALTH") {
    return [
      "事业与财富要看资源怎样被承载、输出和交换。",
      "这一项会分别说明适合怎样发力、财富怎样形成，以及什么条件最容易让路径受阻；不会直接列行业或承诺收益。",
    ];
  }
  if (focus === "RELATIONSHIP_FAMILY") {
    return [
      "关系与家庭要把互动方式和责任模式分开看。",
      "这一项会同时参考对应星轴与日支，不用单一十神推断伴侣性格，也不编造已经发生的经历。",
    ];
  }
  const coordinates = brief.timing.coordinates
    .slice(0, 3)
    .map((item) => `${item.layer} ${item.pillar}（${item.ten_god_label}）`)
    .join("、");
  return [
    "近年趋势会先守住原局基线，再看大运与流年怎样推动或阻断原有路径。",
    coordinates ? `当前已经定位的时间坐标：${coordinates}。` : "时间坐标正在整理。",
  ];
}

const DAY_MASTER_IMAGES: Record<string, { title: string; copy: string }> = {
  甲: { title: "向上生长的乔木", copy: "重方向与骨架，通常更愿意先立住原则再推进；能否舒展仍取决于根、水与环境。" },
  乙: { title: "顺势攀援的花木", copy: "细腻、会观察环境，也擅长借支点生长；柔韧不等于软弱，关键在有没有稳定根基。" },
  丙: { title: "照向四方的太阳", copy: "重清晰、表达与带动感；光能否持续，要看整盘有没有足够承载与调节。" },
  丁: { title: "需要守护的灯火", copy: "感受细、注意力集中，常在具体处照亮别人；稳定与否要看燃料、风势和依托。" },
  戊: { title: "承载万物的高地", copy: "重稳定、边界与担当；厚重是优势，是否迟滞仍要结合全盘流通来看。" },
  己: { title: "能培育作物的田园", copy: "重实际、照料与整合细节；包容能否变成成果，要看水木与节律是否合宜。" },
  庚: { title: "需要锻造的矿石", copy: "行动直接，重效率和规则；锋利能否成为能力，要看火炼与水润是否得当。" },
  辛: { title: "经过琢磨的珠玉", copy: "辨别力细，重品质与分寸；敏锐能否稳定发挥，要看环境是否清润有序。" },
  壬: { title: "汇流而行的江海", copy: "视野宽、流动快，善于连接不同信息；力量能否聚焦，要看河道与落点。" },
  癸: { title: "润物无声的雨露", copy: "感知细、适应强，常从微小处渗透推进；是否内耗，要看承接与去向是否清楚。" },
};

function dayMasterFromBrief(headline: string): string | null {
  return headline.match(/([甲乙丙丁戊己庚辛壬癸])(?:日主|日元)/)?.[1] ?? null;
}

function deterministicEvidence(
  summary: MingliReadingSummaryProjection,
  focus: MingliFocus,
): string[] {
  const brief = summary.reading_brief;
  if (focus === "TIMING") {
    return brief.timing.coordinates.slice(0, 4).map(
      (item) => `${item.layer}：${item.pillar} · ${item.ten_god_label}`,
    );
  }
  const confirmed = brief.confirmed.slice(0, 3);
  if (focus !== "STRUCTURE" && brief.focus.rationale) {
    return [brief.focus.rationale, ...confirmed].slice(0, 4);
  }
  return confirmed;
}
