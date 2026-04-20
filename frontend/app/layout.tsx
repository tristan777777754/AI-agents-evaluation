import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Agent Evaluation Workbench",
  description: "Phase 1 skeleton for the Agent Evaluation Workbench.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
