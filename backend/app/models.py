import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from backend.app.database import Base

def gen_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(64), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    subjects = relationship("Subject", back_populates="user", cascade="all, delete-orphan")
    attempts = relationship("Attempt", back_populates="user", cascade="all, delete-orphan")


class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(String(64), primary_key=True, default=gen_uuid)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    exam_date = Column(String(64), nullable=True) # e.g. "2026-11-15"
    preferred_duration_minutes = Column(Integer, default=20)
    default_mcq_count = Column(Integer, default=4)
    default_subjective_count = Column(Integer, default=2)
    default_subjective_marks = Column(Integer, default=5)
    syllabus_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    user = relationship("User", back_populates="subjects")
    documents = relationship("Document", back_populates="subject", cascade="all, delete-orphan")
    concepts = relationship("Concept", back_populates="subject", cascade="all, delete-orphan")
    syllabus_units = relationship("SyllabusUnit", back_populates="subject", cascade="all, delete-orphan", order_by="SyllabusUnit.unit_number")
    topics = relationship("Topic", back_populates="subject", cascade="all, delete-orphan", order_by="Topic.order_index")
    questions = relationship("Question", back_populates="subject", cascade="all, delete-orphan")
    tests = relationship("Test", back_populates="subject", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String(64), primary_key=True, default=gen_uuid)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False)
    subject_id = Column(String(64), ForeignKey("subjects.id"), nullable=False)
    document_role = Column(String(32), default="notes") # "syllabus" | "notes" | "previous_paper"
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(128), nullable=False)
    file_path = Column(String(512), nullable=False)
    page_count = Column(Integer, default=1)
    status = Column(String(32), default="uploaded") # uploaded, extracting, indexing, ready, failed
    error_message = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    subject = relationship("Subject", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(String(64), primary_key=True, default=gen_uuid)
    document_id = Column(String(64), ForeignKey("documents.id"), nullable=False)
    subject_id = Column(String(64), ForeignKey("subjects.id"), nullable=False)
    page_number = Column(Integer, default=1)
    chunk_index = Column(Integer, default=0)
    content = Column(Text, nullable=False)
    token_estimate = Column(Integer, default=0)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    document = relationship("Document", back_populates="chunks")


class Concept(Base):
    __tablename__ = "concepts"
    
    id = Column(String(64), primary_key=True, default=gen_uuid)
    subject_id = Column(String(64), ForeignKey("subjects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    supporting_chunk_ids = Column(JSON, default=list)
    source_references = Column(JSON, default=list) # [{document_id, filename, page_number, excerpt}]
    is_student_edited = Column(Boolean, default=False)
    is_excluded = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    subject = relationship("Subject", back_populates="concepts")


class SyllabusUnit(Base):
    __tablename__ = "syllabus_units"
    
    id = Column(String(64), primary_key=True, default=gen_uuid)
    subject_id = Column(String(64), ForeignKey("subjects.id"), nullable=False)
    unit_number = Column(Integer, default=1)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    weightage_marks = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    subject = relationship("Subject", back_populates="syllabus_units")
    topics = relationship("Topic", back_populates="unit", cascade="all, delete-orphan", order_by="Topic.order_index")


class Topic(Base):
    __tablename__ = "topics"
    
    id = Column(String(64), primary_key=True, default=gen_uuid)
    subject_id = Column(String(64), ForeignKey("subjects.id"), nullable=False)
    unit_id = Column(String(64), ForeignKey("syllabus_units.id"), nullable=True)
    unit_name = Column(String(255), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True, default="")
    subtopics = Column(JSON, default=list) # list of str
    is_inferred = Column(Boolean, default=False) # True = AI inferred; False = explicitly in syllabus
    is_confirmed = Column(Boolean, default=True) # Inferred topics need confirmation
    practice_priority = Column(String(32), default="normal") # "high" | "medium" | "normal"
    priority_reason = Column(Text, nullable=True) # Explainable reason
    weightage_explicit = Column(Float, nullable=True) # If syllabus explicitly defines marks
    observed_paper_frequency = Column(Integer, default=0) # If previous papers provided
    reference_coverage = Column(String(32), default="none") # "covered" | "partial" | "none"
    supporting_chunk_ids = Column(JSON, default=list)
    source_references = Column(JSON, default=list)
    is_excluded = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    subject = relationship("Subject", back_populates="topics")
    unit = relationship("SyllabusUnit", back_populates="topics")


class Question(Base):
    __tablename__ = "questions"
    
    id = Column(String(64), primary_key=True, default=gen_uuid)
    subject_id = Column(String(64), ForeignKey("subjects.id"), nullable=False)
    concept_ids = Column(JSON, default=list)
    topic_ids = Column(JSON, default=list)
    question_type = Column(String(32), nullable=False) # 'mcq' | 'subjective'
    subjective_subtype = Column(String(32), nullable=True) # 'very_short' | 'short' | 'long'
    source_mode = Column(String(32), default="reference_grounded") # 'reference_grounded' | 'syllabus_scoped'
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=True) # [{"id": "A", "text": "..."}]
    correct_option_id = Column(String(32), nullable=True) # Only for MCQs
    explanation = Column(Text, nullable=True)
    difficulty_label = Column(String(32), default="medium")
    marks = Column(Integer, default=1)
    expected_key_points = Column(JSON, default=list) # For subjective questions
    reference_answer = Column(Text, nullable=True)
    source_references = Column(JSON, default=list) # [{chunk_id, document_id, filename, page_number, excerpt}]
    validation_status = Column(String(32), default="valid") # valid, flagged, rejected
    verification_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    subject = relationship("Subject", back_populates="questions")
    rubric_criteria = relationship("RubricCriterion", back_populates="question", cascade="all, delete-orphan")


class RubricCriterion(Base):
    __tablename__ = "rubric_criteria"
    
    id = Column(String(64), primary_key=True, default=gen_uuid)
    question_id = Column(String(64), ForeignKey("questions.id"), nullable=False)
    criterion_id = Column(String(64), nullable=False) # e.g. "crit_1"
    description = Column(Text, nullable=False)
    max_marks = Column(Float, nullable=False)
    evidence_references = Column(JSON, default=list)
    
    question = relationship("Question", back_populates="rubric_criteria")


class Test(Base):
    __test__ = False
    __tablename__ = "tests"
    
    id = Column(String(64), primary_key=True, default=gen_uuid)
    subject_id = Column(String(64), ForeignKey("subjects.id"), nullable=False)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    test_type = Column(String(32), default="practice") # diagnostic, adaptive, targeted, practice
    source_mode = Column(String(32), default="reference_grounded") # reference_grounded, syllabus_scoped
    target_concept_ids = Column(JSON, default=list)
    target_topic_ids = Column(JSON, default=list)
    test_config = Column(JSON, default=dict) # Full custom builder configuration
    duration_minutes = Column(Integer, default=20)
    total_marks = Column(Integer, default=10)
    total_raw_marks = Column(Float, default=10.0)
    normalized_max_score = Column(Float, default=10.0) # Always normalized out of 10
    rationale = Column(Text, nullable=True) # Why this test was chosen / generated
    status = Column(String(32), default="ready")
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    subject = relationship("Subject", back_populates="tests")
    test_questions = relationship("TestQuestion", back_populates="test", cascade="all, delete-orphan", order_by="TestQuestion.order_index")
    attempts = relationship("Attempt", back_populates="test", cascade="all, delete-orphan")


class TestQuestion(Base):
    __test__ = False
    __tablename__ = "test_questions"
    
    id = Column(String(64), primary_key=True, default=gen_uuid)
    test_id = Column(String(64), ForeignKey("tests.id"), nullable=False)
    question_id = Column(String(64), ForeignKey("questions.id"), nullable=False)
    order_index = Column(Integer, default=0)
    
    test = relationship("Test", back_populates="test_questions")
    question = relationship("Question")


class Attempt(Base):
    __tablename__ = "attempts"
    
    id = Column(String(64), primary_key=True, default=gen_uuid)
    test_id = Column(String(64), ForeignKey("tests.id"), nullable=False)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime(timezone=True), default=utc_now)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    time_spent_seconds = Column(Integer, default=0)
    status = Column(String(32), default="in_progress") # in_progress, submitted, graded
    total_score = Column(Float, default=0.0) # raw total score
    raw_score = Column(Float, default=0.0)
    max_raw_marks = Column(Float, default=0.0)
    normalized_score_10 = Column(Float, default=0.0) # 10 * raw_score / max_raw_marks
    objective_score = Column(Float, default=0.0)
    subjective_score = Column(Float, default=0.0)
    max_possible_score = Column(Float, default=0.0)
    
    test = relationship("Test", back_populates="attempts")
    user = relationship("User", back_populates="attempts")
    answers = relationship("StudentAnswer", back_populates="attempt", cascade="all, delete-orphan")
    evaluations = relationship("Evaluation", back_populates="attempt", cascade="all, delete-orphan")


class StudentAnswer(Base):
    __tablename__ = "student_answers"
    
    id = Column(String(64), primary_key=True, default=gen_uuid)
    attempt_id = Column(String(64), ForeignKey("attempts.id"), nullable=False)
    question_id = Column(String(64), ForeignKey("questions.id"), nullable=False)
    selected_option_id = Column(String(32), nullable=True) # MCQ selection
    answer_text = Column(Text, nullable=True) # Subjective answer
    is_marked_for_review = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    attempt = relationship("Attempt", back_populates="answers")
    question = relationship("Question")


class Evaluation(Base):
    __tablename__ = "evaluations"
    
    id = Column(String(64), primary_key=True, default=gen_uuid)
    attempt_id = Column(String(64), ForeignKey("attempts.id"), nullable=False)
    question_id = Column(String(64), ForeignKey("questions.id"), nullable=False)
    subjective_subtype = Column(String(32), nullable=True) # very_short, short, long
    awarded_marks = Column(Float, default=0.0)
    max_marks = Column(Float, default=0.0)
    normalized_score_10 = Column(Float, nullable=True)
    criterion_results = Column(JSON, default=list) # [{criterion_id, awarded_marks, max_marks, justification, excerpt}]
    correct_points = Column(JSON, default=list)
    missing_points = Column(JSON, default=list)
    misconceptions = Column(JSON, default=list)
    actionable_feedback = Column(Text, nullable=True)
    source_references = Column(JSON, default=list)
    review_needed = Column(Boolean, default=False)
    review_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    attempt = relationship("Attempt", back_populates="evaluations")
    question = relationship("Question")


class ConceptProgress(Base):
    __tablename__ = "concept_progress"
    
    id = Column(String(64), primary_key=True, default=gen_uuid)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False)
    subject_id = Column(String(64), ForeignKey("subjects.id"), nullable=False)
    concept_id = Column(String(64), ForeignKey("concepts.id"), nullable=False)
    total_mcq_attempted = Column(Integer, default=0)
    total_mcq_correct = Column(Integer, default=0)
    subjective_marks_awarded = Column(Float, default=0.0)
    subjective_marks_possible = Column(Float, default=0.0)
    total_observed_attempts = Column(Integer, default=0)
    last_practiced_at = Column(DateTime(timezone=True), nullable=True)
    readiness_indicator = Column(String(64), default="not_enough_evidence") # not_enough_evidence, needs_practice, developing, proficient
    notes = Column(Text, nullable=True)


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    
    id = Column(String(64), primary_key=True, default=gen_uuid)
    job_type = Column(String(64), nullable=False) # document_extract, concept_extract, question_gen, evaluation
    target_id = Column(String(64), nullable=False)
    status = Column(String(32), default="pending") # pending, processing, completed, failed
    error = Column(Text, nullable=True)
    progress_pct = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class AIRequestLog(Base):
    __tablename__ = "ai_request_logs"
    
    id = Column(String(64), primary_key=True, default=gen_uuid)
    provider = Column(String(64), default="nebius")
    model_name = Column(String(128), nullable=False)
    endpoint = Column(String(128), nullable=False)
    duration_ms = Column(Integer, default=0)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    status = Column(String(32), default="success") # success, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
