"use client";

import Image from "next/image";
import type { ReactNode } from "react";
import { ArrowLeft, LogOut } from "lucide-react";

import type { AuthUser } from "@/hooks/useAuthSession";
import { t, type AppLanguage } from "@/lib/i18n";

type Props = {
  language: AppLanguage;
  user: AuthUser | null;
  loading: boolean;
  running?: boolean;
  onRetry?: () => void;
  onLogout: () => void;
  children: ReactNode;
  maxWidthClassName?: string;
};

const brandGoldClass = "bg-gradient-to-r from-amber-200 via-yellow-300 to-amber-500 bg-clip-text text-transparent";

export function V17_AppShell({
  language,
  user,
  loading,
  running = false,
  onRetry,
  onLogout,
  children,
  maxWidthClassName = "max-w-4xl",
}: Props) {
  if (loading || !user) {
    return (
      <main className="min-h-screen bg-zinc-950 p-3 text-zinc-100 sm:p-6">
        <section className={`mx-auto flex w-full ${maxWidthClassName} flex-col gap-4`}>
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5 text-center sm:rounded-3xl sm:p-8">
            <div className="text-[11px] uppercase tracking-[0.28em] text-cyan-300/80">Auth Gate</div>
            <h1 className="mt-3 text-2xl font-semibold text-zinc-50">{t(language, "oracle.auth_gate.title")}</h1>
            <p className="mt-3 text-sm text-zinc-400">
              {loading ? t(language, "oracle.auth_gate.loading") : t(language, "oracle.auth_gate.redirect")}
            </p>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#0B0F16] pb-28 text-zinc-100 sm:p-6">
      <section className={`mx-auto flex w-full ${maxWidthClassName} flex-col gap-3 sm:gap-4`}>
        <header className="sticky top-0 z-30 flex flex-col items-start justify-between gap-3 border-b border-white/10 bg-[#0B0F16]/95 px-4 py-3 text-violet-300 backdrop-blur-xl sm:static sm:flex-row sm:items-center sm:border-b-0 sm:bg-transparent sm:px-0 sm:py-0 sm:backdrop-blur-none">
          <div className="flex min-w-0 items-center gap-3">
            <div className="overflow-hidden rounded-xl border border-amber-300/25 bg-[#03070D] shadow-[0_12px_40px_rgba(0,0,0,0.25)] sm:rounded-2xl">
              <Image
                src="/branding/qiazhi-logo-mark.png"
                alt={t(language, "brand.title")}
                width={512}
                height={512}
                priority
                className="h-11 w-11 object-cover sm:h-16 sm:w-16"
              />
            </div>
            <div className="min-w-0">
              <h1 className={`truncate text-base font-semibold tracking-wide sm:text-xl ${brandGoldClass}`}>{t(language, "brand.title")}</h1>
              <p className="truncate text-[10px] tracking-[0.2em] text-violet-200/65 sm:text-[11px] sm:tracking-[0.24em]">{t(language, "brand.subtitle")}</p>
            </div>
          </div>
          <div className="flex w-full items-center gap-2 overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden sm:w-auto sm:flex-wrap sm:justify-end sm:overflow-visible">
            <span className="rounded-full border border-cyan-500/20 bg-cyan-950/20 px-3 py-1 text-[10px] uppercase tracking-[0.22em] text-cyan-100">
              {user.role}
            </span>
            <span className="max-w-[42vw] truncate rounded-full border border-zinc-700 bg-zinc-900/70 px-3 py-1 text-[10px] text-zinc-200 sm:max-w-none">
              {user.display_name || user.username}
            </span>
            {running && onRetry ? (
              <button
                type="button"
                onClick={onRetry}
                title={t(language, "oracle.action.retry.title")}
                aria-label={t(language, "oracle.action.retry.title")}
                className="inline-flex min-h-9 shrink-0 items-center gap-1.5 rounded-lg border border-violet-300/70 bg-violet-500/20 px-3 py-2 text-sm font-semibold text-violet-50 shadow-[0_0_22px_rgba(168,85,247,0.18)] transition hover:border-violet-200 hover:bg-violet-500/30 hover:text-white"
              >
                <ArrowLeft className="h-4 w-4" />
                {t(language, "oracle.action.retry")}
              </button>
            ) : null}
            <button
              type="button"
              onClick={onLogout}
              className="inline-flex items-center gap-1 rounded-md border border-zinc-700 bg-zinc-900/70 px-2 py-1 text-xs text-zinc-200 hover:border-zinc-600 hover:bg-zinc-900"
            >
              <LogOut className="h-3.5 w-3.5" />
              {t(language, "oracle.action.logout")}
            </button>
          </div>
        </header>
        {children}
      </section>
    </main>
  );
}
