"use client";

import { useCallback, useEffect, useState } from "react";

import { jsonPostInit, noStoreInit, requestJson } from "@/lib/apiClient";
import { useAppLanguage } from "@/hooks/useAppLanguage";
import type { AppLanguage } from "@/lib/i18n";

export type AuthRole = "admin" | "manager" | "practitioner" | "user";

export type AuthUser = {
  id: number;
  username: string;
  display_name: string;
  email?: string;
  role: AuthRole;
  is_active: boolean;
  capabilities: string[];
  surface_access?: {
    oracle?: string[];
    admin?: boolean;
    user_management?: boolean;
  };
};

type AuthState = {
  user: AuthUser | null;
  loading: boolean;
  error: string;
  refresh: () => Promise<void>;
  logout: () => Promise<void>;
};

function asUser(value: unknown): AuthUser | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const row = value as Record<string, unknown>;
  const role = String(row.role || "").trim().toLowerCase();
  if (role !== "admin" && role !== "manager" && role !== "practitioner" && role !== "user") return null;
  return {
    id: Number(row.id || 0),
    username: String(row.username || "").trim(),
    display_name: String(row.display_name || "").trim(),
    email: String(row.email || "").trim(),
    role,
    is_active: Boolean(row.is_active),
    capabilities: Array.isArray(row.capabilities) ? row.capabilities.map((item) => String(item || "")) : [],
    surface_access:
      row.surface_access && typeof row.surface_access === "object" && !Array.isArray(row.surface_access)
        ? (row.surface_access as AuthUser["surface_access"])
        : undefined,
  };
}

function ui(lang: AppLanguage, zh: string, en: string, ko: string): string {
  if (lang === "en") return en;
  if (lang === "ko") return ko;
  return zh;
}

export function useAuthSession(): AuthState {
  const { language } = useAppLanguage();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const { data: payload, ok } = await requestJson<Record<string, unknown>>("/api/auth/me", noStoreInit());
      if (!ok) {
        setUser(null);
        setError(String(payload.detail || ui(language, "登录已失效。", "The login session has expired.", "로그인 세션이 만료되었습니다.")));
        return;
      }
      setUser(asUser(payload.user));
    } catch (err) {
      setUser(null);
      setError(err instanceof Error ? err.message : ui(language, "认证信息加载失败。", "Failed to load authentication info.", "인증 정보를 불러오지 못했습니다."));
    } finally {
      setLoading(false);
    }
  }, [language]);

  const logout = useCallback(async () => {
    try {
      await requestJson("/api/auth/logout", jsonPostInit({}, noStoreInit()));
    } finally {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { user, loading, error, refresh, logout };
}
