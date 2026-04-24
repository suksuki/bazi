"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";

import { V17_AppShell } from "@/components/V17_AppShell";
import type { AuthUser } from "@/hooks/useAuthSession";
import type { AppLanguage } from "@/lib/i18n";

type Props = {
  language: AppLanguage;
  user: AuthUser | null;
  loading: boolean;
  onLogout: () => void;
  children: ReactNode;
  allowed?: boolean;
  loginRedirectTo?: string;
  forbiddenRedirectTo?: string;
  forbiddenContent?: ReactNode;
  maxWidthClassName?: string;
};

export function V17_PageGuard({
  language,
  user,
  loading,
  onLogout,
  children,
  allowed = true,
  loginRedirectTo = "/login",
  forbiddenRedirectTo,
  forbiddenContent = null,
  maxWidthClassName = "max-w-3xl",
}: Props) {
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace(loginRedirectTo);
      return;
    }
    if (!allowed && forbiddenRedirectTo) {
      router.replace(forbiddenRedirectTo);
    }
  }, [allowed, forbiddenRedirectTo, loading, loginRedirectTo, router, user]);

  if (loading || !user) {
    return (
      <V17_AppShell
        language={language}
        user={user}
        loading={loading}
        onLogout={onLogout}
        maxWidthClassName={maxWidthClassName}
      >
        {null}
      </V17_AppShell>
    );
  }

  if (!allowed) {
    return (
      <V17_AppShell
        language={language}
        user={user}
        loading={false}
        onLogout={onLogout}
        maxWidthClassName={maxWidthClassName}
      >
        {forbiddenContent}
      </V17_AppShell>
    );
  }

  return <>{children}</>;
}
