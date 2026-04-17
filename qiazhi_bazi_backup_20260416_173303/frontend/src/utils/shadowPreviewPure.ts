import type { Lang } from "@/types/bazi";

/**
 * 与 `energyFlowPreviewHeal.ts` 无交叉引用；本文件仅含字符串纯变换，便于 Vitest 与多语言插值回归。
 * `shadowPreviewI18n.ts` 负责注入 `STATIC_I18N` 表后再调用此处 API。
 */

export type StaticI18nSlice = Readonly<Record<string, string>>;
export type StaticI18nTable = Partial<Record<Lang, StaticI18nSlice>>;

/** 纯函数：仅替换 `{name}` 占位符，不读全局、不改入参对象 */
export function interpolateNamedPlaceholders(
  template: string,
  params?: Readonly<Record<string, string>>,
): string {
  if (!params) return template;
  let s = template;
  for (const [k, v] of Object.entries(params)) {
    s = s.split(`{${k}}`).join(v);
  }
  return s;
}

/** 纯函数：模板键 → 本地化基串（无占位符阶段），缺省回退 `templateKey` 本身 */
export function resolveTemplateBaseString(table: StaticI18nTable, lang: Lang, templateKey: string): string {
  return table[lang]?.[templateKey] ?? table.ZH?.[templateKey] ?? templateKey;
}

/** 纯函数：整句（常以中文为 key）在当前语言表中的映射 */
export function lookupLocalizedPhrase(table: StaticI18nTable, lang: Lang, phrase: string): string {
  const t = String(phrase || "").trim();
  if (!t) return "";
  return table[lang]?.[t] ?? t;
}
