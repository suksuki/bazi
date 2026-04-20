"use client";

type PhysicsL0FoundationLite = {
  STEM_BASE?: number;
  BRANCH_BASE?: number;
};

type LooseObject = Record<string, unknown>;

type Props = {
  l0Locked: boolean;
  setL0Locked: (value: boolean) => void;
  physicsConstants: LooseObject;
  setPhysicsConstants: (updater: (prev: LooseObject) => LooseObject) => void;
  asLooseObject: (value: unknown) => LooseObject;
  asNumber: (value: unknown, fallback?: number) => number;
  savePhysics: () => Promise<void>;
  solidBtn: string;
};

export function V17_AdminPhysicsPanel({
  l0Locked,
  setL0Locked,
  physicsConstants,
  setPhysicsConstants,
  asLooseObject,
  asNumber,
  savePhysics,
  solidBtn,
}: Props) {
  const l0Foundation = asLooseObject(physicsConstants.L0_FOUNDATION) as PhysicsL0FoundationLite;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-800 pb-2">
        <div>
          <h2 className="text-lg font-bold">V17 物理常数</h2>
          <p className="mt-1 text-[11px] text-zinc-500">维护 L0 冻结基线的核心常量，避免在运行时漂移。</p>
        </div>
        <button
          onClick={() => setL0Locked(!l0Locked)}
          className="rounded-full border border-rose-500/30 bg-rose-950/20 px-3 py-1 text-xs text-rose-300"
        >
          {l0Locked ? "解锁 L0 物理矩阵" : "锁定 L0 物理矩阵"}
        </button>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-950/40 p-4">
          <h3 className="mb-4 text-xs font-bold uppercase tracking-[0.24em] text-zinc-500">L0 基础常量</h3>
          <label className="mb-1 block text-xs text-zinc-400">天干基准权重（STEM_BASE）</label>
          <input
            type="number"
            disabled={l0Locked}
            className="mb-3 w-full rounded border border-zinc-800 bg-zinc-900 p-2"
            value={asNumber(l0Foundation.STEM_BASE, 0)}
            onChange={(e) =>
              setPhysicsConstants((s) => {
                const updatedFoundation = { ...asLooseObject(s.L0_FOUNDATION), STEM_BASE: asNumber(e.target.value, 0) };
                return { ...s, L0_FOUNDATION: updatedFoundation };
              })
            }
          />
          <label className="mb-1 block text-xs text-zinc-400">地支基准权重（BRANCH_BASE）</label>
          <input
            type="number"
            disabled={l0Locked}
            className="mb-3 w-full rounded border border-zinc-800 bg-zinc-900 p-2"
            value={asNumber(l0Foundation.BRANCH_BASE, 0)}
            onChange={(e) =>
              setPhysicsConstants((s) => {
                const updatedFoundation = { ...asLooseObject(s.L0_FOUNDATION), BRANCH_BASE: asNumber(e.target.value, 0) };
                return { ...s, L0_FOUNDATION: updatedFoundation };
              })
            }
          />
          <button onClick={() => void savePhysics()} className={solidBtn}>
            保存物理常数
          </button>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-950/40 p-4">
          <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.24em] text-zinc-500">当前物理快照</div>
          <pre className="max-h-[320px] overflow-auto rounded-xl border border-zinc-800 bg-zinc-950/80 p-3 text-xs text-zinc-300">
            {JSON.stringify(physicsConstants, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}
