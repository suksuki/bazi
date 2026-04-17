/**
 * 终审判词正文流式写入：可与物理骨架的 ### 标题语义对齐，剥离 LLM 重复的标题前缀后流式拼接。
 */

const H3_LINE = /^###\s*(.+)$/;

/** 去掉首尾空白、折叠空白，并剥除末尾括号后缀如 (物理预判)（预判） */
export function normalizeH3HeadingCore(line: string): string | null {
  const t = String(line || "").trim();
  const m = t.match(H3_LINE);
  if (!m) return null;
  let core = String(m[1] || "").trim().replace(/\s+/g, " ");
  for (let i = 0; i < 6; i += 1) {
    const next = core
      .replace(/\s*[\(（][^)）]{0,120}[)）]\s*$/u, "")
      .replace(/\s+/g, " ")
      .trim();
    if (next === core) break;
    core = next;
  }
  return core;
}

/** 文档开头连续的 ### 行（中间允许空行），遇首个有内容的非 ### 行即停 */
export function extractLeadingH3Lines(md: string): string[] {
  const lines = String(md || "").split("\n");
  const out: string[] = [];
  let seenH3 = false;
  for (const raw of lines) {
    const t = raw.trimEnd();
    if (!t.trim()) {
      if (seenH3) continue;
      continue;
    }
    const trimmed = t.trim();
    if (H3_LINE.test(trimmed)) {
      seenH3 = true;
      out.push(trimmed);
      continue;
    }
    if (seenH3) break;
  }
  return out;
}

/** 提取全文内所有 ### 行（旧行为：用于回退） */
export function extractMarkdownH3Lines(md: string): string {
  const lines = String(md || "").split("\n");
  return lines
    .map((l) => l.trimEnd())
    .filter((l) => /^###\s/.test(l.trim()))
    .join("\n");
}

/**
 * 若 LLM 正文开头的 ### 标题与骨架对应标题语义一致，则剥除 LLM 侧重复标题，
 * 并以骨架中的 ### 原文作为前缀（平滑覆盖，避免字符微差阻塞）。
 */
export function stripLeadingH3PrefixIfRedundant(skeleton: string, full: string): { prefix: string; rest: string } {
  const body = String(full || "");
  const skLead = extractLeadingH3Lines(skeleton);
  const fbLead = extractLeadingH3Lines(body);
  if (!skLead.length || !fbLead.length) {
    const heads = extractMarkdownH3Lines(skeleton).trim();
    if (heads && body.startsWith(heads)) {
      const rest = body.slice(heads.length).replace(/^\n+/, "");
      return { prefix: heads, rest };
    }
    return { prefix: "", rest: body };
  }

  let k = 0;
  const max = Math.min(skLead.length, fbLead.length);
  for (; k < max; k += 1) {
    const a = normalizeH3HeadingCore(skLead[k]);
    const b = normalizeH3HeadingCore(fbLead[k]);
    if (!a || !b || a !== b) break;
  }
  if (k === 0) {
    const heads = extractMarkdownH3Lines(skeleton).trim();
    if (heads && body.startsWith(heads)) {
      const rest = body.slice(heads.length).replace(/^\n+/, "");
      return { prefix: heads, rest };
    }
    return { prefix: "", rest: body };
  }

  const prefix = skLead.slice(0, k).join("\n");
  const rest = stripLeadingKH3BlockLines(body, k);
  return { prefix, rest };
}

/** 从 full 开头剥掉前 k 个 ### 标题行（语义对齐后），保留其后正文 */
function stripLeadingKH3BlockLines(full: string, k: number): string {
  const lines = String(full || "").split("\n");
  let removed = 0;
  let i = 0;
  while (i < lines.length && removed < k) {
    const t = lines[i].trimEnd();
    if (!t.trim()) {
      i += 1;
      continue;
    }
    const tr = t.trim();
    if (H3_LINE.test(tr)) {
      removed += 1;
      i += 1;
      continue;
    }
    break;
  }
  while (i < lines.length && !lines[i].trim()) i += 1;
  return lines.slice(i).join("\n").replace(/^\n+/, "");
}

/** 从任意文本中提取 `<!--qiazhi-fingerprint:v1 ...-->`（与后端 append_verdict_fingerprint_html_comment 对齐） */
/**
 * 终判正文容错：若状态里误存了整段 JSON，则尽量剥出 `verdict_body` 的 Markdown 正文，避免 UI 空白。
 * 顺序：去 code fence → JSON.parse → 正则抠带转义字符串。
 */
export function coerceVerdictDisplayBody(raw: string): string {
  let s = String(raw || "").trim();
  if (!s) return "";
  const fence = /^```(?:json)?\s*([\s\S]*?)\s*```$/im.exec(s);
  if (fence) s = String(fence[1] || "").trim();
  const looksJson = s.startsWith("{") || s.startsWith("[") || /"verdict_body"\s*:/.test(s);
  if (looksJson) {
    try {
      const o = JSON.parse(s) as { verdict_body?: unknown };
      if (o && typeof o === "object" && !Array.isArray(o) && typeof o.verdict_body === "string" && o.verdict_body.trim()) {
        return o.verdict_body.trim();
      }
    } catch {
      /* 继续尝试正则 */
    }
    const m = /"verdict_body"\s*:\s*"((?:[^"\\]|\\.)*)"/.exec(s);
    if (m) {
      try {
        return JSON.parse(`"${m[1]}"`) as string;
      } catch {
        return m[1]
          .replace(/\\n/g, "\n")
          .replace(/\\r/g, "\r")
          .replace(/\\t/g, "\t")
          .replace(/\\"/g, '"')
          .replace(/\\\\/g, "\\");
      }
    }
  }
  return String(raw || "").trim();
}

