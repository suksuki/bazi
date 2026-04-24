import { NextRequest, NextResponse } from "next/server";

const BACKEND_BASE = process.env.V17_BACKEND_INTERNAL_URL || "http://127.0.0.1:8017";
const SESSION_COOKIE = "v17_session";
const ROLE_COOKIE = "v17_role";

function cookieConfig(maxAgeSec = 60 * 60 * 24 * 7) {
  return {
    httpOnly: true,
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: maxAgeSec,
  };
}

async function forward(req: NextRequest, path: string[]) {
  const targetPath = path.join("/");
  const url = new URL(`${BACKEND_BASE}/v17/auth/${targetPath}`);
  url.search = req.nextUrl.search;

  const init: RequestInit = {
    method: req.method,
    headers: {
      "Content-Type": req.headers.get("content-type") || "application/json",
      ...(req.headers.get("cookie") ? { cookie: req.headers.get("cookie") as string } : {}),
      ...(req.headers.get("user-agent") ? { "user-agent": req.headers.get("user-agent") as string } : {}),
      ...(req.headers.get("x-forwarded-for") ? { "x-forwarded-for": req.headers.get("x-forwarded-for") as string } : {}),
    },
    cache: "no-store",
  };

  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.text();
  }

  const resp = await fetch(url.toString(), init);
  const text = await resp.text();
  let data: unknown = {};
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { ok: false, detail: text || "non-json response" };
  }
  const responseBody =
    data && typeof data === "object" && !Array.isArray(data)
      ? (() => {
          const row = { ...(data as Record<string, unknown>) };
          delete row.session_token;
          return row;
        })()
      : data;

  const next = NextResponse.json(responseBody, { status: resp.status });
  const op = path[0] || "";
  if ((op === "login" || op === "register") && resp.ok) {
    const row = data && typeof data === "object" ? (data as Record<string, unknown>) : {};
    const token = String(row.session_token || "").trim();
    const role = String((row.user as Record<string, unknown> | undefined)?.role || "").trim();
    if (token) {
      next.cookies.set(SESSION_COOKIE, token, cookieConfig());
    }
    if (role) {
      next.cookies.set(ROLE_COOKIE, role, cookieConfig());
    }
  }
  if (op === "me" && resp.ok) {
    const row = data && typeof data === "object" ? (data as Record<string, unknown>) : {};
    const role = String((row.user as Record<string, unknown> | undefined)?.role || "").trim();
    if (role) {
      next.cookies.set(ROLE_COOKIE, role, cookieConfig());
    }
  }
  if (op === "logout" || (op === "me" && resp.status === 401)) {
    next.cookies.delete(SESSION_COOKIE);
    next.cookies.delete(ROLE_COOKIE);
  }
  return next;
}

export async function GET(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return forward(req, path || []);
}

export async function POST(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return forward(req, path || []);
}
