from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models import (
    Attempt, StudentAnswer, Question, Evaluation, Test, TestQuestion, RubricCriterion
)
from backend.app.services.ai_service import ai_service

class ScoringService:
    @staticmethod
    def score_mcq_answer(question: Question, selected_option_id: Optional[str]) -> tuple[float, bool, str]:
        """
        Deterministic application-code MCQ scoring.
        Returns (awarded_marks, is_correct, explanation)
        """
        if not selected_option_id:
            return 0.0, False, "No option selected."

        is_correct = (selected_option_id == question.correct_option_id)
        awarded = float(question.marks) if is_correct else 0.0
        return awarded, is_correct, question.explanation or ""

    @staticmethod
    def validate_rubric_sum(question_marks: float, rubric_criteria: List[Dict[str, Any]]) -> bool:
        """
        Validates that the sum of rubric criteria max_marks equals question max marks (within epsilon).
        """
        if not rubric_criteria:
            return False
        total = sum(float(c.get("max_marks", 0.0)) for c in rubric_criteria)
        return abs(total - question_marks) < 0.05

    @classmethod
    def evaluate_attempt(cls, db: Session, attempt: Attempt) -> Attempt:
        """
        Grades an attempt idempotently:
        - Deterministically grades MCQs.
        - Evaluates subjective answers against saved rubrics.
        - Clamps marks within bounds.
        - Updates Attempt scores and status.
        """
        if attempt.status == "graded":
            return attempt # Idempotent - already graded

        test = db.query(Test).filter(Test.id == attempt.test_id).first()
        test_questions = db.query(TestQuestion).filter(TestQuestion.test_id == test.id).order_by(TestQuestion.order_index).all()
        question_ids = [tq.question_id for tq in test_questions]
        questions = {q.id: q for q in db.query(Question).filter(Question.id.in_(question_ids)).all()}

        # Load existing answers for this attempt
        answers = {a.question_id: a for a in db.query(StudentAnswer).filter(StudentAnswer.attempt_id == attempt.id).all()}

        total_score = 0.0
        objective_score = 0.0
        subjective_score = 0.0
        max_possible = sum(q.marks for q in questions.values())

        for q_id, question in questions.items():
            ans = answers.get(q_id)
            selected_option = ans.selected_option_id if ans else None
            student_text = ans.answer_text if ans else ""

            # Check if evaluation already exists
            existing_eval = db.query(Evaluation).filter(
                Evaluation.attempt_id == attempt.id,
                Evaluation.question_id == q_id
            ).first()

            if existing_eval:
                total_score += existing_eval.awarded_marks
                if question.question_type == "mcq":
                    objective_score += existing_eval.awarded_marks
                else:
                    subjective_score += existing_eval.awarded_marks
                continue

            if question.question_type == "mcq":
                awarded, is_correct, explanation = cls.score_mcq_answer(question, selected_option)
                eval_entry = Evaluation(
                    attempt_id=attempt.id,
                    question_id=question.id,
                    awarded_marks=awarded,
                    max_marks=float(question.marks),
                    criterion_results=[{
                        "criterion_id": "mcq_exact_match",
                        "awarded_marks": awarded,
                        "max_marks": float(question.marks),
                        "justification": f"Selected {selected_option}. Correct is {question.correct_option_id}." if selected_option else "Unanswered.",
                        "excerpt": selected_option
                    }],
                    correct_points=["Correct option identified"] if is_correct else [],
                    missing_points=[] if is_correct else [f"Correct option is {question.correct_option_id}"],
                    misconceptions=[] if is_correct or not selected_option else [f"Selected incorrect option {selected_option}"],
                    actionable_feedback=explanation,
                    source_references=question.source_references or [],
                    review_needed=False
                )
                db.add(eval_entry)
                total_score += awarded
                objective_score += awarded
            else:
                # Subjective question
                criteria = [
                    {
                        "criterion_id": c.criterion_id,
                        "description": c.description,
                        "max_marks": float(c.max_marks)
                    }
                    for c in question.rubric_criteria
                ]
                
                # If no DB criteria records, construct fallback from question
                if not criteria:
                    criteria = [{
                        "criterion_id": "crit_overall",
                        "description": "Demonstration of core concepts and technical accuracy",
                        "max_marks": float(question.marks)
                    }]

                eval_data = ai_service.grade_subjective_answer(
                    question_text=question.question_text,
                    max_marks=float(question.marks),
                    rubric_criteria=criteria,
                    reference_answer=question.reference_answer or "",
                    student_answer=student_text or "",
                    source_evidence=question.source_references or [],
                    db=db
                )

                # Recompute and clamp in application code
                recomputed_awarded = min(
                    float(question.marks),
                    max(0.0, sum(float(c.get("awarded_marks", 0.0)) for c in eval_data.get("criterion_results", [])))
                )

                eval_entry = Evaluation(
                    attempt_id=attempt.id,
                    question_id=question.id,
                    awarded_marks=recomputed_awarded,
                    max_marks=float(question.marks),
                    criterion_results=eval_data.get("criterion_results", []),
                    correct_points=eval_data.get("correct_points", []),
                    missing_points=eval_data.get("missing_points", []),
                    misconceptions=eval_data.get("misconceptions", []),
                    actionable_feedback=eval_data.get("actionable_feedback", ""),
                    source_references=eval_data.get("source_references", []),
                    review_needed=eval_data.get("review_needed", False),
                    review_reason=eval_data.get("review_reason")
                )
                db.add(eval_entry)
                total_score += recomputed_awarded
                subjective_score += recomputed_awarded

        attempt.status = "graded"
        attempt.total_score = round(total_score, 2)
        attempt.raw_score = round(total_score, 2)
        attempt.max_raw_marks = round(max_possible, 2)
        attempt.objective_score = round(objective_score, 2)
        attempt.subjective_score = round(subjective_score, 2)
        attempt.max_possible_score = round(max_possible, 2)

        # Normalized overall score out of 10:
        # normalized_score = 10 * total_awarded_raw_marks / total_possible_raw_marks
        if max_possible > 0:
            attempt.normalized_score_10 = round(10.0 * (total_score / max_possible), 1)
        else:
            attempt.normalized_score_10 = 0.0

        db.commit()
        db.refresh(attempt)
        return attempt

scoring_service = ScoringService()
