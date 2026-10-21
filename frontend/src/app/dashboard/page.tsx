"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  FileText,
  CheckCircle,
  BrainCircuit,
  TrendingUp,
  ArrowRight,
  BookOpen,
  Plus,
  AlertTriangle,
  Clock,
  Sparkles,
  ChevronRight,
  Database,
  Layers,
  Sliders,
  CheckSquare,
  Trash2
} from "lucide-react";
import { api, DashboardMetrics, Subject } from "@/lib/api";

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [m, s] = await Promise.all([api.getDashboard(), api.listSubjects()]);
      setMetrics(m);
      setSubjects(s);
    } catch (err) {
      console.error("Dashboard load error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleDeleteWorkspace = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete workspace "${name}"? All associated materials, tests, and score history will be removed.`)) return;
    try {
      await api.deleteSubject(id);
      setSubjects(prev => prev.filter(s => s.id !== id));
      api.getDashboard().then(setMetrics).catch(() => {});
    } catch (err: any) {
      alert("Failed to delete workspace: " + err.message);
    }
  };

  const primarySubject = subjects[0];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Hero / Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-[#26382D] pb-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-bold px-3 py-1 rounded-full bg-[#142019] text-[#A3FF70] border border-[#26382D]">
              <Sparkles className="w-3 h-3 inline mr-1 text-[#A3FF70]" />
              Your Material. Fresh Practice.
            </span>
            <span className="text-xs text-[#6C8074]">•</span>
            <span className="text-xs text-[#A7B8AE]">Transparent Rubric Grading out of 10</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-[#F9F9F9] tracking-tight">Exam Practice Platform</h1>
          <p className="text-sm text-[#A7B8AE] mt-1 max-w-xl">
            Upload study materials, review AI-extracted curriculum units, select practice targets, and test yourself with transparent evaluation.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Link
            href="/subjects/new"
            className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-bold rounded-xl bg-[#24EACE] hover:bg-[#A3FF70] text-[#060807] transition shadow-md shadow-[#24EACE]/20"
          >
            <Plus className="w-4 h-4 text-[#060807]" />
            <span>Upload study material</span>
          </Link>

          {primarySubject && (
            <Link
              href={`/subjects/${primarySubject.id}`}
              className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-bold rounded-xl bg-[#142019] hover:bg-[#1B2B22] text-[#F9F9F9] border border-[#26382D] transition shadow-xs"
            >
              <Sparkles className="w-4 h-4 text-[#A3FF70]" />
              <span>Create practice test</span>
            </Link>
          )}
        </div>
      </div>

      {/* Primary Product Flow Pipeline Rail */}
      <div className="bg-[#0D1410] border border-[#26382D] rounded-2xl p-5 sm:p-6 shadow-sm">
        <h2 className="text-xs font-bold uppercase tracking-wider text-[#A7B8AE] mb-4 flex items-center gap-2">
          <Layers className="w-4 h-4 text-[#24EACE]" />
          The ExamLoop Preparation Cycle
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          <div className="p-3.5 rounded-xl bg-[#142019] border border-[#26382D] space-y-1.5 hover:border-[#24EACE]/40 transition">
            <div className="flex items-center justify-between text-[#24EACE] font-semibold">
              <span className="text-[11px] font-bold uppercase">Step 1</span>
              <FileText className="w-4 h-4" />
            </div>
            <div className="font-bold text-[#F9F9F9] text-sm">Upload Material</div>
            <p className="text-[11px] text-[#A7B8AE]">Notes, syllabus, or lecture plans define strict exam boundaries.</p>
          </div>

          <div className="p-3.5 rounded-xl bg-[#142019] border border-[#26382D] space-y-1.5 hover:border-[#24EACE]/40 transition">
            <div className="flex items-center justify-between text-[#24EACE] font-semibold">
              <span className="text-[11px] font-bold uppercase">Step 2</span>
              <CheckSquare className="w-4 h-4" />
            </div>
            <div className="font-bold text-[#F9F9F9] text-sm">Select Topics</div>
            <p className="text-[11px] text-[#A7B8AE]">Inspect curriculum units, explicit vs inferred concepts, and priority tags.</p>
          </div>

          <div className="p-3.5 rounded-xl bg-[#142019] border border-[#26382D] space-y-1.5 hover:border-[#24EACE]/40 transition">
            <div className="flex items-center justify-between text-[#24EACE] font-semibold">
              <span className="text-[11px] font-bold uppercase">Step 3</span>
              <Sliders className="w-4 h-4" />
            </div>
            <div className="font-bold text-[#F9F9F9] text-sm">Configure Builder</div>
            <p className="text-[11px] text-[#A7B8AE]">Set MCQs + very short, short, and long answer question counts.</p>
          </div>

          <div className="p-3.5 rounded-xl bg-[#142019] border border-[#26382D] space-y-1.5 hover:border-[#A3FF70]/40 transition">
            <div className="flex items-center justify-between text-[#A3FF70] font-semibold">
              <span className="text-[11px] font-bold uppercase">Step 4</span>
              <Sparkles className="w-4 h-4" />
            </div>
            <div className="font-bold text-[#F9F9F9] text-sm">Score & Rubric /10</div>
            <p className="text-[11px] text-[#A7B8AE]">Receive normalized marks out of 10 and targeted adaptive follow-ups.</p>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#0D1410] p-5 rounded-2xl border border-[#26382D] space-y-2 hover:border-[#24EACE]/30 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-[#A7B8AE]">Documents</span>
            <FileText className="w-4 h-4 text-[#24EACE]" />
          </div>
          <div className="text-2xl font-black text-[#F9F9F9]">{metrics?.documents_processed ?? 0}</div>
          <p className="text-xs text-[#6C8074]">Syllabus, notes & papers</p>
        </div>

        <div className="bg-[#0D1410] p-5 rounded-2xl border border-[#26382D] space-y-2 hover:border-[#A3FF70]/30 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-[#A7B8AE]">Tests Graded</span>
            <CheckCircle className="w-4 h-4 text-[#A3FF70]" />
          </div>
          <div className="text-2xl font-black text-[#F9F9F9]">{metrics?.tests_completed ?? 0}</div>
          <p className="text-xs text-[#6C8074]">Evaluated with rubrics</p>
        </div>

        <div className="bg-[#0D1410] p-5 rounded-2xl border border-[#26382D] space-y-2 hover:border-[#24EACE]/30 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-[#A7B8AE]">Topics Tested</span>
            <BrainCircuit className="w-4 h-4 text-[#24EACE]" />
          </div>
          <div className="text-2xl font-black text-[#F9F9F9]">{metrics?.concepts_practiced ?? 0}</div>
          <p className="text-xs text-[#6C8074]">With performance data</p>
        </div>

        <div className="bg-[#0D1410] p-5 rounded-2xl border border-[#26382D] space-y-2 hover:border-[#A3FF70]/30 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-[#A7B8AE]">Avg. Score</span>
            <TrendingUp className="w-4 h-4 text-[#A3FF70]" />
          </div>
          <div className="text-2xl font-black text-[#A3FF70]">
            {metrics?.tests_completed ? `${(metrics.average_score_pct / 10).toFixed(1)} / 10` : "—"}
          </div>
          <p className="text-xs text-[#6C8074]">Normalized out of 10</p>
        </div>
      </div>

      {/* Main Grid: Subjects & Weak Topics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Subjects List (2 Cols) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-[#F9F9F9] flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-[#24EACE]" />
              Your Course Workspaces
            </h2>
            <Link href="/subjects/new" className="text-xs font-bold text-[#24EACE] hover:text-[#A3FF70] transition">
              + Add Course / Materials
            </Link>
          </div>

          {subjects.length === 0 ? (
            <div className="bg-[#0D1410] rounded-2xl border border-[#26382D] p-8 text-center space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-[#142019] border border-[#26382D] flex items-center justify-center mx-auto text-[#24EACE]">
                <BookOpen className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-[#F9F9F9]">No course workspaces created</h3>
              <p className="text-xs text-[#A7B8AE] max-w-sm mx-auto">
                Upload your study materials (notes, syllabus, lecture planner, PYQs) to create a workspace, extract topics, and start generating mock tests.
              </p>
              <div className="pt-2 flex justify-center">
                <Link
                  href="/subjects/new"
                  className="px-5 py-2.5 rounded-xl bg-[#24EACE] hover:bg-[#A3FF70] text-[#060807] text-xs font-bold transition shadow-md shadow-[#24EACE]/20 inline-flex items-center gap-2"
                >
                  <Plus className="w-4 h-4 text-[#060807]" />
                  <span>Upload study materials</span>
                </Link>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {subjects.map((s) => (
                <div
                  key={s.id}
                  className="bg-[#0D1410] p-5 rounded-2xl border border-[#26382D] hover:border-[#24EACE]/40 transition flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xs"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-[#F9F9F9] text-base">{s.name}</span>
                      {s.exam_date && (
                        <span className="text-[11px] font-semibold bg-[#142019] text-[#A7B8AE] px-2 py-0.5 rounded-md border border-[#26382D]">
                          Exam: {s.exam_date}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-xs text-[#A7B8AE]">
                      <span>{s.document_count} materials</span>
                      <span>•</span>
                      <span>{s.concept_count} topics</span>
                      <span>•</span>
                      <span>{s.test_count} tests created</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2.5">
                    <Link
                      href={`/subjects/${s.id}`}
                      className="px-4 py-2 rounded-xl bg-[#142019] hover:bg-[#1B2B22] text-[#F9F9F9] font-semibold text-xs border border-[#26382D] transition"
                    >
                      Syllabus & Topics
                    </Link>
                    <Link
                      href={`/subjects/${s.id}?open_builder=true`}
                      className="px-4 py-2 rounded-xl bg-[#24EACE] hover:bg-[#A3FF70] text-[#060807] font-bold text-xs shadow-md shadow-[#24EACE]/20 transition"
                    >
                      Create practice test
                    </Link>
                    <button
                      type="button"
                      onClick={() => handleDeleteWorkspace(s.id, s.name)}
                      title="Delete course workspace"
                      className="p-2 rounded-xl bg-[#142019] hover:bg-red-950/40 text-[#A7B8AE] hover:text-red-400 border border-[#26382D] hover:border-red-800/50 transition cursor-pointer"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Weak Topics / Focus Areas (1 Col) */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-[#F9F9F9] flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              Suggested Practice Focus
            </h2>
            <span className="text-[11px] text-[#6C8074]">Heuristic</span>
          </div>

          <div className="bg-[#0D1410] rounded-2xl border border-[#26382D] p-5 space-y-3">
            {metrics?.topics_needing_practice && metrics.topics_needing_practice.length > 0 ? (
              <div className="space-y-3">
                {metrics.topics_needing_practice.map((t) => (
                  <div
                    key={t.concept_id}
                    className="p-3.5 rounded-xl border border-amber-900/40 bg-amber-950/20 space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-sm text-[#F9F9F9]">{t.name}</span>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-amber-300 bg-amber-900/50 border border-amber-700/40 px-2 py-0.5 rounded-md">
                        Review Needed
                      </span>
                    </div>
                    <div className="text-xs text-[#A7B8AE] flex items-center justify-between">
                      <span>Observed in {t.observed_attempts} attempts</span>
                      <Link
                        href={`/subjects/${t.subject_id}?open_builder=true`}
                        className="text-[#24EACE] font-semibold hover:underline"
                      >
                        Practice this →
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6 text-[#A7B8AE] space-y-2">
                <CheckCircle className="w-8 h-8 text-[#A3FF70] mx-auto" />
                <p className="text-xs">No low-mastery gaps observed yet. Take a practice test to calibrate your focus areas.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Attempts History */}
      <div className="space-y-4 pt-4">
        <h2 className="text-lg font-bold text-[#F9F9F9] flex items-center gap-2">
          <Clock className="w-4 h-4 text-[#A7B8AE]" />
          Recent Attempts & Rubric Feedback
        </h2>

        {metrics?.recent_attempts && metrics.recent_attempts.length > 0 ? (
          <div className="bg-[#0D1410] rounded-2xl border border-[#26382D] overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-[#F9F9F9]">
                <thead className="bg-[#142019] text-xs font-bold uppercase text-[#A7B8AE] border-b border-[#26382D]">
                  <tr>
                    <th className="px-5 py-3.5">Test Title</th>
                    <th className="px-5 py-3.5">Subject</th>
                    <th className="px-5 py-3.5">Score (/10)</th>
                    <th className="px-5 py-3.5">Raw Breakdown</th>
                    <th className="px-5 py-3.5 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1A2820]">
                  {metrics.recent_attempts.map((att) => {
                    const normScore = att.max_possible_score > 0
                      ? (10.0 * att.total_score / att.max_possible_score).toFixed(1)
                      : "0.0";
                    return (
                      <tr key={att.attempt_id} className="hover:bg-[#142019]/70 transition">
                        <td className="px-5 py-4 font-semibold text-[#F9F9F9]">{att.title}</td>
                        <td className="px-5 py-4 text-[#A7B8AE] text-xs">{att.subject_name}</td>
                        <td className="px-5 py-4">
                          <span className="font-black text-[#A3FF70] text-sm">
                            {normScore} / 10
                          </span>
                          <span className="ml-2 text-xs text-[#A7B8AE]">
                            ({att.total_score} / {att.max_possible_score} raw)
                          </span>
                        </td>
                        <td className="px-5 py-4 text-xs text-[#A7B8AE]">
                          MCQ: {att.objective_score} pts • Subj: {att.subjective_score} pts
                        </td>
                        <td className="px-5 py-4 text-right">
                          <Link
                            href={`/results/${att.attempt_id}`}
                            className="inline-flex items-center gap-1 text-xs font-bold text-[#24EACE] hover:text-[#A3FF70] transition"
                          >
                            View Evaluation
                            <ChevronRight className="w-3.5 h-3.5" />
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="bg-[#0D1410] rounded-2xl border border-[#26382D] p-6 text-center text-xs text-[#A7B8AE]">
            No test attempts completed yet. Create and take a practice test to view detailed rubric evaluations.
          </div>
        )}
      </div>
    </div>
  );
}
