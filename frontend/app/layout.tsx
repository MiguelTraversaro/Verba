import type { Metadata } from "next";
import "./globals.css";

import { detectHost } from "./api";

export const metadata: Metadata = {
  title: "Parsed",
  description: "Poli Chatbot",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <link rel="icon" href="icon.ico" />
      <link rel="icon" href="static/icon.ico" />
      <body>{children}</body>
    </html>
  );
}
