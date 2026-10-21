from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- Subject Schemas ---
class SubjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    exam_date: Optional[str] = None
    preferred_duration_minutes: int = Field(default=20, ge=5, le=180)
    default_mcq_count: int = Field(default=4, ge=1, le=50)
    default_subjective_count: int = Field(default=2, ge=0, le=20)
    default_subjective_marks: int = Field(default=5, ge=1, le=20)
    syllabus_text: Optional[str] = None

class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    exam_date: Optional[str] = None
    preferred_duration_minutes: Optional[int] = None
    default_mcq_count: Optional[int] = None
    default_subjective_count: Optional[int] = None
    default_subjective_marks: Optional[int] = None
    syllabus_text: Optional[str] = None

class SubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    name: str
    exam_date: Optional[str]
    preferred_duration_minutes: int
    default_mcq_count: int
    default_subjective_count: int
    default_subjective_marks: int
    syllabus_text: Optional[str]
    created_at: datetime
    document_count: Optional[int] = 0
    concept_count: Optional[int] = 0
    test_count: Optional[int] = 0

# --- Document Schemas ---
class DocumentChunkResponse(BaseModel):
    id: str
    document_id: str
    subject_id: str
    page_number: int
    chunk_index: int
    content: str
    token_estimate: int

    model_config = ConfigDict(from_attributes=True)

class DocumentResponse(BaseModel):
    id: str
    subject_id: str
    filename: str
    original_name: str
    file_size: int
    mime_type: str
    page_count: int
    document_role: str = "notes" # syllabus, notes, previous_paper
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Concept Schemas ---
class SourceReference(BaseModel):
    chunk_id: Optional[str] = None
    document_id: str
    filename: str
    page_number: int
    excerpt: str

class ConceptCreate(BaseModel):
    name: str
    description: str
    supporting_chunk_ids: List[str] = []
    source_references: List[SourceReference] = []

class ConceptUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_excluded: Optional[bool] = None

class ConceptResponse(BaseModel):
    id: str
    subject_id: str
    name: str
    description: str
    supporting_chunk_ids: List[str] = []
    source_references: List[Dict[str, Any]] = []
    is_student_edited: bool
    is_excluded: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Topic & Syllabus Unit Schemas ---
class TopicCreate(BaseModel):
    name: str
    unit_name: Optional[str] = None
    description: Optional[str] = "Student added topic"
    practice_priority: str = "normal"

class TopicUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    unit_name: Optional[str] = None
    is_confirmed: Optional[bool] = None
    is_excluded: Optional[bool] = None
    practice_priority: Optional[str] = None

class TopicMergeRequest(BaseModel):
    source_topic_ids: List[str]
    merged_name: str
    merged_description: Optional[str] = None

class TopicResponse(BaseModel):
    id: str
    subject_id: str
    unit_id: Optional[str] = None
    unit_name: Optional[str] = None
    name: str
    description: str
    subtopics: List[str] = []
    is_inferred: bool = False
    is_confirmed: bool = True
    practice_priority: str = "normal" # high, medium, normal
    priority_reason: Optional[str] = None
    weightage_explicit: Optional[float] = None
    observed_paper_frequency: int = 0
    reference_coverage: str = "none" # covered, partial, none
    source_references: List[Dict[str, Any]] = []
    is_excluded: bool = False
    order_index: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SyllabusUnitResponse(BaseModel):
    id: str
    subject_id: str
    unit_number: int
    title: str
    description: Optional[str] = None
    weightage_marks: Optional[float] = None
    topics: List[TopicResponse] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Question & Rubric Schemas ---
class MCQOption(BaseModel):
    id: str
    text: str

class RubricCriterionSchema(BaseModel):
    criterion_id: str
    description: str
    max_marks: float
    evidence_references: List[Dict[str, Any]] = []

class QuestionResponse(BaseModel):
    id: str
    subject_id: str
    concept_ids: List[str] = []
    topic_ids: List[str] = []
    question_type: str
    subjective_subtype: Optional[str] = None # very_short, short, long
    source_mode: str = "reference_grounded"
    question_text: str
    options: Optional[List[MCQOption]] = None
    explanation: Optional[str] = None
    difficulty_label: str
    marks: int
    expected_key_points: Optional[List[str]] = None
    reference_answer: Optional[str] = None
    source_references: List[Dict[str, Any]] = []
    validation_status: str
    verification_notes: Optional[str] = None
    rubric_criteria: Optional[List[RubricCriterionSchema]] = None

    model_config = ConfigDict(from_attributes=True)

# Student View of Question: Answer keys & rubrics are strictly omitted during test taking
class StudentQuestionView(BaseModel):
    id: str
    question_type: str
    subjective_subtype: Optional[str] = None
    question_text: str
    options: Optional[List[MCQOption]] = None # No correct_option_id!
    marks: int
    difficulty_label: str = "medium"
    order_index: int = 0

    model_config = ConfigDict(from_attributes=True)

