import { useEffect, useState } from "react";

export type V17Frame = {
  layer?: string;
  payload?: {
    render_text?: string;
    deity_scores?: Record<string, number>;
    god_rings?: {
      god_of_use?: string[];
      god_of_taboo?: string[];
    };
  };
};

export function useV17WebStream({
  endpoint = "/v17/stream?will_proxy=stable",
  enabled = true,
  method = "GET",
  body,
}: {
  endpoint?: string | null;
  enabled?: boolean;
  method?: "GET" | "POST";
  body?: Record<string, unknown> | null;
} = {}) {
  const [frames, setFrames] = useState<V17Frame[]>([]);

  useEffect(() => {
    if (!enabled || !endpoint) {
      return;
    }
    const resolvedEndpoint = endpoint;
    let mounted = true;
    const aborter = new AbortController();
    const CACHE_KEY = `v17_mirror_${method}_${resolvedEndpoint}_${body ? JSON.stringify(body) : ""}`;
    
    async function run() {
      try {
        const resp = await fetch(resolvedEndpoint, {
          method,
          signal: aborter.signal,
          headers: method === "POST" ? { "Content-Type": "application/json" } : undefined,
          body: method === "POST" ? JSON.stringify(body || {}) : undefined,
        });
        if (!resp.ok || !resp.body) return;
        const reader = resp.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buf = "";
        
        let localFrames: V17Frame[] = [];
        const cached = localStorage.getItem(CACHE_KEY);
        if (cached) {
          try {
            localFrames = JSON.parse(cached);
            setFrames(localFrames);
          } catch {}
        }

        while (mounted) {
          const { value, done } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });
          const rows = buf.split("\n");
          buf = rows.pop() || "";
          for (const line of rows) {
            const s = String(line || "").trim();
            if (!s) continue;
            try {
              const frame = JSON.parse(s) as V17Frame;
              localFrames = [...localFrames, frame].slice(-120);
              setFrames(localFrames);
              if (frame.layer === "SNAPSHOT") {
                 localStorage.setItem(CACHE_KEY, JSON.stringify(localFrames));
              }
            } catch {
              // ignore malformed chunk
            }
          }
        }
      } catch {
        // silent in demo mode
      }
    }
    
    // Do not setFrames([]) to keep the visual cache intact if moving between modes manually
    void run();
    return () => {
      mounted = false;
      aborter.abort();
    };
  }, [enabled, endpoint, method, body]);

  return { frames };
}
