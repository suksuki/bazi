export type JsonResult<T = unknown> = {
  resp: Response;
  data: T;
  ok: boolean;
  error: string;
};

export async function requestJson<T = unknown>(url: string, init?: RequestInit): Promise<JsonResult<T>> {
  const resp = await fetch(url, init);
  const text = await resp.text();
  let data: unknown = {};

  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { ok: false, error: text.slice(0, 200) || "non-json response" };
  }

  const row = data && typeof data === "object" && !Array.isArray(data) ? (data as Record<string, unknown>) : {};
  const error = String(row.detail || row.error || "");

  return {
    resp,
    data: data as T,
    ok: resp.ok && row.ok !== false,
    error,
  };
}

export function jsonPostInit(body: unknown, init: RequestInit = {}): RequestInit {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");

  return {
    ...init,
    method: "POST",
    headers,
    body: JSON.stringify(body),
  };
}

export function noStoreInit(init: RequestInit = {}): RequestInit {
  return {
    ...init,
    cache: "no-store",
  };
}
