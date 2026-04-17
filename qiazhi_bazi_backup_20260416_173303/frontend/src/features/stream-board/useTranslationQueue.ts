"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { API_BASE, PRELOAD_UI_TEXTS, STATIC_I18N, TRANSLATION_CACHE_MAX, TRANSLATION_DEBOUNCE_MS } from "./constants";
import { cacheKey, isAlreadyTargetLanguage, resolveLocalTermTranslation } from "./utils";
import type { Lang } from "@/types/bazi";

type Params = {
  lang: Lang;
  isExecuting: boolean;
  isStreaming: boolean;
  dynamicTexts: string[];
};

export function useTranslationQueue({ lang, isExecuting, isStreaming, dynamicTexts }: Params) {
  const [translations, setTranslations] = useState<Record<string, string>>({});
  const [i18nCalls, setI18nCalls] = useState(0);
  const translationCacheRef = useRef<Map<string, string>>(new Map());
  const pendingTextsRef = useRef<Set<string>>(new Set());
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const t = (text: string) => translations[text] ?? STATIC_I18N[lang]?.[text] ?? text;

  useEffect(() => () => {
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
  }, []);

  const writeTranslationCache = useCallback((key: string, value: string) => {
    const cache = translationCacheRef.current;
    cache.set(key, value);
    if (cache.size > TRANSLATION_CACHE_MAX) {
      const oldestKey = cache.keys().next().value as string | undefined;
      if (oldestKey) cache.delete(oldestKey);
    }
  }, []);

  const flushTranslationQueue = useCallback(async () => {
    if (lang === "ZH" || isExecuting || isStreaming) return;

    const queued = Array.from(pendingTextsRef.current);
    pendingTextsRef.current.clear();
    if (queued.length === 0) return;

    const merged: Record<string, string> = {};
    const remoteNeeded: string[] = [];

    for (const rawText of queued) {
      const text = rawText.trim();
      if (!text) continue;

      const key = cacheKey(lang, text);
      const cached = translationCacheRef.current.get(key);
      if (cached) {
        merged[text] = cached;
        continue;
      }

      const local = resolveLocalTermTranslation(text, lang);
      if (local) {
        merged[text] = local;
        writeTranslationCache(key, local);
        continue;
      }

      if (isAlreadyTargetLanguage(text, lang)) {
        merged[text] = text;
        writeTranslationCache(key, text);
        continue;
      }

      remoteNeeded.push(text);
    }

    if (Object.keys(merged).length > 0) {
      setTranslations((prev) => ({ ...prev, ...merged }));
    }

    if (remoteNeeded.length === 0) return;

    try {
      setI18nCalls((count) => count + 1);
      const response = await fetch(`${API_BASE}/api/i18n/translate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texts: remoteNeeded, target_lang: lang }),
      });
      const data = await response.json();
      const items = (data?.items ?? []) as string[];
      if (Array.isArray(items) && items.length === remoteNeeded.length) {
        setTranslations((prev) => {
          const next = { ...prev };
          remoteNeeded.forEach((text, index) => {
            next[text] = items[index];
            writeTranslationCache(cacheKey(lang, text), items[index]);
          });
          return next;
        });
      }
    } catch {
      // Ignore translation failures so the main inference flow stays available.
    }
  }, [lang, isExecuting, isStreaming, writeTranslationCache]);

  const enqueueTranslations = useCallback(
    (texts: string[]) => {
      if (lang === "ZH" || isExecuting || isStreaming) return;

      texts.forEach((text) => {
        const value = (text || "").trim();
        if (value) pendingTextsRef.current.add(value);
      });

      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = setTimeout(() => {
        void flushTranslationQueue();
      }, TRANSLATION_DEBOUNCE_MS);
    },
    [lang, isExecuting, isStreaming, flushTranslationQueue],
  );

  useEffect(() => {
    if (lang === "ZH") {
      setTranslations({});
      return;
    }
    enqueueTranslations([...PRELOAD_UI_TEXTS]);
  }, [lang, enqueueTranslations]);

  useEffect(() => {
    if (lang === "ZH" || isExecuting) return;
    enqueueTranslations(dynamicTexts);
  }, [lang, dynamicTexts, isExecuting, isStreaming, enqueueTranslations]);

  return { i18nCalls, t };
}
