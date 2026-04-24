import { NextRequest, NextResponse } from "next/server";

const SESSION_COOKIE = "v17_session";
const ROLE_COOKIE = "v17_role";

function redirectTo(req: NextRequest, pathname: string) {
  const url = req.nextUrl.clone();
  url.pathname = pathname;
  if (pathname === "/login") {
    url.searchParams.set("next", req.nextUrl.pathname);
  } else {
    url.search = "";
  }
  return NextResponse.redirect(url);
}

export function proxy(req: NextRequest) {
  const pathname = req.nextUrl.pathname;
  const hasSession = Boolean(req.cookies.get(SESSION_COOKIE)?.value);
  const role = String(req.cookies.get(ROLE_COOKIE)?.value || "").trim().toLowerCase();

  if (pathname === "/") {
    return redirectTo(req, hasSession ? "/v17/oracle" : "/login");
  }

  if (pathname.startsWith("/login") || pathname.startsWith("/register")) {
    if (hasSession) return redirectTo(req, "/v17/oracle");
    return NextResponse.next();
  }

  if (pathname.startsWith("/v17/admin")) {
    if (!hasSession) return redirectTo(req, "/login");
    if (role !== "admin") return redirectTo(req, "/v17/oracle");
    return NextResponse.next();
  }

  if (pathname.startsWith("/v17/oracle")) {
    if (!hasSession) return redirectTo(req, "/login");
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/", "/login", "/register", "/v17/:path*"],
};
