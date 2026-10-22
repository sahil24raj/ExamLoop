"use client";

import React, { useEffect, useState, useCallback, Suspense } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  FileText,
  ArrowRight,
  TrendingUp,
  Bookmark,
  Sparkles,
  HelpCircle,
  Loader2,
  Clock,
  Layers,
  ChevronRight,
  ExternalLink,
  ShieldAlert,
  ShieldCheck,
  RotateCcw,
  BookOpen
} from "lucide-react";
import { api, AttemptResults, EvaluationDetail } from "@/lib/api";
import { supabase, isSupabaseConfigured } from "@/lib/supabase";
import EvidenceModal from "@/components/EvidenceModal";

export default function ResultsPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#060807] flex items-center justify-center p-4">
          <div className="flex items-center gap-3 text-[#A7B8AE] text-sm">
            <Loader2 className="w-5 h-5 animate-spin text-[#24EACE]" />
            Loading evaluation report and rubric feedback...
          </div>
        </div>
      }
    >
      <ResultsContent />
    </Suspense>
  );
}

function ResultsContent() {
  const params = useParams();
  const router = useRouter();
  const attemptId = params?.id as string;

  const [results, setResults] = useState<AttemptResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [generatingAdaptive, setGeneratingAdaptive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Evidence modal state
  const [modalEvidence, setModalEvidence] = useState<any[]>([]);
  const [modalTitle, setModalTitle] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);

  const loadResults = useCallback(() => {
    if (!attemptId) return;
    api.getAttemptResults(attemptId)
      .then((res) => {
        setResults(res);
        setError(null);
      })
      .catch((err) => {
        setError(err.message || "Failed to load attempt results");
      })
      .finally(() => setLoading(false));
  }, [attemptId]);

  useEffect(() => {
    loadResults();

    if (isSupabaseConfigured) {
      const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
        if (session && attemptId) {
          loadResults();
        }
      });
      return () => {
        subscription.unsubscribe();
      };
    }
  }, [attemptId, loadResults]);

  const handleOpenEvidence = (ev: EvaluationDetail) => {
    setModalEvidence(ev.source_references || []);
    setModalTitle(`Source Grounding: ${ev.question_text.slice(0, 60)}...`);
    setIsModalOpen(true);
  };

  const handleGenerateAdaptive = async () => {
    if (!results?.subject_id) return;
    setGeneratingAdaptive(true);
    try {
      const newTest = await api.generateTest(results.subject_id, {
        test_type: "adaptive",
        target_concept_ids: results.adaptive_recommendation?.target_concept_ids,
        title: `Targeted Practice: ${results.adaptive_recommendation?.primary_focus || results.subject_name}`
      });
      router.push(`/tests/${newTest.id}`);
    } catch (err: any) {
      alert("Failed to generate adaptive test: " + err.message);
      setGeneratingAdaptive(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#060807] flex flex-col items-center justify-center p-6 text-center">
        <Loader2 className="w-9 h-9 animate-spin text-[#24EACE] mb-4" />
        <h2 className="text-base font-semibold text-[#F9F9F9]">Synthesizing Detailed Rubric Feedback</h2>
        <p className="text-xs text-[#A7B8AE] mt-1">Normalizing scores /10 and mapping conceptual weak areas...</p>
      </div>
    );
  }

  if (error || !results) {
    return (
      <div className="min-h-screen bg-[#060807] flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-[#0D1410] border border-[#26382D] rounded-2xl p-6 text-center space-y-4 shadow-xl">
          <AlertTriangle className="w-10 h-10 text-[#F87171] mx-auto" />
          <h2 className="text-lg font-bold text-[#F9F9F9]">Unable to Load Results</h2>
          <p className="text-sm text-[#A7B8AE]">{error || "Attempt data not found."}</p>
          <Link
            href="/dashboard"
            className="inline-block px-5 py-2.5 bg-[#24EACE] hover:bg-[#A3FF70] text-[#060807] rounded-xl text-xs font-bold transition shadow-md shadow-[#24EACE]/20"
          >
            Return to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const rawMarks = results.raw_score ?? results.total_score;
  const maxRawMarks = results.max_raw_marks ?? results.max_possible_score;
  const normalized10 = results.normalized_score_10 !== undefined && results.normalized_score_10 !== null
    ? results.normalized_score_10
    : maxRawMarks > 0
    ? Number(((10 * rawMarks) / maxRawMarks).toFixed(1))
    : 0;

  const scorePct = maxRawMarks > 0 ? Math.round((rawMarks / maxRawMarks) * 100) : 0;

  const getSubtypeLabel = (subtype?: string, type?: string) => {
    if (type === "mcq") return "MCQ";
    if (subtype === "very_short") return "Very Short Answer";
    if (subtype === "short") return "Short Answer";
    if (subtype === "long") return "Long Answer";
    return "Subjective";
  };

  return (
    <div className="min-h-screen bg-[#060807] text-[#F9F9F9] font-sans selection:bg-[#24EACE] selection:text-[#060807]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Navigation Breadcrumb */}
        <div className="space-y-2 border-b border-[#26382D] pb-5">
          <div className="flex items-center gap-2 text-xs text-[#A7B8AE] font-medium">
            <Link href="/dashboard" className="hover:text-[#24EACE] transition">Dashboard</Link>
            <span>/</span>
            <Link href={`/subjects/${results.subject_id}`} className="hover:text-[#24EACE] transition">{results.subject_name}</Link>
            <span>/</span>
            <span className="text-[#24EACE] font-semibold">Practice Evaluation</span>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-[#F9F9F9] tracking-tight">
                Practice Performance & Rubric Feedback
              </h1>
              <p className="text-xs sm:text-sm text-[#A7B8AE] mt-1">
                {results.test_title} • Completed in {Math.round((results.time_spent_seconds || 60) / 60)} minutes
              </p>
            </div>

            <Link
              href={`/subjects/${results.subject_id}`}
              className="inline-flex items-center gap-2 px-4 py-2 bg-[#142019] hover:bg-[#1B2B22] text-[#F9F9F9] text-xs font-semibold rounded-xl border border-[#26382D] transition self-start sm:self-auto"
            >
              <BookOpen className="w-4 h-4 text-[#24EACE]" />
              Syllabus Workspace
            </Link>
          </div>
        </div>

        {/* Source Grounding Mode Alert */}
        {results.source_mode === "syllabus_scoped" ? (
          <div className="p-4 rounded-2xl bg-[#281F0D] border border-[#523F17] flex items-start gap-3 text-xs text-[#FBBF24]">
            <ShieldAlert className="w-4 h-4 text-[#FBBF24] shrink-0 mt-0.5" />
            <div>
              <strong className="font-semibold block text-[#FBBF24]">Syllabus-Scoped AI Practice</strong>
              <span>
                Generated from syllabus topic titles. Answers were evaluated via AI model knowledge and verified criteria, not from uploaded lecture notes.
              </span>
            </div>
          </div>
        ) : (
          <div className="p-4 rounded-2xl bg-[#0D2418] border border-[#1C4D34] flex items-start gap-3 text-xs text-[#A3FF70]">
            <ShieldCheck className="w-4 h-4 text-[#A3FF70] shrink-0 mt-0.5" />
            <div>
              <strong className="font-semibold block text-[#A3FF70]">Reference Grounded Practice</strong>
              <span>
                Evaluated against rubrics directly derived from your course notes and syllabus references.
              </span>
            </div>
          </div>
        )}

        {/* Score Overview Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Main Normalized Score */}
          <div className="bg-[#0D1410] p-6 rounded-2xl border border-[#26382D] shadow-xl space-y-2 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-28 h-28 bg-[#24EACE]/10 rounded-full blur-2xl pointer-events-none" />
            <span className="text-xs font-bold uppercase tracking-wider text-[#A7B8AE]">
              Overall Standardized Score
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-4xl sm:text-5xl font-extrabold text-[#A3FF70] tracking-tight">
                {normalized10.toFixed(1)}
              </span>
              <span className="text-lg text-[#A7B8AE] font-bold">/ 10</span>
              <span className="ml-auto text-xs font-bold px-2.5 py-1 rounded-lg bg-[#0D2418] text-[#A3FF70] border border-[#1C4D34]">
                {scorePct}%
              </span>
            </div>
            <div className="pt-2 border-t border-[#26382D] flex items-center justify-between text-xs text-[#A7B8AE]">
              <span>Raw Marks:</span>
              <span className="font-semibold text-[#F9F9F9]">
                {rawMarks} / {maxRawMarks} marks
              </span>
            </div>
          </div>

          {/* Objective Score */}
          <div className="bg-[#0D1410] p-6 rounded-2xl border border-[#26382D] shadow-xl space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider text-[#A7B8AE]">
              Objective MCQs
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-[#24EACE]">{results.objective_score}</span>
              <span className="text-xs text-[#A7B8AE] font-medium">marks earned</span>
            </div>
            <div className="pt-2 border-t border-[#26382D] text-[11px] text-[#A7B8AE]">
              Deterministic single-choice answer key evaluation
            </div>
          </div>

          {/* Subjective Score */}
          <div className="bg-[#0D1410] p-6 rounded-2xl border border-[#26382D] shadow-xl space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider text-[#A7B8AE]">
              Subjective Explanations
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-[#A3FF70]">{results.subjective_score}</span>
              <span className="text-xs text-[#A7B8AE] font-medium">rubric marks</span>
            </div>
            <div className="pt-2 border-t border-[#26382D] text-[11px] text-[#FBBF24]">
              AI-estimated practice evaluation — not an official examiner grade.
            </div>
          </div>
        </div>

        {/* Adaptive Follow-up / Targeted Weak Concept Practice */}
        {results.adaptive_recommendation && (
          <div className="bg-[#0D1410] border-2 border-[#24EACE]/30 rounded-2xl p-6 sm:p-8 space-y-5 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-[#24EACE]/5 rounded-full blur-3xl pointer-events-none" />

            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#24EACE]">
              <Sparkles className="w-4 h-4 text-[#24EACE]" />
              Targeted Practice Loop
            </div>

            <div className="space-y-2">
              <h2 className="text-xl font-bold text-[#F9F9F9]">
                Next Recommendation: Address Identified Knowledge Gaps
              </h2>
              <p className="text-xs sm:text-sm text-[#D0DBD4] leading-relaxed">
                {results.adaptive_recommendation.rationale}
              </p>
            </div>

            {/* Concepts Breakdown */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              {results.adaptive_recommendation.weak_concept_names && results.adaptive_recommendation.weak_concept_names.length > 0 && (
                <div className="bg-[#261012] p-4 rounded-xl border border-[#542125] space-y-2">
                  <div className="text-xs font-bold text-[#F87171] flex items-center gap-1.5">
                    <XCircle className="w-3.5 h-3.5" />
                    Concepts Requiring Review
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {results.adaptive_recommendation.weak_concept_names.map((name, i) => (
                      <span key={i} className="px-2.5 py-0.5 rounded-md text-xs bg-[#261012] text-[#F87171] border border-[#542125] font-medium">
                        {name}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {results.adaptive_recommendation.strong_concept_names && results.adaptive_recommendation.strong_concept_names.length > 0 && (
                <div className="bg-[#0D2418] p-4 rounded-xl border border-[#1C4D34] space-y-2">
                  <div className="text-xs font-bold text-[#A3FF70] flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Mastered Concepts
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {results.adaptive_recommendation.strong_concept_names.map((name, i) => (
                      <span key={i} className="px-2.5 py-0.5 rounded-md text-xs bg-[#0D2418] text-[#A3FF70] border border-[#1C4D34] font-medium">
                        {name}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-3 border-t border-[#26382D]">
              <div className="text-xs text-[#A7B8AE]">
                Primary Focus Topic:{" "}
                <span className="font-bold text-[#F9F9F9]">
                  {results.adaptive_recommendation.primary_focus}
                </span>
              </div>

              <button
                onClick={handleGenerateAdaptive}
                disabled={generatingAdaptive}
                className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-[#24EACE] hover:bg-[#A3FF70] text-[#060807] font-bold text-xs shadow-md shadow-[#24EACE]/20 transition disabled:opacity-50"
              >
                {generatingAdaptive ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Generating Follow-up...
                  </>
                ) : (
                  <>
                    <RotateCcw className="w-3.5 h-3.5 text-[#060807]" />
                    Practice Weak Concepts Again
                    <ArrowRight className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Detailed Question Review List */}
        <div className="space-y-6">
          <div className="flex items-center justify-between border-b border-[#26382D] pb-3">
            <h2 className="text-lg font-bold text-[#F9F9F9]">
              Per-Question Evidence & Rubric Feedback ({results.evaluations.length})
            </h2>
            <span className="text-xs text-[#A7B8AE]">Criterion-level transparent grading</span>
          </div>

          <div className="space-y-6">
            {results.evaluations.map((ev, idx) => {
              const isFullMarks = ev.awarded_marks >= ev.marks;
              const isZeroMarks = ev.awarded_marks === 0;

              return (
                <div
                  key={ev.question_id || idx}
                  className="bg-[#0D1410] rounded-2xl border border-[#26382D] p-6 sm:p-7 space-y-5 shadow-xl hover:border-[#26382D]/80 transition"
                >
                  {/* Header Row */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#26382D] pb-4">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-bold uppercase tracking-wider text-[#A7B8AE]">
                        Question {idx + 1}
                      </span>
                      <span className="text-xs font-semibold px-2.5 py-0.5 rounded-lg bg-[#0D2418] text-[#A3FF70] border border-[#1C4D34]">
                        {getSubtypeLabel(ev.subjective_subtype, ev.question_type)}
                      </span>
                      {ev.review_needed && (
                        <span className="text-[11px] font-bold uppercase bg-[#281F0D] text-[#FBBF24] px-2.5 py-0.5 rounded-lg border border-[#523F17]">
                          Review Needed
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-3">
                      <span
                        className={`text-xs font-bold px-3 py-1 rounded-xl border ${
                          isFullMarks
                            ? "bg-[#0D2418] text-[#A3FF70] border-[#1C4D34]"
                            : isZeroMarks
                            ? "bg-[#261012] text-[#F87171] border-[#542125]"
                            : "bg-[#281F0D] text-[#FBBF24] border-[#523F17]"
                        }`}
                      >
                        {ev.awarded_marks} / {ev.marks} Raw Marks
                      </span>

                      {/* Source Evidence Button */}
                      {ev.source_references && ev.source_references.length > 0 && (
                        <button
                          onClick={() => handleOpenEvidence(ev)}
                          className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-xl bg-[#142019] hover:bg-[#1B2B22] text-[#F9F9F9] border border-[#26382D] transition"
                        >
                          <Bookmark className="w-3.5 h-3.5 text-[#24EACE]" />
                          <span>Page {ev.source_references[0]?.page_number || 1} Evidence</span>
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Question Text */}
                  <div className="text-base font-semibold text-[#F9F9F9] leading-relaxed">
                    {ev.question_text}
                  </div>

                  {/* MCQ Feedback */}
                  {ev.question_type === "mcq" ? (
                    <div className="p-4 rounded-xl bg-[#142019] border border-[#26382D] space-y-3 text-xs">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div className="text-[#D0DBD4]">
                          <span>Your Choice: </span>
                          <strong className="text-[#F9F9F9] uppercase px-2 py-0.5 bg-[#060807] rounded border border-[#26382D] ml-1">
                            {ev.selected_option_id || "Unanswered"}
                          </strong>
                        </div>
                        <div className="text-[#D0DBD4]">
                          <span>Correct Answer: </span>
                          <strong className="text-[#A3FF70] uppercase px-2 py-0.5 bg-[#0D2418] rounded border border-[#1C4D34] ml-1">
                            {ev.correct_option_id}
                          </strong>
                        </div>
                      </div>

                      {ev.explanation && (
                        <div className="text-[#D0DBD4] pt-3 border-t border-[#26382D] leading-relaxed">
                          <strong className="text-[#F9F9F9]">Explanation: </strong>
                          {ev.explanation}
                        </div>
                      )}
                    </div>
                  ) : (
                    /* Subjective Feedback */
                    <div className="space-y-4">
                      {/* Student's submitted text */}
                      <div className="space-y-1.5">
                        <span className="text-xs font-semibold text-[#A7B8AE] uppercase tracking-wider">
                          Your Submitted Answer:
                        </span>
                        <div className="p-4 rounded-xl bg-[#060807] border border-[#26382D] text-xs font-sans leading-relaxed text-[#D0DBD4] whitespace-pre-wrap">
                          {ev.student_answer_text || (
                            <span className="italic text-[#A7B8AE]/60">Blank response submitted.</span>
                          )}
                        </div>
                      </div>

                      {/* Reference Benchmark Answer */}
                      {ev.reference_answer && (
                        <div className="space-y-1.5">
                          <span className="text-xs font-semibold text-[#24EACE] uppercase tracking-wider flex items-center gap-1.5">
                            <Sparkles className="w-3.5 h-3.5" />
                            Model Reference Answer:
                          </span>
                          <div className="p-4 rounded-xl bg-[#0D2418]/40 border border-[#1C4D34] text-xs font-sans leading-relaxed text-[#D0DBD4] whitespace-pre-wrap">
                            {ev.reference_answer}
                          </div>
                        </div>
                      )}

                      {/* Rubric Criterion Breakdown */}
                      {ev.criterion_results && ev.criterion_results.length > 0 && (
                        <div className="space-y-2.5 pt-1">
                          <span className="text-xs font-bold uppercase tracking-wider text-[#D0DBD4] block">
                            Rubric Criterion Breakdown:
                          </span>

                          <div className="space-y-2">
                            {ev.criterion_results.map((c, cIdx) => (
                              <div
                                key={cIdx}
                                className="p-3.5 rounded-xl border border-[#26382D] bg-[#142019] text-xs space-y-1.5"
                              >
                                <div className="flex items-center justify-between font-semibold">
                                  <span className="text-[#F9F9F9]">{c.justification}</span>
                                  <span className="text-[#A3FF70] bg-[#0D2418] px-2.5 py-0.5 rounded-lg border border-[#1C4D34]">
                                    {c.awarded_marks} / {c.max_marks} marks
                                  </span>
                                </div>

                                {c.excerpt && (
                                  <div className="text-[11px] text-[#A7B8AE] italic bg-[#060807] p-2.5 rounded-lg border border-[#26382D]">
                                    Matched excerpt: &ldquo;{c.excerpt}&rdquo;
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Diagnostic Observations */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                        {ev.correct_points && ev.correct_points.length > 0 && (
                          <div className="p-4 rounded-xl bg-[#0D2418] border border-[#1C4D34] text-xs space-y-1.5">
                            <span className="font-bold text-[#A3FF70] flex items-center gap-1.5">
                              <CheckCircle2 className="w-3.5 h-3.5 text-[#A3FF70]" />
                              Key Points Accurately Stated:
                            </span>
                            <ul className="list-disc list-inside space-y-1 text-[#A3FF70]/90">
                              {ev.correct_points.map((pt, pIdx) => (
                                <li key={pIdx}>{pt}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {ev.missing_points && ev.missing_points.length > 0 && (
                          <div className="p-4 rounded-xl bg-[#281F0D] border border-[#523F17] text-xs space-y-1.5">
                            <span className="font-bold text-[#FBBF24] flex items-center gap-1.5">
                              <AlertTriangle className="w-3.5 h-3.5 text-[#FBBF24]" />
                              Key Concepts Missing:
                            </span>
                            <ul className="list-disc list-inside space-y-1 text-[#FBBF24]/90">
                              {ev.missing_points.map((pt, pIdx) => (
                                <li key={pIdx}>{pt}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {ev.misconceptions && ev.misconceptions.length > 0 && (
                          <div className="p-4 rounded-xl bg-[#261012] border border-[#542125] text-xs space-y-1.5 sm:col-span-2">
                            <span className="font-bold text-[#F87171] flex items-center gap-1.5">
                              <XCircle className="w-3.5 h-3.5 text-[#F87171]" />
                              Identified Technical Misconceptions:
                            </span>
                            <ul className="list-disc list-inside space-y-1 text-[#F87171]/90">
                              {ev.misconceptions.map((m, mIdx) => (
                                <li key={mIdx}>{m}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>

                      {/* Actionable Feedback */}
                      {ev.actionable_feedback && (
                        <div className="p-4 rounded-xl bg-[#142019] border border-[#26382D] text-xs text-[#D0DBD4] space-y-1">
                          <strong className="block text-[#24EACE] font-semibold">Actionable Improvement Guidance:</strong>
                          <p className="leading-relaxed">{ev.actionable_feedback}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Bottom Navigation Actions */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-6 border-t border-[#26382D]">
          <Link
            href={`/subjects/${results.subject_id}`}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#142019] hover:bg-[#1B2B22] text-[#F9F9F9] text-xs font-semibold border border-[#26382D] transition"
          >
            <BookOpen className="w-4 h-4 text-[#24EACE]" />
            Back to Syllabus
          </Link>

          <button
            onClick={handleGenerateAdaptive}
            disabled={generatingAdaptive}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-[#24EACE] hover:bg-[#A3FF70] text-[#060807] text-xs font-bold shadow-md shadow-[#24EACE]/20 transition"
          >
            <RotateCcw className="w-4 h-4 text-[#060807]" />
            Practice Weak Concepts Again
          </button>
        </div>
      </div>

      {/* Evidence Viewer Modal */}
      <EvidenceModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        evidence={modalEvidence}
        title={modalTitle}
      />
    </div>
  );
}
