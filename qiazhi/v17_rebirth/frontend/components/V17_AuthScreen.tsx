"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Languages, LogIn, UserPlus } from "lucide-react";
import { APP_LANGUAGE_OPTIONS, t } from "@/lib/i18n";
import { jsonPostInit, requestJson } from "@/lib/apiClient";
import { useAppLanguage } from "@/hooks/useAppLanguage";

type Props = {
  mode: "login" | "register";
  nextPath?: string;
};

const brandGoldClass = "bg-gradient-to-r from-amber-200 via-yellow-300 to-amber-500 bg-clip-text text-transparent";

function tone(active: boolean) {
  return active
    ? "border-amber-300/80 bg-gradient-to-r from-amber-300 via-yellow-400 to-amber-500 text-zinc-950 shadow-[0_10px_28px_rgba(212,175,55,0.2)]"
    : "border-white/10 bg-white/[0.04] text-zinc-400 hover:border-amber-300/25 hover:bg-white/[0.07] hover:text-zinc-100";
}

function authTabHref(mode: "login" | "register", next: string) {
  if (next && next !== "/v17/oracle") {
    return `/${mode}?next=${encodeURIComponent(next)}`;
  }
  return `/${mode}`;
}

export function V17_AuthScreen({ mode, nextPath }: Props) {
  const router = useRouter();
  const { language, setLanguage } = useAppLanguage();
  const next = nextPath && nextPath.startsWith("/") ? nextPath : "/v17/oracle";
  const [username, setUsername] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setMessage("");
    const normalizedUsername = username.trim();
    if (!normalizedUsername || !password || (mode === "register" && !confirmPassword)) {
      setError(t(language, "auth.error.required"));
      return;
    }
    if (mode === "register" && password !== confirmPassword) {
      setError(t(language, "auth.error.password_mismatch"));
      return;
    }
    setLoading(true);
    try {
      const payload =
        mode === "register"
          ? {
              username: normalizedUsername,
              display_name: displayName.trim() || normalizedUsername,
              email: email.trim(),
              password,
            }
          : {
              identifier: normalizedUsername,
              password,
            };
      const { data, ok } = await requestJson<Record<string, unknown>>(`/api/auth/${mode}`, jsonPostInit(payload));
      if (!ok) {
        setError(String(data.detail || t(language, "auth.error.failed")));
        return;
      }
      setMessage(
        mode === "register"
          ? data.role_request
            ? t(language, "auth.message.register_success_practitioner_pending")
            : t(language, "auth.message.register_success")
          : t(language, "auth.message.login_success"),
      );
      router.replace(next);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : t(language, "auth.error.failed"));
    } finally {
      setLoading(false);
    }
  }

  const languageSelector = (
    <div className="inline-flex max-w-full items-center gap-1 rounded-lg border border-zinc-800 bg-zinc-950/80 p-1">
      <Languages className="ml-1 hidden h-3.5 w-3.5 text-zinc-500 sm:block" />
      {APP_LANGUAGE_OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => setLanguage(option.value)}
          aria-pressed={language === option.value}
          className={`rounded-md px-2.5 py-1.5 text-xs transition ${
            language === option.value
              ? "bg-gradient-to-r from-amber-300 to-yellow-500 text-zinc-950"
              : "text-zinc-400 hover:bg-zinc-900 hover:text-amber-100"
          }`}
        >
          {t(language, `lang.${option.value}`)}
        </button>
      ))}
    </div>
  );

  const headingKey = mode === "register" ? "auth.entry.heading.register" : "auth.entry.heading.login";
  const subtitleKey = mode === "register" ? "auth.entry.subtitle.register" : "auth.entry.subtitle.login";
  const submitIcon = mode === "register" ? <UserPlus className="h-4 w-4" /> : <LogIn className="h-4 w-4" />;
  const inputClass =
    "mt-2 w-full rounded-lg border border-white/10 bg-white/[0.05] px-3.5 py-3 text-base text-zinc-100 outline-none transition placeholder:text-zinc-600 focus:border-amber-300/70 focus:bg-white/[0.07] focus:ring-1 focus:ring-amber-300/40";
  const labelClass = "block text-sm font-medium text-zinc-300";

  return (
    <main className="relative min-h-dvh overflow-hidden bg-[#0B0F16] px-4 py-5 text-zinc-100 sm:px-6 lg:min-h-screen lg:px-8">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_22%_16%,rgba(212,175,55,0.14),transparent_24%),radial-gradient(circle_at_82%_20%,rgba(245,158,11,0.08),transparent_28%),linear-gradient(180deg,#060b10_0%,#0B0F16_58%,#07090d_100%)]" />
      <div className="pointer-events-none absolute left-[-18%] top-[-10%] h-72 w-72 rounded-full border border-amber-400/10 blur-3xl" />
      <div className="pointer-events-none absolute bottom-[-18%] right-[-18%] h-80 w-80 rounded-full border border-amber-400/10 blur-3xl" />
      <div className="mx-auto grid min-h-[calc(100dvh-40px)] w-full max-w-6xl items-center gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(360px,440px)]">
        <section className="relative hidden min-w-0 lg:block">
          <div className="max-w-xl rounded-2xl border border-white/10 bg-white/[0.035] p-8 shadow-[0_28px_90px_rgba(0,0,0,0.34)] backdrop-blur-xl">
            <div className="flex items-center gap-4">
              <div className="overflow-hidden rounded-2xl border border-amber-300/25 bg-white/95 shadow-[0_18px_50px_rgba(0,0,0,0.35)]">
                <Image
                  src="/branding/qiazhi-logo.png"
                  alt={t(language, "brand.title")}
                  width={96}
                  height={96}
                  priority
                  className="h-16 w-16 object-cover"
                />
              </div>
              <div>
                <div className={`text-lg font-semibold ${brandGoldClass}`}>{t(language, "brand.title")}</div>
                <div className="mt-1 text-sm text-zinc-500">{t(language, "brand.subtitle")}</div>
              </div>
            </div>
            <h1 className="mt-8 text-5xl font-semibold leading-tight text-zinc-50">
              {t(language, "auth.entry.hero")}
            </h1>
            <p className="mt-5 max-w-lg text-base leading-8 text-zinc-400">
              {t(language, "auth.entry.hero_subtitle")}
            </p>
            <div className="mt-8 grid h-40 overflow-hidden rounded-2xl border border-amber-400/15 bg-[radial-gradient(circle_at_50%_45%,rgba(212,175,55,0.18),transparent_32%),linear-gradient(135deg,rgba(245,158,11,0.08),rgba(124,58,237,0.06))] p-5">
              <div className="relative flex items-center justify-center">
                <div className="absolute h-24 w-24 rounded-full border border-amber-400/35" />
                <div className="absolute h-32 w-32 rounded-full border border-amber-300/12" />
                <div className="absolute h-px w-56 rotate-12 bg-gradient-to-r from-transparent via-amber-300/40 to-transparent" />
                <div className="absolute h-px w-48 -rotate-12 bg-gradient-to-r from-transparent via-amber-200/25 to-transparent" />
                <span className="rounded-full border border-amber-300/30 bg-black/35 px-4 py-2 text-sm font-semibold text-amber-200">
                  {t(language, "brand.subtitle")}
                </span>
              </div>
            </div>
            <div className="mt-5 flex flex-wrap gap-2">
              {["admin", "manager", "practitioner", "user"].map((role) => (
                <span key={role} className="rounded-md border border-zinc-800 bg-zinc-950/70 px-3 py-2 text-xs font-medium text-zinc-300">
                  {t(language, `auth.role.${role}.title`)}
                </span>
              ))}
            </div>
          </div>
        </section>

        <section className="relative min-w-0 justify-self-center rounded-2xl border border-white/10 bg-[#0B0F16]/80 p-5 shadow-[0_28px_80px_rgba(0,0,0,0.42)] backdrop-blur-xl sm:w-full sm:max-w-md sm:p-6">
          <div className="mb-5 flex justify-end lg:hidden">{languageSelector}</div>
          <div className="flex flex-col items-center gap-3 text-center lg:hidden">
              <div className="overflow-hidden rounded-2xl border border-amber-300/25 bg-white/95 shadow-[0_16px_42px_rgba(0,0,0,0.28)]">
                <Image
                  src="/branding/qiazhi-logo.png"
                  alt={t(language, "brand.title")}
                  width={64}
                  height={64}
                  priority
                  className="h-16 w-16 object-cover"
                />
              </div>
            <div className={`text-2xl font-semibold ${brandGoldClass}`}>{t(language, "brand.title")}</div>
            <p className="text-sm text-zinc-400">{t(language, "auth.entry.hero_subtitle")}</p>
          </div>
          <div className="hidden items-start justify-between gap-3 lg:flex">
            <div className="min-w-0">
              <div className={`truncate text-sm font-medium ${brandGoldClass}`}>{t(language, "brand.title")}</div>
              <h1 className="mt-1 text-2xl font-semibold text-zinc-50">{t(language, headingKey)}</h1>
            </div>
            <div className="shrink-0">{languageSelector}</div>
          </div>
          <div className="mt-6 lg:mt-4">
            <h1 className="text-center text-xl font-semibold text-zinc-50 lg:hidden">{t(language, headingKey)}</h1>
            <p className="mt-2 text-center text-sm leading-6 text-zinc-400 lg:text-left">{t(language, subtitleKey)}</p>
          </div>

          <div className="mt-5 grid min-w-0 grid-cols-2 gap-2">
            <Link href={authTabHref("login", next)} className={`inline-flex min-w-0 items-center justify-center gap-1.5 rounded-lg border px-3 py-2.5 text-center text-sm font-medium transition ${tone(mode === "login")}`}>
              <LogIn className="h-4 w-4" />
              {t(language, "auth.tab.login")}
            </Link>
            <Link href={authTabHref("register", next)} className={`inline-flex min-w-0 items-center justify-center gap-1.5 rounded-lg border px-3 py-2.5 text-center text-sm font-medium transition ${tone(mode === "register")}`}>
              <UserPlus className="h-4 w-4" />
              {t(language, "auth.tab.register")}
            </Link>
          </div>

          <form onSubmit={onSubmit} noValidate className="mt-5 space-y-4">
            <label className="block">
              <span className={labelClass}>
                {mode === "login" ? t(language, "auth.field.identifier") : t(language, "auth.field.username")}
              </span>
              <input
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                autoComplete={mode === "login" ? "username" : "username"}
                className={inputClass}
                placeholder={mode === "login" ? t(language, "auth.placeholder.identifier") : t(language, "auth.placeholder.username")}
              />
            </label>

            {mode === "register" ? (
              <>
                <label className="block">
                  <span className={labelClass}>{t(language, "auth.field.display_name")}</span>
                  <input
                    value={displayName}
                    onChange={(event) => setDisplayName(event.target.value)}
                    autoComplete="name"
                    className={inputClass}
                    placeholder={t(language, "auth.placeholder.display_name")}
                  />
                </label>
                <label className="block">
                  <span className={labelClass}>{t(language, "auth.field.email")}</span>
                  <input
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    autoComplete="email"
                    type="email"
                    className={inputClass}
                    placeholder={t(language, "auth.placeholder.email")}
                  />
                </label>
              </>
            ) : null}

            <label className="block">
              <span className={labelClass}>{t(language, "auth.field.password")}</span>
              <input
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                type="password"
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                className={inputClass}
                placeholder={t(language, "auth.placeholder.password")}
              />
            </label>

            {mode === "register" ? (
              <label className="block">
                <span className={labelClass}>{t(language, "auth.field.confirm_password")}</span>
                <input
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  type="password"
                  autoComplete="new-password"
                  className={inputClass}
                  placeholder={t(language, "auth.placeholder.confirm_password")}
                />
              </label>
            ) : null}

            {mode === "register" ? (
              <div className="rounded-xl border border-amber-300/15 bg-amber-950/10 p-3">
                <p className="text-sm font-medium text-amber-100">{t(language, "auth.field.practitioner_request")}</p>
                <p className="mt-1 text-xs leading-5 text-zinc-500">{t(language, "auth.field.practitioner_request_note")}</p>
              </div>
            ) : null}

            {error ? <p className="rounded-md border border-rose-500/30 bg-rose-950/25 px-3.5 py-3 text-sm text-rose-200">{error}</p> : null}
            {message ? <p className="rounded-md border border-emerald-500/30 bg-emerald-950/25 px-3.5 py-3 text-sm text-emerald-200">{message}</p> : null}

            <button
              type="submit"
              disabled={loading}
              className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-lg border border-amber-300/70 bg-gradient-to-r from-amber-300 via-yellow-400 to-amber-500 px-4 py-3 text-base font-semibold text-zinc-950 shadow-[0_14px_30px_rgba(212,175,55,0.22)] transition-all duration-200 hover:brightness-105 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? null : submitIcon}
              {loading
                ? t(language, "auth.button.loading")
                : mode === "login"
                  ? t(language, "auth.button.login")
                  : t(language, "auth.button.register")}
            </button>
          </form>
        </section>
      </div>
    </main>
  );
}
