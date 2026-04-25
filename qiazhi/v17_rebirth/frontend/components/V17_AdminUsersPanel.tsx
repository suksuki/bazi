"use client";

import { useMemo, useState } from "react";

export type AdminAuthUser = {
  id: number;
  username: string;
  display_name: string;
  email?: string;
  role: "admin" | "manager" | "practitioner" | "user";
  is_active: boolean;
  created_at?: string;
  last_login_at?: string;
  latest_ip_address?: string;
  latest_user_agent?: string;
  latest_seen_at?: string;
  role_request_id?: number;
  role_request_status?: "pending" | "approved" | "rejected" | "cancelled" | "";
  role_request_role?: AdminAuthUser["role"] | "";
  role_request_reason?: string;
  role_request_created_at?: string;
  role_request_updated_at?: string;
};

type Props = {
  users: AdminAuthUser[];
  loading: boolean;
  onRefresh: () => void;
  onUpdateRole: (userId: number, role: AdminAuthUser["role"]) => Promise<void>;
  onDecideRoleRequest?: (requestId: number, decision: "approved" | "rejected") => Promise<void>;
  operatorRole?: AdminAuthUser["role"];
  compact?: boolean;
  title?: string;
  description?: string;
};

function roleOptionsForUser(
  user: AdminAuthUser,
  operatorRole: AdminAuthUser["role"] = "admin",
): Array<AdminAuthUser["role"]> {
  if (user.role === "admin") return ["admin"];
  if (operatorRole === "manager") return ["manager", "practitioner", "user"];
  return ["manager", "practitioner", "user"];
}

