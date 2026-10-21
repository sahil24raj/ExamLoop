"use client";

import React, { useState, useEffect } from "react";
import {
  Sliders,
  CheckCircle2,
  FileText,
  Clock,
  Sparkles,
  AlertCircle,
  X,
  Loader2,
  Plus,
  Minus,
  Zap,
  BookOpen,
  Award,
  Layers
} from "lucide-react";
import { CustomTestConfig } from "@/lib/api";

interface TestBuilderModalProps {
  isOpen: boolean;
  onClose: () => void;
  subjectName: string;
  selectedTopicIds: string[];
  selectedTopicNames: string[];
  onGenerate: (config: CustomTestConfig) => Promise<void>;
  generating: boolean;
}

export default function TestBuilderModal({
  isOpen,
  onClose,
  subjectName,
  selectedTopicIds,
  selectedTopicNames,
  onGenerate,
  generating
}: TestBuilderModalProps) {
  // Question mode: objective_only | subjective_only | mixed
  const [mode, setMode] = useState<"objective_only" | "subjective_only" | "mixed">("mixed");
  const [globalDifficulty, setGlobalDifficulty] = useState<"easy" | "medium" | "hard">("medium");

  // Objective controls
  const [mcqCount, setMcqCount] = useState<number>(1);
  const [mcqDiff, setMcqDiff] = useState<"easy" | "medium" | "hard">("medium");

  // Subjective subtypes
  const [vsCount, setVsCount] = useState<number>(0);
  const [vsDiff, setVsDiff] = useState<"easy" | "medium" | "hard">("easy");

  const [sCount, setSCount] = useState<number>(1);
  const [sDiff, setSDiff] = useState<"easy" | "medium" | "hard">("medium");

  const [lCount, setLCount] = useState<number>(1);
  const [lDiff, setLDiff] = useState<"easy" | "medium" | "hard">("hard");

  // Timed settings
  const [isTimed, setIsTimed] = useState<boolean>(false);
  const [durationMinutes, setDurationMinutes] = useState<number>(20);

  // Animated generation progress tracker
  const [genStep, setGenStep] = useState(0);
  const steps = [
    "Analyzing subject syllabus & scope...",
    "Synthesizing questions & marking rubrics...",
    "Validating exact subtype quotas (MCQ/Short/Long)...",
    "Finalizing test & rubric criteria..."
  ];

  useEffect(() => {
    if (!generating) {
      setGenStep(0);
      return;
    }
    const interval = setInterval(() => {
      setGenStep((prev) => (prev < steps.length - 1 ? prev + 1 : prev));
    }, 2400);
    return () => clearInterval(interval);
  }, [generating, steps.length]);

  if (!isOpen) return null;

  // Active counts based on mode
  const effectiveMcq = mode === "subjective_only" ? 0 : mcqCount;
  const effectiveVs = mode === "objective_only" ? 0 : vsCount;
  const effectiveS = mode === "objective_only" ? 0 : sCount;
  const effectiveL = mode === "objective_only" ? 0 : lCount;

  const totalQuestions = effectiveMcq + effectiveVs + effectiveS + effectiveL;

  // Marks: MCQ = 2, Very Short = 2, Short = 5, Long = 10
  const marksMcq = 2;
  const marksVs = 2;
  const marksS = 5;
  const marksL = 10;

  const totalRawMarks =
    effectiveMcq * marksMcq +
    effectiveVs * marksVs +
    effectiveS * marksS +
    effectiveL * marksL;

  const isValid = totalQuestions > 0;

  const handleGlobalDifficultyChange = (diff: "easy" | "medium" | "hard") => {
    setGlobalDifficulty(diff);
    setMcqDiff(diff);
    setVsDiff(diff === "hard" ? "medium" : "easy");
    setSDiff(diff);
    setLDiff(diff === "easy" ? "medium" : "hard");
  };

  // Presets
  const applyPreset = (preset: "quick_triad" | "standard" | "mcq_blitz" | "deep_subjective") => {
    if (preset === "quick_triad") {
      setMode("mixed");
      setMcqCount(1);
      setVsCount(0);
      setSCount(1);
      setLCount(1);
      setDurationMinutes(15);
    } else if (preset === "standard") {
      setMode("mixed");
      setMcqCount(4);
      setVsCount(2);
      setSCount(2);
      setLCount(1);
      setDurationMinutes(30);
    } else if (preset === "mcq_blitz") {
      setMode("objective_only");
      setMcqCount(5);
      setVsCount(0);
      setSCount(0);
      setLCount(0);
      setDurationMinutes(10);
    } else if (preset === "deep_subjective") {
      setMode("subjective_only");
      setMcqCount(0);
      setVsCount(1);
      setSCount(2);
      setLCount(1);
      setDurationMinutes(35);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValid || generating) return;

    const config: CustomTestConfig = {
      title: `${subjectName} Custom Practice`,
      mode,
      global_difficulty: globalDifficulty,
      target_topic_ids: selectedTopicIds,
      mcq_count: effectiveMcq,
      mcq_difficulty: mcqDiff,
      very_short_count: effectiveVs,
      very_short_difficulty: vsDiff,
      short_count: effectiveS,
      short_difficulty: sDiff,
      long_count: effectiveL,
      long_difficulty: lDiff,
      marks_per_type: {
        mcq: marksMcq,
        very_short: marksVs,
        short: marksS,
        long: marksL
      },
      is_timed: isTimed,
      duration_minutes: isTimed ? durationMinutes : 0,
      topic_distribution: "balanced",
      shuffle_questions: true
    };

    await onGenerate(config);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-xs overflow-y-auto">
      <div className="relative w-full max-w-3xl my-8 rounded-3xl bg-[#0D1410] border border-[#26382D] shadow-2xl overflow-hidden flex flex-col text-[#F9F9F9]">
        {/* Modal Header */}
        <div className="p-6 border-b border-[#26382D] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#142019] border border-[#26382D] flex items-center justify-center text-[#24EACE]">
              <Sliders className="w-5 h-5 text-[#24EACE]" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-[#F9F9F9] tracking-tight">Custom Test Builder</h2>
              <p className="text-xs text-[#A7B8AE]">
                {selectedTopicIds.length > 0
                  ? `Targeting ${selectedTopicIds.length} selected topic(s) • ${subjectName}`
                  : `Comprehensive Full Mock Test • All ${subjectName} Material Included`}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={generating}
            className="p-2 rounded-xl text-[#A7B8AE] hover:text-[#F9F9F9] hover:bg-[#142019] transition disabled:opacity-30"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6 flex-1 overflow-y-auto max-h-[70vh]">
          {/* Quick Preset Buttons */}
          <div className="space-y-2">
            <span className="text-xs font-semibold text-[#A7B8AE] flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-[#24EACE]" />
              Quick Presets:
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <button
                type="button"
                onClick={() => applyPreset("quick_triad")}
                className="p-2.5 rounded-xl border border-[#26382D] bg-[#142019] hover:border-[#24EACE]/50 text-left transition group"
              >
                <div className="text-xs font-bold text-[#F9F9F9] group-hover:text-[#24EACE] transition">
                  Triad (1+1+1)
                </div>
                <div className="text-[10px] text-[#A7B8AE]">1 MCQ • 1 Short • 1 Long</div>
              </button>

              <button
                type="button"
                onClick={() => applyPreset("standard")}
                className="p-2.5 rounded-xl border border-[#26382D] bg-[#142019] hover:border-[#24EACE]/50 text-left transition group"
              >
                <div className="text-xs font-bold text-[#F9F9F9] group-hover:text-[#24EACE] transition">
                  Standard Mock
                </div>
                <div className="text-[10px] text-[#A7B8AE]">4 MCQ • 2 Short • 1 Long</div>
              </button>

              <button
                type="button"
                onClick={() => applyPreset("mcq_blitz")}
                className="p-2.5 rounded-xl border border-[#26382D] bg-[#142019] hover:border-[#24EACE]/50 text-left transition group"
              >
                <div className="text-xs font-bold text-[#F9F9F9] group-hover:text-[#24EACE] transition">
                  MCQ Blitz
                </div>
                <div className="text-[10px] text-[#A7B8AE]">5 Rapid MCQs</div>
              </button>

              <button
                type="button"
                onClick={() => applyPreset("deep_subjective")}
                className="p-2.5 rounded-xl border border-[#26382D] bg-[#142019] hover:border-[#24EACE]/50 text-left transition group"
              >
                <div className="text-xs font-bold text-[#F9F9F9] group-hover:text-[#24EACE] transition">
                  Subjective Focus
                </div>
                <div className="text-[10px] text-[#A7B8AE]">Short + Long with Rubrics</div>
              </button>
            </div>
          </div>

          {/* Section: Mode & Global Difficulty */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[#A7B8AE] block">Question Mode</label>
              <div className="grid grid-cols-3 gap-1.5 p-1 rounded-xl bg-[#142019] border border-[#26382D]">
                <button
                  type="button"
                  onClick={() => setMode("mixed")}
                  className={`py-1.5 text-xs font-bold rounded-lg transition ${
                    mode === "mixed"
                      ? "bg-[#24EACE] text-[#060807] shadow-xs"
                      : "text-[#A7B8AE] hover:text-[#F9F9F9]"
                  }`}
                >
                  Mixed
                </button>
                <button
                  type="button"
                  onClick={() => setMode("objective_only")}
                  className={`py-1.5 text-xs font-bold rounded-lg transition ${
                    mode === "objective_only"
                      ? "bg-[#24EACE] text-[#060807] shadow-xs"
                      : "text-[#A7B8AE] hover:text-[#F9F9F9]"
                  }`}
                >
                  MCQ Only
                </button>
                <button
                  type="button"
                  onClick={() => setMode("subjective_only")}
                  className={`py-1.5 text-xs font-bold rounded-lg transition ${
                    mode === "subjective_only"
                      ? "bg-[#24EACE] text-[#060807] shadow-xs"
                      : "text-[#A7B8AE] hover:text-[#F9F9F9]"
                  }`}
                >
                  Subjective
                </button>
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[#A7B8AE] block">Global Default Difficulty</label>
              <div className="grid grid-cols-3 gap-1.5 p-1 rounded-xl bg-[#142019] border border-[#26382D]">
                {(["easy", "medium", "hard"] as const).map((d) => (
                  <button
                    key={d}
                    type="button"
                    onClick={() => handleGlobalDifficultyChange(d)}
                    className={`py-1.5 text-xs font-bold rounded-lg capitalize transition ${
                      globalDifficulty === d
                        ? "bg-[#24EACE] text-[#060807] shadow-xs"
                        : "text-[#A7B8AE] hover:text-[#F9F9F9]"
                    }`}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Section: Objective Section */}
          {mode !== "subjective_only" && (
            <div className="p-4 rounded-2xl bg-[#142019] border border-[#26382D] space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-[#24EACE]" />
                  <span className="text-sm font-bold text-[#F9F9F9]">Objective Questions (MCQs)</span>
                </div>
                <span className="text-xs text-[#A7B8AE]">{marksMcq} marks each</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1 items-center">
                <div className="space-y-1">
                  <span className="text-xs text-[#A7B8AE] block">MCQ Count</span>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setMcqCount(Math.max(0, mcqCount - 1))}
                      className="w-8 h-8 rounded-lg bg-[#0D1410] border border-[#26382D] text-[#A7B8AE] hover:text-[#F9F9F9] flex items-center justify-center transition"
                    >
                      <Minus className="w-3.5 h-3.5" />
                    </button>
                    <input
                      type="number"
                      min={0}
                      max={20}
                      value={mcqCount}
                      onChange={(e) => setMcqCount(Math.max(0, parseInt(e.target.value) || 0))}
                      className="w-16 text-center py-1.5 rounded-lg border border-[#26382D] bg-[#0D1410] text-[#F9F9F9] text-sm font-bold focus:outline-hidden focus:ring-1 focus:ring-[#24EACE]"
                    />
                    <button
                      type="button"
                      onClick={() => setMcqCount(Math.min(20, mcqCount + 1))}
                      className="w-8 h-8 rounded-lg bg-[#0D1410] border border-[#26382D] text-[#A7B8AE] hover:text-[#F9F9F9] flex items-center justify-center transition"
                    >
                      <Plus className="w-3.5 h-3.5" />
                    </button>
                    <span className="text-xs text-[#A7B8AE] ml-1">({effectiveMcq * marksMcq} marks)</span>
                  </div>
                </div>

                <div className="space-y-1">
                  <span className="text-xs text-[#A7B8AE] block">MCQ Difficulty</span>
                  <select
                    value={mcqDiff}
                    onChange={(e) => setMcqDiff(e.target.value as any)}
                    className="w-full px-3 py-2 rounded-lg border border-[#26382D] bg-[#0D1410] text-[#F9F9F9] text-xs focus:outline-hidden focus:ring-1 focus:ring-[#24EACE]"
                  >
                    <option value="easy">Easy (Direct recall & definitions)</option>
                    <option value="medium">Medium (Application & comparisons)</option>
                    <option value="hard">Hard (Analysis & scenario reasoning)</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Section: Subjective Subtypes */}
          {mode !== "objective_only" && (
            <div className="p-4 rounded-2xl bg-[#142019] border border-[#26382D] space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-[#A3FF70]" />
                  <span className="text-sm font-bold text-[#F9F9F9]">Subjective Questions (Typed + Rubrics)</span>
                </div>
                <span className="text-xs text-[#A7B8AE]">Strict Quota Guarantee</span>
              </div>

              {/* Subtype 1: Very Short */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-center p-3 rounded-xl bg-[#0D1410] border border-[#26382D]">
                <div>
                  <div className="text-xs font-bold text-[#F9F9F9]">Very Short Answer</div>
                  <div className="text-[11px] text-[#A7B8AE]">1-2 sentences • {marksVs} marks each</div>
                </div>
                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() => setVsCount(Math.max(0, vsCount - 1))}
                    className="w-7 h-7 rounded-md bg-[#142019] border border-[#26382D] text-[#A7B8AE] hover:text-[#F9F9F9] flex items-center justify-center transition"
                  >
                    <Minus className="w-3 h-3" />
                  </button>
                  <input
                    type="number"
                    min={0}
                    max={10}
                    value={vsCount}
                    onChange={(e) => setVsCount(Math.max(0, parseInt(e.target.value) || 0))}
                    className="w-12 text-center py-1 rounded-md border border-[#26382D] bg-[#142019] text-[#F9F9F9] text-xs font-bold"
                  />
                  <button
                    type="button"
                    onClick={() => setVsCount(Math.min(10, vsCount + 1))}
                    className="w-7 h-7 rounded-md bg-[#142019] border border-[#26382D] text-[#A7B8AE] hover:text-[#F9F9F9] flex items-center justify-center transition"
                  >
                    <Plus className="w-3 h-3" />
                  </button>
                </div>
                <div>
                  <select
                    value={vsDiff}
                    onChange={(e) => setVsDiff(e.target.value as any)}
                    className="w-full px-2 py-1.5 rounded-md border border-[#26382D] bg-[#142019] text-[#F9F9F9] text-xs"
                  >
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                </div>
              </div>

              {/* Subtype 2: Short */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-center p-3 rounded-xl bg-[#0D1410] border border-[#26382D]">
                <div>
                  <div className="text-xs font-bold text-[#F9F9F9]">Short Answer</div>
                  <div className="text-[11px] text-[#A7B8AE]">Multi-point breakdown • {marksS} marks each</div>
                </div>
                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() => setSCount(Math.max(0, sCount - 1))}
                    className="w-7 h-7 rounded-md bg-[#142019] border border-[#26382D] text-[#A7B8AE] hover:text-[#F9F9F9] flex items-center justify-center transition"
                  >
                    <Minus className="w-3 h-3" />
                  </button>
                  <input
                    type="number"
                    min={0}
                    max={10}
                    value={sCount}
                    onChange={(e) => setSCount(Math.max(0, parseInt(e.target.value) || 0))}
                    className="w-12 text-center py-1 rounded-md border border-[#26382D] bg-[#142019] text-[#F9F9F9] text-xs font-bold"
                  />
                  <button
                    type="button"
                    onClick={() => setSCount(Math.min(10, sCount + 1))}
                    className="w-7 h-7 rounded-md bg-[#142019] border border-[#26382D] text-[#A7B8AE] hover:text-[#F9F9F9] flex items-center justify-center transition"
                  >
                    <Plus className="w-3 h-3" />
                  </button>
                </div>
                <div>
                  <select
                    value={sDiff}
                    onChange={(e) => setSDiff(e.target.value as any)}
                    className="w-full px-2 py-1.5 rounded-md border border-[#26382D] bg-[#142019] text-[#F9F9F9] text-xs"
                  >
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                </div>
              </div>

              {/* Subtype 3: Long */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-center p-3 rounded-xl bg-[#0D1410] border border-[#26382D]">
                <div>
                  <div className="text-xs font-bold text-[#F9F9F9]">Long Answer</div>
                  <div className="text-[11px] text-[#A7B8AE]">Deep Analysis / Scenario • {marksL} marks each</div>
                </div>
                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() => setLCount(Math.max(0, lCount - 1))}
                    className="w-7 h-7 rounded-md bg-[#142019] border border-[#26382D] text-[#A7B8AE] hover:text-[#F9F9F9] flex items-center justify-center transition"
                  >
                    <Minus className="w-3 h-3" />
                  </button>
                  <input
                    type="number"
                    min={0}
                    max={5}
                    value={lCount}
                    onChange={(e) => setLCount(Math.max(0, parseInt(e.target.value) || 0))}
                    className="w-12 text-center py-1 rounded-md border border-[#26382D] bg-[#142019] text-[#F9F9F9] text-xs font-bold"
                  />
                  <button
                    type="button"
                    onClick={() => setLCount(Math.min(5, lCount + 1))}
                    className="w-7 h-7 rounded-md bg-[#142019] border border-[#26382D] text-[#A7B8AE] hover:text-[#F9F9F9] flex items-center justify-center transition"
                  >
                    <Plus className="w-3 h-3" />
                  </button>
                </div>
                <div>
                  <select
                    value={lDiff}
                    onChange={(e) => setLDiff(e.target.value as any)}
                    className="w-full px-2 py-1.5 rounded-md border border-[#26382D] bg-[#142019] text-[#F9F9F9] text-xs"
                  >
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Timed Mode Toggle */}
          <div className="flex items-center justify-between p-4 rounded-2xl bg-[#142019] border border-[#26382D]">
            <div className="flex items-center gap-3">
              <Clock className="w-4 h-4 text-[#24EACE]" />
              <div>
                <span className="text-xs font-bold text-[#F9F9F9] block">Timed Practice Mode</span>
                <span className="text-[11px] text-[#A7B8AE]">Enforce exam countdown timer or practice untimed</span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {isTimed && (
                <div className="flex items-center gap-1.5">
                  <input
                    type="number"
                    min={5}
                    max={180}
                    value={durationMinutes}
                    onChange={(e) => setDurationMinutes(Math.max(5, parseInt(e.target.value) || 20))}
                    className="w-16 px-2 py-1 text-xs rounded-md border border-[#26382D] bg-[#0D1410] text-[#F9F9F9] text-center font-bold"
                  />
                  <span className="text-xs text-[#A7B8AE]">mins</span>
                </div>
              )}
              <button
                type="button"
                onClick={() => setIsTimed(!isTimed)}
                className={`w-11 h-6 rounded-full transition relative ${
                  isTimed ? "bg-[#06AB63]" : "bg-[#26382D]"
                }`}
              >
                <span
                  className={`block w-4 h-4 rounded-full bg-[#F9F9F9] transition transform ${
                    isTimed ? "translate-x-6 bg-[#24EACE]" : "translate-x-1"
                  }`}
                />
              </button>
            </div>
          </div>

          {/* Live Summary Panel */}
          <div className="p-4 rounded-2xl bg-[#0D1410] border border-[#26382D] space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-[#F9F9F9] flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-[#24EACE]" />
                Selected Question Composition:
              </span>
              <span className="text-[#A3FF70] font-bold">
                Final Score Scaled to /10
              </span>
            </div>
            <div className="text-xs text-[#F9F9F9] font-medium">
              {totalQuestions} questions · {selectedTopicIds.length > 0 ? `${selectedTopicIds.length} topics selected` : `Full Syllabus (${subjectName})`} · {totalRawMarks} raw marks
            </div>
            <div className="text-[11px] text-[#A7B8AE] flex flex-wrap gap-x-4 gap-y-1">
              <span className="bg-[#142019] px-2 py-0.5 rounded border border-[#26382D]">MCQs: <strong className="text-[#24EACE]">{effectiveMcq}</strong></span>
              <span className="bg-[#142019] px-2 py-0.5 rounded border border-[#26382D]">Very Short: <strong className="text-[#A3FF70]">{effectiveVs}</strong></span>
              <span className="bg-[#142019] px-2 py-0.5 rounded border border-[#26382D]">Short: <strong className="text-[#A3FF70]">{effectiveS}</strong></span>
              <span className="bg-[#142019] px-2 py-0.5 rounded border border-[#26382D]">Long: <strong className="text-[#A3FF70]">{effectiveL}</strong></span>
              <span className="bg-[#142019] px-2 py-0.5 rounded border border-[#26382D]">Timer: <strong className="text-[#F9F9F9]">{isTimed ? `${durationMinutes}m` : "Untimed"}</strong></span>
            </div>
          </div>

          {/* Animated Generation Stage Banner when generating */}
          {generating && (
            <div className="p-4 rounded-2xl bg-[#142019] border border-[#24EACE]/40 space-y-3 animate-pulse">
              <div className="flex items-center gap-2 text-xs font-bold text-[#24EACE]">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Generating Test Engine ({genStep + 1} of {steps.length})</span>
              </div>
              <p className="text-xs text-[#F9F9F9] font-medium">{steps[genStep]}</p>
              <div className="w-full bg-[#0D1410] rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-linear-to-r from-[#24EACE] to-[#A3FF70] h-1.5 rounded-full transition-all duration-500"
                  style={{ width: `${((genStep + 1) / steps.length) * 100}%` }}
                />
              </div>
            </div>
          )}

          {!isValid && (
            <div className="p-3 rounded-xl bg-[#281F0D] border border-[#523F17] text-xs text-amber-300 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
              <span>Please configure at least 1 question to generate your test.</span>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-[#26382D]">
            <button
              type="button"
              onClick={onClose}
              disabled={generating}
              className="px-4 py-2 text-xs font-semibold text-[#A7B8AE] hover:text-[#F9F9F9] transition disabled:opacity-40"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!isValid || generating}
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-[#24EACE] hover:bg-[#A3FF70] text-[#060807] font-bold text-xs shadow-md shadow-[#24EACE]/20 transition disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed"
            >
              {generating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-[#060807]" />
                  <span>Synthesizing Test...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 text-[#060807]" />
                  <span>Generate Practice Test</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