export function extractQiazhiVerdictFingerprintComment(source: string): string | null {
  const s = String(source || "");
  const start = s.indexOf("<!--qiazhi-fingerprint:v1");
  if (start < 0) return null;
  const end = s.indexOf("-->", start + 8);
  if (end < 0) return null;
  return s.slice(start, end + 3).trim();
}

/** 若正文尚无指纹注释，则在末尾追加（供 DOM 隐藏节点注入） */
export function ensureVerdictFingerprintSuffix(body: string, fp: string | null): string {
  const b = String(body || "");
  if (!fp || !b.trim()) return b;
  if (extractQiazhiVerdictFingerprintComment(b)) return b;
  return `${b.trimEnd()}\n\n${fp}\n`;
}

export async function streamVerdictBodyIntoState(
  setBody: (v: string) => void,
  full: string,
  opts?: {
    skeletonForHeadingAlign?: string | null;
    chunkSize?: number;
    tickMs?: number;
    labelMorphMs?: number;
  },
) {
  const chunkSize = opts?.chunkSize ?? 4;
  const tickMs = opts?.tickMs ?? 11;
  const labelMorphMs = opts?.labelMorphMs ?? 120;
  const sk = (opts?.skeletonForHeadingAlign || "").trim();
  const raw = String(full || "");
  const { prefix, rest } = sk ? stripLeadingH3PrefixIfRedundant(sk, raw) : { prefix: "", rest: raw };

  const compose = (r: string) => (prefix ? `${prefix}\n${r}` : r);

  if (!prefix && !rest) {
    setBody("");
    return;
  }

  if (prefix) {
    setBody(`${prefix}\n`);
    await new Promise((r) => setTimeout(r, labelMorphMs));
  }

  if (!rest) {
    setBody(compose(""));
    return;
  }

  for (let i = chunkSize; i <= rest.length + chunkSize; i += chunkSize) {
    setBody(compose(rest.slice(0, Math.min(i, rest.length))));
    await new Promise((r) => setTimeout(r, tickMs));
  }
  setBody(compose(rest));
}
