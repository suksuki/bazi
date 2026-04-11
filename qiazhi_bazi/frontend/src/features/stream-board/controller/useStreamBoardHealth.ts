"use client";

import { useCallback, useState } from "react";
import { adminHeaders } from "@/features/stream-board/constants";

type Health = { dbOk: boolean; llmOk: boolean };

export function useStreamBoardHealth(apiBase: string) {
  const [health, setHealth] = useState<Health>({ dbOk: false, llmOk: false });
  const [llmModelName, setLlmModelName] = useState("LLM");

  const refreshHealth = useCallback(async (): Promise<Health> => {
    let dbOk = false;
    let llmOk = false;

    try {
      const dbResponse = await fetch(`${apiBase}/api/admin/db-status`, { headers: adminHeaders });
      const dbData = await dbResponse.json();
      dbOk = Boolean(dbData?.ok);
    } catch {
      dbOk = false;
    }

    try {
      const configResponse = await fetch(`${apiBase}/api/admin/runtime-config`, { headers: adminHeaders });
      const configData = await configResponse.json();
      const llm = configData?.config?.llm ?? {};
      setLlmModelName(String(llm.model || "LLM"));

      const modelsResponse = await fetch(`${apiBase}/api/admin/llm-models`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...adminHeaders },
        body: JSON.stringify({ base_url: llm.base_url, api_key: llm.api_key }),
      });
      const modelsData = await modelsResponse.json();
      llmOk = Boolean(modelsData?.ok && Array.isArray(modelsData?.models));
    } catch {
      llmOk = false;
      setLlmModelName("LLM");
    }

    const next = { dbOk, llmOk };
    setHealth(next);
    return next;
  }, [apiBase]);

  return { health, setHealth, llmModelName, setLlmModelName, refreshHealth };
}
