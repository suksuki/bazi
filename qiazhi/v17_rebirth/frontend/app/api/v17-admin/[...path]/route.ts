import { NextRequest, NextResponse } from "next/server";

const BACKEND_BASE = process.env.V17_BACKEND_INTERNAL_URL || "http://127.0.0.1:8017";

async function forward(req: NextRequest, path: string[]) {
  const targetPath = path.join("/");
  const url = new URL(`${BACKEND_BASE}/v17/admin/${targetPath}`);
  url.search = req.nextUrl.search;

  const init: RequestInit = {
    method: req.method,
    headers: { "Content-Type": req.headers.get("content-type") || "application/json" },
    cache: "no-store",
  };

  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.text();
  }

  const resp = await fetch(url.toString(), init);
  const text = await resp.text();
  return new NextResponse(text, {
    status: resp.status,
    headers: { "Content-Type": resp.headers.get("content-type") || "application/json" },
  });
}

export async function GET(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return forward(req, path || []);
}

export async function POST(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  return forward(req, path || []);
}
