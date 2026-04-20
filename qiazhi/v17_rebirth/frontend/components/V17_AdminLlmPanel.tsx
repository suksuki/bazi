"use client";

type LlmNodeLite = {
  provider: string;
  host: string;
  port: number;
  model: string;
  httpTimeoutSec: number;
  fuseWaitSec: number;
};

type Props = {
  llm: LlmNodeLite;
  setLlm: (updater: (prev: LlmNodeLite) => LlmNodeLite) => void;
  llmBaseUrl: string;
  llmProbeMeta: string;
  llmPrompt: string;
  setLlmPrompt: (value: string) => void;
  llmModels: string[];
  llmTestReply: string;
  busy: string | null;
  saveLlm: () => Promise<void>;
  testLlm: () => Promise<void>;
  loadModels: () => Promise<void>;
  testLlmChat: () => Promise<void>;
  solidBtn: string;
  ghostBtn: string;
};

export function V17_AdminLlmPanel({
  llm,
  setLlm,
  llmBaseUrl,
  llmProbeMeta,
  llmPrompt,
  setLlmPrompt,
  llmModels,
  llmTestReply,
  busy,
  saveLlm,
  testLlm,
  loadModels,
  testLlmChat,
  solidBtn,
  ghostBtn,
}: Props) {
  return (
    <div className="space-y-4">
      <h2 className="border-b border-zinc-800 pb-2 text-lg font-bold">LLM 节点配置</h2>
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-3 rounded-xl border border-zinc-800 bg-zinc-950/40 p-4">
          <div className="grid gap-3 md:grid-cols-2">
            <label className="text-xs text-zinc-400">
              提供商
              <input className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={llm.provider} onChange={(e) => setLlm((s) => ({ ...s, provider: e.target.value }))} />
            </label>
            <label className="text-xs text-zinc-400">
              模型
              <input className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={llm.model} onChange={(e) => setLlm((s) => ({ ...s, model: e.target.value }))} />
            </label>
            <label className="text-xs text-zinc-400">
              主机
              <input className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={llm.host} onChange={(e) => setLlm((s) => ({ ...s, host: e.target.value }))} />
            </label>
            <label className="text-xs text-zinc-400">
              端口
              <input className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={llm.port} onChange={(e) => setLlm((s) => ({ ...s, port: Number(e.target.value) }))} />
            </label>
            <label className="text-xs text-zinc-400">
              接口超时
              <input className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={llm.httpTimeoutSec} onChange={(e) => setLlm((s) => ({ ...s, httpTimeoutSec: Number(e.target.value) }))} />
            </label>
            <label className="text-xs text-zinc-400">
              熔断等待
              <input className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 p-2 text-sm" value={llm.fuseWaitSec} onChange={(e) => setLlm((s) => ({ ...s, fuseWaitSec: Number(e.target.value) }))} />
            </label>
          </div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-2 text-[11px] text-zinc-400">
            接口地址：<span className="text-zinc-200">{llmBaseUrl}</span>
          </div>
          <div className="flex flex-wrap gap-2">
            <button onClick={() => void saveLlm()} className={solidBtn} disabled={busy === "saveLlm"}>保存配置</button>
            <button onClick={() => void testLlm()} className={ghostBtn} disabled={busy === "testLlm"}>连通测试</button>
            <button onClick={() => void loadModels()} className={ghostBtn} disabled={busy === "loadModels"}>加载模型</button>
          </div>
          {llmProbeMeta ? <div className="text-xs text-emerald-300">{llmProbeMeta}</div> : null}
        </div>

        <div className="space-y-3 rounded-xl border border-zinc-800 bg-zinc-950/40 p-4">
          <div>
            <div className="mb-2 text-xs text-zinc-400">模型测试</div>
            <textarea
              className="min-h-[120px] w-full rounded border border-zinc-800 bg-zinc-950 p-2 text-sm"
              value={llmPrompt}
              onChange={(e) => setLlmPrompt(e.target.value)}
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <button onClick={() => void testLlmChat()} className={solidBtn} disabled={busy === "testLlmChat" || !llm.model}>测试对话</button>
          </div>
          {llmModels.length ? (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
              <div className="mb-2 text-[11px] uppercase tracking-wide text-zinc-500">可用模型</div>
              <div className="flex max-h-40 flex-wrap gap-2 overflow-auto">
                {llmModels.map((model) => (
                  <button
                    key={model}
                    type="button"
                    onClick={() => setLlm((s) => ({ ...s, model }))}
                    className={`rounded-full border px-2 py-1 text-[11px] ${llm.model === model ? "border-cyan-400 bg-cyan-950/40 text-cyan-100" : "border-zinc-700 bg-zinc-950 text-zinc-300"}`}
                  >
                    {model}
                  </button>
                ))}
              </div>
            </div>
          ) : null}
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
            <div className="mb-2 text-[11px] uppercase tracking-wide text-zinc-500">测试回复</div>
            <div className="min-h-[120px] whitespace-pre-wrap text-sm text-zinc-200">
              {llmTestReply || "尚未执行测试。"}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
