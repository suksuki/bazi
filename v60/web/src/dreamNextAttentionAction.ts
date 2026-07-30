import type { Dispatch, SetStateAction } from "react";

import { selectDreamNextAttention } from "./api";
import {
  dreamEntryState,
  failedRuntimeAction,
  type RuntimeState,
} from "./appRuntime";
import { isDreamReturnAttentionDisplayable } from "./dreamAttentionTypes";

export function createDreamNextAttentionHandler(
  runtime: RuntimeState,
  setRuntime: Dispatch<SetStateAction<RuntimeState>>,
) {
  return (observationRef: string) =>
    commitDreamNextAttention({ observationRef, runtime, setRuntime });
}

async function commitDreamNextAttention({
  observationRef,
  runtime,
  setRuntime,
}: {
  observationRef: string;
  runtime: RuntimeState;
  setRuntime: Dispatch<SetStateAction<RuntimeState>>;
}) {
  const prompt = runtime.grove?.next_attention;
  if (
    !isDreamReturnAttentionDisplayable(prompt) ||
    prompt.status !== "AWAITING_SELECTION" ||
    !prompt.options.some(
      (option) => option.observation_ref === observationRef,
    )
  ) {
    return;
  }
  setRuntime((current) => ({ ...current, busy: true, error: null }));
  try {
    const entry = await selectDreamNextAttention(prompt, observationRef);
    setRuntime((current) => ({
      ...current,
      ...dreamEntryState(entry),
      busy: false,
    }));
  } catch (error) {
    setRuntime((current) => failedRuntimeAction(current, error));
  }
}
