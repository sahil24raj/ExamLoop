from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Document, Test, Attempt, ConceptProgress, Concept, Subject
from backend.app.schemas import DashboardMetricsResponse
from backend.app.routers.subjects import get_or_create_default_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/metrics", response_model=DashboardMetricsResponse)
def get_dashboard_metrics(db: Session = Depends(get_db)):
    user = get_or_create_default_user(db)

    doc_count = db.query(Document).filter(Document.user_id == user.id, Document.is_deleted == False).count()
    completed_attempts = db.query(Attempt).filter(
        Attempt.user_id == user.id,
        Attempt.status == "graded"
    ).order_by(Attempt.submitted_at.desc()).all()

    test_count = len(completed_attempts)
    avg_score = 0.0
    if completed_attempts:
        percentages = [
            (a.total_score / a.max_possible_score * 100)
            for a in completed_attempts
            if a.max_possible_score and a.max_possible_score > 0
        ]
        if percentages:
            avg_score = round(sum(percentages) / len(percentages), 1)

    progress_records = db.query(ConceptProgress).filter(ConceptProgress.user_id == user.id).all()
    concepts_practiced = len([p for p in progress_records if p.total_observed_attempts > 0])

    recent_attempts_data = []
    for a in completed_attempts[:5]:
        t = a.test
        s = t.subject if t else None
        pct = round((a.total_score / a.max_possible_score * 100), 1) if a.max_possible_score else 0.0
        recent_attempts_data.append({
            "attempt_id": a.id,
            "test_id": a.test_id,
            "title": t.title if t else "Exam Practice",
            "subject_name": s.name if s else "Subject",
            "submitted_at": a.submitted_at.isoformat() if a.submitted_at else "",
            "total_score": a.total_score,
            "max_possible_score": a.max_possible_score,
            "score_percentage": pct,
            "objective_score": a.objective_score,
            "subjective_score": a.subjective_score
        })

    # Find topics needing practice
    weak_progress = db.query(ConceptProgress).filter(
        ConceptProgress.user_id == user.id,
        ConceptProgress.readiness_indicator == "needs_practice"
    ).all()

    weak_concept_ids = [wp.concept_id for wp in weak_progress]
    weak_concepts = {c.id: c for c in db.query(Concept).filter(Concept.id.in_(weak_concept_ids)).all()}

    topics_needing_practice = []
    for wp in weak_progress:
        c = weak_concepts.get(wp.concept_id)
        if c:
            topics_needing_practice.append({
                "concept_id": c.id,
                "name": c.name,
                "subject_id": c.subject_id,
                "readiness_indicator": wp.readiness_indicator,
                "observed_attempts": wp.total_observed_attempts
            })

    # Determine next recommended action
    next_action = {
        "action_type": "create_subject",
        "title": "Set up your first subject",
        "description": "Create a subject workspace and upload study notes or searchable lecture slides.",
        "link": "/subjects/new"
    }

    if doc_count == 0 and db.query(Subject).filter(Subject.user_id == user.id).count() > 0:
        first_sub = db.query(Subject).filter(Subject.user_id == user.id).first()
        next_action = {
            "action_type": "upload_notes",
            "title": f"Upload notes for {first_sub.name}",
            "description": "Upload searchable PDFs or text files to extract concepts and create your diagnostic test.",
            "link": f"/subjects/{first_sub.id}"
        }
    elif topics_needing_practice:
        wp = topics_needing_practice[0]
        next_action = {
            "action_type": "targeted_test",
            "title": f"Targeted Practice: {wp['name']}",
            "description": f"Recent rubric evaluations flagged gaps in {wp['name']}. Start a focused adaptive session.",
            "link": f"/subjects/{wp['subject_id']}"
        }
    elif doc_count > 0 and test_count == 0:
        first_sub = db.query(Subject).filter(Subject.user_id == user.id).first()
        next_action = {
            "action_type": "diagnostic_test",
            "title": f"Take Diagnostic Test for {first_sub.name}",
            "description": "Assess baseline strengths and uncover key areas needing targeted exam preparation.",
            "link": f"/subjects/{first_sub.id}"
        }

    return DashboardMetricsResponse(
        documents_processed=doc_count,
        tests_completed=test_count,
        concepts_practiced=concepts_practiced,
        average_score_pct=avg_score,
        recent_attempts=recent_attempts_data,
        topics_needing_practice=topics_needing_practice,
        next_recommended_action=next_action
    )
