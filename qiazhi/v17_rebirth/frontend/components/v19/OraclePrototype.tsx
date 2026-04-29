"use client";

import { useState } from "react";
import { Check } from "lucide-react";
import type { BirthInput } from "@/lib/v19/chartStructureTypes";
import { deriveFlowYear } from "@/lib/v19/timeStructureEngine";
import { computeOracleStateFromBirthInput } from "./oracleEngineAdapters";
import {
  BirthInputPanel,
  ChartStructureSummary,
  EvidenceCardList,
  FeedbackPanel,
  FlowYearSelector,
  InferenceSignalList,
  MobileUserNav,
  ReplayCard,
  ResultCard,
  SystemContractHeader,
  ThemeSelector,
  TimeStructureSummary,
  UnsupportedBoundaryCard,
} from "./oracleComponents";
import { LayerDivider, SectionContainer } from "./primitives";
import type { FeedbackPanelProps, SupportedThemeId, ThemeOption, UiLocale } from "./types";

export function OraclePrototype() {
  const locale: UiLocale = "en";
  const [birthInput, setBirthInput] = useState<BirthInput>({
    year: 1990,
    month: 5,
    day: 12,
    hour: 10,
    calendar_type: "solar",
    gender: "male",
  });
  const [submittedInput, setSubmittedInput] = useState<BirthInput>(birthInput);
  const [selectedFlowYear, setSelectedFlowYear] = useState(2025);
  const [selectedThemeId, setSelectedThemeId] = useState<SupportedThemeId>("income_stability");
  const computedState = computeOracleStateFromBirthInput(submittedInput);
  const timeStructure =
    computedState.status === "ok" && Number.isInteger(selectedFlowYear)
      ? { flowYear: deriveFlowYear(computedState.chart, selectedFlowYear) }
      : null;
  const themeOptions = buildThemeOptions();

  return (
    <main className="min-h-screen bg-[#f7f2e9] pb-10 text-slate-950">
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute left-[-12rem] top-[-10rem] h-96 w-96 rounded-full bg-blue-200/40 blur-3xl" />
        <div className="absolute right-[-10rem] top-40 h-96 w-96 rounded-full bg-amber-200/40 blur-3xl" />
        <div className="absolute bottom-[-16rem] left-1/3 h-96 w-96 rounded-full bg-emerald-100/50 blur-3xl" />
      </div>

      <div className="relative mx-auto flex w-full max-w-[1480px] flex-col gap-5 px-4 py-4 sm:px-6 sm:py-6 xl:px-8">
        <SystemContractHeader locale={locale} />

        <div className="grid gap-5 xl:grid-cols-[420px_minmax(0,1fr)] xl:items-start">
          <div className="space-y-4">
            <LayerDivider
              layer="input"
              label={{ zh: "输入", en: "Input", ko: "입력" }}
              state="ready"
              locale={locale}
            />
            <SectionContainer
              layer="input"
              title={{ zh: "出生信息", en: "Birth Input", ko: "출생 정보" }}
              subtitle={{ zh: "本地 P1/P2 纯函数计算，不接 API。", en: "Local P1/P2 pure-function computation. No API connected.", ko: "로컬 P1/P2 순수 함수 계산입니다. API에 연결되지 않았습니다." }}
              locale={locale}
            >
              <BirthInputPanel
                birthInput={birthInput}
                onChange={setBirthInput}
                onSubmit={() => setSubmittedInput(birthInput)}
              />
            </SectionContainer>

            {computedState.status === "unsupported" ? (
              <SectionContainer
                layer="system_contract"
                title={{ zh: "能力边界", en: "Capability Boundary", ko: "능력 경계" }}
                subtitle={{ zh: "P3 只支持 solar。", en: "P3 supports solar input only.", ko: "P3는 solar 입력만 지원합니다." }}
                status="blocked"
                locale={locale}
              >
                <UnsupportedBoundaryCard reason={computedState.reason} />
              </SectionContainer>
            ) : null}

            <LayerDivider
              layer="chart"
              label={{ zh: "命盘结构", en: "Chart Structure", ko: "명식 구조" }}
              state="ready"
              locale={locale}
            />
            <SectionContainer
              layer="chart"
              title={{ zh: "命盘结构摘要", en: "Chart Structure Summary", ko: "명식 구조 요약" }}
              subtitle={{ zh: "最多 5 个结构信号。", en: "Maximum 5 structural signals.", ko: "최대 5개의 구조 신호." }}
              locale={locale}
            >
              {computedState.status === "ok" ? <ChartStructureSummary chart={computedState.chartSummary} locale={locale} /> : null}
            </SectionContainer>

            <LayerDivider
              layer="time"
              label={{ zh: "时间结构", en: "Time Structure", ko: "시간 구조" }}
              state="ready"
              locale={locale}
            />
            <SectionContainer
              layer="time"
              title={{ zh: "流年选择", en: "Time Selection", ko: "시간 선택" }}
              subtitle={{ zh: "只生成时间结构，不影响结果。", en: "Generates time structure only. Result is unchanged.", ko: "시간 구조만 생성하며 결과는 변경하지 않습니다." }}
              locale={locale}
            >
              <FlowYearSelector selectedYear={selectedFlowYear} onChange={setSelectedFlowYear} />
            </SectionContainer>
            <SectionContainer
              layer="time"
              title={{ zh: "时间结构摘要", en: "Time Structure Summary", ko: "시간 구조 요약" }}
              subtitle={{ zh: "context only，不生成预测结论。", en: "Context only. No conclusion is generated.", ko: "context only. 결론을 생성하지 않습니다." }}
              locale={locale}
            >
              {timeStructure ? <TimeStructureSummary timeStructure={timeStructure} /> : null}
            </SectionContainer>

            <LayerDivider
              layer="inference"
              label={{ zh: "推理信号", en: "Inference Signals", ko: "추론 신호" }}
              state="ready"
              locale={locale}
            />
            <SectionContainer
              layer="inference"
              title={{ zh: "推理信号", en: "Inference Signals", ko: "추론 신호" }}
              subtitle={{ zh: "默认折叠，只显示结构信号。", en: "Collapsed by default. Structural signals only.", ko: "기본 접힘. 구조 신호만 표시." }}
              collapsible
              defaultCollapsed
              locale={locale}
            >
              {computedState.status === "ok" ? <InferenceSignalList inference={computedState.inferenceSignals} locale={locale} /> : null}
            </SectionContainer>

            <LayerDivider
              layer="theme"
              label={{ zh: "主题选择", en: "Theme Selection", ko: "주제 선택" }}
              state="ready"
              locale={locale}
            />
            <SectionContainer
              layer="theme"
              title={{ zh: "选择可支持主题", en: "Choose a supported theme", ko: "지원되는 주제 선택" }}
              subtitle={{ zh: "不支持的主题必须禁用并说明原因。", en: "Unsupported themes stay disabled with reasons.", ko: "지원되지 않는 주제는 이유와 함께 비활성화됩니다." }}
              locale={locale}
            >
              <ThemeSelector
                options={themeOptions}
                selectedThemeId={selectedThemeId}
                onSelect={setSelectedThemeId}
                locale={locale}
              />
            </SectionContainer>
          </div>

          <div className="space-y-4">
            <LayerDivider
              layer="result"
              label={{ zh: "验证结果", en: "Verified Result", ko: "검증 결과" }}
              state="verified"
              locale={locale}
            />
            <SectionContainer
              layer="result"
              title={{ zh: "结果", en: "Result", ko: "결과" }}
              subtitle={{ zh: "TrustBar 先于结果内容。", en: "TrustBar appears before result content.", ko: "TrustBar가 결과보다 먼저 표시됩니다." }}
              trustAnchor
              status="verified"
              locale={locale}
            >
              {computedState.status === "ok" ? <ResultCard result={computedState.result} locale={locale} /> : null}
            </SectionContainer>

            <LayerDivider
              layer="evidence"
              label={{ zh: "证据", en: "Evidence", ko: "근거" }}
              state="verified"
              locale={locale}
            />
            <SectionContainer
              layer="evidence"
              title={{ zh: "证据", en: "Evidence", ko: "근거" }}
              subtitle={{ zh: "默认显示 2 条，可展开。", en: "Showing 2 by default. Expandable.", ko: "기본 2개 표시. 확장 가능." }}
              locale={locale}
            >
              {computedState.status === "ok" ? <EvidenceCardList evidenceList={computedState.evidence} locale={locale} /> : null}
            </SectionContainer>

            <LayerDivider
              layer="feedback"
              label={{ zh: "反馈", en: "Feedback", ko: "피드백" }}
              state="ready"
              locale={locale}
            />
            <SectionContainer
              layer="feedback"
              title={{ zh: "反馈", en: "Feedback", ko: "피드백" }}
              subtitle={{ zh: "反馈只进入 learning signal，不改 active rule。", en: "Feedback becomes learning signal only. It does not change active rules.", ko: "피드백은 learning signal로만 들어가며 active rule을 바꾸지 않습니다." }}
              locale={locale}
            >
              {computedState.status === "ok" ? <FeedbackPanel feedback={buildFeedback(computedState.replay.predictionId)} /> : null}
            </SectionContainer>

            <LayerDivider
              layer="replay"
              label={{ zh: "回放", en: "Replay", ko: "리플레이" }}
              state="verified"
              locale={locale}
            />
            <SectionContainer
              layer="replay"
              title={{ zh: "回放与验证", en: "Replay & Verification", ko: "리플레이 및 검증" }}
              subtitle={{ zh: "公开安全模式下隐私脱敏。", en: "Privacy is redacted in public-safe mode.", ko: "public-safe 모드에서는 개인정보가 가려집니다." }}
              trustAnchor
              status="verified"
              locale={locale}
            >
              {computedState.status === "ok" ? <ReplayCard replay={computedState.replay} locale={locale} /> : null}
            </SectionContainer>
          </div>
        </div>

        <div className="rounded-3xl border border-emerald-200 bg-emerald-50/80 p-4 text-sm leading-6 text-emerald-900 shadow-sm">
          <div className="flex items-start gap-3">
            <Check className="mt-1 h-5 w-5 shrink-0" aria-hidden="true" />
            <p>
              V19 P3 Oracle Prototype computes P1 Chart Structure and P2 Income Stability Inference locally. No backend
              API, no LLM, no database write, no production prediction, and no V18 UI reuse.
            </p>
          </div>
        </div>
      </div>

      <MobileUserNav />
    </main>
  );
}

