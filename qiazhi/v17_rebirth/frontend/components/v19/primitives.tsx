"use client";

import type { ReactNode } from "react";
import { useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  FileCheck2,
  Fingerprint,
  Gauge,
  Lock,
  ShieldCheck,
} from "lucide-react";
import type {
  CognitiveLayer,
  LocalizedLabel,
  OracleStateName,
  TrustBarProps,
  UiLocale,
} from "./types";
import { labelText } from "./types";

const layerAccent: Record<CognitiveLayer, string> = {
  system_contract: "border-blue-200 bg-blue-50/70 text-blue-950",
  input: "border-slate-200 bg-white text-slate-950",
  chart: "border-amber-200 bg-amber-50/50 text-slate-950",
  time: "border-cyan-200 bg-cyan-50/50 text-slate-950",
  inference: "border-slate-200 bg-slate-50 text-slate-950",
  theme: "border-blue-200 bg-blue-50/40 text-slate-950",
  result: "border-blue-200 bg-white text-slate-950",
  evidence: "border-slate-200 bg-white text-slate-950",
  feedback: "border-emerald-200 bg-emerald-50/50 text-slate-950",
  replay: "border-slate-200 bg-slate-50 text-slate-950",
  governance: "border-slate-300 bg-slate-50 text-slate-950",
};

export function SectionContainer({
  layer,
  title,
  subtitle,
  collapsible = false,
  defaultCollapsed = false,
  trustAnchor = false,
  status = "ready",
  locale,
  children,
}: {
  layer: CognitiveLayer;
  title: LocalizedLabel;
  subtitle?: LocalizedLabel;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  trustAnchor?: boolean;
  status?: "pending" | "ready" | "verified" | "blocked" | "warning";
  locale: UiLocale;
  children: ReactNode;
}) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);

  return (
    <section className={`rounded-2xl border shadow-sm shadow-slate-200/60 ${layerAccent[layer]}`}>
      <button
        type="button"
        className={`flex w-full items-start justify-between gap-4 px-4 py-4 text-left ${
          collapsible ? "cursor-pointer" : "cursor-default"
        }`}
        onClick={() => collapsible && setCollapsed((value) => !value)}
        aria-expanded={!collapsed}
      >
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
              {layer.replace("_", " ")}
            </span>
            {trustAnchor ? (
              <span className="rounded-full bg-emerald-100 px-2 py-1 text-[0.65rem] font-semibold text-emerald-700">
                trust anchor
              </span>
            ) : null}
            <span className="rounded-full bg-white/80 px-2 py-1 text-[0.65rem] font-semibold text-slate-500">
              {status}
            </span>
          </div>
          <h2 className="text-base font-semibold text-slate-950">{labelText(title, locale)}</h2>
          {subtitle ? <p className="text-sm leading-6 text-slate-600">{labelText(subtitle, locale)}</p> : null}
        </div>
        {collapsible ? (
          <ChevronDown
            className={`mt-1 h-5 w-5 shrink-0 text-slate-500 transition ${collapsed ? "" : "rotate-180"}`}
            aria-hidden="true"
          />
        ) : null}
      </button>
      {collapsed ? null : <div className="border-t border-black/5 px-4 py-4">{children}</div>}
    </section>
  );
}

export function LayerDivider({
  layer,
  label,
  state = "ready",
  locale,
}: {
  layer: CognitiveLayer;
  label: LocalizedLabel;
  state?: "pending" | "ready" | "verified" | "blocked";
  locale: UiLocale;
}) {
  return (
    <div className="flex items-center gap-3 py-2 text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
      <span>{labelText(label, locale)}</span>
      <span className="h-px flex-1 bg-slate-200" />
      <span className="rounded-full bg-white px-2 py-1 normal-case tracking-normal text-slate-500">{state}</span>
      <span className="sr-only">{layer}</span>
    </div>
  );
}

export function TrustBar({
  trust,
}: {
  trust: TrustBarProps;
}) {
  const statusTone =
    trust.verifierStatus === "passed"
      ? "border-emerald-200 bg-emerald-50 text-emerald-800"
      : trust.verifierStatus === "warning"
        ? "border-amber-200 bg-amber-50 text-amber-800"
        : trust.verifierStatus === "blocked"
          ? "border-red-200 bg-red-50 text-red-800"
          : "border-slate-200 bg-slate-50 text-slate-700";

  const items = [
    {
      label: "Verifier",
      value: trust.verifierStatus,
      icon: trust.verifierStatus === "passed" ? ShieldCheck : AlertTriangle,
      tone: statusTone,
    },
    {
      label: "Confidence",
      value: typeof trust.confidence === "number" ? `${Math.round(trust.confidence * 100)}%` : "unknown",
      icon: Gauge,
      tone: "border-blue-200 bg-blue-50 text-blue-800",
    },
    {
      label: "Evidence",
      value: String(trust.evidenceCount ?? "unknown"),
      icon: FileCheck2,
      tone: "border-slate-200 bg-white text-slate-800",
    },
    {
      label: "Contract",
      value: trust.contractHash ?? "not available",
      icon: Fingerprint,
      tone: "border-slate-200 bg-white text-slate-800",
    },
    {
      label: "Schema",
      value: trust.schemaVersion ?? "unknown",
      icon: CheckCircle2,
      tone: "border-slate-200 bg-white text-slate-800",
    },
    {
      label: "Mapping",
      value: trust.mappingVersion ?? "unknown",
      icon: CheckCircle2,
      tone: "border-slate-200 bg-white text-slate-800",
    },
  ];

  return (
    <div className="grid gap-2 rounded-2xl border border-slate-200 bg-slate-50/80 p-2 sm:grid-cols-2 xl:grid-cols-6">
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <div key={item.label} className={`rounded-xl border px-3 py-3 ${item.tone}`}>
            <div className="flex items-center gap-2 text-[0.7rem] font-semibold uppercase tracking-[0.16em] opacity-75">
              <Icon className="h-3.5 w-3.5" aria-hidden="true" />
              {item.label}
            </div>
            <div className="break-safe mt-1 text-sm font-semibold">{item.value}</div>
          </div>
        );
      })}
    </div>
  );
}

export function StateGate({
  enabled,
  reason,
  requiredState,
  locale,
  children,
}: {
  enabled: boolean;
  reason?: LocalizedLabel;
  requiredState?: OracleStateName;
  locale: UiLocale;
  children: ReactNode;
}) {
  return (
    <div
      className={`rounded-xl border p-3 transition ${
        enabled ? "border-blue-200 bg-white shadow-sm" : "border-slate-200 bg-slate-50 text-slate-400"
      }`}
      aria-disabled={!enabled}
    >
      {children}
      {!enabled ? (
        <div className="mt-2 flex items-start gap-2 text-xs leading-5 text-slate-500">
          <Lock className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
          <span>{reason ? labelText(reason, locale) : `requires ${requiredState ?? "supported state"}`}</span>
        </div>
      ) : null}
    </div>
  );
}