class TestTakingView(BaseModel):
    attempt_id: str
    test_id: str
    subject_id: str
    title: str
    source_mode: str = "reference_grounded"
    duration_minutes: int
    total_marks: int
    started_at: datetime
    questions: List[StudentQuestionView]
    saved_answers: Dict[str, Dict[str, Any]] # question_id -> {selected_option_id, answer_text}

# --- Test Schemas ---
class TestCreateRequest(BaseModel):
    subject_id: Optional[str] = None
    test_type: str = "diagnostic" # diagnostic, targeted, adaptive, practice
    target_concept_ids: Optional[List[str]] = None
    target_topic_ids: Optional[List[str]] = None
    mcq_count: Optional[int] = None
    subjective_count: Optional[int] = None
    title: Optional[str] = None

class CustomTestCreateRequest(BaseModel):
    subject_id: Optional[str] = None
    title: Optional[str] = None
    mode: str = "mixed" # objective_only, subjective_only, mixed
    global_difficulty: str = "medium" # easy, medium, hard
    target_topic_ids: List[str] = []
    # Objective
    mcq_count: int = 0
    mcq_difficulty: str = "medium"
    # Subjective subtypes
    very_short_count: int = 0
    very_short_difficulty: str = "easy"
    short_count: int = 0
    short_difficulty: str = "medium"
    long_count: int = 0
    long_difficulty: str = "hard"
    # Marks config
    marks_per_type: Optional[Dict[str, int]] = None # e.g. {"mcq": 1, "very_short": 2, "short": 5, "long": 10}
    # Settings
    is_timed: bool = False
    duration_minutes: int = 30
    topic_distribution: str = "balanced"
    shuffle_questions: bool = True

class TestResponse(BaseModel):
    id: str
    subject_id: str
    title: str
    test_type: str
    source_mode: str = "reference_grounded"
    target_concept_ids: List[str] = []
    target_topic_ids: List[str] = []
    test_config: Dict[str, Any] = {}
    duration_minutes: int
    total_marks: int
    total_raw_marks: float = 10.0
    normalized_max_score: float = 10.0
    rationale: Optional[str] = None
    status: str
    created_at: datetime
    question_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)

# --- Attempt & Answering Schemas ---
class AnswerSaveRequest(BaseModel):
    question_id: str
    selected_option_id: Optional[str] = None
    answer_text: Optional[str] = None
    is_marked_for_review: Optional[bool] = False

class AttemptSubmitRequest(BaseModel):
    time_spent_seconds: int = 0
    answers: List[AnswerSaveRequest] = []

# --- Evaluation & Results Schemas ---
class CriterionResultSchema(BaseModel):
    criterion_id: str
    criterion_name: Optional[str] = None
    awarded_points: Optional[float] = None
    max_points: Optional[float] = None
    awarded_marks: Optional[float] = None
    max_marks: Optional[float] = None
    justification: str
    excerpt: Optional[str] = None

class EvaluationDetailResponse(BaseModel):
    question_id: str
    question_type: str
    subjective_subtype: Optional[str] = None
    question_text: str
    marks: int
    awarded_marks: float
    normalized_score_10: Optional[float] = None
    selected_option_id: Optional[str] = None
    student_answer_text: Optional[str] = None
    correct_option_id: Optional[str] = None
    explanation: Optional[str] = None
    reference_answer: Optional[str] = None
    criterion_results: List[CriterionResultSchema] = []
    correct_points: List[str] = []
    missing_points: List[str] = []
    misconceptions: List[str] = []
    actionable_feedback: Optional[str] = None
    source_references: List[Dict[str, Any]] = []
    review_needed: bool = False
    review_reason: Optional[str] = None

class AttemptResultResponse(BaseModel):
    attempt_id: str
    test_id: str
    subject_id: str
    subject_name: str
    test_title: str
    source_mode: str = "reference_grounded"
    started_at: datetime
    submitted_at: Optional[datetime]
    time_spent_seconds: int
    total_score: float # raw total score
    raw_score: float = 0.0
    max_raw_marks: float = 0.0
    normalized_score_10: float = 0.0
    score_display: str = "" # e.g. "7.2 / 10 · 18 / 25 raw marks"
    objective_score: float
    subjective_score: float
    max_possible_score: float
    evaluations: List[EvaluationDetailResponse]
    next_recommended_action: Optional[str] = None
    adaptive_recommendation: Optional[Dict[str, Any]] = None

# --- Diagnostics & Settings ---
class SettingsStatusResponse(BaseModel):
    app_name: str
    app_env: str
    demo_mode: bool
    live_ai_available: bool
    nebius_base_url: str
    nebius_fast_model: str
    nebius_reasoning_model: str
    embedding_provider: str
    storage_dir: str
    database_url_redacted: str
    active_user: Dict[str, str]
    supabase_configured: Optional[bool] = False
    supabase_db_connected: Optional[bool] = False
    supabase_url_redacted: Optional[str] = None

class DashboardMetricsResponse(BaseModel):
    documents_processed: int
    tests_completed: int
    concepts_practiced: int
    average_score_pct: float
    recent_attempts: List[Dict[str, Any]]
    topics_needing_practice: List[Dict[str, Any]]
    next_recommended_action: Dict[str, Any]
