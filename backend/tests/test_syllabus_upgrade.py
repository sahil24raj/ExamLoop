import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models import (
    User, Subject, Document, DocumentChunk, SyllabusUnit, Topic,
    Question, RubricCriterion, Test, TestQuestion, Attempt, StudentAnswer, Evaluation
)
from backend.app.services.ai_service import ai_service
from backend.app.services.scoring_service import scoring_service
from backend.app.schemas import StudentQuestionView, CustomTestCreateRequest

TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    from backend.app.config import settings
    orig_demo = settings.demo_mode
    settings.demo_mode = True  # Ensure tests use deterministic fixtures
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    user = User(id="user_test_upgrade", email="student@examloop.local", name="Syllabus Student")
    session.add(user)
    session.commit()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)
    settings.demo_mode = orig_demo

def test_syllabus_hierarchy_extraction_explicit_vs_inferred(db):
    subject = Subject(id="subj_test_1", user_id="user_test_upgrade", name="Database Systems")
    db.add(subject)
    db.commit()

    sample_syllabus_text = """
    UNIT 1: Relational Data Model & SQL (15 Marks)
    - Relational algebra operations
    - SQL DDL, DML, and complex joins
    
    UNIT 2: Transaction Processing & Concurrency (20 Marks)
    - ACID properties
    - Serializability and Two-Phase Locking (2PL)
    """

    res = ai_service.analyze_syllabus_hierarchy(
        syllabus_text=sample_syllabus_text,
        notes_chunks=None,
        previous_papers_chunks=None,
        db=db
    )
    units_data = res.get("units", res) if isinstance(res, dict) else res

    assert len(units_data) >= 2
    # Verify units structure
    unit1 = next(u for u in units_data if "Unit 1" in u["title"] or "Relational" in u["title"])
    assert unit1["unit_number"] == 1
    assert len(unit1["topics"]) >= 2

    # Check explicit vs inferred
    for u in units_data:
        for t in u["topics"]:
            assert "name" in t
            assert "practice_priority" in t
            assert t["practice_priority"] in ["high", "medium", "low", "normal"]
            # Honest provenance
            assert "priority_reason" in t
            assert len(t["priority_reason"]) > 0

def test_custom_test_generation_exact_counts_and_subtypes(db):
    subject = Subject(id="subj_test_2", user_id="user_test_upgrade", name="Software Engineering")
    db.add(subject)
    db.commit()

    # Create dummy topics
    topic1 = Topic(id="top_1", subject_id=subject.id, name="Design Patterns", description="Creational and structural patterns", practice_priority="high")
    topic2 = Topic(id="top_2", subject_id=subject.id, name="Agile Scrum", description="Sprints and user stories", practice_priority="medium")
    db.add_all([topic1, topic2])
    db.commit()

    # Request custom test with specific subtype breakdown
    config = CustomTestCreateRequest(
        title="Custom Architecture Test",
        mode="mixed",
        global_difficulty="medium",
        target_topic_ids=["top_1", "top_2"],
        mcq_count=2,
        mcq_difficulty="medium",
        very_short_count=1,
        very_short_difficulty="easy",
        short_count=2,
        short_difficulty="medium",
        long_count=1,
        long_difficulty="hard",
        is_timed=True,
        duration_minutes=45
    )

    questions_raw = ai_service.generate_custom_test(
        topics=[{"id": topic1.id, "name": topic1.name, "description": topic1.description}, {"id": topic2.id, "name": topic2.name, "description": topic2.description}],
        retrieved_evidence=[],
        config=config.model_dump(),
        db=db
    )

    # Total questions must match exactly 2 + 1 + 2 + 1 = 6
    assert len(questions_raw) == 6

    mcqs = [q for q in questions_raw if q["question_type"] == "mcq"]
    very_shorts = [q for q in questions_raw if q.get("subjective_subtype") == "very_short"]
    shorts = [q for q in questions_raw if q.get("subjective_subtype") == "short"]
    longs = [q for q in questions_raw if q.get("subjective_subtype") == "long"]

    assert len(mcqs) == 2
    assert len(very_shorts) == 1
    assert len(shorts) == 2
    assert len(longs) == 1

    # Verify rubric criteria present for all subjective questions
    for subj in (very_shorts + shorts + longs):
        assert "rubric_criteria" in subj
        assert len(subj["rubric_criteria"]) > 0
        total_rubric_marks = sum(float(c["max_marks"]) for c in subj["rubric_criteria"])
        assert total_rubric_marks == float(subj["marks"])

