from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import (
    Attempt, StudentAnswer, Test, TestQuestion, Question, Evaluation
)
from backend.app.schemas import (
    AnswerSaveRequest, AttemptSubmitRequest, AttemptResultResponse, EvaluationDetailResponse,
    CriterionResultSchema
)
from backend.app.services.scoring_service import scoring_service
from backend.app.services.adaptive_service import adaptive_service
from backend.app.auth import get_current_user
from backend.app.models import User

import logging
from backend.app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/attempts", tags=["Attempts"])

@router.post("/{attempt_id}/save")
def save_answer(
    attempt_id: str,
    payload: AnswerSaveRequest,
    db: Session = Depends(get_db)
):
    attempt = db.query(Attempt).filter(Attempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    if attempt.status == "graded":
        raise HTTPException(status_code=400, detail="Cannot edit answers for an already graded attempt.")

    ans = db.query(StudentAnswer).filter(
        StudentAnswer.attempt_id == attempt_id,
        StudentAnswer.question_id == payload.question_id
    ).first()

    if not ans:
        ans = StudentAnswer(
            attempt_id=attempt_id,
            question_id=payload.question_id,
            selected_option_id=payload.selected_option_id,
            answer_text=payload.answer_text,
            is_marked_for_review=payload.is_marked_for_review or False
        )
        db.add(ans)
    else:
        if payload.selected_option_id is not None:
            ans.selected_option_id = payload.selected_option_id
        if payload.answer_text is not None:
            ans.answer_text = payload.answer_text
        if payload.is_marked_for_review is not None:
            ans.is_marked_for_review = payload.is_marked_for_review
        ans.updated_at = datetime.now(timezone.utc)

    db.commit()
    return {"status": "saved", "question_id": payload.question_id}

@router.post("/{attempt_id}/submit", response_model=AttemptResultResponse)
def submit_attempt(
    attempt_id: str,
    payload: AttemptSubmitRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    attempt = db.query(Attempt).filter(Attempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    if attempt.user_id != user.id:
        if attempt.user_id == settings.default_user_id:
            attempt.user_id = user.id
            db.commit()
        elif user.id == settings.default_user_id:
            pass
        else:
            raise HTTPException(status_code=403, detail="Not authorized to submit this attempt")

    # Save any final answers passed in payload
    for ans_data in payload.answers:
        ans = db.query(StudentAnswer).filter(
            StudentAnswer.attempt_id == attempt_id,
            StudentAnswer.question_id == ans_data.question_id
        ).first()
        if not ans:
            ans = StudentAnswer(
                attempt_id=attempt_id,
                question_id=ans_data.question_id,
                selected_option_id=ans_data.selected_option_id,
                answer_text=ans_data.answer_text
            )
            db.add(ans)
        else:
            if ans_data.selected_option_id is not None:
                ans.selected_option_id = ans_data.selected_option_id
            if ans_data.answer_text is not None:
                ans.answer_text = ans_data.answer_text

    attempt.time_spent_seconds = payload.time_spent_seconds
    attempt.submitted_at = datetime.now(timezone.utc)
    db.commit()

    # Idempotent scoring
    try:
        attempt = scoring_service.evaluate_attempt(db, attempt)
    except Exception as e:
        logger.error(f"Error during attempt evaluation {attempt_id}: {e}", exc_info=True)
        attempt.status = "graded"
        db.commit()

    # Update concept progress heuristics
    try:
        adaptive_service.update_concept_progress(db, attempt)
    except Exception as e:
        logger.error(f"Error updating concept progress for attempt {attempt_id}: {e}", exc_info=True)

    return get_attempt_results(attempt_id, db, user)

@router.get("/{attempt_id}/results", response_model=AttemptResultResponse)
def get_attempt_results(
    attempt_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    attempt = db.query(Attempt).filter(Attempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    if attempt.user_id != user.id:
        if attempt.user_id == settings.default_user_id:
            attempt.user_id = user.id
            db.commit()
        elif user.id == settings.default_user_id:
            pass
        else:
            raise HTTPException(status_code=403, detail="Not authorized to view this attempt")

    test = db.query(Test).filter(Test.id == attempt.test_id).first()
    subject = test.subject if test else None

    # Load questions in order
    test_questions = db.query(TestQuestion).filter(TestQuestion.test_id == test.id).order_by(TestQuestion.order_index).all()
    q_ids = [tq.question_id for tq in test_questions]
    questions_map = {q.id: q for q in db.query(Question).filter(Question.id.in_(q_ids)).all()}

    # Load student answers
    answers_map = {a.question_id: a for a in db.query(StudentAnswer).filter(StudentAnswer.attempt_id == attempt.id).all()}

    # Load evaluations
    evals_map = {e.question_id: e for e in db.query(Evaluation).filter(Evaluation.attempt_id == attempt.id).all()}

    evaluation_details = []
    for q_id in q_ids:
        q = questions_map.get(q_id)
        if not q:
            continue
        ans = answers_map.get(q_id)
        ev = evals_map.get(q_id)

        crit_schemas = []
        if ev and ev.criterion_results:
            for c in ev.criterion_results:
                if isinstance(c, dict):
                    crit_schemas.append(
                        CriterionResultSchema(
                            criterion_id=str(c.get("criterion_id", "crit")),
                            awarded_marks=float(c.get("awarded_marks", 0.0) or 0.0),
                            max_marks=float(c.get("max_marks", 1.0) or 1.0),
                            justification=str(c.get("justification", "")),
                            excerpt=c.get("excerpt")
                        )
                    )

        normalized_q_score = None
        if ev and ev.awarded_marks is not None and (q.marks or 0) > 0:
            normalized_q_score = round(10.0 * (float(ev.awarded_marks) / float(q.marks)), 1)

        evaluation_details.append(
            EvaluationDetailResponse(
                question_id=q.id,
                question_type=q.question_type,
                subjective_subtype=q.subjective_subtype,
                question_text=q.question_text,
                marks=q.marks,
                awarded_marks=ev.awarded_marks if ev else 0.0,
                normalized_score_10=normalized_q_score,
                selected_option_id=ans.selected_option_id if ans else None,
                student_answer_text=ans.answer_text if ans else None,
                correct_option_id=q.correct_option_id,
                explanation=q.explanation,
                reference_answer=q.reference_answer,
                criterion_results=crit_schemas,
                correct_points=ev.correct_points if ev else [],
                missing_points=ev.missing_points if ev else [],
                misconceptions=ev.misconceptions if ev else [],
                actionable_feedback=ev.actionable_feedback if ev else None,
                source_references=q.source_references or [],
                review_needed=ev.review_needed if ev else False,
                review_reason=ev.review_reason if ev else None
            )
        )

    # Compute adaptive recommendation for next test
    recommendation = {
        "target_concept_ids": [],
        "primary_focus": subject.name if subject else "General Review",
        "rationale": "Continue regular concept testing.",
        "weak_concept_names": [],
        "strong_concept_names": []
    }
    if subject:
        try:
            recommendation = adaptive_service.recommend_adaptive_blueprint(db, subject.id, user.id)
        except Exception as e:
            logger.warning(f"Could not compute adaptive recommendation: {e}")

    raw_score = float(attempt.raw_score if attempt.raw_score is not None else attempt.total_score or 0.0)
    max_raw = float(attempt.max_raw_marks if attempt.max_raw_marks is not None else attempt.max_possible_score or 1.0)
    norm_score = float(attempt.normalized_score_10 if attempt.normalized_score_10 is not None else (round(10.0 * raw_score / max_raw, 1) if max_raw > 0 else 0.0))
    score_disp = f"{norm_score:.1f} / 10 · {raw_score:g} / {max_raw:g} raw marks"

    return AttemptResultResponse(
        attempt_id=attempt.id,
        test_id=test.id,
        subject_id=subject.id if subject else "",
        subject_name=subject.name if subject else "General Subject",
        test_title=test.title,
        source_mode=test.source_mode or "reference_grounded",
        started_at=attempt.started_at,
        submitted_at=attempt.submitted_at,
        time_spent_seconds=attempt.time_spent_seconds or 0,
        total_score=attempt.total_score or 0.0,
        raw_score=raw_score,
        max_raw_marks=max_raw,
        normalized_score_10=norm_score,
        score_display=score_disp,
        objective_score=attempt.objective_score or 0.0,
        subjective_score=attempt.subjective_score or 0.0,
        max_possible_score=attempt.max_possible_score or 0.0,
        evaluations=evaluation_details,
        next_recommended_action=f"Generate targeted follow-up test focusing on {recommendation['primary_focus']}",
        adaptive_recommendation=recommendation
    )
