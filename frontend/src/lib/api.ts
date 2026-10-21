const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export interface Subject {
  id: string;
  name: string;
  exam_date?: string;
  preferred_duration_minutes: number;
  default_mcq_count: number;
  default_subjective_count: number;
  default_subjective_marks: number;
  syllabus_text?: string;
  created_at: string;
  document_count: number;
  concept_count: number;
  test_count: number;
}

export interface DocumentItem {
  id: string;
  subject_id: string;
  filename: string;
  original_name: string;
  document_role: "syllabus" | "notes" | "previous_paper";
  file_size: number;
  mime_type: string;
  page_count: number;
  status: "uploaded" | "extracting" | "indexing" | "ready" | "failed";
  error_message?: string;
  created_at: string;
}

export interface TopicItem {
  id: string;
  subject_id: string;
  unit_id?: string;
  unit_name?: string;
  name: string;
  description?: string;
  subtopics: string[];
  is_inferred: boolean;
  is_confirmed: boolean;
  practice_priority: "high" | "medium" | "low";
  priority_reason?: string;
  weightage_explicit?: number;
  observed_paper_frequency?: number;
  reference_coverage: "good" | "partial" | "missing";
  is_excluded: boolean;
  order_index: number;
}

export interface SyllabusUnitItem {
  id: string;
  subject_id: string;
  unit_number: number;
  title: string;
  description?: string;
  weightage_marks?: number;
  created_at: string;
  topics: TopicItem[];
}

export interface StudentQuestion {
  id: string;
  question_type: "mcq" | "subjective";
  subjective_subtype?: "very_short" | "short" | "long";
  question_text: string;
  options?: Array<{ id: string; text: string }>;
  marks: number;
  difficulty_label: string;
  order_index: number;
}

export interface TestTakingData {
  attempt_id: string;
  test_id: string;
  subject_id: string;
  title: string;
  source_mode: "reference_grounded" | "syllabus_scoped";
  duration_minutes: number;
  total_marks: number;
  started_at: string;
  questions: StudentQuestion[];
  saved_answers: Record<string, { selected_option_id?: string; answer_text?: string; is_marked_for_review?: boolean }>;
}

export interface CriterionResult {
  criterion_id: string;
  criterion_name?: string;
  awarded_marks: number;
  max_marks: number;
  justification: string;
  excerpt?: string;
}

export interface EvaluationDetail {
  question_id: string;
  question_type: "mcq" | "subjective";
  subjective_subtype?: "very_short" | "short" | "long";
  question_text: string;
  marks: number;
  awarded_marks: number;
  normalized_score_10?: number;
  selected_option_id?: string;
  student_answer_text?: string;
  correct_option_id?: string;
  explanation?: string;
  reference_answer?: string;
  criterion_results: CriterionResult[];
  correct_points: string[];
  missing_points: string[];
  misconceptions: string[];
  actionable_feedback?: string;
  source_references: Array<{
    document_id?: string;
    filename?: string;
    page_number?: number;
    excerpt?: string;
    supporting_text?: string;
  }>;
  review_needed: boolean;
  review_reason?: string;
}

export interface AttemptResults {
  attempt_id: string;
  test_id: string;
  subject_id: string;
  subject_name: string;
  test_title: string;
  source_mode: "reference_grounded" | "syllabus_scoped";
  started_at: string;
  submitted_at: string;
  time_spent_seconds: number;
  total_score: number;
  raw_score: number;
  max_raw_marks: number;
  normalized_score_10: number;
  score_display: string;
  objective_score: number;
  subjective_score: number;
  max_possible_score: number;
  evaluations: EvaluationDetail[];
  next_recommended_action?: string;
  adaptive_recommendation?: {
    target_concept_ids: string[];
    primary_focus: string;
    rationale: string;
    weak_concept_names: string[];
    strong_concept_names: string[];
  };
}

export interface CustomTestConfig {
  subject_id?: string;
  title?: string;
  mode: "objective_only" | "subjective_only" | "mixed";
  global_difficulty: "easy" | "medium" | "hard";
  target_topic_ids: string[];
  mcq_count: number;
  mcq_difficulty: "easy" | "medium" | "hard";
  very_short_count: number;
  very_short_difficulty: "easy" | "medium" | "hard";
  short_count: number;
  short_difficulty: "easy" | "medium" | "hard";
  long_count: number;
  long_difficulty: "easy" | "medium" | "hard";
  marks_per_type?: {
    mcq: number;
    very_short: number;
    short: number;
    long: number;
  };
  is_timed: boolean;
  duration_minutes: number;
  topic_distribution: "balanced" | "custom";
  shuffle_questions: boolean;
}

