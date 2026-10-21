"use client";

import React, { useEffect, useState, useRef, Suspense } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Clock,
  CheckCircle,
  AlertCircle,
  Bookmark,
  ChevronLeft,
  ChevronRight,
  Send,
  Loader2,
  Check,
  FileQuestion,
  Info,
  ShieldCheck,
  Sparkles,
  ArrowLeft
} from "lucide-react";
import { api, TestTakingData, StudentQuestion } from "@/lib/api";

export default function TestTakingPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#060807] flex items-center justify-center p-4">
          <div className="flex items-center gap-3 text-[#A7B8AE] text-sm">
            <Loader2 className="w-5 h-5 animate-spin text-[#24EACE]" />
            Initializing secure examination environment...
          </div>
        </div>
      }
    >
      <TestTakingContent />
    </Suspense>
  );
}

function TestTakingContent() {
  const params = useParams();
  const router = useRouter();
  const testId = params?.id as string;

  const [testData, setTestData] = useState<TestTakingData | null>(null);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, { selected_option_id?: string; answer_text?: string; is_marked_for_review?: boolean }>>({});
  const [loading, setLoading] = useState(true);
  const [savingStatus, setSavingStatus] = useState<"saved" | "saving" | "idle">("saved");
  const [submitting, setSubmitting] = useState(false);
  const [showSubmitModal, setShowSubmitModal] = useState(false);
  const [showExitModal, setShowExitModal] = useState(false);
  const [secondsRemaining, setSecondsRemaining] = useState<number>(20 * 60);
  const [timeSpentSeconds, setTimeSpentSeconds] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Load test data
  useEffect(() => {
    if (!testId) return;
    api.getTestTakingView(testId)
      .then((data) => {
        setTestData(data);
        setAnswers(data.saved_answers || {});
        setSecondsRemaining(data.duration_minutes * 60);
      })
      .catch((err) => {
        setError(err.message || "Failed to load test");
      })
      .finally(() => setLoading(false));
  }, [testId]);

  // Timer countdown
  useEffect(() => {
    if (loading || !testData) return;
    const timer = setInterval(() => {
      setSecondsRemaining((prev) => (prev > 0 ? prev - 1 : 0));
      setTimeSpentSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [loading, testData]);

  // Format time mm:ss
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  // Autosave handler with debounce
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const triggerAutosave = (qId: string, updatedAnswer: { selected_option_id?: string; answer_text?: string; is_marked_for_review?: boolean }) => {
    if (!testData?.attempt_id) return;
    setSavingStatus("saving");
    if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);

    saveTimeoutRef.current = setTimeout(async () => {
      try {
        await api.saveAnswer(testData.attempt_id, {
          question_id: qId,
          ...updatedAnswer
        });
        setSavingStatus("saved");
      } catch (err) {
        console.error("Autosave failed:", err);
        setSavingStatus("idle");
      }
    }, 400);
  };

  const handleSelectOption = (optionId: string) => {
    if (!currentQuestion) return;
    const current = answers[currentQuestion.id] || {};
    const updated = { ...current, selected_option_id: optionId };
    setAnswers((prev) => ({ ...prev, [currentQuestion.id]: updated }));
    triggerAutosave(currentQuestion.id, updated);
  };

  const handleTextChange = (text: string) => {
    if (!currentQuestion) return;
    const current = answers[currentQuestion.id] || {};
    const updated = { ...current, answer_text: text };
    setAnswers((prev) => ({ ...prev, [currentQuestion.id]: updated }));
    triggerAutosave(currentQuestion.id, updated);
  };

  const handleToggleReview = () => {
    if (!currentQuestion) return;
    const current = answers[currentQuestion.id] || {};
    const updated = { ...current, is_marked_for_review: !current.is_marked_for_review };
    setAnswers((prev) => ({ ...prev, [currentQuestion.id]: updated }));
    triggerAutosave(currentQuestion.id, updated);
  };

  const handleSubmit = async () => {
    if (!testData?.attempt_id) return;
    setSubmitting(true);
    setError(null);
    try {
      const payloadAnswers = Object.entries(answers).map(([qId, val]) => ({
        question_id: qId,
        selected_option_id: val.selected_option_id,
        answer_text: val.answer_text,
        is_marked_for_review: val.is_marked_for_review
      }));

      await api.submitAttempt(testData.attempt_id, {
        time_spent_seconds: timeSpentSeconds,
        answers: payloadAnswers
      });

      router.push(`/results/${testData.attempt_id}`);
    } catch (err: any) {
      setError(err.message || "Failed to submit test");
      setSubmitting(false);
      setShowSubmitModal(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#060807] flex flex-col items-center justify-center p-6 text-center">
        <Loader2 className="w-9 h-9 animate-spin text-[#24EACE] mb-4" />
        <h2 className="text-base font-semibold text-[#F9F9F9]">Preparing Examination Workspace</h2>
        <p className="text-xs text-[#A7B8AE] mt-1">Securing question items and initializing rubric grading engine...</p>
      </div>
    );
  }

  if (error || !testData || !testData.questions.length) {
    return (
      <div className="min-h-screen bg-[#060807] flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-[#0D1410] border border-[#26382D] rounded-2xl p-6 text-center space-y-4 shadow-xl">
          <AlertCircle className="w-10 h-10 text-[#F87171] mx-auto" />
          <h2 className="text-lg font-bold text-[#F9F9F9]">Error Loading Test</h2>
          <p className="text-sm text-[#A7B8AE]">{error || "No questions found for this test."}</p>
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

  const questions = testData.questions;
  const currentQuestion: StudentQuestion = questions[currentIdx];
  const currentAns = answers[currentQuestion.id] || {};

  // Compute answered counts
  const answeredCount = questions.filter((q) => {
    const a = answers[q.id];
    return a && (a.selected_option_id || (a.answer_text && a.answer_text.trim().length > 0));
  }).length;

  const markedForReviewCount = questions.filter((q) => answers[q.id]?.is_marked_for_review).length;

  const getSubtypeLabel = (subtype?: string, type?: string) => {
    if (type === "mcq") return "Single-Choice MCQ";
    if (subtype === "very_short") return "Very Short Answer";
    if (subtype === "short") return "Short Answer";
    if (subtype === "long") return "Long Answer";
    return "Subjective Response";
  };

  const getSubtypeDescription = (subtype?: string, type?: string) => {
    if (type === "mcq") return "Select the single most accurate option.";
    if (subtype === "very_short") return "State concise definition, factual point, or key term.";
    if (subtype === "short") return "Provide 2–3 key principles or comparative distinctions.";
    if (subtype === "long") return "Provide a thorough technical breakdown with trade-offs & mechanics.";
    return "Write a structured response addressable by rubric criteria.";
  };

  const wordCount = (currentAns.answer_text || "").trim().split(/\s+/).filter(Boolean).length;
  const charCount = (currentAns.answer_text || "").length;

  return (
    <div className="min-h-screen bg-[#060807] text-[#F9F9F9] flex flex-col font-sans selection:bg-[#24EACE] selection:text-[#060807]">
      {/* Sticky Top Test Header */}
      <header className="sticky top-0 z-30 bg-[#0D1410]/95 backdrop-blur-md border-b border-[#26382D]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <button
              onClick={() => setShowExitModal(true)}
              className="p-1.5 rounded-lg text-[#A7B8AE] hover:text-[#F9F9F9] hover:bg-[#142019] transition"
              title="Save & Return to Subject"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div className="min-w-0">
              <h1 className="font-bold text-[#F9F9F9] text-sm sm:text-base truncate max-w-xs sm:max-w-md">
                {testData.title}
              </h1>
              <div className="flex items-center gap-2 text-[11px] text-[#A7B8AE]">
                <span>{testData.total_marks} Raw Marks Total</span>
                <span>•</span>
                <span className="text-[#A3FF70] font-medium">Final score /10</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Timer */}
            <div
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-mono font-bold border ${
                secondsRemaining < 300
                  ? "bg-[#261012] text-[#F87171] border-[#542125] animate-pulse"
                  : "bg-[#142019] text-[#A3FF70] border-[#26382D]"
              }`}
            >
              <Clock className="w-3.5 h-3.5 text-[#24EACE]" />
              {formatTime(secondsRemaining)}
            </div>

            {/* Autosave status */}
            <div className="hidden sm:inline-flex items-center gap-1.5 text-xs text-[#A7B8AE] font-medium px-2.5 py-1 bg-[#142019] rounded-lg border border-[#26382D]">
              {savingStatus === "saving" ? (
                <>
                  <Loader2 className="w-3 h-3 animate-spin text-[#24EACE]" />
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Check className="w-3 h-3 text-[#A3FF70]" />
                  <span className="text-[#A3FF70]">Saved</span>
                </>
              )}
            </div>

            {/* Submit CTA */}
            <button
              onClick={() => setShowSubmitModal(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#24EACE] hover:bg-[#A3FF70] text-[#060807] font-bold text-xs shadow-md shadow-[#24EACE]/20 transition active:scale-95"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Submit Test</span>
            </button>
          </div>
        </div>
      </header>

      {/* Syllabus Mode Notice Banner */}
      {testData.source_mode === "syllabus_scoped" ? (
        <div className="bg-[#281F0D] border-b border-[#523F17] px-4 py-2 text-center text-xs text-[#FBBF24] flex items-center justify-center gap-2">
          <Info className="w-3.5 h-3.5 shrink-0" />
          <span>
            <strong>Syllabus Practice Mode:</strong> AI-generated practice based on your syllabus. Answers are not verified against uploaded study notes.
          </span>
        </div>
      ) : (
        <div className="bg-[#0D2418] border-b border-[#1C4D34] px-4 py-2 text-center text-xs text-[#A3FF70] flex items-center justify-center gap-2">
          <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
          <span>
            <strong>Reference Grounded:</strong> Questions and evaluation rubrics are grounded in your uploaded course materials.
          </span>
        </div>
      )}

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 w-full flex-1 flex flex-col md:flex-row gap-6">
        {/* Left: Question Navigator Sidebar */}
        <aside className="w-full md:w-72 shrink-0 space-y-4">
          <div className="bg-[#0D1410] rounded-2xl border border-[#26382D] p-5 space-y-4 shadow-xl">
            <div className="flex items-center justify-between text-xs font-semibold text-[#D0DBD4] border-b border-[#26382D] pb-3">
              <span>Question Palette</span>
              <span className="text-[#24EACE] font-medium">
                {answeredCount} / {questions.length} answered
              </span>
            </div>

            {/* Questions Grid */}
            <div className="grid grid-cols-5 gap-2">
              {questions.map((q, idx) => {
                const isCurrent = idx === currentIdx;
                const a = answers[q.id];
                const isAnswered = a && (a.selected_option_id || (a.answer_text && a.answer_text.trim().length > 0));
                const isReview = a?.is_marked_for_review;

                return (
                  <button
                    key={q.id}
                    onClick={() => setCurrentIdx(idx)}
                    className={`h-10 rounded-xl font-semibold text-xs flex items-center justify-center transition relative ${
                      isCurrent
                        ? "bg-[#24EACE] text-[#060807] font-bold ring-2 ring-[#A3FF70] shadow-md shadow-[#24EACE]/20"
                        : isAnswered
                        ? "bg-[#0D2418] text-[#A3FF70] border border-[#1C4D34] hover:bg-[#142D20]"
                        : "bg-[#142019] text-[#A7B8AE] hover:bg-[#1B2B22] hover:text-[#F9F9F9] border border-[#26382D]"
                    }`}
                  >
                    {idx + 1}
                    {isReview && (
                      <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-[#FBBF24] rounded-full border border-[#0D1410]" />
                    )}
                  </button>
                );
              })}
            </div>

            {/* Legend */}
            <div className="pt-3 border-t border-[#26382D] space-y-2 text-xs text-[#A7B8AE]">
              <div className="flex items-center gap-2">
                <span className="w-3.5 h-3.5 rounded bg-[#0D2418] border border-[#1C4D34]" />
                <span>Answered</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3.5 h-3.5 rounded bg-[#142019] border border-[#26382D]" />
                <span>Unanswered</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3.5 h-3.5 rounded-full bg-[#FBBF24]" />
                <span>Marked for review</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Right: Active Question Card */}
        <main className="flex-1 flex flex-col">
          <div className="bg-[#0D1410] rounded-2xl border border-[#26382D] shadow-xl p-6 sm:p-8 flex-1 flex flex-col justify-between space-y-6">
            <div className="space-y-6">
              {/* Question metadata row */}
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#26382D] pb-4">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#A7B8AE]">
                    Question {currentIdx + 1} of {questions.length}
                  </span>
                  <span className="px-2.5 py-0.5 rounded-lg text-xs font-semibold bg-[#0D2418] text-[#A3FF70] border border-[#1C4D34]">
                    {getSubtypeLabel(currentQuestion.subjective_subtype, currentQuestion.question_type)}
                  </span>
                  {currentQuestion.difficulty_label && (
                    <span className="px-2 py-0.5 rounded-lg text-[11px] font-semibold uppercase bg-[#142019] text-[#A7B8AE] border border-[#26382D]">
                      {currentQuestion.difficulty_label}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-xs font-bold text-[#A3FF70] bg-[#0D2418] px-3 py-1 rounded-lg border border-[#1C4D34]">
                    {currentQuestion.marks} Raw Marks
                  </span>

                  <button
                    onClick={handleToggleReview}
                    className={`inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1 rounded-lg transition border ${
                      currentAns.is_marked_for_review
                        ? "bg-[#281F0D] text-[#FBBF24] border-[#523F17]"
                        : "bg-[#142019] text-[#A7B8AE] border-[#26382D] hover:text-[#F9F9F9]"
                    }`}
                  >
                    <Bookmark className="w-3.5 h-3.5" />
                    {currentAns.is_marked_for_review ? "Marked for Review" : "Mark for Review"}
                  </button>
                </div>
              </div>

              {/* Subtype guidance hint */}
              <p className="text-xs text-[#A7B8AE] italic">
                {getSubtypeDescription(currentQuestion.subjective_subtype, currentQuestion.question_type)}
              </p>

              {/* Question Text */}
              <div className="text-base sm:text-lg font-medium text-[#F9F9F9] leading-relaxed">
                {currentQuestion.question_text}
              </div>

              {/* Answering Area */}
              {currentQuestion.question_type === "mcq" ? (
                <div className="space-y-3 pt-2">
                  {currentQuestion.options?.map((opt) => {
                    const isSelected = currentAns.selected_option_id === opt.id;
                    return (
                      <button
                        key={opt.id}
                        onClick={() => handleSelectOption(opt.id)}
                        className={`w-full text-left p-4 rounded-xl border text-sm font-medium transition flex items-center justify-between gap-3 ${
                          isSelected
                            ? "bg-[#142019] border-2 border-[#24EACE] text-[#F9F9F9] shadow-lg shadow-[#24EACE]/10 ring-1 ring-[#24EACE]"
                            : "bg-[#142019]/60 border-[#26382D] text-[#D0DBD4] hover:border-[#24EACE]/50 hover:bg-[#142019]"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <span
                            className={`w-7 h-7 rounded-lg text-xs font-bold flex items-center justify-center shrink-0 uppercase transition ${
                              isSelected ? "bg-[#24EACE] text-[#060807]" : "bg-[#0D1410] text-[#A7B8AE] border border-[#26382D]"
                            }`}
                          >
                            {opt.id}
                          </span>
                          <span>{opt.text}</span>
                        </div>
                        {isSelected && <Check className="w-4 h-4 text-[#24EACE] shrink-0" />}
                      </button>
                    );
                  })}
                </div>
              ) : (
                <div className="space-y-3 pt-2">
                  <div className="flex items-center justify-between text-xs text-[#A7B8AE]">
                    <span>Type your technical explanation:</span>
                    <span className="font-mono text-[#A7B8AE]">
                      {wordCount} words • {charCount} chars
                    </span>
                  </div>
                  <textarea
                    rows={currentQuestion.subjective_subtype === "long" ? 10 : currentQuestion.subjective_subtype === "short" ? 7 : 4}
                    value={currentAns.answer_text || ""}
                    onChange={(e) => handleTextChange(e.target.value)}
                    placeholder="Write a clear, structured response. Credit is awarded based on semantic accuracy against course rubrics."
                    className="w-full p-4 rounded-xl border border-[#26382D] text-sm font-sans leading-relaxed text-[#F9F9F9] focus:outline-none focus:ring-2 focus:ring-[#24EACE] focus:border-[#24EACE] transition bg-[#060807] placeholder:text-[#A7B8AE]/60"
                  />
                  <div className="flex items-center justify-between text-[11px] text-[#A7B8AE]">
                    <span>Answers are evaluated on conceptual completeness, not rigid length.</span>
                    <span>Autosaves as you type</span>
                  </div>
                </div>
              )}
            </div>

            {/* Bottom Nav Controls */}
            <div className="flex items-center justify-between border-t border-[#26382D] pt-5">
              <button
                onClick={() => setCurrentIdx((prev) => Math.max(0, prev - 1))}
                disabled={currentIdx === 0}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl border border-[#26382D] text-xs font-semibold text-[#D0DBD4] bg-[#142019] hover:bg-[#1B2B22] disabled:opacity-30 transition"
              >
                <ChevronLeft className="w-4 h-4" />
                Previous
              </button>

              <div className="text-xs text-[#A7B8AE] font-medium">
                Question {currentIdx + 1} of {questions.length}
              </div>

              {currentIdx < questions.length - 1 ? (
                <button
                  onClick={() => setCurrentIdx((prev) => Math.min(questions.length - 1, prev + 1))}
                  className="inline-flex items-center gap-1.5 px-5 py-2 rounded-xl bg-[#142019] hover:bg-[#1B2B22] text-[#F9F9F9] text-xs font-semibold border border-[#26382D] transition"
                >
                  Next
                  <ChevronRight className="w-4 h-4" />
                </button>
              ) : (
                <button
                  onClick={() => setShowSubmitModal(true)}
                  className="inline-flex items-center gap-1.5 px-5 py-2 rounded-xl bg-[#24EACE] hover:bg-[#A3FF70] text-[#060807] text-xs font-bold shadow-md shadow-[#24EACE]/20 transition"
                >
                  Finish & Submit
                  <Send className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        </main>
      </div>

      {/* Confirmation Submit Modal */}
      {showSubmitModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0D1410] rounded-2xl max-w-md w-full p-6 space-y-5 shadow-2xl border border-[#26382D]">
            <h3 className="text-lg font-bold text-[#F9F9F9]">Confirm Test Submission</h3>

            <div className="space-y-2 text-sm bg-[#142019] p-4 rounded-xl border border-[#26382D]">
              <div className="flex justify-between text-[#D0DBD4]">
                <span>Total Questions:</span>
                <span className="font-semibold text-[#F9F9F9]">{questions.length}</span>
              </div>
              <div className="flex justify-between text-[#D0DBD4]">
                <span>Answered:</span>
                <span className="font-semibold text-[#A3FF70]">{answeredCount}</span>
              </div>
              <div className="flex justify-between text-[#D0DBD4]">
                <span>Unanswered:</span>
                <span className="font-semibold text-[#F87171]">{questions.length - answeredCount}</span>
              </div>
              {markedForReviewCount > 0 && (
                <div className="flex justify-between text-[#FBBF24]">
                  <span>Marked for review:</span>
                  <span className="font-semibold">{markedForReviewCount}</span>
                </div>
              )}
            </div>

            <p className="text-xs text-[#A7B8AE] leading-relaxed">
              Upon submission, objective MCQs will be scored deterministically, and subjective answers will be evaluated criterion-by-criterion against pre-persisted rubrics with normalized score out of 10.
            </p>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setShowSubmitModal(false)}
                disabled={submitting}
                className="px-4 py-2 text-xs font-semibold text-[#A7B8AE] hover:text-[#F9F9F9]"
              >
                Keep Practicing
              </button>
              <button
                onClick={handleSubmit}
                disabled={submitting}
                className="px-5 py-2.5 rounded-xl bg-[#24EACE] hover:bg-[#A3FF70] text-[#060807] text-xs font-bold shadow-md shadow-[#24EACE]/20 transition disabled:opacity-50 flex items-center gap-1.5"
              >
                {submitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                {submitting ? "Evaluating Rubrics..." : "Confirm & Submit"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Save & Exit Modal */}
      {showExitModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0D1410] rounded-2xl max-w-sm w-full p-6 space-y-4 shadow-2xl border border-[#26382D]">
            <h3 className="text-base font-bold text-[#F9F9F9]">Save and Return</h3>
            <p className="text-xs text-[#A7B8AE] leading-relaxed">
              Your answers are continuously autosaved. You can return to this attempt at any time to resume where you left off.
            </p>
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setShowExitModal(false)}
                className="px-4 py-2 text-xs font-semibold text-[#A7B8AE] hover:text-[#F9F9F9]"
              >
                Continue Practice
              </button>
              <Link
                href="/dashboard"
                className="px-4 py-2 bg-[#142019] hover:bg-[#1B2B22] text-[#F9F9F9] text-xs font-semibold rounded-xl border border-[#26382D] transition"
              >
                Exit to Dashboard
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
