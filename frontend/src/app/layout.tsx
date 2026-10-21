import { Suspense } from "react";
import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "ExamLoop — Source-Grounded Adaptive Exam Preparation",
  description: "Personalized, source-grounded exam preparation cycle turning university study notes into targeted diagnostic and adaptive practice tests.",
  other: {
    "darkreader-lock": "true",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning className="h-full bg-[#060807] text-[#F9F9F9] antialiased">
      <head>
        <meta name="darkreader-lock" content="true" />
      </head>
      <body suppressHydrationWarning className="min-h-full flex flex-col font-sans bg-[#060807] text-[#F9F9F9]">
        <Suspense fallback={<div className="h-16 border-b border-[#26382D] bg-[#0D1410]" />}>
          <Navbar />
        </Suspense>
        <div className="flex-1 flex flex-col bg-[#060807]">{children}</div>
      </body>
    </html>
  );
}