export interface ConceptItem {
  id: string;
  subject_id: string;
  name: string;
  description: string;
  supporting_chunk_ids: string[];
  source_references: Array<{
    chunk_id?: string;
    document_id: string;
    filename: string;
    page_number: number;
    excerpt: string;
  }>;
  is_student_edited: boolean;
  is_excluded: boolean;
  created_at: string;
}

export interface SettingsStatus {
  app_name: string;
  app_env: string;
  demo_mode: boolean;
  live_ai_available: boolean;
  nebius_base_url: string;
  nebius_fast_model: string;
  nebius_reasoning_model: string;
  embedding_provider: string;
  storage_dir: string;
  database_url_redacted: string;
  active_user: {
    id: string;
    name: string;
    email: string;
  };
}

export interface DashboardMetrics {
  documents_processed: number;
  tests_completed: number;
  concepts_practiced: number;
  average_score_pct: number;
  recent_attempts: Array<{
    attempt_id: string;
    test_id: string;
    title: string;
    subject_name: string;
    submitted_at: string;
    total_score: number;
    max_possible_score: number;
    score_percentage: number;
    objective_score: number;
    subjective_score: number;
  }>;
  topics_needing_practice: Array<{
    concept_id: string;
    name: string;
    subject_id: string;
    readiness_indicator: string;
    observed_attempts: number;
  }>;
  next_recommended_action: {
    action_type: string;
    title: string;
    description: string;
    link: string;
  };
}

