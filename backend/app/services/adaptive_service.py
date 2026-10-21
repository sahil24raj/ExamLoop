from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models import (
    ConceptProgress, Concept, Attempt, Evaluation, Question, Test, TestQuestion
)
from backend.app.services.ai_service import ai_service

class AdaptiveService:
    @staticmethod
    def update_concept_progress(db: Session, attempt: Attempt) -> None:
        """
        Calculates and updates per-concept heuristic metrics following a graded attempt.
        """
        evaluations = db.query(Evaluation).filter(Evaluation.attempt_id == attempt.id).all()
        eval_map = {e.question_id: e for e in evaluations}
        
        question_ids = list(eval_map.keys())
        questions = db.query(Question).filter(Question.id.in_(question_ids)).all()
        test = db.query(Test).filter(Test.id == attempt.test_id).first()
        if not test:
            return

        subject_id = test.subject_id
        user_id = attempt.user_id

        for q in questions:
            e = eval_map.get(q.id)
            if not e:
                continue

            for concept_id in (q.concept_ids or []):
                progress = db.query(ConceptProgress).filter(
                    ConceptProgress.user_id == user_id,
                    ConceptProgress.subject_id == subject_id,
                    ConceptProgress.concept_id == concept_id
                ).first()

                if not progress:
                    progress = ConceptProgress(
                        user_id=user_id,
                        subject_id=subject_id,
                        concept_id=concept_id,
                        total_mcq_attempted=0,
                        total_mcq_correct=0,
                        subjective_marks_awarded=0.0,
                        subjective_marks_possible=0.0,
                        total_observed_attempts=0,
                        readiness_indicator="not_enough_evidence"
                    )
                    db.add(progress)

                progress.total_observed_attempts += 1
                progress.last_practiced_at = datetime.now(timezone.utc)

                if q.question_type == "mcq":
                    progress.total_mcq_attempted += 1
                    if e.awarded_marks >= q.marks:
                        progress.total_mcq_correct += 1
                else:
                    progress.subjective_marks_awarded += e.awarded_marks
                    progress.subjective_marks_possible += float(q.marks)

                # Explainable readiness heuristic calculation
                obs = progress.total_observed_attempts
                if obs < 2:
                    progress.readiness_indicator = "not_enough_evidence"
                else:
                    # Compute weighted ratio
                    mcq_ratio = (progress.total_mcq_correct / progress.total_mcq_attempted) if progress.total_mcq_attempted > 0 else 0.5
                    subj_ratio = (progress.subjective_marks_awarded / progress.subjective_marks_possible) if progress.subjective_marks_possible > 0 else mcq_ratio
                    overall_ratio = (mcq_ratio * 0.4) + (subj_ratio * 0.6)

                    if overall_ratio < 0.55:
                        progress.readiness_indicator = "needs_practice"
                    elif overall_ratio < 0.80:
                        progress.readiness_indicator = "developing"
                    else:
                        progress.readiness_indicator = "proficient"

        db.commit()

    @classmethod
    def recommend_adaptive_blueprint(cls, db: Session, subject_id: str, user_id: str) -> Dict[str, Any]:
        """
        Determines targeted concepts and generates an explainable rationale.
        """
        all_concepts = db.query(Concept).filter(
            Concept.subject_id == subject_id,
            Concept.is_excluded == False
        ).all()

        if not all_concepts:
            return {
                "target_concept_ids": [],
                "primary_focus": "General Overview",
                "rationale": "No active concepts available for targeted practice.",
                "weak_concept_names": [],
                "strong_concept_names": []
            }

        progress_records = db.query(ConceptProgress).filter(
            ConceptProgress.subject_id == subject_id,
            ConceptProgress.user_id == user_id
        ).all()
        prog_map = {p.concept_id: p for p in progress_records}

        weak_concepts = []
        developing_concepts = []
        untested_concepts = []
        strong_concepts = []

        for c in all_concepts:
            p = prog_map.get(c.id)
            if not p or p.readiness_indicator == "not_enough_evidence":
                untested_concepts.append(c)
            elif p.readiness_indicator == "needs_practice":
                weak_concepts.append(c)
            elif p.readiness_indicator == "developing":
                developing_concepts.append(c)
            else:
                strong_concepts.append(c)

        # Prioritize: Weak concepts first, then developing, then untested, plus 1 revision strong concept
        target_concepts = []
        if weak_concepts:
            target_concepts.extend(weak_concepts[:2])
            primary_focus = weak_concepts[0].name
        elif developing_concepts:
            target_concepts.extend(developing_concepts[:2])
            primary_focus = developing_concepts[0].name
        elif untested_concepts:
            target_concepts.extend(untested_concepts[:2])
            primary_focus = untested_concepts[0].name
        else:
            target_concepts.extend(all_concepts[:2])
            primary_focus = all_concepts[0].name

        # Add 1 revision concept if available
        if strong_concepts and strong_concepts[0] not in target_concepts:
            target_concepts.append(strong_concepts[0])

        weak_names = [c.name for c in weak_concepts]
        strong_names = [c.name for c in strong_concepts]

        # Fetch recent misconceptions for explainability
        recent_eval = db.query(Evaluation).join(Attempt).filter(
            Attempt.user_id == user_id
        ).order_by(Evaluation.created_at.desc()).first()
        recent_misconceptions = recent_eval.misconceptions if recent_eval else []

        rationale = ai_service.explain_next_test(
            weak_concept_names=weak_names,
            strong_concept_names=strong_names,
            observed_attempts=len(progress_records),
            primary_focus=primary_focus,
            recent_misconceptions=recent_misconceptions
        )

        return {
            "target_concept_ids": [c.id for c in target_concepts],
            "primary_focus": primary_focus,
            "rationale": rationale,
            "weak_concept_names": weak_names,
            "strong_concept_names": strong_names
        }

adaptive_service = AdaptiveService()
