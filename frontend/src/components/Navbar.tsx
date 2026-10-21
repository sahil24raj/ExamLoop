"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  BookOpen, 
  LayoutDashboard, 
  Settings as SettingsIcon, 
  Sparkles, 
  Database, 
  PlusCircle, 
  LogIn, 
  LogOut, 
  User as UserIcon,
  ShieldCheck
} from "lucide-react";
import { api, SettingsStatus } from "@/lib/api";
import { supabase, isSupabaseConfigured } from "@/lib/supabase";
import AuthModal from "@/components/AuthModal";
import type { User } from "@supabase/supabase-js";

export default function Navbar() {
  const pathname = usePathname();
  const [status, setStatus] = useState<SettingsStatus | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  function loadSettings() {
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
          active_user: { id: "usr_01", name: "Demo Student", email: "student@examloop.local" }
        });
      });
  }

  useEffect(() => {
    setMounted(true);
    loadSettings();

    // Check current Supabase session
    if (isSupabaseConfigured) {
      supabase.auth.getUser().then(({ data }) => {
        if (data.user) {
          setUser(data.user);
          loadSettings();
        }
      });

      const { data: authListener } = supabase.auth.onAuthStateChange((_event, session) => {
        setUser(session?.user || null);
        loadSettings();
      });

      return () => {
        authListener?.subscription.unsubscribe();
      };
    }
  }, []);

  async function handleSignOut() {
    if (isSupabaseConfigured) {
      await supabase.auth.signOut();
      setUser(null);
      loadSettings();
    }
  }

  const navLinks = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/subjects/new", label: "Upload Materials", icon: BookOpen },
    { href: "/settings", label: "Settings", icon: SettingsIcon },
  ];

  return (
    <>
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

          {/* Right side: Execution mode indicator, Supabase Auth status, & Primary Action */}
          <div className="flex items-center gap-2.5 sm:gap-3">
            {status && (
              <div className="hidden lg:flex items-center gap-2">
                {status.supabase_db_connected ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-[#0D2418] text-[#24EACE] border border-[#1C4D34]">
                    <ShieldCheck className="w-3 h-3 text-[#24EACE]" />
                    Supabase DB
                  </span>
                ) : null}

                {status.live_ai_available ? (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#0D2418] text-[#A3FF70] border border-[#1C4D34]">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#A3FF70] animate-pulse" />
                    <Sparkles className="w-3.5 h-3.5 text-[#A3FF70]" />
                    Live AI
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#281F0D] text-[#FBBF24] border border-[#523F17]">
                    <Database className="w-3.5 h-3.5 text-[#FBBF24]" />
                    Demo Mode
                  </span>
                )}
              </div>
            )}

            {/* Supabase User Authentication Section */}
            {mounted && (
              user ? (
                <div className="flex items-center gap-2 pl-2 border-l border-[#26382D]">
                  <div className="hidden md:flex flex-col text-right">
                    <span className="text-xs font-bold text-[#F9F9F9] max-w-[120px] truncate">
                      {user.user_metadata?.full_name || user.email?.split("@")[0] || "Student"}
                    </span>
                    <span className="text-[10px] text-[#A7B8AE] max-w-[120px] truncate">
                      {user.email}
                    </span>
                  </div>
                  <div className="w-8 h-8 rounded-full bg-[#142019] border border-[#24EACE]/50 flex items-center justify-center text-[#24EACE] text-xs font-bold shadow-xs">
                    {(user.email?.[0] || "U").toUpperCase()}
                  </div>
                  <button
                    onClick={handleSignOut}
                    title="Sign Out"
                    className="p-1.5 rounded-lg text-[#A7B8AE] hover:text-rose-400 hover:bg-[#142019] transition"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setIsAuthModalOpen(true)}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl border border-[#26382D] bg-[#0D1410] hover:bg-[#142019] text-[#F9F9F9] transition"
                >
                  <LogIn className="w-3.5 h-3.5 text-[#24EACE]" />
                  <span>Sign In</span>
                </button>
              )
            )}

            <Link
              href="/subjects/new"
              className="inline-flex items-center gap-2 text-xs font-bold px-3.5 sm:px-4 py-2 rounded-xl bg-[#24EACE] hover:bg-[#A3FF70] text-[#060807] transition shadow-md shadow-[#24EACE]/20"
            >
              <PlusCircle className="w-4 h-4 text-[#060807]" />
              <span className="hidden sm:inline">Upload Materials</span>
              <span className="sm:hidden">Upload</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Supabase Authentication Modal */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onAuthSuccess={() => {
          loadSettings();
        }}
      />
    </>
  );
}
