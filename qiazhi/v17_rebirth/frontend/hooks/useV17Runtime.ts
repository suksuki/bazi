"use client";

import { useCallback, useMemo } from "react";

import { createAccessPolicy } from "@/lib/accessControl";
import { t, translateTerm, type AppLanguage } from "@/lib/i18n";
import { useAppLanguage } from "@/hooks/useAppLanguage";
import { useAuthSession } from "@/hooks/useAuthSession";

export function useV17Runtime() {
  const { language, setLanguage } = useAppLanguage();
  const auth = useAuthSession();
  const access = useMemo(() => createAccessPolicy(auth.user), [auth.user]);

  const tx = useCallback(
    (key: string, vars?: Record<string, string | number>) => t(language, key, vars),
    [language],
  );

  const term = useCallback((value: string) => translateTerm(language, value), [language]);
  const termList = useCallback((values: string[]) => values.map((value) => translateTerm(language, value)), [language]);

  const ui = useCallback(
    (zh: string, en: string, ko: string) => {
      const labels: Record<AppLanguage, string> = { zh, en, ko };
      return labels[language] || zh;
    },
    [language],
  );

  return {
    language,
    setLanguage,
    auth,
    access,
    user: auth.user,
    authLoading: auth.loading,
    authError: auth.error,
    refreshAuth: auth.refresh,
    logout: auth.logout,
    tx,
    term,
    termList,
    ui,
  };
}
