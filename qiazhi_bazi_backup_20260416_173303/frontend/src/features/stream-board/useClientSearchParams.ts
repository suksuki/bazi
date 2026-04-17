"use client";

import { usePathname } from "next/navigation";
import { useCallback, useLayoutEffect, useState } from "react";

/**
 * 读取当前 URL 查询串，不调用 next/navigation 的 useSearchParams，
 * 从而避免子树进入 Suspense（部分移动 Chrome 会长期停在 fallback「加载中…」）。
 */
export function useClientSearchParams(): URLSearchParams {
  const pathname = usePathname();
  const [params, setParams] = useState<URLSearchParams>(() => new URLSearchParams());

  const read = useCallback(() => {
    if (typeof window === "undefined") return new URLSearchParams();
    return new URLSearchParams(window.location.search);
  }, []);

  useLayoutEffect(() => {
    setParams(read());

    const onChange = () => {
      setParams(read());
    };

    window.addEventListener("popstate", onChange);

    const h = history;
    const nativePush = h.pushState.bind(h);
    const nativeReplace = h.replaceState.bind(h);

    h.pushState = (...args: Parameters<History["pushState"]>) => {
      const ret = nativePush(...args);
      queueMicrotask(onChange);
      return ret;
    };
    h.replaceState = (...args: Parameters<History["replaceState"]>) => {
      const ret = nativeReplace(...args);
      queueMicrotask(onChange);
      return ret;
    };

    return () => {
      window.removeEventListener("popstate", onChange);
      h.pushState = nativePush;
      h.replaceState = nativeReplace;
    };
  }, [pathname, read]);

  return params;
}
