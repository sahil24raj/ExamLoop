"use client";

import React from "react";
import Link from "next/link";
import {
  BookOpen,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  FileText,
  Sparkles,
  TrendingUp,
  Layers,
  Check
} from "lucide-react";

export default function LandingPage() {
  return (
    <div suppressHydrationWarning className="min-h-screen bg-[#060807] text-[#F9F9F9] flex flex-col font-sans selection:bg-[#06AB63] selection:text-[#060807]">
      {/* Top Banner */}
      <div className="bg-[#0D1410] text-[#A7B8AE] px-4 py-2 text-xs text-center font-medium border-b border-[#26382D]">
        <span className="text-[#24EACE] font-bold mr-1.5">ExamLoop:</span>
        Your material. Fresh practice. Source-grounded adaptive examination engine.
      </div>

      {/* Hero Section */}
      <main className="flex-1 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 relative overflow-hidden">
        {/* Subtle Ambient Radial Glow */}
        <div className="absolute top-1/4 right-5 w-96 h-96 bg-[#06AB63]/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-10 left-10 w-80 h-80 bg-[#24EACE]/5 rounded-full blur-3xl pointer-events-none" />

        <div className="text-center space-y-6 max-w-3xl mx-auto relative z-10">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-bold bg-[#142019] text-[#A3FF70] border border-[#26382D] shadow-xs">
            <Sparkles className="w-3.5 h-3.5 text-[#A3FF70]" />
            Adaptive Exam Preparation Platform
          </div>

          <h1 className="text-4xl sm:text-6xl font-black tracking-tight text-[#F9F9F9] leading-[1.12]">
            Turn Study Material Into{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#24EACE] via-[#A3FF70] to-[#06AB63]">
              Targeted Practice
            </span>
          </h1>

          <p className="text-base sm:text-lg text-[#A7B8AE] leading-relaxed max-w-2xl mx-auto font-normal">
            Upload your syllabus, lecture notes, or past papers. ExamLoop structures your curriculum into units, generates verified practice tests with academic rubrics, and dynamically targets your weak spots.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Link
              href="/dashboard"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-7 py-3.5 rounded-xl bg-[#24EACE] hover:bg-[#A3FF70] text-[#060807] font-bold text-base shadow-lg shadow-[#24EACE]/20 transition group"
            >
              <span>Start Preparing</span>
              <ArrowRight className="w-4 h-4 text-[#060807] group-hover:translate-x-0.5 transition-transform" />
            </Link>

            <Link
              href="/subjects/new"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl bg-[#142019] hover:bg-[#1B2B22] text-[#F9F9F9] font-semibold text-base border border-[#26382D] transition shadow-xs"
            >
              <BookOpen className="w-4 h-4 text-[#A7B8AE]" />
              <span>Upload Study Materials</span>
            </Link>
          </div>

          <p className="text-xs text-[#6C8074] pt-2">
            Includes full DBMS workspace with verified units & topics ready for instant practice.
          </p>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-20 relative z-10">
          <div className="bg-[#0D1410] p-7 rounded-2xl border border-[#26382D] hover:border-[#24EACE]/40 transition space-y-4 shadow-sm group">
            <div className="w-12 h-12 rounded-xl bg-[#142019] text-[#24EACE] border border-[#26382D] flex items-center justify-center group-hover:scale-105 transition">
              <FileText className="w-6 h-6" />
            </div>
            <h2 className="text-lg font-bold text-[#F9F9F9]">1. Source-Grounded Questions</h2>
            <p className="text-sm text-[#A7B8AE] leading-relaxed">
              Every MCQ and subjective prompt cites exact page numbers and stored excerpts from your notes. No hallucinations or unsupported claims.
            </p>
          </div>

          <div className="bg-[#0D1410] p-7 rounded-2xl border border-[#26382D] hover:border-[#A3FF70]/40 transition space-y-4 shadow-sm group">
            <div className="w-12 h-12 rounded-xl bg-[#142019] text-[#A3FF70] border border-[#26382D] flex items-center justify-center group-hover:scale-105 transition">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h2 className="text-lg font-bold text-[#F9F9F9]">2. Transparent Rubric Grading</h2>
            <p className="text-sm text-[#A7B8AE] leading-relaxed">
              Rubrics are persisted before test-taking. Subjective answers receive criterion-by-criterion marks, missing key points, and actionable feedback.
            </p>
          </div>

          <div className="bg-[#0D1410] p-7 rounded-2xl border border-[#26382D] hover:border-[#06AB63]/60 transition space-y-4 shadow-sm group">
            <div className="w-12 h-12 rounded-xl bg-[#142019] text-[#06AB63] border border-[#26382D] flex items-center justify-center group-hover:scale-105 transition">
              <TrendingUp className="w-6 h-6" />
            </div>
            <h2 className="text-lg font-bold text-[#F9F9F9]">3. Explainable Next Test</h2>
            <p className="text-sm text-[#A7B8AE] leading-relaxed">
              No black-box scores. ExamLoop explains exactly why your next test changed based on rubric performance on your recent attempts.
            </p>
          </div>
        </div>

        {/* Comparison Section */}
        <div className="mt-20 bg-[#0D1410] rounded-2xl border border-[#26382D] p-8 sm:p-10 relative z-10 shadow-sm">
          <div className="text-center max-w-xl mx-auto space-y-2 mb-10">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#F9F9F9] tracking-tight">Why ExamLoop Outperforms Generic Quiz Makers</h2>
            <p className="text-sm text-[#A7B8AE]">
              Generic quiz apps produce random trivia without academic rigor or verification.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 divide-y md:divide-y-0 md:divide-x divide-[#26382D]">
            {/* Generic Apps */}
            <div className="space-y-4 pt-4 md:pt-0">
              <div className="text-xs font-bold uppercase tracking-wider text-[#6C8074]">Generic PDF-to-Quiz Generators</div>
              <ul className="space-y-3.5 text-sm text-[#A7B8AE]">
                <li className="flex items-start gap-3">
                  <span className="text-[#EF4444] font-bold text-base leading-none">✕</span>
                  <span>Shallow recall MCQs with unverified answer keys</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-[#EF4444] font-bold text-base leading-none">✕</span>
                  <span>No subjective answer evaluation or feedback</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-[#EF4444] font-bold text-base leading-none">✕</span>
                  <span>Disconnected one-off tests with zero learning loop</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-[#EF4444] font-bold text-base leading-none">✕</span>
                  <span>Black-box mastery percentages fabricated without evidence</span>
                </li>
              </ul>
            </div>

            {/* ExamLoop */}
            <div className="space-y-4 md:pl-8 pt-6 md:pt-0">
              <div className="text-xs font-bold uppercase tracking-wider text-[#24EACE]">The ExamLoop Cycle</div>
              <ul className="space-y-3.5 text-sm text-[#F9F9F9] font-medium">
                <li className="flex items-start gap-3">
                  <Check className="w-4 h-4 text-[#A3FF70] shrink-0 mt-0.5" />
                  <span>Page-verified source grounding for every question & explanation</span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-4 h-4 text-[#A3FF70] shrink-0 mt-0.5" />
                  <span>Criterion-level subjective grading against saved academic rubrics</span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-4 h-4 text-[#A3FF70] shrink-0 mt-0.5" />
                  <span>Explainable adaptive generation targeting identified misconceptions</span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-4 h-4 text-[#A3FF70] shrink-0 mt-0.5" />
                  <span>Honest readiness signals with clear evidence thresholds</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Demo Callout Card */}
        <div className="mt-16 bg-[#142019] border border-[#26382D] rounded-2xl p-6 sm:p-8 flex flex-col sm:flex-row items-center justify-between gap-6 relative z-10">
          <div className="space-y-1 text-center sm:text-left">
            <h3 className="text-lg font-bold text-[#F9F9F9]">Want to see the entire loop in action?</h3>
            <p className="text-sm text-[#A7B8AE]">
              Explore our seeded DBMS module, review a practice test, grade a subjective answer, and inspect your mastery.
            </p>
          </div>
          <Link
            href="/dashboard"
            className="shrink-0 px-6 py-3 bg-[#24EACE] hover:bg-[#A3FF70] text-[#060807] text-sm font-bold rounded-xl shadow-md shadow-[#24EACE]/20 transition"
          >
            Launch Study Workspace
          </Link>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#26382D] bg-[#060807] py-6 relative z-10">
        <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between text-xs text-[#A7B8AE] gap-3">
          <span>ExamLoop — Your material. Fresh practice.</span>
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="hover:text-[#F9F9F9] transition">Dashboard</Link>
            <Link href="/subjects/new" className="hover:text-[#F9F9F9] transition">Upload Materials</Link>
            <Link href="/settings" className="hover:text-[#F9F9F9] transition">Settings</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
