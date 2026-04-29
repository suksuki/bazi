"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { V18_AdminKnowledgeBasePanel } from "@/components/V18_AdminKnowledgeBasePanel";
import { useAuthSession } from "@/hooks/useAuthSession";

export default function V17AdminKnowledgeBasePage() {
  const router = useRouter();
  const { user, loading, logout } = useAuthSession();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, router, user]);

  if (loading || !user) {
    return (
      <main className="grid min-h-screen place-items-center bg-[#0b0f0a] text-slate-100">
        <div className="rounded-3xl border border-white/10 bg-white/[0.06] px-6 py-5 text-sm text-slate-300">
          正在进入 Knowledge Base Admin...
        </div>
      </main>
    );
  }

  if (user.role !== "admin") {
    return (
      <main className="grid min-h-screen place-items-center bg-[#0b0f0a] px-4 text-slate-100">
        <section className="max-w-md rounded-[2rem] border border-rose-300/20 bg-rose-500/10 p-6 text-center shadow-2xl shadow-black/30">
          <h1 className="text-2xl font-semibold">Admin only</h1>
          <p className="mt-3 text-sm leading-6 text-rose-100/90">
            Knowledge Base 入口只允许 admin 访问。KB 只能生成 sandbox candidate，不能直接进入正式预测裁决。
          </p>
        </section>
      </main>
    );
  }

  return <V18_AdminKnowledgeBasePanel displayName={user.display_name || user.username} onLogout={logout} />;
}
