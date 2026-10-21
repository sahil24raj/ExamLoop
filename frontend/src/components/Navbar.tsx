"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookOpen, LayoutDashboard, Settings as SettingsIcon, Sparkles, Database, PlusCircle } from "lucide-react";
import { api, SettingsStatus } from "@/lib/api";

export default function Navbar() {
  const pathname = usePathname();
  const [status, setStatus] = useState<SettingsStatus | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    api.getSettings()
      .then(setStatus)
      .catch(() => {
        setStatus({
          app_name: "ExamLoop",
          app_env: "development",
          demo_mode: false,
          live_ai_available: true,
          nebius_base_url: "",
          nebius_fast_model: "",
          nebius_reasoning_model: "",
          embedding_provider: "lexical",
          storage_dir: "./storage",
          database_url_redacted: "sqlite:///examloop.db",
          active_user: { id: "usr_01", name: "Student", email: "student@examloop.local" }
        });
      });
  }, []);

  const navLinks = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/subjects/new", label: "Upload Materials", icon: BookOpen },
    { href: "/settings", label: "Settings", icon: SettingsIcon },
  ];

  return (
    <header suppressHydrationWarning className="sticky top-0 z-40 w-full border-b border-[#26382D] bg-[#060807]/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-3 group">
            {/* Custom ExamLoop Neon Mark */}
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#24EACE] to-[#06AB63] flex items-center justify-center text-[#060807] shadow-md shadow-[#24EACE]/20 group-hover:scale-105 transition">
              <svg className="w-5 h-5 text-[#060807]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                <path d="M3 3v5h5" />
                <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
                <path d="M16 16h5v5" />
                <circle cx="12" cy="12" r="2" fill="currentColor" stroke="none" />
              </svg>
            </div>
            <div className="flex flex-col">
              <span className="text-lg font-extrabold tracking-tight text-[#F9F9F9] flex items-center gap-1.5">
                ExamLoop
                <span className="text-[10px] tracking-normal font-semibold text-[#A3FF70] bg-[#142019] border border-[#26382D] px-2 py-0.5 rounded-full">
                  AI Practice
                </span>
              </span>
              <span className="text-[11px] text-[#A7B8AE] hidden sm:inline">Your material. Fresh practice.</span>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1.5 ml-4">
            {navLinks.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 px-3.5 py-1.5 text-sm font-semibold rounded-xl transition ${
                    isActive
                      ? "bg-[#142019] text-[#24EACE] border border-[#26382D] shadow-xs"
                      : "text-[#A7B8AE] hover:text-[#F9F9F9] hover:bg-[#0D1410]"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Right side: Execution mode indicator & Primary Action */}
        <div className="flex items-center gap-3">
          {status && (
            <div className="hidden sm:flex items-center">
              {status.live_ai_available ? (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#0D2418] text-[#A3FF70] border border-[#1C4D34]">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#A3FF70] animate-pulse" />
                  <Sparkles className="w-3.5 h-3.5 text-[#A3FF70]" />
                  Live AI Engine
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#281F0D] text-[#FBBF24] border border-[#523F17]">
                  <Database className="w-3.5 h-3.5 text-[#FBBF24]" />
                  Demo Mode
                </span>
              )}
            </div>
          )}

          <Link
            href="/subjects/new"
            className="inline-flex items-center gap-2 text-xs font-bold px-4 py-2 rounded-xl bg-[#24EACE] hover:bg-[#A3FF70] text-[#060807] transition shadow-md shadow-[#24EACE]/20"
          >
            <PlusCircle className="w-4 h-4 text-[#060807]" />
            <span>Upload Materials</span>
          </Link>
        </div>
      </div>
    </header>
  );
}
