"use client";

type DbBridgeLite = {
  driver: string;
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  sslmode: string;
  url: string;
  enabled: boolean;
};

type Props = {
  db: DbBridgeLite;
  setDb: (updater: (prev: DbBridgeLite) => DbBridgeLite) => void;
  dbProbeMeta: string;
  busy: string | null;
  saveDb: () => Promise<void>;
  testDb: () => Promise<void>;
  solidBtn: string;
  ghostBtn: string;
};

export function V17_AdminDbPanel({
  db,
  setDb,
  dbProbeMeta,
  busy,
  saveDb,
  testDb,
  solidBtn,
  ghostBtn,
}: Props) {
  return (
    <div className="min-w-0 space-y-4">
      <h2 className="border-b border-zinc-800 pb-2 text-lg font-bold">数据库桥接</h2>
      <div className="grid min-w-0 gap-4 lg:grid-cols-2">
        <div className="min-w-0 space-y-3 rounded-xl border border-zinc-800 bg-zinc-950/40 p-4">
          <div className="grid min-w-0 gap-3 sm:grid-cols-2">
            <label className="text-xs text-zinc-400">
              驱动
              <input className="mt-1 w-full min-w-0 rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={db.driver} onChange={(e) => setDb((s) => ({ ...s, driver: e.target.value }))} />
            </label>
            <label className="text-xs text-zinc-400">
              主机
              <input className="mt-1 w-full min-w-0 rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={db.host} onChange={(e) => setDb((s) => ({ ...s, host: e.target.value }))} />
            </label>
            <label className="text-xs text-zinc-400">
              端口
              <input className="mt-1 w-full min-w-0 rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={db.port} onChange={(e) => setDb((s) => ({ ...s, port: Number(e.target.value) }))} />
            </label>
            <label className="text-xs text-zinc-400">
              数据库
              <input className="mt-1 w-full min-w-0 rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={db.database} onChange={(e) => setDb((s) => ({ ...s, database: e.target.value }))} />
            </label>
            <label className="text-xs text-zinc-400">
              用户名
              <input className="mt-1 w-full min-w-0 rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={db.username} onChange={(e) => setDb((s) => ({ ...s, username: e.target.value }))} />
            </label>
            <label className="text-xs text-zinc-400">
              密码
              <input type="password" className="mt-1 w-full min-w-0 rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={db.password} onChange={(e) => setDb((s) => ({ ...s, password: e.target.value }))} />
            </label>
            <label className="text-xs text-zinc-400">
              SSL 模式
              <input className="mt-1 w-full min-w-0 rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={db.sslmode} onChange={(e) => setDb((s) => ({ ...s, sslmode: e.target.value }))} />
            </label>
            <label className="text-xs text-zinc-400">
              地址
              <input className="mt-1 w-full min-w-0 rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={db.url} onChange={(e) => setDb((s) => ({ ...s, url: e.target.value }))} />
            </label>
          </div>
          <label className="flex items-center gap-2 text-sm text-zinc-300">
            <input type="checkbox" checked={db.enabled} onChange={(e) => setDb((s) => ({ ...s, enabled: e.target.checked }))} />
            启用数据库桥接
          </label>
          <div className="flex flex-wrap gap-2">
            <button onClick={() => void saveDb()} className={solidBtn} disabled={busy === "saveDb"}>保存配置</button>
            <button onClick={() => void testDb()} className={ghostBtn} disabled={busy === "testDb"}>连通测试</button>
          </div>
          {dbProbeMeta ? <div className="break-words text-xs text-emerald-300">{dbProbeMeta}</div> : null}
        </div>

        <div className="min-w-0 rounded-xl border border-zinc-800 bg-zinc-950/40 p-4">
          <div className="mb-2 text-[11px] uppercase tracking-wide text-zinc-500">桥接状态</div>
          <pre className="max-w-full overflow-auto whitespace-pre-wrap break-words rounded-lg border border-zinc-800 bg-zinc-900/60 p-3 text-[11px] text-zinc-300 sm:text-xs">
            {JSON.stringify(db, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}
