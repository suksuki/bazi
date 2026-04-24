"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { APP_LANGUAGE_OPTIONS, t } from "@/lib/i18n";
import { useAppLanguage } from "@/hooks/useAppLanguage";

type Props = {
  mode: "login" | "register";
  nextPath?: string;
};

function tone(active: boolean) {
  return active
    ? "border-cyan-400/40 bg-cyan-950/40 text-cyan-50"
    : "border-zinc-800 bg-zinc-950/60 text-zinc-400 hover:border-zinc-700 hover:text-zinc-200";
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
    if (mode === "register" && password !== confirmPassword) {
      setError(t(language, "auth.error.password_mismatch"));
      return;
    }
    setLoading(true);
    try {
      const payload =
        mode === "register"
          ? {
              username,
              display_name: displayName || username,
              email,
              password,
            }
          : {
              identifier: username,
              password,
            };
      const resp = await fetch(`/api/auth/${mode}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = (await resp.json().catch(() => ({}))) as Record<string, unknown>;
      if (!resp.ok) {
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

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,rgba(34,211,238,0.12),transparent_22%),linear-gradient(180deg,#09090b_0%,#111827_100%)] px-4 py-10 text-zinc-100">
      <div className="mx-auto grid max-w-5xl gap-8 lg:grid-cols-[1.15fr_0.85fr]">
        <section className="rounded-[28px] border border-cyan-500/15 bg-[linear-gradient(145deg,rgba(17,24,39,0.92),rgba(9,9,11,0.98))] p-8 shadow-[0_30px_80px_rgba(0,0,0,0.45)]">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="text-[11px] uppercase tracking-[0.28em] text-cyan-300/80">{t(language, "brand.title")}</div>
            <div className="inline-flex rounded-xl border border-zinc-800 bg-zinc-950/70 p-1">
              {APP_LANGUAGE_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setLanguage(option.value)}
                  className={`rounded-lg px-3 py-1.5 text-xs transition ${
                    language === option.value
                      ? "bg-cyan-300 text-black"
                      : "text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100"
                  }`}
                >
                  {t(language, `lang.${option.value}`)}
                </button>
              ))}
            </div>
          </div>
          <h1 className="mt-4 text-3xl font-semibold tracking-tight text-zinc-50">
            {t(language, mode === "register" ? "auth.title.register" : "auth.title.login")}
          </h1>
          <p className="mt-4 max-w-2xl text-sm leading-7 text-zinc-400">
            {t(language, "auth.description")}
          </p>
          <div className="mt-6 grid gap-3 md:grid-cols-3">
            {[
              ["admin", t(language, "auth.role.admin.desc")],
              ["manager", t(language, "auth.role.manager.desc")],
              ["user", t(language, "auth.role.user.desc")],
            ].map(([title, desc]) => (
              <div key={title} className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4">
                <div className="text-[10px] uppercase tracking-[0.24em] text-zinc-500">
                  {t(language, `auth.role.${title}.title`)}
                </div>
                <p className="mt-3 text-sm leading-6 text-zinc-300">{desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-[28px] border border-zinc-800 bg-[linear-gradient(180deg,rgba(24,24,27,0.8),rgba(9,9,11,0.96))] p-6 shadow-[0_24px_70px_rgba(0,0,0,0.32)]">
          <div className="flex gap-2">
            <Link href={next && next !== "/v17/oracle" ? `/login?next=${encodeURIComponent(next)}` : "/login"} className={`flex-1 rounded-xl border px-4 py-3 text-center text-sm transition ${tone(mode === "login")}`}>
              {t(language, "auth.tab.login")}
            </Link>
            <Link href={next && next !== "/v17/oracle" ? `/register?next=${encodeURIComponent(next)}` : "/register"} className={`flex-1 rounded-xl border px-4 py-3 text-center text-sm transition ${tone(mode === "register")}`}>
              {t(language, "auth.tab.register")}
            </Link>
          </div>

          <form onSubmit={onSubmit} className="mt-6 space-y-4">
            <label className="block">
              <span className="text-[11px] uppercase tracking-[0.2em] text-zinc-500">
                {mode === "login" ? t(language, "auth.field.identifier") : t(language, "auth.field.username")}
              </span>
              <input
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                className="mt-2 w-full rounded-xl border border-zinc-800 bg-black/45 px-4 py-3 text-sm text-zinc-100 outline-none transition focus:border-cyan-500/50"
                placeholder={mode === "login" ? t(language, "auth.placeholder.identifier") : t(language, "auth.placeholder.username")}
                required
              />
            </label>

            {mode === "register" ? (
              <>
                <label className="block">
                  <span className="text-[11px] uppercase tracking-[0.2em] text-zinc-500">{t(language, "auth.field.display_name")}</span>
                  <input
                    value={displayName}
                    onChange={(event) => setDisplayName(event.target.value)}
                    className="mt-2 w-full rounded-xl border border-zinc-800 bg-black/45 px-4 py-3 text-sm text-zinc-100 outline-none transition focus:border-cyan-500/50"
                    placeholder={t(language, "auth.placeholder.display_name")}
                  />
                </label>
                <label className="block">
                  <span className="text-[11px] uppercase tracking-[0.2em] text-zinc-500">{t(language, "auth.field.email")}</span>
                  <input
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    className="mt-2 w-full rounded-xl border border-zinc-800 bg-black/45 px-4 py-3 text-sm text-zinc-100 outline-none transition focus:border-cyan-500/50"
                    placeholder={t(language, "auth.placeholder.email")}
                  />
                </label>
              </>
            ) : null}

            <label className="block">
              <span className="text-[11px] uppercase tracking-[0.2em] text-zinc-500">{t(language, "auth.field.password")}</span>
              <input
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                type="password"
                className="mt-2 w-full rounded-xl border border-zinc-800 bg-black/45 px-4 py-3 text-sm text-zinc-100 outline-none transition focus:border-cyan-500/50"
                placeholder={t(language, "auth.placeholder.password")}
                required
              />
            </label>

            {mode === "register" ? (
              <label className="block">
                <span className="text-[11px] uppercase tracking-[0.2em] text-zinc-500">{t(language, "auth.field.confirm_password")}</span>
                <input
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  type="password"
                  className="mt-2 w-full rounded-xl border border-zinc-800 bg-black/45 px-4 py-3 text-sm text-zinc-100 outline-none transition focus:border-cyan-500/50"
                  placeholder={t(language, "auth.placeholder.confirm_password")}
                  required
                />
              </label>
            ) : null}

            {error ? <p className="rounded-xl border border-rose-500/25 bg-rose-950/25 px-4 py-3 text-sm text-rose-200">{error}</p> : null}
            {message ? <p className="rounded-xl border border-emerald-500/25 bg-emerald-950/25 px-4 py-3 text-sm text-emerald-200">{message}</p> : null}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl border border-cyan-400/40 bg-cyan-300 px-4 py-3 text-sm font-semibold text-black transition disabled:cursor-not-allowed disabled:opacity-60"
            >
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
