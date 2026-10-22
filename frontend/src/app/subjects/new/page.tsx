"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  UploadCloud,
  FileCheck,
  Sparkles,
  AlertCircle,
  FileText,
  Loader2
} from "lucide-react";
import { api } from "@/lib/api";

export default function NewSubjectPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [activeTab, setActiveTab] = useState<"upload" | "paste">("upload");
  const [syllabusText, setSyllabusText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Please enter a course / subject name.");
      return;
    }
    if (activeTab === "paste" && !syllabusText.trim()) {
      setError("Please paste your syllabus or study material text to begin analysis.");
      return;
    }
    if (activeTab === "upload" && !file) {
      setError("Please select a study material file (PDF or TXT) to upload.");
      return;
    }

    setLoading(true);
    setError(null);
    setStatusMsg("Creating course workspace...");

    try {
      // 1. Create Subject with standard defaults
      const subject = await api.createSubject({
        name: name.trim(),
        preferred_duration_minutes: 20,
        default_mcq_count: 3,
        default_subjective_count: 2,
        default_subjective_marks: 5,
        syllabus_text: activeTab === "paste" ? syllabusText.trim() : undefined,
      });

      // 2. Ingest uploaded file or pasted text
      if (activeTab === "upload" && file) {
        setStatusMsg("Uploading & indexing study materials...");
        await api.uploadDocument(subject.id, file, "syllabus");
      } else if (activeTab === "paste" && syllabusText.trim()) {
        setStatusMsg("Saving syllabus outline...");
        await api.pasteTextDocument(subject.id, {
          title: "Syllabus / Study Material Outline",
          content: syllabusText.trim(),
          document_role: "syllabus"
        });
      }

      // 3. Trigger AI syllabus hierarchy analysis asynchronously in background
      setStatusMsg("Study materials ready! Opening workspace...");
      api.analyzeSyllabus(subject.id).catch((analyzeErr) => {
        console.warn("Background syllabus analysis note:", analyzeErr);
      });

      router.push(`/subjects/${subject.id}`);
    } catch (err: any) {
      setError(err.message || "Failed to create subject and analyze materials");
      setLoading(false);
      setStatusMsg("");
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-10 space-y-8">
      {/* Back button */}
      <div>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#A7B8AE] hover:text-[#F9F9F9] transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Dashboard
        </Link>
      </div>

      {/* Header section */}
      <div className="space-y-2 border-b border-[#26382D] pb-6">
        <div className="inline-flex items-center gap-2 text-xs font-bold px-3 py-1 rounded-full bg-[#142019] text-[#A3FF70] border border-[#26382D]">
          <Sparkles className="w-3.5 h-3.5 text-[#A3FF70]" />
          Study Materials & Syllabus Setup
        </div>
        <h1 className="text-2xl sm:text-3xl font-black text-[#F9F9F9] tracking-tight">
          Upload study material
        </h1>
        <p className="text-sm text-[#A7B8AE] leading-relaxed">
          Add notes, syllabus, lecture plans, or other study documents. ExamLoop will automatically extract syllabus units, priority topics, and verified question rubrics.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-[#261012] border border-[#542125] text-sm text-[#F87171] flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-[#F87171] shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Simplified, Clean Form */}
      <form onSubmit={handleSubmit} className="bg-[#0D1410] rounded-2xl border border-[#26382D] p-6 sm:p-8 space-y-6 shadow-sm">
        {/* Course / Subject Name */}
        <div className="space-y-2">
          <label className="block text-sm font-semibold text-[#F9F9F9]">
            Course / Subject Name <span className="text-[#24EACE]">*</span>
          </label>
          <input
            type="text"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Database Management Systems (DBMS), Operating Systems, System Design"
            className="w-full px-4 py-3 rounded-xl border border-[#26382D] bg-[#142019] text-[#F9F9F9] text-sm focus:outline-hidden focus:ring-2 focus:ring-[#24EACE] focus:border-transparent transition placeholder:text-[#6C8074]"
          />
        </div>

        {/* Study Materials Source: Upload File vs Paste Syllabus */}
        <div className="space-y-3 pt-2">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <label className="block text-sm font-semibold text-[#F9F9F9] flex items-center gap-1.5">
              <FileCheck className="w-4 h-4 text-[#24EACE]" />
              Study Materials or Syllabus Outline <span className="text-[#24EACE]">*</span>
            </label>
            <div className="flex bg-[#142019] p-0.5 rounded-lg border border-[#26382D] self-start sm:self-auto">
              <button
                type="button"
                onClick={() => setActiveTab("upload")}
                className={`px-3 py-1 rounded-md text-xs font-bold transition ${
                  activeTab === "upload"
                    ? "bg-[#24EACE] text-[#060807] shadow-xs"
                    : "text-[#A7B8AE] hover:text-[#F9F9F9]"
                }`}
              >
                Upload File (PDF/TXT)
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("paste")}
                className={`px-3 py-1 rounded-md text-xs font-bold transition ${
                  activeTab === "paste"
                    ? "bg-[#24EACE] text-[#060807] shadow-xs"
                    : "text-[#A7B8AE] hover:text-[#F9F9F9]"
                }`}
              >
                Paste Syllabus
              </button>
            </div>
          </div>

          {activeTab === "upload" ? (
            <div className="space-y-3">
              <label className="border-2 border-dashed border-[#26382D] hover:border-[#24EACE]/70 rounded-2xl p-8 flex flex-col items-center justify-center cursor-pointer bg-[#142019] transition group">
                <UploadCloud className="w-10 h-10 text-[#24EACE] group-hover:scale-110 transition mb-3" />
                <span className="text-sm font-bold text-[#F9F9F9] text-center">
                  {file ? file.name : "Click to select or drag and drop study materials"}
                </span>
                <span className="text-xs text-[#A7B8AE] mt-1 text-center">
                  Searchable PDF or plain TXT notes, syllabus, lecture planner, or PYQs (Max 25MB)
                </span>
                <input
                  type="file"
                  accept=".pdf,.txt"
                  className="hidden"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                />
              </label>

              {file && (
                <div className="flex items-center justify-between p-3.5 rounded-xl bg-[#142019] border border-[#26382D] text-xs">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-[#24EACE]" />
                    <span className="font-semibold text-[#F9F9F9]">{file.name}</span>
                    <span className="text-[#6C8074]">({(file.size / 1024).toFixed(1)} KB)</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setFile(null)}
                    className="text-xs text-[#F87171] hover:underline font-semibold transition"
                  >
                    Remove
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              <textarea
                rows={8}
                required
                value={syllabusText}
                onChange={(e) => setSyllabusText(e.target.value)}
                placeholder={"Paste your syllabus outline, lecture planner, or course topics here. Example:\n\nUnit 1: Relational Model & Normalization (1NF, 2NF, 3NF, BCNF, MVDs)\nUnit 2: Transactions & Concurrency Control (ACID, Serializability, Strict 2PL, Deadlocks)\nUnit 3: Storage & Indexing (B+ Trees, Hash Indexes, Query Execution Engine)\nUnit 4: Distributed Databases & Consensus (Two-Phase Commit, Raft, Replication)"}
                className="w-full px-4 py-3 rounded-xl border border-[#26382D] bg-[#142019] text-[#F9F9F9] text-xs font-mono focus:outline-hidden focus:ring-2 focus:ring-[#24EACE] transition placeholder:text-[#6C8074] leading-relaxed"
              />
              <p className="text-[11px] text-[#A7B8AE]">
                ExamLoop parses this content into curriculum units, extracting explicit topics and testable concepts automatically.
              </p>
            </div>
          )}
        </div>

        {/* Action Button */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-4 border-t border-[#26382D]">
          <span className="text-xs text-[#24EACE] font-medium">
            {statusMsg && (
              <span className="inline-flex items-center gap-1.5">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-[#24EACE]" />
                {statusMsg}
              </span>
            )}
          </span>

          <div className="flex items-center gap-3">
            <Link
              href="/dashboard"
              className="px-4 py-2 text-xs font-semibold text-[#A7B8AE] hover:text-[#F9F9F9] transition"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-[#24EACE] hover:bg-[#A3FF70] text-[#060807] font-bold text-xs shadow-md shadow-[#24EACE]/20 transition disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-[#060807]" />
                  <span>Processing Materials...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 text-[#060807]" />
                  <span>Analyze Materials & Begin</span>
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
