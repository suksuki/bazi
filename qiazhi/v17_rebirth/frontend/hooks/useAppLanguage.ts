"use client";

import { useCallback, useEffect, useState } from "react";

import {
  APP_LANGUAGE_COOKIE,
  APP_LANGUAGE_STORAGE_KEY,
  DEFAULT_APP_LANGUAGE,
  normalizeAppLanguage,
  type AppLanguage,
} from "@/lib/i18n";

function readCookie(name: string): string {
  if (typeof document === "undefined") return "";
  const parts = document.cookie.split(";").map((part) => part.trim());
  const hit = parts.find((part) => part.startsWith(`${name}=`));
  return hit ? decodeURIComponent(hit.slice(name.length + 1)) : "";
}

function persistLanguage(lang: AppLanguage) {
  if (typeof document !== "undefined") {
    document.cookie = `${APP_LANGUAGE_COOKIE}=${encodeURIComponent(lang)}; path=/; max-age=31536000; samesite=lax`;
    document.documentElement.lang = lang === "zh" ? "zh-CN" : lang === "ko" ? "ko" : "en";
  }
  if (typeof window !== "undefined") {
    try {
      window.localStorage.setItem(APP_LANGUAGE_STORAGE_KEY, lang);
    } catch {
      // ignore storage failure
    }
  }
}

function resolveInitialLanguage(): AppLanguage {
  try {
    const stored =
      typeof window !== "undefined"
        ? window.localStorage.getItem(APP_LANGUAGE_STORAGE_KEY)
        : "";
    const cookie = readCookie(APP_LANGUAGE_COOKIE);
    return normalizeAppLanguage(stored || cookie || DEFAULT_APP_LANGUAGE);
  } catch {
    return DEFAULT_APP_LANGUAGE;
  }
}

export function useAppLanguage() {
  const [language, setLanguageState] = useState<AppLanguage>(resolveInitialLanguage);

  useEffect(() => {
    persistLanguage(language);
  }, [language]);

  const setLanguage = useCallback((value: AppLanguage) => {
    const next = normalizeAppLanguage(value);
    setLanguageState(next);
  }, []);

  return {
    language,
    setLanguage,
  };
}
