import type { Lang } from "@/types/bazi";

const STEMS: Record<string, Record<Lang, string>> = {
  甲: { ZH: "甲", EN: "Jia", KO: "갑" },
  乙: { ZH: "乙", EN: "Yi", KO: "을" },
  丙: { ZH: "丙", EN: "Bing", KO: "병" },
  丁: { ZH: "丁", EN: "Ding", KO: "정" },
  戊: { ZH: "戊", EN: "Wu", KO: "무" },
  己: { ZH: "己", EN: "Ji", KO: "기" },
  庚: { ZH: "庚", EN: "Geng", KO: "경" },
  辛: { ZH: "辛", EN: "Xin", KO: "신" },
  壬: { ZH: "壬", EN: "Ren", KO: "임" },
  癸: { ZH: "癸", EN: "Gui", KO: "계" },
};

const BRANCHES: Record<string, Record<Lang, string>> = {
  子: { ZH: "子", EN: "Zi", KO: "자" },
  丑: { ZH: "丑", EN: "Chou", KO: "축" },
  寅: { ZH: "寅", EN: "Yin", KO: "인" },
  卯: { ZH: "卯", EN: "Mao", KO: "묘" },
  辰: { ZH: "辰", EN: "Chen", KO: "진" },
  巳: { ZH: "巳", EN: "Si", KO: "사" },
  午: { ZH: "午", EN: "Wu", KO: "오" },
  未: { ZH: "未", EN: "Wei", KO: "미" },
  申: { ZH: "申", EN: "Shen", KO: "신" },
  酉: { ZH: "酉", EN: "You", KO: "유" },
  戌: { ZH: "戌", EN: "Xu", KO: "술" },
  亥: { ZH: "亥", EN: "Hai", KO: "해" },
};

const TEN_GODS: Record<string, Record<Lang, string>> = {
  比肩: { ZH: "比肩", EN: "Friend", KO: "비견" },
  劫财: { ZH: "劫财", EN: "Jie Cai (Rival Wealth)", KO: "겁재" },
  食神: { ZH: "食神", EN: "Shi Shen (Eating God)", KO: "식신" },
  伤官: { ZH: "伤官", EN: "Shang Guan (Hurting Officer)", KO: "상관" },
  偏财: { ZH: "偏财", EN: "Pian Cai (Indirect Wealth)", KO: "편재" },
  正财: { ZH: "正财", EN: "Zheng Cai (Direct Wealth)", KO: "정재" },
  七杀: { ZH: "七杀", EN: "Qi Sha (Seven Killings)", KO: "칠살" },
  正官: { ZH: "正官", EN: "Zheng Guan (Direct Officer)", KO: "정관" },
  偏印: { ZH: "偏印", EN: "Pian Yin (Indirect Resource)", KO: "편인" },
  正印: { ZH: "正印", EN: "Zheng Yin (Direct Resource)", KO: "정인" },
};

const FIVE_ELEMENTS: Record<string, Record<Lang, string>> = {
  木: { ZH: "木", EN: "Wood", KO: "목" },
  火: { ZH: "火", EN: "Fire", KO: "화" },
  土: { ZH: "土", EN: "Earth", KO: "토" },
  金: { ZH: "金", EN: "Metal", KO: "금" },
  水: { ZH: "水", EN: "Water", KO: "수" },
};

export function mapStem(x: string, lang: Lang): string {
  return STEMS[x]?.[lang] ?? x;
}

export function mapBranch(x: string, lang: Lang): string {
  return BRANCHES[x]?.[lang] ?? x;
}

export function mapGanZhi(gz: string, lang: Lang): string {
  if (!gz || gz.length < 2) return gz;
  return `${mapStem(gz[0], lang)} ${mapBranch(gz[1], lang)}`;
}

export function mapConflictDetail(detail: string, lang: Lang): string {
  let out = detail;
  if (lang !== "ZH") {
    out = out.replace(/([子丑寅卯辰巳午未申酉戌亥])([子丑寅卯辰巳午未申酉戌亥])(冲|合|刑|害|破|穿)/g, (_, a: string, b: string, rel: string) => {
      const relEn: Record<string, string> = {
        冲: "Clash",
        合: "Combine",
        刑: "Punishment",
        害: "Harm",
        破: "Destruction",
        穿: "Pierce",
      };
      const relKo: Record<string, string> = { 冲: "충", 合: "합", 刑: "형", 害: "해", 破: "파", 穿: "관통" };
      if (lang === "EN") return `${mapBranch(a, lang)}-${mapBranch(b, lang)} ${relEn[rel] ?? rel}`;
      return `${mapBranch(a, lang)}${mapBranch(b, lang)} ${relKo[rel] ?? rel}`;
    });
  }
  // 十神与五行术语硬映射替换
  for (const [k, v] of Object.entries(TEN_GODS)) {
    out = out.replaceAll(k, v[lang]);
  }
  for (const [k, v] of Object.entries(FIVE_ELEMENTS)) {
    out = out.replaceAll(k, v[lang]);
  }
  return out;
}

const STEM_ELEMENT: Record<string, "wood" | "fire" | "earth" | "metal" | "water"> = {
  甲: "wood", 乙: "wood", 丙: "fire", 丁: "fire", 戊: "earth",
  己: "earth", 庚: "metal", 辛: "metal", 壬: "water", 癸: "water",
};
const BRANCH_ELEMENT: Record<string, "wood" | "fire" | "earth" | "metal" | "water"> = {
  子: "water", 丑: "earth", 寅: "wood", 卯: "wood", 辰: "earth", 巳: "fire",
  午: "fire", 未: "earth", 申: "metal", 酉: "metal", 戌: "earth", 亥: "water",
};

export function detectElementFromText(text: string): "wood" | "fire" | "earth" | "metal" | "water" | null {
  for (const ch of text) {
    if (STEM_ELEMENT[ch]) return STEM_ELEMENT[ch];
    if (BRANCH_ELEMENT[ch]) return BRANCH_ELEMENT[ch];
  }
  return null;
}

export function elementColorClass(element: ReturnType<typeof detectElementFromText>): string {
  switch (element) {
    case "wood":
      return "bg-emerald-400";
    case "fire":
      return "bg-rose-400";
    case "earth":
      return "bg-amber-300";
    case "metal":
      return "bg-slate-300";
    case "water":
      return "bg-sky-400";
    default:
      return "bg-zinc-500";
  }
}
