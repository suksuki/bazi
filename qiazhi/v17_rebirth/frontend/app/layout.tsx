import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "掐指一算",
  description: "八字 · 命理 · 运势",
  icons: {
    icon: "/favicon.png",
    apple: "/apple-icon.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className="h-full antialiased"
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
