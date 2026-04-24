import type { V17SurfaceTabItem } from "@/components/V17_SurfaceTabs";
import type { V17AccessPolicy, OracleSurface } from "@/lib/accessControl";
import { t, type AppLanguage } from "@/lib/i18n";

type LocalizedLabel = {
  zh: string;
  en: string;
  ko: string;
};

type FeatureModule<TId extends string, TContext> = {
  id: TId;
  order: number;
  label: (language: AppLanguage, context: TContext) => string;
  description: (language: AppLanguage, context: TContext) => string;
  badge?: (language: AppLanguage, context: TContext) => string | number;
  visible?: (access: V17AccessPolicy, context: TContext) => boolean;
};

type ResolveFeatureTabsOptions<TContext> = {
  language: AppLanguage;
  access: V17AccessPolicy;
  context: TContext;
};

function localized(language: AppLanguage, labels: LocalizedLabel): string {
  return labels[language] || labels.zh;
}

export function resolveFeatureTabs<TId extends string, TContext>(
  modules: Array<FeatureModule<TId, TContext>>,
  options: ResolveFeatureTabsOptions<TContext>,
): Array<V17SurfaceTabItem<TId>> {
  const { access, context, language } = options;

  return modules
    .filter((module) => (module.visible ? module.visible(access, context) : true))
    .sort((a, b) => a.order - b.order)
    .map((module) => ({
      id: module.id,
      label: module.label(language, context),
      description: module.description(language, context),
      badge: module.badge?.(language, context),
    }));
}

export type OracleFeatureContext = {
  decisionCount: number;
  auxiliarySignalCount: number;
  traceSignalCount: number;
};

export const ORACLE_FEATURE_MODULES: Array<FeatureModule<OracleSurface, OracleFeatureContext>> = [
  {
    id: "core",
    order: 10,
    label: (language) => t(language, "oracle.tab.core"),
    description: (language) => t(language, "oracle.tab.core.desc"),
    badge: (language, context) => `${t(language, "oracle.count.decisions")} ${context.decisionCount}`,
    visible: (access) => access.canAccessOracleSurface("core"),
  },
  {
    id: "auxiliary",
    order: 20,
    label: (language) => t(language, "oracle.tab.aux"),
    description: (language) => t(language, "oracle.tab.aux.desc"),
    badge: (language, context) => `${t(language, "oracle.count.signals")} ${context.auxiliarySignalCount}`,
    visible: (access) => access.canAccessOracleSurface("auxiliary"),
  },
  {
    id: "trace",
    order: 30,
    label: (language) => t(language, "oracle.tab.trace"),
    description: (language) => t(language, "oracle.tab.trace.desc"),
    badge: (language, context) => `${t(language, "oracle.count.trace")} ${context.traceSignalCount}`,
    visible: (access) => access.canAccessOracleSurface("trace"),
  },
];

export const ADMIN_FEATURE_MODULE_IDS = [
  "llm",
  "db",
  "plugins",
  "physics",
  "evolution",
  "learning",
  "users",
] as const;

export type AdminFeatureTabKey = (typeof ADMIN_FEATURE_MODULE_IDS)[number];

export type AdminFeatureContext = {
  llmModel: string;
  dbEnabled: boolean;
  pluginsCount: number;
  l0Locked: boolean;
  evolutionLogCount: number;
  learningStatus: string;
  authUserCount: number;
};

export const ADMIN_FEATURE_MODULES: Array<FeatureModule<AdminFeatureTabKey, AdminFeatureContext>> = [
  {
    id: "llm",
    order: 10,
    label: (language) => localized(language, { zh: "LLM 节点", en: "LLM Node", ko: "LLM 노드" }),
    description: (language) => localized(language, { zh: "模型、节点与连通测试", en: "Models, endpoints, and connectivity tests", ko: "모델, 노드, 연결 테스트" }),
    badge: (_language, context) => context.llmModel || "model",
  },
  {
    id: "db",
    order: 20,
    label: (language) => localized(language, { zh: "数据库桥接", en: "Database Bridge", ko: "데이터베이스 브리지" }),
    description: (language) => localized(language, { zh: "Postgres 桥接与连通测试", en: "Postgres bridge and connection test", ko: "Postgres 브리지와 연결 테스트" }),
    badge: (_language, context) => (context.dbEnabled ? "on" : "off"),
  },
  {
    id: "plugins",
    order: 30,
    label: (language) => localized(language, { zh: "插件链", en: "Plugin Chain", ko: "플러그인 체인" }),
    description: (language) => localized(language, { zh: "L0-L4 插件、运行态与冲突裁决", en: "L0-L4 plugins, runtime state, and arbitration", ko: "L0-L4 플러그인, 런타임, 충돌 중재" }),
    badge: (_language, context) => context.pluginsCount,
  },
  {
    id: "physics",
    order: 40,
    label: (language) => localized(language, { zh: "宇宙常数", en: "Physics Constants", ko: "물리 상수" }),
    description: (language) => localized(language, { zh: "L0 物理常数与核心参数", en: "L0 constants and core parameters", ko: "L0 상수와 핵심 파라미터" }),
    badge: (_language, context) => (context.l0Locked ? "locked" : "edit"),
  },
  {
    id: "evolution",
    order: 50,
    label: (language) => localized(language, { zh: "演化审计", en: "Evolution Audit", ko: "진화 감사" }),
    description: (language) => localized(language, { zh: "演化日志与反馈账本", en: "Evolution logs and feedback ledger", ko: "진화 로그와 피드백 장부" }),
    badge: (_language, context) => context.evolutionLogCount,
  },
  {
    id: "learning",
    order: 60,
    label: (language) => localized(language, { zh: "自动学习", en: "Auto Learning", ko: "자동 학습" }),
    description: (language) => localized(language, { zh: "学习 Campaign 与 LLM 复核", en: "Learning campaigns and LLM review", ko: "학습 캠페인과 LLM 검토" }),
    badge: (_language, context) => context.learningStatus || "idle",
  },
  {
    id: "users",
    order: 70,
    label: (language) => localized(language, { zh: "用户权限", en: "User Access", ko: "사용자 권한" }),
    description: (language) => localized(language, { zh: "账号、角色与协作权限", en: "Accounts, roles, and collaboration access", ko: "계정, 역할, 협업 권한" }),
    badge: (_language, context) => context.authUserCount,
  },
];
