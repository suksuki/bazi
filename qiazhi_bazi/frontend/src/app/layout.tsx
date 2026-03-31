import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "掐指 · 测算",
  description: "Qiazhi-Bazi 引导式测算",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="bg-zinc-950 text-zinc-100 antialiased">{children}</body>
    </html>
  );
}
