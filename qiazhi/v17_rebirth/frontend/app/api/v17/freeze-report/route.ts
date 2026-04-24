import { NextRequest, NextResponse } from "next/server";

const BACKEND_BASE = process.env.V17_BACKEND_INTERNAL_URL || "http://127.0.0.1:8017";

export async function POST(req: NextRequest) {
  const target = `${BACKEND_BASE}/v17/freeze-report`;
  const body = await req.text();
  const resp = await fetch(target, {
    method: "POST",
    headers: {
      "Content-Type": req.headers.get("content-type") || "application/json",
      ...(req.headers.get("cookie") ? { cookie: req.headers.get("cookie") as string } : {}),
    },
    body,
    cache: "no-store",
  });
  const text = await resp.text();
  return new NextResponse(text, {
    status: resp.status,
    headers: { "Content-Type": resp.headers.get("content-type") || "application/json" },
  });
}
