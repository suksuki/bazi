"use client";

import { useState } from "react";
import { BriefcaseBusiness, ChevronDown, FileSearch, Sparkles } from "lucide-react";

import { jsonPostInit, requestJson } from "@/lib/apiClient";
import type { AppLanguage } from "@/lib/i18n";

type LocalizeText = (zh: string, en: string, ko: string) => string;
type TranslateText = (value: string) => string;
type WealthPreviewMode = "llm" | "contract" | "";

function asLooseRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

function asNumberValue(value: unknown, fallback = 0): number {
  const next = Number(value);
  return Number.isFinite(next) ? next : fallback;
}

function asStringList(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => String(item || "").trim()).filter(Boolean) : [];
}

function percentLabel(value: unknown): string {
  const raw = asNumberValue(value);
  const normalized = raw <= 1 ? raw * 100 : raw;
  return `${Math.round(normalized)}%`;
}

function localizedWealthStance(value: unknown, ui: LocalizeText): string {
  const key = String(value || "").trim();
  if (key === "active") return ui("活跃", "Active", "활성");
  if (key === "volatile") return ui("波动", "Volatile", "변동");
  if (key === "watch") return ui("观察", "Watch", "관찰");
  if (key === "latent") return ui("潜伏", "Latent", "잠재");
  return ui("未定", "Pending", "미정");
}

function localizedWealthUsableState(value: unknown, ui: LocalizeText): string {
  const key = String(value || "").trim();
  if (key === "wealth_as_use") return ui("顺侧可用", "Usable", "사용 가능");
  if (key === "wealth_as_taboo") return ui("忌侧承压", "Pressure", "압박");
  if (key === "wealth_needs_bridge") return ui("需要桥接", "Needs bridge", "연결 필요");
  return ui("待观察", "Watch", "관찰");
}

function localizedWealthVisibility(value: unknown, ui: LocalizeText): string {
  const key = String(value || "").trim();
  if (key === "explicit_wealth") return ui("显性财富", "Explicit", "명시 재물");
  if (key === "hidden_wealth") return ui("暗线财富", "Hidden", "숨은 재물");
  if (key === "indirect_wealth") return ui("间接财富", "Indirect", "간접 재물");
  return ui("弱信号", "Weak signal", "약한 신호");
}

function wealthResultReasonLabel(value: unknown, ui: LocalizeText): string {
  const reason = String(value || "").trim();
  if (reason === "execute_llm_disabled") return ui("仅生成合同", "Contract only", "계약만 생성");
  if (reason === "missing_wealth_profile") return ui("缺少财富画像", "Missing profile", "프로필 없음");
  if (reason === "llm_config_incomplete") return ui("模型未配置", "Model not configured", "모델 미설정");
  if (reason === "llm_dispatch_failed") return ui("调用失败", "Dispatch failed", "호출 실패");
  if (reason === "not_dispatched") return ui("未调用", "Not dispatched", "미호출");
  return reason;
}