export function V17_AdminUsersPanel({
  users,
  loading,
  onRefresh,
  onUpdateRole,
  onDecideRoleRequest,
  operatorRole = "admin",
  compact = false,
  title,
  description,
}: Props) {
  const [busyUserId, setBusyUserId] = useState<number | null>(null);
  const [busyRequestId, setBusyRequestId] = useState<number | null>(null);
  const [draftRoles, setDraftRoles] = useState<Record<number, AdminAuthUser["role"]>>({});

	  const counts = useMemo(() => {
	    return users.reduce(
	      (acc, row) => {
	        acc.total += 1;
	        acc[row.role] += 1;
        return acc;
      },
	      { total: 0, admin: 0, manager: 0, practitioner: 0, user: 0 },
	    );
	  }, [users]);
  const pendingRoleRequests = useMemo(
    () => users.filter((row) => row.role_request_status === "pending" && row.role_request_role === "practitioner").length,
    [users],
  );

	  async function commitRole(user: AdminAuthUser) {
	    const nextRole = draftRoles[user.id] || user.role;
    if (nextRole === user.role) return;
    setBusyUserId(user.id);
    try {
      await onUpdateRole(user.id, nextRole);
    } finally {
	      setBusyUserId(null);
	    }
	  }

  async function decideRoleRequest(requestId: number, decision: "approved" | "rejected") {
    if (!onDecideRoleRequest) return;
    setBusyRequestId(requestId);
    try {
      await onDecideRoleRequest(requestId, decision);
    } finally {
      setBusyRequestId(null);
    }
  }

  const panelTitle = title || (compact ? "协作权限" : "用户与权限");
  const panelDescription =
    description ||
    "账号写入数据库。系统保留唯一管理员账号 `admin`，后续账号默认注册为 `user`；管理员或经理可将账号调整为 `manager / practitioner / user`。";

  return (
    <section className="min-w-0 space-y-5">
      <div className="rounded-2xl border border-zinc-800/80 bg-zinc-950/50 p-4 sm:rounded-3xl sm:p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="text-[11px] uppercase tracking-[0.28em] text-cyan-300/80">RBAC</div>
              <h2 className="mt-2 text-xl font-semibold text-zinc-50">{panelTitle}</h2>
              <p className="mt-2 max-w-3xl text-xs leading-6 text-zinc-400">{panelDescription}</p>
            </div>
          <button
            onClick={onRefresh}
            className="rounded-full border border-zinc-700 bg-zinc-900/70 px-4 py-2 text-xs text-zinc-200 transition hover:border-zinc-600 hover:bg-zinc-900"
          >
            刷新列表
          </button>
        </div>

        {!compact ? (
	          <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-6">
	            {[
	              { label: "总用户", value: counts.total, tone: "text-zinc-50" },
	              { label: "管理员", value: counts.admin, tone: "text-cyan-100" },
	              { label: "经理", value: counts.manager, tone: "text-amber-100" },
	              { label: "命理师", value: counts.practitioner, tone: "text-violet-100" },
	              { label: "普通用户", value: counts.user, tone: "text-emerald-100" },
	              { label: "待审申请", value: pendingRoleRequests, tone: "text-yellow-100" },
	            ].map((item) => (
              <div key={item.label} className="rounded-2xl border border-zinc-800 bg-black/35 p-4">
                <div className="text-[10px] uppercase tracking-[0.22em] text-zinc-500">{item.label}</div>
                <div className={`mt-3 text-2xl font-semibold ${item.tone}`}>{item.value}</div>
              </div>
            ))}
          </div>
        ) : (
          <div className="mt-4 flex flex-wrap gap-2 text-[10px]">
            <span className="rounded-full border border-zinc-700 bg-zinc-900/70 px-3 py-1 text-zinc-100">总用户 {counts.total}</span>
            <span className="rounded-full border border-cyan-500/25 bg-cyan-950/20 px-3 py-1 text-cyan-100">管理员 {counts.admin}</span>
	            <span className="rounded-full border border-amber-500/25 bg-amber-950/20 px-3 py-1 text-amber-100">经理 {counts.manager}</span>
	            <span className="rounded-full border border-violet-500/25 bg-violet-950/20 px-3 py-1 text-violet-100">命理师 {counts.practitioner}</span>
	            <span className="rounded-full border border-emerald-500/25 bg-emerald-950/20 px-3 py-1 text-emerald-100">用户 {counts.user}</span>
	            {pendingRoleRequests ? (
	              <span className="rounded-full border border-yellow-500/30 bg-yellow-950/20 px-3 py-1 text-yellow-100">待审 {pendingRoleRequests}</span>
	            ) : null}
	          </div>
        )}
      </div>

      <div className="space-y-3">
	        {users.map((user) => {
	          const nextRole = draftRoles[user.id] || user.role;
	          const saving = busyUserId === user.id;
	          const roleOptions = roleOptionsForUser(user, operatorRole);
	          const roleRequestPending =
	            user.role_request_status === "pending" &&
	            user.role_request_role === "practitioner" &&
	            Boolean(user.role_request_id);
	          const requestBusy = busyRequestId === user.role_request_id;
	          return (
            <article key={user.id} className={`min-w-0 rounded-2xl border border-zinc-800 bg-[linear-gradient(180deg,rgba(24,24,27,0.72),rgba(9,9,11,0.92))] ${compact ? "p-3" : "p-4"}`}>
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="min-w-0 space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="break-words text-base font-semibold text-zinc-50">{user.display_name || user.username}</h3>
                    <span className="rounded-full border border-zinc-700 bg-zinc-900/70 px-2 py-1 text-[10px] uppercase tracking-[0.22em] text-zinc-300">
                      {user.role}
                    </span>
                  </div>
                  <p className="break-all text-xs text-zinc-400">@{user.username}{user.email ? ` · ${user.email}` : ""}</p>
                  <p className="break-words text-[11px] text-zinc-500">
                    创建 {user.created_at || "—"} · 最近登录 {user.last_login_at || "—"}
                  </p>
                  <p className="break-words text-[11px] text-zinc-500">
                    最近活跃 {user.latest_seen_at || "—"} · 最近 IP {user.latest_ip_address || "—"}
                  </p>
                </div>

                <div className="flex w-full flex-wrap items-center gap-2 sm:w-auto">
                  <select
                    value={nextRole}
                    onChange={(event) =>
                      setDraftRoles((prev) => ({
                        ...prev,
                        [user.id]: event.target.value as AdminAuthUser["role"],
                      }))
                    }
                    className="w-full rounded-xl border border-zinc-800 bg-black/45 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-cyan-500/50 sm:w-auto"
                    disabled={roleOptions.length === 1}
                  >
                    {roleOptions.map((role) => (
                      <option key={role} value={role}>
                        {role}
                      </option>
                    ))}
                  </select>
                  <button
                    onClick={() => void commitRole(user)}
                    disabled={loading || saving || nextRole === user.role}
                    className="w-full rounded-xl border border-cyan-400/30 bg-cyan-300 px-4 py-2 text-sm font-semibold text-black transition disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
                  >
                    {saving ? "保存中..." : "更新角色"}
	                  </button>
	                </div>
	              </div>
	              {roleRequestPending ? (
	                <div className="mt-3 rounded-xl border border-amber-400/25 bg-amber-950/15 p-3">
	                  <div className="flex flex-wrap items-start justify-between gap-3">
	                    <div className="min-w-0">
	                      <div className="text-xs font-semibold text-amber-100">命理师权限申请</div>
	                      <p className="mt-1 break-words text-[11px] leading-5 text-zinc-400">
	                        {user.role_request_reason || "申请人暂未填写补充说明。"}
	                      </p>
	                      <p className="mt-1 text-[10px] text-zinc-500">
	                        提交 {user.role_request_created_at || "—"}
	                      </p>
	                    </div>
	                    {onDecideRoleRequest ? (
	                      <div className="flex w-full gap-2 sm:w-auto">
	                        <button
	                          type="button"
	                          disabled={loading || requestBusy}
	                          onClick={() => void decideRoleRequest(Number(user.role_request_id || 0), "approved")}
	                          className="flex-1 rounded-lg border border-emerald-400/30 bg-emerald-400/15 px-3 py-2 text-xs font-semibold text-emerald-100 transition hover:bg-emerald-400/20 disabled:cursor-not-allowed disabled:opacity-60 sm:flex-none"
	                        >
	                          {requestBusy ? "处理中..." : "批准"}
	                        </button>
	                        <button
	                          type="button"
	                          disabled={loading || requestBusy}
	                          onClick={() => void decideRoleRequest(Number(user.role_request_id || 0), "rejected")}
	                          className="flex-1 rounded-lg border border-rose-400/25 bg-rose-400/10 px-3 py-2 text-xs font-semibold text-rose-100 transition hover:bg-rose-400/15 disabled:cursor-not-allowed disabled:opacity-60 sm:flex-none"
	                        >
	                          驳回
	                        </button>
	                      </div>
	                    ) : null}
	                  </div>
	                </div>
	              ) : null}
	            </article>
	          );
	        })}
        {!users.length ? (
          <div className="rounded-2xl border border-zinc-800 bg-zinc-950/50 p-6 text-sm text-zinc-400">
            当前还没有用户记录。
          </div>
        ) : null}
      </div>
    </section>
  );
}
