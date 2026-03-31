import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Qiazhi-Bazi",
  description: "掐指八字 · AI-native 命理推演",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="font-sans">{children}</body>
    </html>
  );
}
