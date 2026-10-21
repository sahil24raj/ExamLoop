"use client";

import React, { useState } from "react";
import { supabase, isSupabaseConfigured } from "@/lib/supabase";
import { X, Mail, Lock, Sparkles, AlertCircle, LogIn, UserPlus } from "lucide-react";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAuthSuccess?: () => void;
}

export default function AuthModal({ isOpen, onClose, onAuthSuccess }: AuthModalProps) {
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  async function handleEmailAuth(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setLoading(true);

    try {
      if (!isSupabaseConfigured) {
        throw new Error(
          "Supabase credentials are not configured yet. Please configure NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in frontend/.env.local."
        );
      }

      if (isSignUp) {
        const { data, error: signUpErr } = await supabase.auth.signUp({
          email,
          password,
          options: {
            data: {
              full_name: fullName || email.split("@")[0],
            },
          },
        });
        if (signUpErr) throw signUpErr;

        if (data.session) {
          setSuccessMsg("Account created and signed in successfully!");
          setTimeout(() => {
            onAuthSuccess?.();
            onClose();
          }, 1200);
        } else {
          setSuccessMsg("Account created! Please check your email for confirmation instructions.");
        }
      } else {
        const { error: signInErr } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (signInErr) throw signInErr;

        setSuccessMsg("Signed in successfully!");
        setTimeout(() => {
          onAuthSuccess?.();
          onClose();
        }, 800);
      }
    } catch (err: any) {
      setError(err?.message || "Authentication failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  }

  async function handleGoogleOAuth() {
    setError(null);
    if (!isSupabaseConfigured) {
      setError("Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY first.");
      return;
    }
    try {
      const { error: oauthErr } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: {
          redirectTo: typeof window !== "undefined" ? window.location.origin : undefined,
        },
      });
      if (oauthErr) throw oauthErr;
    } catch (err: any) {
      setError(err?.message || "Failed to initialize Google authentication.");
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
      <div 
        className="relative w-full max-w-md rounded-2xl bg-[#0D1410] border border-[#26382D] p-6 sm:p-8 shadow-2xl shadow-black/80"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-[#A7B8AE] hover:text-[#F9F9F9] hover:bg-[#142019] transition"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#24EACE] to-[#06AB63] flex items-center justify-center text-[#060807] shadow-lg shadow-[#24EACE]/20">
            <Sparkles className="w-5 h-5 text-[#060807]" />
          </div>
          <div>
            <h3 className="text-xl font-extrabold text-[#F9F9F9]">
              {isSignUp ? "Create an ExamLoop Account" : "Sign In to ExamLoop"}
            </h3>
            <p className="text-xs text-[#A7B8AE]">
              {isSignUp
                ? "Save your exam syllabus, practice tests, and progress in Supabase"
                : "Welcome back! Connect your personalized exam practice history"}
            </p>
          </div>
        </div>

        {!isSupabaseConfigured && (
          <div className="mb-4 p-3 rounded-xl bg-[#281F0D] border border-[#523F17] flex items-start gap-2.5 text-xs text-[#FBBF24]">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Supabase Setup Notice</p>
              <p className="mt-0.5 text-[#FBBF24]/90">
                To enable live Supabase authentication, configure <code className="bg-black/40 px-1 py-0.5 rounded">NEXT_PUBLIC_SUPABASE_URL</code> and <code className="bg-black/40 px-1 py-0.5 rounded">NEXT_PUBLIC_SUPABASE_ANON_KEY</code> in <code className="bg-black/40 px-1 py-0.5 rounded">.env.local</code>.
              </p>
            </div>
          </div>
        )}

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-rose-950/40 border border-rose-900/60 flex items-start gap-2 text-xs text-rose-300">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        {successMsg && (
          <div className="mb-4 p-3 rounded-xl bg-[#0D2418] border border-[#1C4D34] flex items-start gap-2 text-xs text-[#A3FF70]">
            <Sparkles className="w-4 h-4 shrink-0 mt-0.5 text-[#A3FF70]" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* OAuth Buttons */}
        <button
          type="button"
          onClick={handleGoogleOAuth}
          className="w-full flex items-center justify-center gap-2.5 px-4 py-2.5 mb-4 rounded-xl border border-[#26382D] bg-[#142019] hover:bg-[#1A2C22] text-[#F9F9F9] text-sm font-semibold transition"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24">
            <path
              fill="#EA4335"
              d="M12 5c1.6 0 3 .6 4.1 1.6l3.1-3.1C17.3 1.7 14.8 1 12 1 7.5 1 3.7 3.6 1.9 7.3l3.7 2.9C6.5 7.4 9 5 12 5z"
            />
            <path
              fill="#4285F4"
              d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.5h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.8z"
            />
            <path
              fill="#FBBC05"
              d="M5.6 14.8c-.2-.7-.4-1.5-.4-2.3s.2-1.6.4-2.3L1.9 7.3C.7 9.7 0 12.3 0 15.2s.7 5.5 1.9 7.9l3.7-2.9z"
            />
            <path
              fill="#34A853"
              d="M12 23.5c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3 0-5.5-2.4-6.4-5.2L1.9 16.5C3.7 20.3 7.5 23.5 12 23.5z"
            />
          </svg>
          Continue with Google
        </button>

        <div className="flex items-center gap-3 my-4">
          <div className="h-px flex-1 bg-[#26382D]" />
          <span className="text-[11px] font-semibold tracking-wider text-[#A7B8AE] uppercase">or with email</span>
          <div className="h-px flex-1 bg-[#26382D]" />
        </div>

        {/* Email & Password Form */}
        <form onSubmit={handleEmailAuth} className="space-y-3.5">
          {isSignUp && (
            <div>
              <label className="block text-xs font-semibold text-[#A7B8AE] mb-1.5">Full Name</label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. Sahil Raj"
                className="w-full px-3.5 py-2.5 rounded-xl bg-[#060807] border border-[#26382D] text-sm text-[#F9F9F9] placeholder-[#5A6D61] focus:outline-hidden focus:border-[#24EACE] transition"
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-[#A7B8AE] mb-1.5">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 absolute left-3.5 top-3 text-[#5A6D61]" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="student@university.edu"
                className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-[#060807] border border-[#26382D] text-sm text-[#F9F9F9] placeholder-[#5A6D61] focus:outline-hidden focus:border-[#24EACE] transition"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#A7B8AE] mb-1.5">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 absolute left-3.5 top-3 text-[#5A6D61]" />
              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-[#060807] border border-[#26382D] text-sm text-[#F9F9F9] placeholder-[#5A6D61] focus:outline-hidden focus:border-[#24EACE] transition"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-2.5 px-4 rounded-xl bg-[#24EACE] hover:bg-[#A3FF70] text-[#060807] text-sm font-bold transition flex items-center justify-center gap-2 shadow-lg shadow-[#24EACE]/20 disabled:opacity-50"
          >
            {loading ? (
              <span>Connecting to Supabase...</span>
            ) : isSignUp ? (
              <>
                <UserPlus className="w-4 h-4" />
                <span>Create Account</span>
              </>
            ) : (
              <>
                <LogIn className="w-4 h-4" />
                <span>Sign In</span>
              </>
            )}
          </button>
        </form>

        {/* Toggle Sign In / Sign Up */}
        <div className="mt-5 text-center">
          <button
            type="button"
            onClick={() => {
              setIsSignUp(!isSignUp);
              setError(null);
              setSuccessMsg(null);
            }}
            className="text-xs text-[#24EACE] hover:text-[#A3FF70] transition font-semibold"
          >
            {isSignUp
              ? "Already have an account? Sign in here"
              : "Don't have an account yet? Create one here"}
          </button>
        </div>
      </div>
    </div>
  );
}
