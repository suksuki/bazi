"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { V18_OracleUserAgentExperience } from "@/components/V18_OracleUserAgentExperience";
import { useAuthSession } from "@/hooks/useAuthSession";

export default function V17AgentPage() {
  const router = useRouter();
  const { user, loading, logout } = useAuthSession();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, router, user]);

  if (loading || !user) {
    return (
      <main className="grid min-h-screen place-items-center bg-[#090d14] text-slate-100">
        <div className="rounded-3xl border border-white/10 bg-white/[0.06] px-6 py-5 text-sm text-slate-300">
          正在进入 Agent...
        </div>
      </main>
    );
  }

  return (
    <V18_OracleUserAgentExperience
      displayName={user.display_name || user.username}
      roleLabel={user.role}
      isAdmin={user.role === "admin"}
      onLogout={logout}
    />
  );
}
