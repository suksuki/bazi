import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const BACKEND_BASE = process.env.V17_BACKEND_INTERNAL_URL || "http://127.0.0.1:8017";

type RouteContext = {
  params: Promise<{ path?: string[] }>;
};

async function resolvePath(context: RouteContext): Promise<string> {
  const params = await context.params;
  const path = Array.isArray(params.path) ? params.path : [];
  return path.map((part) => encodeURIComponent(part)).join("/");
}

async function proxyToV18(req: NextRequest, context: RouteContext): Promise<NextResponse> {
  const path = await resolvePath(context);
  const sourceUrl = new URL(req.url);
  const targetUrl = new URL(`/v18.1/${path}`, BACKEND_BASE);
  sourceUrl.searchParams.forEach((value, key) => {
    targetUrl.searchParams.append(key, value);
  });

  const headers = new Headers();
  const contentType = req.headers.get("content-type");
  const accept = req.headers.get("accept");
  const cookie = req.headers.get("cookie");
  if (contentType) headers.set("content-type", contentType);
  if (accept) headers.set("accept", accept);
  if (cookie) headers.set("cookie", cookie);

  const init: RequestInit = {
    method: req.method,
    headers,
    cache: "no-store",
    redirect: "manual",
  };

  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.text();
  }

  const upstream = await fetch(targetUrl, init);
  const body = await upstream.text();
  const responseHeaders = new Headers();
  responseHeaders.set("content-type", upstream.headers.get("content-type") || "application/json; charset=utf-8");
  const setCookie = upstream.headers.get("set-cookie");
  if (setCookie) responseHeaders.set("set-cookie", setCookie);

  return new NextResponse(body, {
    status: upstream.status,
    headers: responseHeaders,
  });
}

export async function GET(req: NextRequest, context: RouteContext): Promise<NextResponse> {
  return proxyToV18(req, context);
}

export async function POST(req: NextRequest, context: RouteContext): Promise<NextResponse> {
  return proxyToV18(req, context);
}

export async function PUT(req: NextRequest, context: RouteContext): Promise<NextResponse> {
  return proxyToV18(req, context);
}

export async function PATCH(req: NextRequest, context: RouteContext): Promise<NextResponse> {
  return proxyToV18(req, context);
}