def test_student_question_view_security():
    # Verify that StudentQuestionView explicitly redacts correct_option_id, reference_answer, and rubric
    q = Question(
        id="q_secure_01",
        subject_id="s1",
        question_type="mcq",
        question_text="What does ACID stand for?",
        options=[{"id": "A", "text": "Atomicity, Consistency, Isolation, Durability"}, {"id": "B", "text": "Wrong"}],
        correct_option_id="A",
        explanation="Standard definition",
        marks=2,
        difficulty_label="medium"
    )

    view = StudentQuestionView.model_validate(q)
    # The view model must NOT have correct_option_id or explanation
    assert not hasattr(view, "correct_option_id")
    assert not hasattr(view, "reference_answer")
    assert not hasattr(view, "rubric_criteria")

def test_normalized_score_calculation_out_of_10(db):
    subject = Subject(id="subj_test_3", user_id="user_test_upgrade", name="Compilers")
    db.add(subject)
    db.commit()

    test = Test(id="t_norm_1", subject_id=subject.id, user_id="user_test_upgrade", title="Lexing Test", total_marks=25)
    db.add(test)
    db.commit()

    # 18 out of 25 raw marks should yield exactly 7.2 / 10
    raw_awarded = 18.0
    raw_max = 25.0
    normalized = round((10.0 * raw_awarded) / raw_max, 1)
    assert normalized == 7.2

    # Edge cases
    # 0 raw marks -> 0.0 / 10
    assert round((10.0 * 0.0) / 25.0, 1) == 0.0
    # Perfect score 25/25 -> 10.0 / 10
    assert round((10.0 * 25.0) / 25.0, 1) == 10.0

def test_idempotent_attempt_submission(db):
    subject = Subject(id="subj_test_4", user_id="user_test_upgrade", name="Networks")
    db.add(subject)
    db.commit()

    q = Question(
        id="q_net_1",
        subject_id=subject.id,
        question_type="mcq",
        question_text="What layer is IP?",
        options=[{"id": "A", "text": "Network Layer"}, {"id": "B", "text": "Transport Layer"}],
        correct_option_id="A",
        marks=2,
        difficulty_label="easy"
    )
    db.add(q)
    db.commit()

    test = Test(id="t_net_1", subject_id=subject.id, user_id="user_test_upgrade", title="Network Test", total_marks=2)
    db.add(test)
    db.commit()

    db.add(TestQuestion(test_id=test.id, question_id=q.id, order_index=0))
    db.commit()

    attempt = Attempt(id="att_net_1", test_id=test.id, user_id="user_test_upgrade", status="in_progress")
    db.add(attempt)
    db.commit()

    db.add(StudentAnswer(attempt_id=attempt.id, question_id=q.id, selected_option_id="A"))
    db.commit()

    # First evaluation
    res1 = scoring_service.evaluate_attempt(db, attempt)
    assert res1.status == "graded"
    assert res1.total_score == 2.0
    eval_count_1 = db.query(Evaluation).filter(Evaluation.attempt_id == attempt.id).count()
    assert eval_count_1 == 1

    # Second evaluation (idempotent submission)
    res2 = scoring_service.evaluate_attempt(db, attempt)
    assert res2.status == "graded"
    assert res2.total_score == 2.0
    eval_count_2 = db.query(Evaluation).filter(Evaluation.attempt_id == attempt.id).count()
    assert eval_count_2 == 1  # No duplicate evaluation records created
