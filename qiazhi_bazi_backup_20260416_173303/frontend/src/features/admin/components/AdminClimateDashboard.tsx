"use client";

import { useCallback, useEffect, useState } from "react";
import { ADMIN_HEADERS, API_BASE } from "@/features/admin-settings/constants";
import { ClimateFieldStrengthCompare } from "@/features/admin/components/ClimateFieldStrengthCompare";
import { ConflictTopologyLossPanel } from "@/features/admin/components/ConflictTopologyLossPanel";

type ManifestDoc = Record<string, unknown>;

export function AdminClimateDashboard() {
  const [editorText, setEditorText] = useState("");
  const [sha, setSha] = useState("");
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  const [seedDate, setSeedDate] = useState("1990-06-14");
  const [seedTime, setSeedTime] = useState("12:00");
  const [seedCalendar, setSeedCalendar] = useState("solar");
  const [seedGender, setSeedGender] = useState<"male" | "female">("male");
  const [seedRefYear, setSeedRefYear] = useState("2024");
  const [collisionBusy, setCollisionBusy] = useState(false);
  const [collisionErr, setCollisionErr] = useState("");
  const [physicsTensor, setPhysicsTensor] = useState<Record<string, unknown> | null>(null);
  const [patternRowsCount, setPatternRowsCount] = useState<number | null>(null);

  const parseApiJson = useCallback(async (r: Response) => {
    const ct = (r.headers.get("content-type") || "").toLowerCase();
    if (ct.includes("text/html")) {
      throw new Error("[CRITICAL_ERROR] Backend returned HTML instead of JSON.");
    }
    return r.json() as Promise<unknown>;
  }, []);

  const loadManifest = useCallback(async () => {
    setErr("");
    setLoading(true);
    try {
      const r = await fetch(`${API_BASE}/api/v1/admin/climate/manifest`, { headers: { ...ADMIN_HEADERS } });
      const j = (await parseApiJson(r)) as { ok?: boolean; manifest?: ManifestDoc; sha256?: string; detail?: string };
      if (!r.ok) throw new Error(String(j.detail || r.statusText));
      setSha(String(j.sha256 || ""));
      setEditorText(JSON.stringify(j.manifest ?? {}, null, 2));
      setMsg("已加载调候法典");
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, [parseApiJson]);

  useEffect(() => {
    void loadManifest();
  }, [loadManifest]);

  const saveServer = useCallback(async () => {
    setErr("");
    let doc: ManifestDoc;
    try {
      doc = JSON.parse(editorText) as ManifestDoc;
    } catch {
      setErr("调候法典 JSON 解析失败");
      return;
    }
    setLoading(true);
    try {
      const r = await fetch(`${API_BASE}/api/v1/admin/climate/update`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", ...ADMIN_HEADERS },
        body: JSON.stringify({ manifest: doc }),
      });
      const j = (await parseApiJson(r)) as { ok?: boolean; detail?: string; sha256?: string; backup_path?: string | null };
      if (!r.ok) throw new Error(String(j.detail || r.statusText));
      setSha(String(j.sha256 || ""));
      setMsg(`已写入服务器（规范 SHA256）${j.backup_path ? ` · 备份 ${j.backup_path}` : ""}`);
      await loadManifest();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, [editorText, loadManifest, parseApiJson]);

  const reloadServer = useCallback(async () => {
    setErr("");
    setLoading(true);
    try {
      const r = await fetch(`${API_BASE}/api/v1/admin/climate/reload`, {
        method: "POST",
        headers: { ...ADMIN_HEADERS },
      });
      const j = (await parseApiJson(r)) as { ok?: boolean; detail?: string; sha256?: string };
      if (!r.ok) throw new Error(String(j.detail || r.statusText));
      setSha(String(j.sha256 || ""));
      setMsg("已重新加载磁盘法典并刷新指纹");
      await loadManifest();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, [loadManifest, parseApiJson]);

  const restoreLatestBackup = useCallback(async () => {
    if (!window.confirm("确定从最新时间戳备份恢复调候法典？当前文件会先再备份一次。")) return;
    setErr("");
    setLoading(true);
    try {
      const r = await fetch(`${API_BASE}/api/v1/admin/climate/restore-latest`, {
        method: "POST",
        headers: { ...ADMIN_HEADERS },
      });
      const j = (await parseApiJson(r)) as { ok?: boolean; detail?: string; sha256?: string };
      if (!r.ok) throw new Error(String(j.detail || r.statusText));
      setSha(String(j.sha256 || ""));
      setMsg("已从最新备份恢复");
      await loadManifest();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, [loadManifest, parseApiJson]);

  const runCollisionPreview = useCallback(async () => {
    setCollisionErr("");
    setCollisionBusy(true);
    try {
      const ref = parseInt(seedRefYear, 10);
      const r = await fetch(`${API_BASE}/api/v1/admin/patterns/collision-preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...ADMIN_HEADERS },
        body: JSON.stringify({
          date: seedDate.trim(),
          time: seedTime.trim() || "12:00",
          calendar: seedCalendar,
          gender: seedGender,
          reference_year: Number.isFinite(ref) ? ref : undefined,
          enabled_plugins: ["classical.pattern_detector.v2"],
        }),
      });
      const j = (await parseApiJson(r)) as {
        ok?: boolean;
        detail?: string;
        rows?: unknown[];
        physics_tensor?: Record<string, unknown>;
      };
      if (!r.ok) throw new Error(String(j.detail || r.statusText));
      const rows = j.rows ?? [];
      setPatternRowsCount(rows.length);
      setPhysicsTensor(
        j.physics_tensor && typeof j.physics_tensor === "object" ? (j.physics_tensor as Record<string, unknown>) : null,
      );
      setMsg(`演算完成：${rows.length} 条格局轨迹；场强对比见下（修改未月土_mod 等后请先「保存」再「重新加载」磁盘，然后再次运行演算）。`);
    } catch (e) {
      setCollisionErr(e instanceof Error ? e.message : String(e));
    } finally {
      setCollisionBusy(false);
    }
  }, [parseApiJson, seedCalendar, seedDate, seedGender, seedRefYear, seedTime]);

  return (
    <div className="space-y-4 text-[13px] text-zinc-200">
      <section className="rounded-lg border border-cyan-800/50 bg-zinc-950/80 p-3">
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-widest text-cyan-300/90">调候法典 · climate_manifest.json</p>
        <p className="mb-2 text-[10px] leading-relaxed text-zinc-500">
          与格局法典一致：规范 JSON 的 SHA256 指纹用于运维核对；写入时生成时间戳备份及同目录{" "}
          <span className="font-mono text-cyan-600/80">climate_manifest.sha256</span>。
        </p>
        <div className="mb-2 flex flex-wrap gap-2">
          <button
            type="button"
            disabled={loading}
            onClick={() => void loadManifest()}
            className="rounded border border-zinc-600 bg-zinc-900 px-2 py-1 text-[11px] hover:bg-zinc-800 disabled:opacity-40"
          >
            刷新读取
          </button>
          <button
            type="button"
            disabled={loading}
            onClick={() => void reloadServer()}
            className="rounded border border-cyan-700/50 bg-cyan-950/40 px-2 py-1 text-[11px] text-cyan-100 hover:bg-cyan-950/60 disabled:opacity-40"
          >
            重新加载
          </button>
          <button
            type="button"
            disabled={loading}
            onClick={() => void saveServer()}
            className="rounded border border-amber-600/50 bg-amber-950/30 px-2 py-1 text-[11px] text-amber-100 hover:bg-amber-950/50 disabled:opacity-40"
          >
            保存到服务器
          </button>
          <button
            type="button"
            disabled={loading}
            onClick={() => void restoreLatestBackup()}
            className="rounded border border-rose-700/40 bg-rose-950/25 px-2 py-1 text-[11px] text-rose-100 hover:bg-rose-950/40 disabled:opacity-40"
          >
            从最新备份恢复
          </button>
        </div>
        <p className="mb-1 font-mono text-[10px] text-zinc-400">
          SHA256（规范序）: <span className="text-cyan-200/90">{sha || "—"}</span>
        </p>
        {msg ? <p className="text-[10px] text-emerald-400/90">{msg}</p> : null}
        {err ? <p className="text-[10px] text-rose-400">{err}</p> : null}
        <textarea
          className="mt-2 h-[min(42vh,360px)] w-full resize-y rounded border border-zinc-700 bg-black/50 p-2 font-mono text-[11px] leading-snug text-zinc-100"
          spellCheck={false}
          value={editorText}
          onChange={(ev) => setEditorText(ev.target.value)}
        />
      </section>

      <section className="rounded-lg border border-violet-800/40 bg-zinc-950/70 p-3">
        <p className="mb-2 text-[11px] font-semibold text-violet-200/95">演算验证 · L2 连锁</p>
        <p className="mb-2 text-[10px] text-zinc-500">
          修改 TABLE 中某月支的 *_mod 后保存 → 重新加载 → 运行演算：物理张量中的调候对比与格局亲和度应随之变化。
        </p>
        <div className="flex flex-wrap items-end gap-2">
          <label className="flex min-w-[120px] flex-1 flex-col gap-0.5 text-[10px] text-zinc-500">
            生日
            <input
              className="rounded border border-zinc-700 bg-zinc-950 px-2 py-1.5 font-mono text-[12px]"
              value={seedDate}
              onChange={(ev) => setSeedDate(ev.target.value)}
            />
          </label>
          <label className="w-[88px] flex-col gap-0.5 text-[10px] text-zinc-500 sm:flex">
            时刻
            <input
              className="rounded border border-zinc-700 bg-zinc-950 px-2 py-1.5 font-mono text-[12px]"
              value={seedTime}
              onChange={(ev) => setSeedTime(ev.target.value)}
            />
          </label>
          <label className="w-[100px] flex-col gap-0.5 text-[10px] text-zinc-500 sm:flex">
            历法
            <select
              className="rounded border border-zinc-700 bg-zinc-950 px-2 py-1.5 font-mono text-[12px]"
              value={seedCalendar}
              onChange={(ev) => setSeedCalendar(ev.target.value)}
            >
              <option value="solar">solar</option>
              <option value="lunar">lunar</option>
            </select>
          </label>
          <label className="w-[92px] flex-col gap-0.5 text-[10px] text-zinc-500 sm:flex">
            性别
            <select
              className="rounded border border-zinc-700 bg-zinc-950 px-2 py-1.5 font-mono text-[12px]"
              value={seedGender}
              onChange={(ev) => setSeedGender(ev.target.value as "male" | "female")}
            >
              <option value="male">男</option>
              <option value="female">女</option>
            </select>
          </label>
          <label className="w-[100px] flex-col gap-0.5 text-[10px] text-zinc-500 sm:flex">
            参考年
            <input
              className="rounded border border-zinc-700 bg-zinc-950 px-2 py-1.5 font-mono text-[12px]"
              value={seedRefYear}
              onChange={(ev) => setSeedRefYear(ev.target.value)}
            />
          </label>
          <button
            type="button"
            disabled={collisionBusy || loading}
            onClick={() => void runCollisionPreview()}
            className="rounded-md border border-violet-500/60 bg-violet-600/45 px-3 py-2 text-[12px] font-semibold text-white hover:bg-violet-600/65 disabled:opacity-40"
          >
            {collisionBusy ? "演算中…" : "运行演算"}
          </button>
        </div>
        {collisionErr ? <p className="mt-2 text-[11px] text-rose-400">{collisionErr}</p> : null}
        {typeof patternRowsCount === "number" ? (
          <p className="mt-2 text-[10px] text-zinc-500">本次 L2 行数：{patternRowsCount}</p>
        ) : null}
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <ClimateFieldStrengthCompare physicsTensor={physicsTensor} />
          <ConflictTopologyLossPanel physicsTensor={physicsTensor} />
        </div>
      </section>
    </div>
  );
}
