"use client";

import { useCallback, useEffect, useState } from "react";

export type AuthRole = "admin" | "manager" | "user";

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
  if (role !== "admin" && role !== "manager" && role !== "user") return null;
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

export function useAuthSession(): AuthState {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const resp = await fetch("/api/auth/me", { cache: "no-store" });
      const payload = (await resp.json().catch(() => ({}))) as Record<string, unknown>;
      if (!resp.ok) {
        setUser(null);
        setError(String(payload.detail || "登录已失效。"));
        return;
      }
      setUser(asUser(payload.user));
    } catch (err) {
      setUser(null);
      setError(err instanceof Error ? err.message : "认证信息加载失败。");
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await fetch("/api/auth/logout", { method: "POST", cache: "no-store" });
    } finally {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { user, loading, error, refresh, logout };
}
