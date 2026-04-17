import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const BACKEND_BASE = process.env.V17_BACKEND_INTERNAL_URL || "http://127.0.0.1:8017";

async function forward(req: NextRequest) {
  const target = new URL(`${BACKEND_BASE}/v17/stream`);
  target.search = req.nextUrl.search;

  const init: RequestInit = {
    method: req.method,
    headers: { "Content-Type": req.headers.get("content-type") || "application/json" },
    cache: "no-store",
  };

  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.text();
  }

  const resp = await fetch(target.toString(), init);
  const h = new Headers();
  h.set("Content-Type", resp.headers.get("content-type") || "application/x-ndjson");
  h.set("Cache-Control", "no-cache, no-store");
  h.set("Pragma", "no-cache");
  h.set("Connection", "keep-alive");
  h.set("X-Accel-Buffering", "no");
  const ab = resp.headers.get("x-accel-buffering");
  if (ab) h.set("X-Accel-Buffering", ab);
  return new NextResponse(resp.body, {
    status: resp.status,
    headers: h,
  });
}

export async function GET(req: NextRequest) {
  return forward(req);
}

export async function POST(req: NextRequest) {
  return forward(req);
}
