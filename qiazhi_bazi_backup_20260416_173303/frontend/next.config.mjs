function envTruthy(name) {
  const v = String(process.env[name] ?? "")
    .toLowerCase()
    .trim();
  return v === "1" || v === "true" || v === "yes";
}

/**
 * 生产构建且未配置「公网绝对 URL」的 API 时，默认启用 /api → uvicorn（避免线上包误带 127.0.0.1）。
 * 公网 API 填 https://api.example.com 时不会启用。
 */
function implicitSameOriginApiRewrite() {
  if (envTruthy("NEXT_PUBLIC_QIAZHI_DISABLE_SAME_ORIGIN_REWRITE")) return false;
  if (process.env.NODE_ENV !== "production") return false;
  const v = String(
    process.env.NEXT_PUBLIC_QIAZHI_API ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "",
  ).trim();
  if (!v) return true;
  if (!/^https?:\/\//i.test(v)) return true;
  try {
    const h = new URL(v).hostname.toLowerCase();
    return h === "127.0.0.1" || h === "localhost" || h === "::1";
  } catch {
    return true;
  }
}

/** 仅 Node 可见：Next 把 /api 反代到本机 uvicorn，浏览器只打同源 /api（无 CORS、不暴露 127.0.0.1） */
const internalApi = String(process.env.QIAZHI_INTERNAL_API_URL || "http://127.0.0.1:8001").replace(/\/$/, "");
const sameOriginApiProxy =
  envTruthy("NEXT_PUBLIC_QIAZHI_SAME_ORIGIN_PROXY") || implicitSameOriginApiRewrite();

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    if (!sameOriginApiProxy) return [];
    return [{ source: "/api/:path*", destination: `${internalApi}/api/:path*` }];
  },
  /** 减轻「已缓存旧 HTML + 新 BUILD_ID」导致的 Server Action / RSC 500；静态 chunk 仍走默认长缓存 */
  async headers() {
    return [
      {
        source: "/",
        headers: [{ key: "Cache-Control", value: "private, max-age=0, must-revalidate" }],
      },
    ];
  },
};

export default nextConfig;
