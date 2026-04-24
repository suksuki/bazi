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

function tone(active: boolean) {
  return active
    ? "border-cyan-300 bg-cyan-300 text-zinc-950 shadow-[0_10px_28px_rgba(34,211,238,0.18)]"
    : "border-zinc-800 bg-zinc-950/70 text-zinc-400 hover:border-zinc-600 hover:text-zinc-100";
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
          ? t(language, "auth.message.register_success")
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
              ? "bg-cyan-300 text-zinc-950"
              : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-100"
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

  return (
    <main className="min-h-dvh overflow-x-hidden bg-[linear-gradient(180deg,#07080b_0%,#0b1018_54%,#09090b_100%)] px-4 py-5 text-zinc-100 sm:px-6 lg:min-h-screen lg:px-8">
      <div className="mx-auto grid min-h-[calc(100dvh-40px)] w-full max-w-6xl items-center gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(360px,440px)]">
        <section className="hidden min-w-0 lg:block">
          <div className="max-w-xl">
            <div className="flex items-center gap-4">
              <div className="overflow-hidden rounded-lg border border-zinc-800 bg-white/95 shadow-[0_18px_50px_rgba(0,0,0,0.35)]">
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
                <div className="text-sm font-medium text-cyan-200">{t(language, "brand.title")}</div>
                <div className="mt-1 text-sm text-zinc-500">{t(language, "brand.subtitle")}</div>
              </div>
            </div>
            <h1 className="mt-8 text-5xl font-semibold leading-tight text-zinc-50">
              {t(language, "auth.entry.hero")}
            </h1>
            <p className="mt-5 max-w-lg text-base leading-8 text-zinc-400">
              {t(language, "auth.entry.hero_subtitle")}
            </p>
            <div className="mt-8 flex flex-wrap gap-2">
              {["admin", "manager", "user"].map((role) => (
                <span key={role} className="rounded-md border border-zinc-800 bg-zinc-950/70 px-3 py-2 text-xs font-medium text-zinc-300">
                  {t(language, `auth.role.${role}.title`)}
                </span>
              ))}
            </div>
          </div>
        </section>

        <section className="min-w-0 justify-self-center rounded-lg border border-zinc-800 bg-zinc-950/82 p-4 shadow-[0_28px_80px_rgba(0,0,0,0.42)] sm:w-full sm:max-w-md sm:p-5">
          <div className="flex items-start justify-between gap-3">
            <div className="flex min-w-0 items-center gap-3">
              <div className="overflow-hidden rounded-lg border border-zinc-800 bg-white/95 lg:hidden">
                <Image
                  src="/branding/qiazhi-logo.png"
                  alt={t(language, "brand.title")}
                  width={64}
                  height={64}
                  priority
                  className="h-11 w-11 object-cover"
                />
              </div>
              <div className="min-w-0">
                <div className="truncate text-sm font-medium text-cyan-200">{t(language, "brand.title")}</div>
                <h1 className="mt-1 text-2xl font-semibold text-zinc-50">{t(language, headingKey)}</h1>
              </div>
            </div>
            <div className="shrink-0">{languageSelector}</div>
          </div>
          <p className="mt-4 text-sm leading-6 text-zinc-400">{t(language, subtitleKey)}</p>

          <div className="mt-5 grid min-w-0 grid-cols-2 gap-2">
            <Link href={authTabHref("login", next)} className={`inline-flex min-w-0 items-center justify-center gap-1.5 rounded-md border px-3 py-2.5 text-center text-sm font-medium transition ${tone(mode === "login")}`}>
              <LogIn className="h-4 w-4" />
              {t(language, "auth.tab.login")}
            </Link>
            <Link href={authTabHref("register", next)} className={`inline-flex min-w-0 items-center justify-center gap-1.5 rounded-md border px-3 py-2.5 text-center text-sm font-medium transition ${tone(mode === "register")}`}>
              <UserPlus className="h-4 w-4" />
              {t(language, "auth.tab.register")}
            </Link>
          </div>

          <form onSubmit={onSubmit} noValidate className="mt-5 space-y-4">
            <label className="block">
              <span className="text-sm font-medium text-zinc-300">
                {mode === "login" ? t(language, "auth.field.identifier") : t(language, "auth.field.username")}
              </span>
              <input
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                autoComplete={mode === "login" ? "username" : "username"}
                className="mt-2 w-full rounded-md border border-zinc-800 bg-black/45 px-3.5 py-3 text-base text-zinc-100 outline-none transition placeholder:text-zinc-600 focus:border-cyan-400/70 focus:bg-black/65"
                placeholder={mode === "login" ? t(language, "auth.placeholder.identifier") : t(language, "auth.placeholder.username")}
              />
            </label>

            {mode === "register" ? (
              <>
                <label className="block">
                  <span className="text-sm font-medium text-zinc-300">{t(language, "auth.field.display_name")}</span>
                  <input
                    value={displayName}
                    onChange={(event) => setDisplayName(event.target.value)}
                    autoComplete="name"
                    className="mt-2 w-full rounded-md border border-zinc-800 bg-black/45 px-3.5 py-3 text-base text-zinc-100 outline-none transition placeholder:text-zinc-600 focus:border-cyan-400/70 focus:bg-black/65"
                    placeholder={t(language, "auth.placeholder.display_name")}
                  />
                </label>
                <label className="block">
                  <span className="text-sm font-medium text-zinc-300">{t(language, "auth.field.email")}</span>
                  <input
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    autoComplete="email"
                    type="email"
                    className="mt-2 w-full rounded-md border border-zinc-800 bg-black/45 px-3.5 py-3 text-base text-zinc-100 outline-none transition placeholder:text-zinc-600 focus:border-cyan-400/70 focus:bg-black/65"
                    placeholder={t(language, "auth.placeholder.email")}
                  />
                </label>
              </>
            ) : null}

            <label className="block">
              <span className="text-sm font-medium text-zinc-300">{t(language, "auth.field.password")}</span>
              <input
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                type="password"
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                className="mt-2 w-full rounded-md border border-zinc-800 bg-black/45 px-3.5 py-3 text-base text-zinc-100 outline-none transition placeholder:text-zinc-600 focus:border-cyan-400/70 focus:bg-black/65"
                placeholder={t(language, "auth.placeholder.password")}
              />
            </label>

            {mode === "register" ? (
              <label className="block">
                <span className="text-sm font-medium text-zinc-300">{t(language, "auth.field.confirm_password")}</span>
                <input
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  type="password"
                  autoComplete="new-password"
                  className="mt-2 w-full rounded-md border border-zinc-800 bg-black/45 px-3.5 py-3 text-base text-zinc-100 outline-none transition placeholder:text-zinc-600 focus:border-cyan-400/70 focus:bg-black/65"
                  placeholder={t(language, "auth.placeholder.confirm_password")}
                />
              </label>
            ) : null}

            {error ? <p className="rounded-md border border-rose-500/30 bg-rose-950/25 px-3.5 py-3 text-sm text-rose-200">{error}</p> : null}
            {message ? <p className="rounded-md border border-emerald-500/30 bg-emerald-950/25 px-3.5 py-3 text-sm text-emerald-200">{message}</p> : null}

            <button
              type="submit"
              disabled={loading}
              className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-md border border-cyan-300 bg-cyan-300 px-4 py-3 text-base font-semibold text-zinc-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60"
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
