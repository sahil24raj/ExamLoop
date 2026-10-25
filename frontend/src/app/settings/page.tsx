"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Settings as SettingsIcon,
  ShieldCheck,
  Cpu,
  Database,
  Folder,
  Sparkles,
  CheckCircle,
  AlertTriangle,
  ArrowLeft,
  Server,
  Zap,
  Layers
} from "lucide-react";
import { api, SettingsStatus } from "@/lib/api";

export default function SettingsPage() {
  const [status, setStatus] = useState<SettingsStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getSettings()
      .then(setStatus)
      .catch((err) => console.error("Settings load failed:", err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-[#060807] text-[#F9F9F9] font-sans selection:bg-[#24EACE] selection:text-[#060807]">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Breadcrumb */}
        <div>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#A7B8AE] hover:text-[#24EACE] transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Dashboard
          </Link>
        </div>

        <div className="space-y-1 border-b border-[#26382D] pb-5">
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#F9F9F9] tracking-tight">System & AI Settings</h1>
          <p className="text-sm text-[#A7B8AE]">
            OpenRouter AI model priority, local isolated storage, and academic privacy diagnostics.
          </p>
        </div>

        {/* Mode Status Card */}
        <div className="bg-[#0D1410] rounded-2xl border border-[#26382D] p-6 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="text-xs font-bold uppercase tracking-wider text-[#A7B8AE]">Active Execution Mode</div>
            <div className="text-xl font-bold text-[#F9F9F9] flex items-center gap-2">
              {status?.live_ai_available ? (
                <span className="text-[#A3FF70] flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-[#24EACE]" />
                  Live AI Mode Active (OpenRouter)
                </span>
              ) : (
                <span className="text-[#FBBF24] flex items-center gap-2">
                  <Database className="w-5 h-5 text-[#FBBF24]" />
                  Deterministic Demo Fixtures Active
                </span>
              )}
            </div>
            <p className="text-xs text-[#A7B8AE]">
              {status?.live_ai_available
                ? "Requests are processed live via OpenRouter AI with NVIDIA Nemotron model hierarchy."
                : "Using verified deterministic fixtures for reproducible zero-token testing."}
            </p>
          </div>

          <span
            className={`px-3 py-1.5 rounded-full text-xs font-semibold self-start sm:self-auto border ${
              status?.live_ai_available
                ? "bg-[#0D2418] text-[#A3FF70] border-[#1C4D34]"
                : "bg-[#281F0D] text-[#FBBF24] border-[#523F17]"
            }`}
          >
            {status?.live_ai_available ? "Live API Verified" : "Demo Mode"}
          </span>
        </div>

        {/* Model Benchmark & Architecture Report */}
        <div className="bg-[#0D1410] rounded-2xl border border-[#26382D] p-6 space-y-4 shadow-xl">
          <h2 className="text-base font-bold text-[#F9F9F9] flex items-center gap-2">
            <Cpu className="w-4 h-4 text-[#24EACE]" />
            AI Model Hierarchy & OpenRouter Benchmark Report
          </h2>
          <p className="text-xs text-[#A7B8AE] leading-relaxed">
            ExamLoop runs with a multi-tier fallback architecture prioritizing NVIDIA Nemotron models:
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
            {/* Tier 1 */}
            <div className="p-4 rounded-xl border border-[#1C4D34] bg-[#0D2418]/60 space-y-2 text-xs">
              <span className="font-bold text-[#A3FF70] block">1st Priority: NVIDIA Ultra 550B</span>
              <div className="font-mono text-[11px] text-[#A3FF70] bg-[#060807] p-2 rounded-lg border border-[#1C4D34]">
                nvidia/nemotron-3-ultra-550b-a55b:free
              </div>
              <p className="text-[11px] text-[#D0DBD4]">
                550B parameter powerhouse. Tested across extraction, generation & rubric grading with <strong className="text-[#F9F9F9]">100% valid JSON</strong> adherence. Zero cost.
              </p>
            </div>

            {/* Tier 2 */}
            <div className="p-4 rounded-xl border border-[#26382D] bg-[#142019] space-y-2 text-xs">
              <span className="font-bold text-[#24EACE] block">2nd Priority: NVIDIA Lightning</span>
              <div className="font-mono text-[11px] text-[#24EACE] bg-[#060807] p-2 rounded-lg border border-[#26382D]">
                nvidia/nemotron-3.5-lightning:free
              </div>
              <p className="text-[11px] text-[#D0DBD4]">
                Fast secondary free tier fallback for quick subjective evaluation and question generation.
              </p>
            </div>

            {/* Tier 3 */}
            <div className="p-4 rounded-xl border border-[#26382D] bg-[#0D1410] space-y-2 text-xs">
              <span className="font-bold text-[#F9F9F9] block">3rd Priority: Cohere Fallback</span>
              <div className="font-mono text-[11px] text-[#A7B8AE] bg-[#060807] p-2 rounded-lg border border-[#26382D]">
                cohere/north-mini-code:free
              </div>
              <p className="text-[11px] text-[#A7B8AE]">
                Benchmark latency: <strong className="text-[#F9F9F9]">14.5s</strong>. Resilient free backup in case of upstream provider load.
              </p>
            </div>
          </div>
        </div>

        {/* Storage & Retrieval Engine */}
        <div className="bg-[#0D1410] rounded-2xl border border-[#26382D] p-6 space-y-4 shadow-xl">
          <h2 className="text-base font-bold text-[#F9F9F9] flex items-center gap-2">
            <Server className="w-4 h-4 text-[#A7B8AE]" />
            Storage & Retrieval Diagnostics
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-3.5 rounded-xl border border-[#26382D] bg-[#142019] space-y-1">
              <span className="font-semibold text-[#A7B8AE] uppercase tracking-wider block">Retrieval Mode</span>
              <span className="font-mono font-bold text-[#F9F9F9] text-sm">{status?.embedding_provider || "lexical_bm25"}</span>
              <p className="text-[11px] text-[#A7B8AE]">Strict subject-scoped lexical BM25 ranking (vector-ready)</p>
            </div>

            <div className="p-3.5 rounded-xl border border-[#26382D] bg-[#142019] space-y-1">
              <span className="font-semibold text-[#A7B8AE] uppercase tracking-wider block">Database Storage</span>
              <span className="font-mono font-bold text-[#F9F9F9] text-sm truncate block">{status?.database_url_redacted}</span>
              <p className="text-[11px] text-[#A7B8AE]">SQLAlchemy with JSON support and migrations</p>
            </div>

            <div className="p-3.5 rounded-xl border border-[#26382D] bg-[#142019] space-y-1 sm:col-span-2">
              <span className="font-semibold text-[#A7B8AE] uppercase tracking-wider block">Local File Storage</span>
              <span className="font-mono font-bold text-[#F9F9F9] text-sm block">{status?.storage_dir}</span>
              <p className="text-[11px] text-[#A7B8AE]">Subject-isolated safe storage adapter</p>
            </div>
          </div>
        </div>

        {/* Privacy & Security Guarantees */}
        <div className="bg-[#0D1410] rounded-2xl border border-[#26382D] p-6 space-y-3 shadow-xl">
          <h2 className="text-base font-bold text-[#F9F9F9] flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-[#A3FF70]" />
            Academic Privacy & Security Contract
          </h2>

          <ul className="space-y-2 text-xs text-[#D0DBD4]">
            <li className="flex items-start gap-2">
              <CheckCircle className="w-3.5 h-3.5 text-[#24EACE] shrink-0 mt-0.5" />
              <span><strong className="text-[#F9F9F9]">Server-side ownership verification:</strong> Retrieval queries are strictly restricted to the authenticated student and subject.</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-3.5 h-3.5 text-[#24EACE] shrink-0 mt-0.5" />
              <span><strong className="text-[#F9F9F9]">Untrusted reference treatment:</strong> Uploaded notes and student answers cannot override examiner grading instructions or inject prompts.</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-3.5 h-3.5 text-[#24EACE] shrink-0 mt-0.5" />
              <span><strong className="text-[#F9F9F9]">Private document isolation:</strong> Uploaded materials are stored in isolated subject directories and excluded upon deletion.</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-3.5 h-3.5 text-[#24EACE] shrink-0 mt-0.5" />
              <span><strong className="text-[#F9F9F9]">No training on notes:</strong> Study materials are queried ephemerally for test generation and rubric grading only.</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