// API methods
export async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options?.headers || {}),
      },
    });
  } catch (netErr: any) {
    if (typeof window !== "undefined" && window.location.hostname !== "localhost") {
      throw new Error(
        `Backend server unreachable at ${API_BASE || 'default'}. Please set NEXT_PUBLIC_API_URL in your Vercel settings to your deployed FastAPI backend URL.`
      );
    }
    throw new Error(`Cannot connect to Backend at ${API_BASE}. Make sure FastAPI is running (python -m uvicorn backend.app.main:app --port 8000).`);
  }

  if (!res.ok) {
    let errorMsg = `HTTP Error ${res.status}`;
    try {
      const errData = await res.json();
      if (typeof errData.detail === "string") {
        errorMsg = errData.detail;
      } else if (Array.isArray(errData.detail)) {
        errorMsg = errData.detail.map((d: any) => d.msg ? `${d.loc?.slice(-1)[0] || 'field'}: ${d.msg}` : JSON.stringify(d)).join("; ");
      } else if (errData.detail) {
        errorMsg = JSON.stringify(errData.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(errorMsg);
  }
  return res.json();
}

export const api = {
  getSettings: () => apiFetch<SettingsStatus>("/api/settings/status"),
  getDashboard: () => apiFetch<DashboardMetrics>("/api/dashboard/metrics"),
  
  // Subjects
  listSubjects: () => apiFetch<Subject[]>("/api/subjects"),
  getSubject: (id: string) => apiFetch<Subject>(`/api/subjects/${id}`),
  createSubject: (data: Partial<Subject>) =>
    apiFetch<Subject>("/api/subjects", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  deleteSubject: (id: string) =>
    apiFetch<{ message: string }>(`/api/subjects/${id}`, {
      method: "DELETE",
    }),
  seedDemo: (subjectId: string) =>
    apiFetch<{ message: string }>(`/api/subjects/${subjectId}/seed-demo`, {
      method: "POST",
    }),

  // Documents
  listDocuments: (subjectId: string) =>
    apiFetch<DocumentItem[]>(`/api/subjects/${subjectId}/documents`),
  uploadDocument: async (subjectId: string, file: File, documentRole: "syllabus" | "notes" | "previous_paper" = "notes") => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("document_role", documentRole);
    let res: Response;
    try {
      res = await fetch(`${API_BASE}/api/subjects/${subjectId}/documents/upload`, {
        method: "POST",
        body: formData,
      });
    } catch (netErr: any) {
      if (typeof window !== "undefined" && window.location.hostname !== "localhost") {
        throw new Error(
          `Backend server unreachable at ${API_BASE || 'default'}. Please set NEXT_PUBLIC_API_URL in your Vercel settings to your deployed FastAPI backend URL.`
        );
      }
      throw new Error(`Cannot connect to Backend at ${API_BASE}. Make sure FastAPI is running (python -m uvicorn backend.app.main:app --port 8000).`);
    }

    if (!res.ok) {
      let msg = "Upload failed";
      try {
        const err = await res.json();
        msg = err.detail || msg;
      } catch {}
      throw new Error(msg);
    }
    return res.json() as Promise<DocumentItem>;
  },
  pasteTextDocument: (subjectId: string, data: { title: string; content: string; document_role: "syllabus" | "notes" | "previous_paper" }) =>
    apiFetch<DocumentItem>(`/api/subjects/${subjectId}/documents/paste-text`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  deleteDocument: (documentId: string) =>
    apiFetch<{ message: string }>(`/api/documents/${documentId}`, {
      method: "DELETE",
    }),

  // Syllabus & Topics Hierarchy
  analyzeSyllabus: (subjectId: string) =>
    apiFetch<SyllabusUnitItem[]>(`/api/subjects/${subjectId}/syllabus/analyze`, {
      method: "POST",
    }),
  listUnits: (subjectId: string) =>
    apiFetch<SyllabusUnitItem[]>(`/api/subjects/${subjectId}/units`),
  listTopics: (subjectId: string, params?: { unit_id?: string; priority?: string; include_excluded?: boolean }) => {
    const query = new URLSearchParams();
    if (params?.unit_id) query.append("unit_id", params.unit_id);
    if (params?.priority) query.append("priority", params.priority);
    if (params?.include_excluded) query.append("include_excluded", "true");
    const qStr = query.toString();
    return apiFetch<TopicItem[]>(`/api/subjects/${subjectId}/topics${qStr ? `?${qStr}` : ""}`);
  },
  createTopic: (subjectId: string, data: Partial<TopicItem>) =>
    apiFetch<TopicItem>(`/api/subjects/${subjectId}/topics`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateTopic: (topicId: string, data: Partial<TopicItem>) =>
    apiFetch<TopicItem>(`/api/topics/${topicId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  mergeTopics: (targetTopicId: string, sourceTopicIds: string[]) =>
    apiFetch<{ status: string; target_topic_id: string; target_topic_name: string; merged_count: number }>(
      "/api/topics/merge",
      {
        method: "POST",
        body: JSON.stringify({
          target_topic_id: targetTopicId,
          source_topic_ids: sourceTopicIds,
        }),
      }
    ),

  // Legacy Concepts fallback
  listConcepts: (subjectId: string) =>
    apiFetch<ConceptItem[]>(`/api/subjects/${subjectId}/concepts`),
  extractConcepts: (subjectId: string) =>
    apiFetch<ConceptItem[]>(`/api/subjects/${subjectId}/concepts/extract`, {
      method: "POST",
    }),
  updateConcept: (conceptId: string, data: { name?: string; description?: string; is_excluded?: boolean }) =>
    apiFetch<ConceptItem>(`/api/concepts/${conceptId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  // Tests & Custom Test Builder
  generateTest: (subjectId: string, params: { test_type?: string; target_concept_ids?: string[]; title?: string }) =>
    apiFetch<{ id: string; title: string; total_marks: number }>(`/api/subjects/${subjectId}/tests/generate`, {
      method: "POST",
      body: JSON.stringify(params),
    }),
  createCustomTest: (subjectId: string, config: CustomTestConfig) =>
    apiFetch<{
      id: string;
      title: string;
      total_marks: number;
      total_raw_marks: number;
      normalized_max_score: number;
      source_mode: string;
      rationale: string;
      question_count: number;
    }>(`/api/subjects/${subjectId}/tests/custom`, {
      method: "POST",
      body: JSON.stringify(config),
    }),
  listTests: (subjectId: string) =>
    apiFetch<Array<{
      id: string;
      title: string;
      test_type: string;
      source_mode: string;
      total_marks: number;
      total_raw_marks: number;
      normalized_max_score: number;
      rationale?: string;
      created_at: string;
      question_count: number;
    }>>(`/api/subjects/${subjectId}/tests`),
  getTestTakingView: (testId: string) =>
    apiFetch<TestTakingData>(`/api/tests/${testId}/take`),
  saveAnswer: (attemptId: string, data: { question_id: string; selected_option_id?: string; answer_text?: string; is_marked_for_review?: boolean }) =>
    apiFetch<{ status: string }>(`/api/attempts/${attemptId}/save`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  submitAttempt: (attemptId: string, data: { time_spent_seconds: number; answers: any[] }) =>
    apiFetch<AttemptResults>(`/api/attempts/${attemptId}/submit`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  getAttemptResults: (attemptId: string) =>
    apiFetch<AttemptResults>(`/api/attempts/${attemptId}/results`),
};
