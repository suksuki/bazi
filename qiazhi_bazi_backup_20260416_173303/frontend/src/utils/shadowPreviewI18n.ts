import { STATIC_I18N } from "@/constants/locales";
import type { Lang } from "@/types/bazi";
import { interpolateNamedPlaceholders, lookupLocalizedPhrase, resolveTemplateBaseString } from "@/utils/shadowPreviewPure";

/** 将 {key} 占位符替换为 params[key]（表数据由调用方固定为 STATIC_I18N，纯变换在 shadowPreviewPure） */
export function formatShadowPreviewTemplate(
  lang: Lang,
  templateKey: string,
  params: Record<string, string> | undefined,
): string {
  const base = resolveTemplateBaseString(STATIC_I18N, lang, templateKey);
  return interpolateNamedPlaceholders(base, params);
}

type PatternAlertI18n =
  | { template: string; params?: Record<string, string>; parts?: undefined }
  | { parts: Array<{ template: string; params?: Record<string, string> }>; template?: undefined }
  | null
  | undefined;

/** 格局预警：优先 i18n 模板 / 多段 parts，否则按当前语言查表整句，再退回原文 */
export function resolveShadowPreviewPatternAlert(
  lang: Lang,
  fallbackZh: string,
  i18n: PatternAlertI18n,
): string {
  if (i18n && "template" in i18n && i18n.template) {
    return formatShadowPreviewTemplate(lang, i18n.template, i18n.params || {});
  }
  if (i18n && "parts" in i18n && Array.isArray(i18n.parts) && i18n.parts.length) {
    return i18n.parts.map((p) => formatShadowPreviewTemplate(lang, p.template, p.params || {})).join("");
  }
  const trimmed = String(fallbackZh || "").trim();
  if (!trimmed) return "";
  return lookupLocalizedPhrase(STATIC_I18N, lang, trimmed);
}

/** 单条结构预览 VF 行 */
export function resolveShadowPreviewVfLine(
  lang: Lang,
  lineZh: string,
  i18nTemplate: string | undefined,
  i18nParams: Record<string, string> | undefined,
): string {
  if (i18nTemplate) {
    return formatShadowPreviewTemplate(lang, i18nTemplate, i18nParams || {});
  }
  const t = String(lineZh || "").trim();
  if (!t) return "";
  return lookupLocalizedPhrase(STATIC_I18N, lang, t);
}
