import type { AppLanguage } from "@/lib/i18n";

type Copy = Record<AppLanguage, string>;

const ERROR_COPY: Record<string, Copy> = {
  RULE_SCOPE_VIOLATION: {
    zh: "这个问题目前不在系统的可验证规则范围内。你可以改问财运趋势、收入稳定性，或财富机会与风险。",
    en: "This question is outside the current verifiable rule scope. Try asking about wealth trends, income stability, or financial risk and opportunity.",
    ko: "이 질문은 현재 검증 가능한 규칙 범위 밖에 있습니다. 재물 흐름, 수입 안정성, 기회와 리스크에 대해 질문해 주세요.",
  },
  CONTRACT_SCHEMA_INVALID: {
    zh: "这次请求缺少必要信息。请补齐问题和出生信息后再试。",
    en: "Some required information is missing. Please complete the question and birth details, then try again.",
    ko: "필수 정보가 부족합니다. 질문과 출생 정보를 보완한 뒤 다시 시도해 주세요.",
  },
  LEDGER_NOT_FOUND: {
    zh: "没有找到这条预测记录。请确认链接是否完整，或重新生成一次预测。",
    en: "This prediction record was not found. Check the link or generate a new prediction.",
    ko: "이 예측 기록을 찾을 수 없습니다. 링크를 확인하거나 새 예측을 생성해 주세요.",
  },
  RATE_LIMITED: {
    zh: "请求有点太频繁了。请稍等一下再试。",
    en: "Too many requests in a short time. Please wait a moment and try again.",
    ko: "짧은 시간에 요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.",
  },
  VERIFIER_BLOCKED: {
    zh: "系统校验没有通过，所以这次不会展示预测结果。请换一个财富相关问题再试。",
    en: "The verifier did not approve this output, so no prediction is shown. Please try a wealth-related question.",
    ko: "검증을 통과하지 못해 이번 예측 결과는 표시하지 않습니다. 재물 관련 질문으로 다시 시도해 주세요.",
  },
  DUPLICATE_FEEDBACK: {
    zh: "这条反馈已经记录过了。谢谢，你的反馈会进入学习信号。",
    en: "This feedback has already been recorded. Thank you; it will be used as a learning signal.",
    ko: "이 피드백은 이미 기록되었습니다. 감사합니다. 학습 신호로 반영됩니다.",
  },
  FEEDBACK_LOCKED: {
    zh: "这条记录当前不能重复写入。你可以刷新后查看最新状态。",
    en: "This record cannot be written again right now. Refresh to view the latest state.",
    ko: "이 기록은 지금 중복 저장할 수 없습니다. 새로고침 후 최신 상태를 확인해 주세요.",
  },
  LOCK_BUSY: {
    zh: "系统正在处理同一条记录。请稍等片刻再试。",
    en: "The system is already processing this record. Please try again shortly.",
    ko: "시스템이 같은 기록을 처리 중입니다. 잠시 후 다시 시도해 주세요.",
  },
  ADMIN_REQUIRED: {
    zh: "这个操作需要管理员权限。",
    en: "This action requires admin permission.",
    ko: "이 작업에는 관리자 권한이 필요합니다.",
  },
  NETWORK_ERROR: {
    zh: "网络连接暂时不可用。请稍后重试。",
    en: "The network connection is temporarily unavailable. Please try again later.",
    ko: "네트워크 연결이 일시적으로 불안정합니다. 잠시 후 다시 시도해 주세요.",
  },
  DEFAULT: {
    zh: "系统暂时无法完成这次请求。请稍后重试，或换一个财富相关问题。",
    en: "The system could not complete this request right now. Please try again later, or ask a wealth-related question.",
    ko: "현재 요청을 완료할 수 없습니다. 잠시 후 다시 시도하거나 재물 관련 질문으로 바꿔 주세요.",
  },
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === "object" && !Array.isArray(value));
}

function unwrapEnvelope(value: unknown): Record<string, unknown> {
  if (isRecord(value) && isRecord(value.data)) return value.data;
  return isRecord(value) ? value : {};
}

function readString(source: unknown, keys: string[]): string {
  if (!isRecord(source)) return "";
  for (const key of keys) {
    const value = source[key];
    if (typeof value === "string" && value.trim()) return value.trim();
  }
  return "";
}

function copyFor(code: string, language: AppLanguage, fallback: string): string {
  const normalized = code.trim().toUpperCase();
  return ERROR_COPY[normalized]?.[language] || ERROR_COPY.DEFAULT[language] || fallback;
}

function codeFromText(value: string): string {
  const text = value.toUpperCase();
  for (const code of Object.keys(ERROR_COPY)) {
    if (code !== "DEFAULT" && text.includes(code)) return code;
  }
  if (text.includes("FAILED TO FETCH") || text.includes("NETWORK") || text.includes("NON-JSON")) return "NETWORK_ERROR";
  return "";
}

export function userFacingApiMessage(
  value: unknown,
  requestError: string | undefined,
  fallback: string,
  language: AppLanguage,
): string {
  const row = isRecord(value) ? value : {};
  const data = unwrapEnvelope(value);
  const explicit = row.user_message || row.userMessage || data.user_message || data.userMessage;
  if (isRecord(explicit)) {
    const localized = readString(explicit, [language]);
    if (localized) return localized;
  }
  const code = readString(row, ["code"]) || readString(data, ["code"]) || codeFromText(String(requestError || ""));
  if (code) return copyFor(code, language, fallback);
  return fallback || ERROR_COPY.DEFAULT[language];
}

export function userFacingExceptionMessage(error: unknown, fallback: string, language: AppLanguage): string {
  const message = error instanceof Error ? error.message : String(error || "");
  const code = codeFromText(message);
  if (code) return copyFor(code, language, fallback);
  if (!message || message.length > 180) return fallback || ERROR_COPY.DEFAULT[language];
  return message;
}