function shortPreviewTime(value: unknown): string {
  const raw = String(value || "").trim();
  if (!raw) return "";
  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) return raw.slice(0, 16);
  return date.toLocaleString(undefined, {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function V17_WealthAssertionPreviewPanel({
  ui,
  term,
  language,
  sessionId,
  resetKey,
  wealthProfile,
  initialPreview,
  canRequest,
  physicsReady,
}: {
  ui: LocalizeText;
  term: TranslateText;
  language: AppLanguage;
  sessionId: string;
  resetKey: string;
  wealthProfile: Record<string, unknown>;
  initialPreview: Record<string, unknown>;
  canRequest: boolean;
  physicsReady: boolean;
}) {
  const [previewOverride, setPreviewOverride] = useState<{ resetKey: string; preview: Record<string, unknown> } | null>(null);
  const [pendingMode, setPendingMode] = useState<WealthPreviewMode>("");
  const [errorState, setErrorState] = useState<{ resetKey: string; message: string } | null>(null);

  const preview = previewOverride?.resetKey === resetKey ? previewOverride.preview : initialPreview;
  const error = errorState?.resetKey === resetKey ? errorState.message : "";
  const previewProfile = asLooseRecord(preview.wealth_profile);
  const profile = Object.keys(wealthProfile).length ? wealthProfile : previewProfile;
  const channels = Array.isArray(profile.primary_channels)
    ? (profile.primary_channels as Array<unknown>).map(asLooseRecord).filter((row) => String(row.id || row.label || "").trim())
    : [];
  const topChannel = channels[0] || {};
  const strengths = asStringList(profile.strengths).slice(0, 3);
  const risks = asStringList(profile.risks).slice(0, 3);
  const bridgeRequirements = asStringList(profile.bridge_requirements).slice(0, 3);
  const evidence = asStringList(profile.evidence).slice(0, 4);
  const llmResult = asLooseRecord(preview.llm_result);
  const promptContract = asLooseRecord(preview.prompt_contract);
  const reply = String(llmResult.reply || "").trim();
  const promptText = String(preview.prompt_text || "").trim();
  const previewCreatedAt = String(preview.created_at || "").trim();
  const hasProfile = Object.keys(profile).length > 0;
  const hasPreview = Object.keys(preview).length > 0;
  const canSubmit = canRequest && physicsReady && Boolean(sessionId) && !pendingMode;
  const score = percentLabel(profile.score);
  const confidence = percentLabel(profile.confidence);
  const risk = percentLabel(profile.risk);

  async function requestPreview(executeLlm: boolean) {
    if (!canRequest) {
      setErrorState({ resetKey, message: ui("需要管理员权限。", "Admin access required.", "관리자 권한이 필요합니다.") });
      return;
    }
    if (!sessionId || !physicsReady) {
      setErrorState({ resetKey, message: ui("等待命盘快照。", "Waiting for chart snapshot.", "명반 스냅샷 대기 중입니다.") });
      return;
    }
    const mode: WealthPreviewMode = executeLlm ? "llm" : "contract";
    setPendingMode(mode);
    setErrorState(null);
    const { data, ok, error: requestError } = await requestJson<Record<string, unknown>>(
      "/api/v17-admin/topic/wealth-assertion-preview",
      jsonPostInit({
        v17_origin: "v17_rebirth",
        session_id: sessionId,
        ui_lang: language,
        execute_llm: executeLlm,
        persist: true,
      }),
    );
    setPendingMode("");
    const nextPreview = asLooseRecord(data.preview);
    if (!ok || data.ok === false || !Object.keys(nextPreview).length) {
      setErrorState({
        resetKey,
        message: requestError || String(data.detail || "") || ui("财富预览生成失败。", "Failed to create wealth preview.", "재물 미리보기를 만들지 못했습니다."),
      });
      return;
    }
    setPreviewOverride({ resetKey, preview: nextPreview });
  }

  return (
    <section className="rounded-xl border border-emerald-400/18 bg-[linear-gradient(135deg,rgba(6,78,59,0.22),rgba(24,24,27,0.92)_48%,rgba(120,53,15,0.18))] p-4 shadow-[0_18px_60px_rgba(6,78,59,0.12)]">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-emerald-300/20 bg-emerald-400/10 text-emerald-100">
              <BriefcaseBusiness className="h-4 w-4" />
            </span>
            <div>
              <p className="text-[10px] uppercase tracking-[0.22em] text-emerald-300">
                {ui("财富专题", "Wealth Topic", "재물 주제")}
              </p>
              <h3 className="mt-0.5 text-base font-semibold text-zinc-50">
                {ui("财富断言预览", "Wealth Assertion Preview", "재물 단언 미리보기")}
              </h3>
            </div>
          </div>
        </div>
        <div className="flex flex-wrap gap-1.5">
          <span className="rounded-full border border-emerald-300/20 bg-emerald-400/10 px-2 py-1 text-[10px] text-emerald-100">
            {hasProfile ? `${ui("画像", "Profile", "프로필")} ${score}` : ui("画像待定", "Profile pending", "프로필 대기")}
          </span>
          <span className="rounded-full border border-amber-300/20 bg-amber-400/10 px-2 py-1 text-[10px] text-amber-100">
            {hasPreview ? ui("已有审计", "Audited", "감사 있음") : ui("未预览", "No preview", "미리보기 없음")}
          </span>
        </div>
      </div>

      {hasProfile ? (
        <div className="mt-4 grid gap-3 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="space-y-3">
            <div className="flex flex-wrap gap-1.5">
              {[
                `${ui("置信", "Confidence", "신뢰")} ${confidence}`,
                `${ui("风险", "Risk", "위험")} ${risk}`,
                localizedWealthStance(profile.stance, ui),
                localizedWealthUsableState(profile.usable_state, ui),
                localizedWealthVisibility(profile.visibility, ui),
              ].map((item) => (
                <span key={item} className="rounded-full border border-white/10 bg-black/20 px-2 py-1 text-[11px] text-zinc-200">
                  {item}
                </span>
              ))}
            </div>

            {topChannel.id || topChannel.label ? (
              <div>
                <p className="text-[11px] text-zinc-500">{ui("主财富通道", "Primary channel", "주 재물 경로")}</p>
                <p className="mt-1 text-sm font-semibold text-zinc-100">
                  {term(String(topChannel.label || topChannel.id || ""))}
                  <span className="ml-2 text-[11px] font-medium text-emerald-200">{percentLabel(topChannel.score)}</span>
                </p>
              </div>
            ) : null}

            {channels.length ? (
              <div className="space-y-2">
                {channels.slice(0, 3).map((channel) => {
                  const label = term(String(channel.label || channel.id || ""));
                  const width = Math.max(6, Math.min(100, asNumberValue(channel.score) * 100));
                  return (
                    <div key={String(channel.id || label)} className="grid grid-cols-[minmax(0,1fr)_56px] items-center gap-2">
                      <div className="min-w-0">
                        <div className="flex items-center justify-between gap-2 text-[11px] text-zinc-300">
                          <span className="truncate">{label}</span>
                        </div>
                        <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-white/10">
                          <div className="h-full rounded-full bg-emerald-300" style={{ width: `${width}%` }} />
                        </div>
                      </div>
                      <span className="text-right text-[11px] text-emerald-100">{percentLabel(channel.score)}</span>
                    </div>
                  );
                })}
              </div>
            ) : null}
          </div>

          <div className="space-y-3 border-t border-white/10 pt-3 lg:border-l lg:border-t-0 lg:pl-4 lg:pt-0">
            {reply ? (
              <div>
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-amber-200" />
                  <p className="text-[12px] font-semibold text-amber-50">
                    {ui("财富断言", "Wealth assertion", "재물 단언")}
                  </p>
                </div>
                <p className="mt-2 whitespace-pre-line text-sm leading-7 text-zinc-100">{reply}</p>
              </div>
            ) : (
              <div>
                <p className="text-[12px] font-semibold text-zinc-100">
                  {hasPreview
                    ? wealthResultReasonLabel(llmResult.reason, ui)
                    : ui("等待财富预览", "Preview pending", "미리보기 대기")}
                </p>
                <p className="mt-1 text-[12px] leading-5 text-zinc-500">
                  {String(profile.llm_prompt_focus ? asStringList(profile.llm_prompt_focus)[0] : "") ||
                    ui("财富画像已就绪。", "Wealth profile is ready.", "재물 프로필이 준비되었습니다.")}
                </p>
              </div>
            )}

            <div className="grid gap-2 sm:grid-cols-3">
              {[
                { key: "strengths", label: ui("优势", "Strengths", "강점"), values: strengths },
                { key: "bridge", label: ui("承接", "Bridge", "연결"), values: bridgeRequirements },
                { key: "risks", label: ui("风险", "Risks", "위험"), values: risks },
              ].map((group) => (
                <div key={group.key} className="min-w-0">
                  <p className="text-[11px] text-zinc-500">{group.label}</p>
                  <div className="mt-1 space-y-1">
                    {group.values.length ? group.values.map((item) => (
                      <p key={`${group.key}_${item}`} className="line-clamp-2 text-[11px] leading-5 text-zinc-300">
                        {term(item)}
                      </p>
                    )) : (
                      <p className="text-[11px] text-zinc-600">{ui("待定", "Pending", "대기")}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <p className="mt-4 text-[12px] leading-5 text-zinc-500">
          {ui("等待财富画像进入命盘快照。", "Waiting for wealth profile in the chart snapshot.", "명반 스냅샷에 재물 프로필이 들어오기를 기다립니다.")}
        </p>
      )}

      <div className="mt-4 flex flex-col gap-2 border-t border-white/10 pt-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap gap-1.5 text-[10px] text-zinc-500">
          {previewCreatedAt ? (
            <span className="rounded-full border border-white/10 bg-white/[0.035] px-2 py-1">
              {shortPreviewTime(previewCreatedAt)}
            </span>
          ) : null}
          {evidence.slice(0, 2).map((item) => (
            <span key={`wealth_evidence_${item}`} className="max-w-full truncate rounded-full border border-white/10 bg-white/[0.035] px-2 py-1 sm:max-w-[260px]">
              {term(item)}
            </span>
          ))}
        </div>
        <div className="grid grid-cols-2 gap-2 sm:flex sm:justify-end">
          <button
            type="button"
            disabled={!canSubmit}
            onClick={() => void requestPreview(false)}
            className="inline-flex min-h-9 items-center justify-center gap-1.5 rounded-lg border border-zinc-600/50 bg-zinc-900/70 px-3 py-2 text-[12px] font-semibold text-zinc-200 transition hover:border-emerald-300/45 hover:text-emerald-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <FileSearch className="h-3.5 w-3.5" />
            {pendingMode === "contract" ? ui("生成中", "Building", "생성 중") : ui("看合同", "Contract", "계약")}
          </button>
          <button
            type="button"
            disabled={!canSubmit}
            onClick={() => void requestPreview(true)}
            className="inline-flex min-h-9 items-center justify-center gap-1.5 rounded-lg border border-amber-300/30 bg-amber-400/10 px-3 py-2 text-[12px] font-semibold text-amber-50 transition hover:border-amber-200/55 hover:bg-amber-400/15 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Sparkles className="h-3.5 w-3.5" />
            {pendingMode === "llm" ? ui("生成中", "Writing", "작성 중") : ui("生成预览", "Preview", "미리보기")}
          </button>
        </div>
      </div>

      {!canRequest ? (
        <p className="mt-2 text-[11px] text-zinc-500">
          {ui("后台预览仅管理员可调用。", "Backstage preview requires admin access.", "백스테이지 미리보기는 관리자만 호출할 수 있습니다.")}
        </p>
      ) : null}
      {error ? (
        <p className="mt-2 rounded-lg border border-rose-400/20 bg-rose-500/10 px-3 py-2 text-[11px] text-rose-100">
          {error}
        </p>
      ) : null}

      {promptText || Object.keys(promptContract).length ? (
        <details className="group mt-3 border-t border-white/10 pt-3">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-[11px] text-zinc-400">
            <span>{ui("审计材料", "Audit material", "감사 자료")}</span>
            <ChevronDown className="h-3.5 w-3.5 transition group-open:rotate-180" />
          </summary>
          <div className="mt-2 max-h-80 overflow-auto rounded-lg border border-white/10 bg-black/25 p-3">
            {Object.keys(promptContract).length ? (
              <pre className="whitespace-pre-wrap break-words text-[10px] leading-5 text-emerald-100/85">
                {JSON.stringify(promptContract, null, 2)}
              </pre>
            ) : null}
            {promptText ? (
              <pre className="mt-3 whitespace-pre-wrap break-words border-t border-white/10 pt-3 text-[10px] leading-5 text-zinc-300">
                {promptText}
              </pre>
            ) : null}
          </div>
        </details>
      ) : null}
    </section>
  );
}
