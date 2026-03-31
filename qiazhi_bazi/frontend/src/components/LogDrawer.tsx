"use client";

import { motion } from "framer-motion";
import type { DecisionStep } from "@/types/bazi";

type Props = {
  open: boolean;
  steps: DecisionStep[];
  onClose: () => void;
  onRollback: (id: string) => void;
  t?: (s: string) => string;
};

export function LogDrawer({ open, steps, onClose, onRollback, t = (s) => s }: Props) {
  return (
    <>
      {open ? <button aria-label="close" className="fixed inset-0 z-30 bg-black/40" onClick={onClose} /> : null}
      <motion.aside
        initial={false}
        animate={{ x: open ? 0 : 360 }}
        transition={{ type: "spring", damping: 28, stiffness: 280 }}
        className="fixed right-0 top-0 z-40 h-full w-80 border-l border-zinc-800 bg-zinc-950 p-4 shadow-2xl"
      >
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-sm font-medium">{t("Decision History")}</h3>
          <button type="button" className="text-xs text-zinc-400" onClick={onClose}>
            {t("关闭")}
          </button>
        </div>
        <div className="space-y-2 overflow-y-auto pb-8">
          {steps.length === 0 ? <p className="text-xs text-zinc-500">{t("暂无历史记录。")}</p> : null}
          {steps.map((s) => (
            <article key={s.id} className="rounded-lg border border-zinc-800 bg-zinc-900 p-3">
              <p className="text-xs text-zinc-500">{new Date(s.createdAt).toLocaleTimeString()}</p>
              <p className="mt-1 text-sm">{s.title}</p>
              {s.answer ? <p className="mt-1 text-xs text-zinc-400">{s.answer}</p> : null}
              <button
                type="button"
                onClick={() => onRollback(s.id)}
                className="mt-2 rounded-md border border-zinc-700 px-2 py-1 text-xs"
              >
                {s.id.startsWith("db-") ? t("记录回滚事件") : t("仅本地撤销")}
              </button>
            </article>
          ))}
        </div>
      </motion.aside>
    </>
  );
}