function buildThemeOptions(): ThemeOption[] {
  const reviewedRulesReason = {
    zh: "not yet supported by reviewed rules",
    en: "not yet supported by reviewed rules",
    ko: "not yet supported by reviewed rules",
  };

  return [
    {
      themeId: "income_stability",
      label: { zh: "Income Stability", en: "Income Stability", ko: "Income Stability" },
      enabled: true,
      requiredSignals: ["income_stability"],
    },
    {
      themeId: "wealth_structure",
      label: { zh: "Wealth Structure", en: "Wealth Structure", ko: "Wealth Structure" },
      enabled: false,
      disabledReason: reviewedRulesReason,
    },
    {
      themeId: "risk_opportunity",
      label: { zh: "Risk & Opportunity", en: "Risk & Opportunity", ko: "Risk & Opportunity" },
      enabled: false,
      disabledReason: reviewedRulesReason,
    },
    {
      themeId: "career",
      label: { zh: "Career", en: "Career", ko: "Career" },
      enabled: false,
      disabledReason: reviewedRulesReason,
    },
    {
      themeId: "relationship",
      label: { zh: "Relationship", en: "Relationship", ko: "Relationship" },
      enabled: false,
      disabledReason: reviewedRulesReason,
    },
    {
      themeId: "health",
      label: { zh: "Health", en: "Health", ko: "Health" },
      enabled: false,
      disabledReason: reviewedRulesReason,
    },
    {
      themeId: "full_chart_general_reading",
      label: { zh: "Full Chart General Reading", en: "Full Chart General Reading", ko: "Full Chart General Reading" },
      enabled: false,
      disabledReason: reviewedRulesReason,
    },
  ];
}

function buildFeedback(predictionId: string): FeedbackPanelProps {
  return {
    predictionId,
    allowedValues: ["accurate", "partly_accurate", "unclear", "wrong", "unsafe_or_unsupported"],
    submitted: false,
  };
}
