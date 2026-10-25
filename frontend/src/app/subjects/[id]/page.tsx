"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  BookOpen,
  UploadCloud,
  FileText,
  Trash2,
  Sparkles,
  Layers,
  CheckSquare,
  Square,
  Search,
  Filter,
  ArrowLeft,
  RefreshCw,
  Loader2,
  AlertCircle,
  HelpCircle,
  ChevronDown,
  ChevronRight,
  Info,
  Sliders,
  CheckCircle2,
  Plus
} from "lucide-react";
import {
  api,
  Subject,
  DocumentItem,
  SyllabusUnitItem,
  TopicItem,
  CustomTestConfig
} from "@/lib/api";
import { supabase, isSupabaseConfigured } from "@/lib/supabase";
import TestBuilderModal from "@/components/TestBuilderModal";

export default function SubjectWorkspacePage() {
  return (
    <Suspense fallback={<div className="max-w-7xl mx-auto px-4 py-20 text-center text-sm text-[#A7B8AE]">Loading study workspace...</div>}>
      <SubjectWorkspaceContent />
    </Suspense>
  );
}

function SubjectWorkspaceContent() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const subjectId = params?.id as string;

  const [subject, setSubject] = useState<Subject | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [units, setUnits] = useState<SyllabusUnitItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedRole, setSelectedRole] = useState<"syllabus" | "notes" | "previous_paper">("notes");
  const [analyzing, setAnalyzing] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [isBuilderOpen, setIsBuilderOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Topic Selection State
  const [selectedTopicIds, setSelectedTopicIds] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState("");
  const [priorityFilter, setPriorityFilter] = useState<string>("all");
  const [selectedUnitFilter, setSelectedUnitFilter] = useState<string>("all");

  // "Why this priority?" modal state
  const [priorityModalTopic, setPriorityModalTopic] = useState<TopicItem | null>(null);

  // Load Subject & Syllabus Hierarchy
  const loadData = async (retryCount = 0) => {
    if (!subjectId) return;
    try {
      const s = await api.getSubject(subjectId);
      setSubject(s);
      setError(null);

      // Load documents and units with settled promises so partial responses don't zero out subject
      const [docsRes, unitsRes] = await Promise.allSettled([
        api.listDocuments(subjectId),
        api.listUnits(subjectId)
      ]);

      if (docsRes.status === "fulfilled") {
        setDocuments(docsRes.value);
      }
      if (unitsRes.status === "fulfilled") {
        const u = unitsRes.value;
        setUnits(u);

        // Default: select all active topics if none selected yet
        if (selectedTopicIds.size === 0 && u.length > 0) {
          const allIds = new Set<string>();
          u.forEach(unit => {
            unit.topics.forEach(t => {
              if (!t.is_excluded) allIds.add(t.id);
            });
          });
          setSelectedTopicIds(allIds);
        }
      }
      setLoading(false);
    } catch (err: any) {
      console.warn("Failed to load syllabus workspace attempt", retryCount, err);
      if (retryCount < 2) {
        setTimeout(() => {
          loadData(retryCount + 1);
        }, (retryCount + 1) * 600);
        return;
      }
      setError(err.message || "Failed to load syllabus workspace");
      setLoading(false);
    }
  };

  useEffect(() => {
    if (subjectId) {
      loadData(0);
    }

    if (isSupabaseConfigured) {
      const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
        if (session && subjectId) {
          loadData(0);
        }
      });
      return () => {
        subscription.unsubscribe();
      };
    }
  }, [subjectId]);

  // Auto-refresh units in background if they were recently created or being analyzed
  useEffect(() => {
    if (!subjectId || !subject || units.length > 0) return;

    let pollAttempts = 0;
    const interval = setInterval(async () => {
      pollAttempts++;
      try {
        const freshUnits = await api.listUnits(subjectId);
        if (freshUnits && freshUnits.length > 0) {
          setUnits(freshUnits);
          const allIds = new Set<string>();
          freshUnits.forEach(unit => {
            unit.topics.forEach(t => {
              if (!t.is_excluded) allIds.add(t.id);
            });
          });
          setSelectedTopicIds(allIds);
          clearInterval(interval);
        }
      } catch {
        // silent background poll
      }
      if (pollAttempts >= 8) {
        clearInterval(interval);
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [subjectId, subject, units.length]);

  useEffect(() => {
    if (searchParams?.get("open_builder") === "true") {
      setIsBuilderOpen(true);
    }
  }, [searchParams]);

  // Document Upload
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError(null);
    try {
      await api.uploadDocument(subjectId, file, selectedRole);
      const docs = await api.listDocuments(subjectId);
      setDocuments(docs);

      // Refresh units immediately with quick progressive retry if auto-extraction finishes
      for (let attempt = 0; attempt < 3; attempt++) {
        try {
          const freshUnits = await api.listUnits(subjectId);
          if (freshUnits && freshUnits.length > 0) {
            setUnits(freshUnits);
            const allIds = new Set<string>();
            freshUnits.forEach(unit => {
              unit.topics.forEach(t => {
                if (!t.is_excluded) allIds.add(t.id);
              });
            });
            setSelectedTopicIds(allIds);
            break;
          }
        } catch {
          // ignore transient poll error
        }
        if (attempt < 2) {
          await new Promise((r) => setTimeout(r, 1200));
        }
      }
    } catch (err: any) {
      setError(err.message || "Failed to upload document");
    } finally {
      setUploading(false);
      // Reset input value so the same file can be re-uploaded if needed
      e.target.value = "";
    }
  };

  const handleDeleteDocument = async (docId: string) => {
    if (!confirm("Are you sure you want to remove this document?")) return;
    try {
      await api.deleteDocument(docId);
      setDocuments(prev => prev.filter(d => d.id !== docId));
      // Refresh units after deleting document
      try {
        const u = await api.listUnits(subjectId);
        setUnits(u);
      } catch (e) {
        // units refresh fallback
      }
    } catch (err: any) {
      alert("Failed to delete document: " + (err.message || "Unknown error"));
    }
  };

  const handleDeleteWorkspace = async () => {
    if (!confirm(`Are you sure you want to permanently delete this course workspace "${subject?.name}"? All study materials, extracted topics, and tests will be removed.`)) return;
    try {
      await api.deleteSubject(subjectId);
      router.push("/dashboard");
    } catch (err: any) {
      alert("Failed to delete workspace: " + (err.message || "Unknown error"));
    }
  };

  // Re-run Syllabus Analysis
  const handleReanalyze = async () => {
    setAnalyzing(true);
    setError(null);
    try {
      const updatedUnits = await api.analyzeSyllabus(subjectId);
      setUnits(updatedUnits);

      // Reselect all valid topics
      const allIds = new Set<string>();
      updatedUnits.forEach(unit => {
        unit.topics.forEach(t => {
          if (!t.is_excluded) allIds.add(t.id);
        });
      });
      setSelectedTopicIds(allIds);
    } catch (err: any) {
      setError(err.message || "Failed to re-analyze syllabus");
    } finally {
      setAnalyzing(false);
    }
  };

  // Selection toggle handlers
  const toggleTopic = (id: string) => {
    const next = new Set(selectedTopicIds);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    setSelectedTopicIds(next);
  };

  const selectAllTopics = () => {
    const all = new Set<string>();
    units.forEach(u => {
      u.topics.forEach(t => {
        if (!t.is_excluded) all.add(t.id);
      });
    });
    setSelectedTopicIds(all);
  };

  const clearSelection = () => {
    setSelectedTopicIds(new Set());
  };

  const selectUnitTopics = (unit: SyllabusUnitItem) => {
    const next = new Set(selectedTopicIds);
    unit.topics.forEach(t => {
      if (!t.is_excluded) next.add(t.id);
    });
    setSelectedTopicIds(next);
  };

  // Generate Custom Test Handshake
  const handleCustomTestGenerate = async (config: CustomTestConfig) => {
    setGenerating(true);
    try {
      const res = await api.createCustomTest(subjectId, config);
      setIsBuilderOpen(false);
      router.push(`/tests/${res.id}`);
    } catch (err: any) {
      alert("Failed to generate test: " + err.message);
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-24 text-center">
        <Loader2 className="w-8 h-8 animate-spin mx-auto text-[#24EACE] mb-3" />
        <p className="text-sm text-[#A7B8AE]">Loading course curriculum & units...</p>
      </div>
    );
  }

  if (!subject) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-24 text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-[#EF4444] mx-auto" />
        <h2 className="text-xl font-bold text-[#F9F9F9]">Subject Not Found</h2>
        {error && (
          <p className="text-xs text-[#A7B8AE] max-w-md mx-auto">{error}</p>
        )}
        <div className="flex items-center justify-center gap-3 pt-2">
          <button
            onClick={() => {
              setLoading(true);
              setError(null);
              loadData(0);
            }}
            className="px-4 py-2 rounded-xl bg-[#24EACE] hover:bg-[#A3FF70] text-[#060807] font-bold text-xs transition inline-flex items-center gap-1.5 cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Retry
          </button>
          <Link href="/dashboard" className="px-4 py-2 rounded-xl bg-[#142019] text-[#A7B8AE] hover:text-[#F9F9F9] border border-[#26382D] text-xs font-semibold transition">
            Return to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  // All topics flat list for count & filters
  const allTopics: TopicItem[] = [];
  units.forEach(u => allTopics.push(...u.topics));

  const filteredUnits = units.map(u => {
    let topics = u.topics;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      topics = topics.filter(t => t.name.toLowerCase().includes(q) || (t.description || "").toLowerCase().includes(q));
    }
    if (priorityFilter !== "all") {
      topics = topics.filter(t => t.practice_priority === priorityFilter);
    }
    return { ...u, topics };
  }).filter(u => selectedUnitFilter === "all" || u.id === selectedUnitFilter);

  const selectedNames = allTopics
    .filter(t => selectedTopicIds.has(t.id))
    .map(t => t.name);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Breadcrumb */}
      <div>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#A7B8AE] hover:text-[#F9F9F9] transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Dashboard
        </Link>
      </div>

      {/* Hero / Course Workspace Header */}
      <div className="bg-[#0D1410] rounded-3xl border border-[#26382D] p-6 sm:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-sm">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold px-3 py-1 rounded-full bg-[#142019] text-[#A3FF70] border border-[#26382D]">
              Syllabus Workspace
            </span>
            {subject.exam_date && (
              <span className="text-xs text-[#A7B8AE]">Target Exam: {subject.exam_date}</span>
            )}
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-[#F9F9F9] tracking-tight">{subject.name}</h1>
          <p className="text-xs text-[#A7B8AE] max-w-xl">
            {units.length} Unit(s) • {allTopics.length} Extracted Topics • {documents.length} Study Material(s)
          </p>
        </div>

        {/* Primary Action Buttons */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={handleDeleteWorkspace}
            className="inline-flex items-center gap-2 px-4 py-3 rounded-xl bg-[#142019] hover:bg-red-950/40 text-[#A7B8AE] hover:text-red-400 border border-[#26382D] hover:border-red-800/50 font-semibold text-xs transition cursor-pointer"
            title="Delete this workspace"
          >
            <Trash2 className="w-4 h-4" />
            <span>Delete Workspace</span>
          </button>

          <button
            type="button"
            onClick={() => setIsBuilderOpen(true)}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#24EACE] hover:bg-[#A3FF70] text-[#060807] font-bold text-xs shadow-md shadow-[#24EACE]/20 transition cursor-pointer"
          >
            <Sparkles className="w-4 h-4 text-[#060807]" />
            <span>
              {selectedTopicIds.size > 0
                ? `Create practice test (${selectedTopicIds.size} topics)`
                : "Create practice test (All Material)"}
            </span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-[#261012] border border-[#542125] text-sm text-[#F87171] flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-[#F87171] shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Grid: Left Column (Materials & Ingestion) + Right Column (Topic Selection Explorer) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Course Materials & Roles */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-[#F9F9F9] flex items-center gap-2">
              <FileText className="w-4 h-4 text-[#24EACE]" />
              Study Documents ({documents.length})
            </h2>
            <button
              onClick={handleReanalyze}
              disabled={analyzing || documents.length === 0}
              className="text-[11px] font-semibold text-[#24EACE] hover:text-[#A3FF70] inline-flex items-center gap-1 disabled:opacity-50 transition"
            >
              {analyzing ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
              Re-analyze
            </button>
          </div>

          {/* Upload Dropzone with Role Selector */}
          <div className="bg-[#0D1410] rounded-2xl border border-[#26382D] p-5 space-y-3">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-[#A7B8AE] block">Select Material Role</label>
              <select
                value={selectedRole}
                onChange={(e) => setSelectedRole(e.target.value as any)}
                className="w-full px-3 py-2 rounded-xl border border-[#26382D] bg-[#142019] text-[#F9F9F9] text-xs focus:outline-hidden focus:ring-1 focus:ring-[#24EACE]"
              >
                <option value="notes">Supporting Lecture Notes (Grounding)</option>
                <option value="syllabus">Syllabus Document (Defines Scope)</option>
                <option value="previous_paper">Previous Year Paper (Frequency Analysis)</option>
              </select>
            </div>

            <label className="border-2 border-dashed border-[#26382D] hover:border-[#24EACE]/60 rounded-xl p-5 flex flex-col items-center justify-center cursor-pointer bg-[#142019] transition group">
              <UploadCloud className="w-6 h-6 text-[#24EACE] group-hover:scale-110 transition mb-1" />
              <span className="text-xs font-bold text-[#F9F9F9]">Upload PDF or TXT</span>
              <span className="text-[10px] text-[#A7B8AE]">Drag & drop or click to add material (up to 100MB)</span>
              <input
                type="file"
                accept=".pdf,.txt"
                className="hidden"
                onChange={handleFileUpload}
                disabled={uploading}
              />
            </label>
            {uploading && (
              <div className="p-3.5 rounded-xl bg-[#142019] border border-[#24EACE]/40 space-y-2 animate-pulse">
                <div className="flex items-center gap-2 text-xs font-bold text-[#24EACE]">
                  <Loader2 className="w-4 h-4 animate-spin text-[#24EACE]" />
                  <span>Processing & Extracting Topics...</span>
                </div>
                <p className="text-[11px] text-[#D0DBD4] leading-relaxed">
                  Streaming document, parsing content pages, and discovering syllabus topics.
                </p>
                <div className="w-full bg-[#0D1410] rounded-full h-1.5 overflow-hidden">
                  <div className="bg-linear-to-r from-[#24EACE] to-[#A3FF70] h-1.5 rounded-full w-4/5 animate-pulse" />
                </div>
              </div>
            )}
          </div>

          {/* Document list with badges */}
          <div className="space-y-2">
            {documents.length === 0 ? (
              <p className="text-xs text-[#6C8074] italic text-center py-3">
                No materials uploaded yet.
              </p>
            ) : (
              documents.map((doc) => (
                <div
                  key={doc.id}
                  className="bg-[#0D1410] p-3.5 rounded-xl border border-[#26382D] flex items-center justify-between gap-3 text-xs shadow-xs"
                >
                  <div className="space-y-1 overflow-hidden">
                    <div className="font-semibold text-[#F9F9F9] truncate">{doc.original_name}</div>
                    <div className="flex items-center gap-2 text-[10px] text-[#A7B8AE]">
                      <span className="px-2 py-0.5 rounded-md bg-[#142019] border border-[#26382D] text-[#24EACE] font-medium capitalize">
                        {doc.document_role.replace("_", " ")}
                      </span>
                      <span>{doc.page_count} pages</span>
                    </div>
                  </div>

                  <button
                    onClick={() => handleDeleteDocument(doc.id)}
                    className="p-1.5 text-[#6C8074] hover:text-[#EF4444] rounded transition"
                    title="Remove document"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Topic Hierarchy & Topic Selection Explorer */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-bold text-[#F9F9F9] flex items-center gap-2">
                <Layers className="w-4 h-4 text-[#24EACE]" />
                {units.length <= 1 ? "Important Topics & Practice Selection" : "Curriculum Topics & Practice Selection"}
              </h2>
              <p className="text-xs text-[#A7B8AE]">
                {selectedTopicIds.size} of {allTopics.length} topic(s) selected for next practice test
              </p>
            </div>

            {/* Quick bulk selection */}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={selectAllTopics}
                className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[#142019] hover:bg-[#1B2B22] text-[#F9F9F9] border border-[#26382D] transition"
              >
                Select All
              </button>
              <button
                type="button"
                onClick={clearSelection}
                className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[#142019] hover:bg-[#1B2B22] text-[#A7B8AE] hover:text-[#F9F9F9] border border-[#26382D] transition"
              >
                Clear
              </button>
            </div>
          </div>

          {/* Filter & Search Bar */}
          <div className="flex flex-col sm:flex-row items-center gap-3 bg-[#0D1410] p-3.5 rounded-2xl border border-[#26382D]">
            <div className="relative flex-1 w-full">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-[#6C8074]" />
              <input
                type="text"
                placeholder="Search topics or concepts..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 rounded-xl border border-[#26382D] bg-[#142019] text-[#F9F9F9] text-xs focus:outline-hidden focus:ring-1 focus:ring-[#24EACE] placeholder:text-[#6C8074]"
              />
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto">
              {units.length > 1 && (
                <select
                  value={selectedUnitFilter}
                  onChange={(e) => setSelectedUnitFilter(e.target.value)}
                  className="px-3 py-1.5 rounded-xl border border-[#26382D] bg-[#142019] text-[#F9F9F9] text-xs"
                >
                  <option value="all">All Units</option>
                  {units.map(u => (
                    <option key={u.id} value={u.id}>{u.title}</option>
                  ))}
                </select>
              )}

              <select
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
                className="px-3 py-1.5 rounded-xl border border-[#26382D] bg-[#142019] text-[#F9F9F9] text-xs"
              >
                <option value="all">All Priorities</option>
                <option value="high">High Priority</option>
                <option value="medium">Medium Priority</option>
                <option value="low">Low Priority</option>
              </select>
            </div>
          </div>

          {/* Units and Topics Accordion / List */}
          {allTopics.length === 0 ? (
            <div className="bg-[#0D1410] rounded-2xl border border-[#26382D] p-8 sm:p-10 text-center space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-[#142019] border border-[#26382D] flex items-center justify-center mx-auto text-[#24EACE]">
                <Sparkles className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-[#F9F9F9]">Full Mock Test Ready</h3>
              <p className="text-xs text-[#A7B8AE] max-w-md mx-auto">
                {documents.length > 0
                  ? `AI can generate a practice test directly across all ${documents.length} uploaded study material(s). You can also extract structured units with AI.`
                  : "Upload notes or syllabus in the left column, or click below to launch a comprehensive practice test."}
              </p>
              <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsBuilderOpen(true)}
                  className="px-6 py-2.5 rounded-xl bg-[#24EACE] hover:bg-[#A3FF70] text-[#060807] font-bold text-xs shadow-md shadow-[#24EACE]/20 transition inline-flex items-center gap-2 cursor-pointer"
                >
                  <Sparkles className="w-4 h-4 text-[#060807]" />
                  <span>Generate Full Mock Test</span>
                </button>
                {documents.length > 0 && (
                  <button
                    type="button"
                    onClick={handleReanalyze}
                    disabled={analyzing}
                    className="px-5 py-2.5 rounded-xl bg-[#142019] hover:bg-[#1B2B22] text-[#F9F9F9] border border-[#26382D] font-semibold text-xs transition inline-flex items-center gap-2 disabled:opacity-50 cursor-pointer"
                  >
                    {analyzing ? <Loader2 className="w-3.5 h-3.5 animate-spin text-[#24EACE]" /> : <RefreshCw className="w-3.5 h-3.5 text-[#24EACE]" />}
                    <span>Extract Topics with AI</span>
                  </button>
                )}
              </div>
            </div>
          ) : filteredUnits.length === 0 ? (
            <div className="bg-[#0D1410] rounded-2xl border border-[#26382D] p-8 text-center space-y-3">
              <Layers className="w-8 h-8 text-[#6C8074] mx-auto" />
              <h3 className="text-sm font-semibold text-[#F9F9F9]">No topics match current filters</h3>
              <p className="text-xs text-[#A7B8AE]">Try adjusting your search query or priority filters.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredUnits.map((u) => (
                <div key={u.id} className="bg-[#0D1410] rounded-2xl border border-[#26382D] overflow-hidden">
                  {/* Unit Title Bar */}
                  <div className="px-5 py-3.5 bg-[#142019] border-b border-[#26382D] flex items-center justify-between">
                    <div>
                      <span className="text-xs font-bold text-[#F9F9F9] flex items-center gap-2 flex-wrap">
                        <span className="w-2 h-2 rounded-full bg-[#24EACE]" />
                        {u.title}
                        {units.length === 1 && (
                          <span className="text-[10px] font-semibold text-[#A3FF70] bg-[#0D2418] border border-[#1C4D34] px-2 py-0.5 rounded-md">
                            Single Chapter Notes
                          </span>
                        )}
                      </span>
                      {u.description && (
                        <p className="text-[11px] text-[#A7B8AE] mt-0.5">{u.description}</p>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => selectUnitTopics(u)}
                      className="text-[11px] font-bold text-[#24EACE] hover:text-[#A3FF70] transition"
                    >
                      {units.length === 1 ? "Select All in Chapter" : "Select Unit"}
                    </button>
                  </div>

                  {/* Topics in this unit */}
                  <div className="divide-y divide-[#1A2820]">
                    {u.topics.map((t) => {
                      const isSelected = selectedTopicIds.has(t.id);

                      // Priority badge styling
                      let badgeClass = "bg-[#142019] text-[#A7B8AE] border-[#26382D]";
                      if (t.practice_priority === "high") {
                        badgeClass = "bg-[#0D2418] text-[#A3FF70] border-[#1C4D34]";
                      } else if (t.practice_priority === "medium") {
                        badgeClass = "bg-[#281F0D] text-[#FBBF24] border-[#523F17]";
                      }

                      return (
                        <div
                          key={t.id}
                          onClick={() => toggleTopic(t.id)}
                          className={`p-4 transition cursor-pointer flex items-start gap-3.5 ${
                            isSelected
                              ? "bg-[#142019]/80 border-l-2 border-l-[#24EACE]"
                              : "hover:bg-[#142019]/40 opacity-80"
                          }`}
                        >
                          {/* Checkbox */}
                          <div className="mt-0.5">
                            {isSelected ? (
                              <CheckSquare className="w-4 h-4 text-[#24EACE]" />
                            ) : (
                              <Square className="w-4 h-4 text-[#6C8074]" />
                            )}
                          </div>

                          {/* Topic Details */}
                          <div className="flex-1 space-y-1">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="text-sm font-bold text-[#F9F9F9]">{t.name}</span>

                              {/* Priority Pill */}
                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setPriorityModalTopic(t);
                                }}
                                className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full border flex items-center gap-1 ${badgeClass}`}
                              >
                                <span>{t.practice_priority} Priority</span>
                                <HelpCircle className="w-2.5 h-2.5 opacity-70" />
                              </button>

                              {/* Inferred Topic Confirmation Badge */}
                              {t.is_inferred && (
                                <span className="text-[10px] font-semibold bg-[#281F0D] text-[#FBBF24] border border-[#523F17] px-2 py-0.5 rounded-md">
                                  AI-Inferred Topic
                                </span>
                              )}

                              {/* Reference Coverage Badge */}
                              <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-md ${
                                t.reference_coverage === "good"
                                  ? "bg-[#0D2418] text-[#A3FF70] border border-[#1C4D34]"
                                  : "bg-[#142019] text-[#A7B8AE] border border-[#26382D]"
                              }`}>
                                {t.reference_coverage === "good" ? "Notes Available" : "Syllabus-Only"}
                              </span>
                            </div>

                            {t.description && (
                              <p className="text-xs text-[#A7B8AE] leading-relaxed">{t.description}</p>
                            )}

                            {/* Subtopics tag cloud */}
                            {t.subtopics && t.subtopics.length > 0 && (
                              <div className="flex flex-wrap gap-1.5 pt-1">
                                {t.subtopics.map((sub, idx) => (
                                  <span
                                    key={idx}
                                    className="text-[10px] bg-[#142019] text-[#A7B8AE] border border-[#26382D] px-2 py-0.5 rounded-md"
                                  >
                                    {sub}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* "Why this priority?" Modal */}
      {priorityModalTopic && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-2xl bg-[#0D1410] border border-[#26382D] p-6 space-y-4 text-[#F9F9F9] shadow-2xl">
            <div className="flex items-center justify-between border-b border-[#26382D] pb-3">
              <div className="flex items-center gap-2">
                <Info className="w-4 h-4 text-[#24EACE]" />
                <h3 className="font-bold text-sm">Why this practice priority?</h3>
              </div>
              <button
                type="button"
                onClick={() => setPriorityModalTopic(null)}
                className="text-[#A7B8AE] hover:text-[#F9F9F9]"
              >
                ✕
              </button>
            </div>

            <div className="space-y-2 text-xs">
              <div className="font-bold text-[#F9F9F9] text-sm">{priorityModalTopic.name}</div>
              <div className="p-3.5 rounded-xl bg-[#142019] border border-[#26382D] text-[#A7B8AE] leading-relaxed">
                {priorityModalTopic.priority_reason || "Suggested based on academic conceptual dependencies and common university examination questions."}
              </div>
              {priorityModalTopic.observed_paper_frequency !== undefined && priorityModalTopic.observed_paper_frequency !== null && (
                <div className="text-[11px] text-[#A3FF70] font-semibold">
                  Observed in {priorityModalTopic.observed_paper_frequency} question(s) within uploaded previous papers.
                </div>
              )}
              <p className="text-[11px] text-[#6C8074] italic">
                Note: Priority is an AI study recommendation, not an official exam guarantee.
              </p>
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={() => setPriorityModalTopic(null)}
                className="px-4 py-2 rounded-xl bg-[#24EACE] hover:bg-[#A3FF70] text-[#060807] font-bold text-xs transition"
              >
                Got it
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Custom Test Builder Modal */}
      <TestBuilderModal
        isOpen={isBuilderOpen}
        onClose={() => setIsBuilderOpen(false)}
        subjectName={subject.name}
        selectedTopicIds={Array.from(selectedTopicIds)}
        selectedTopicNames={selectedNames}
        onGenerate={handleCustomTestGenerate}
        generating={generating}
      />
    </div>
  );
}
