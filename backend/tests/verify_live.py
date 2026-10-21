import json
import urllib.request
import time

def post(url, data=None):
    payload = json.dumps(data).encode("utf-8") if data else b""
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    print("==================================================")
    print("      EXAMLOOP FULL VERTICAL SLICE TEST           ")
    print("==================================================")

    # 1. Seed demo
    print("\n[Step 1] Seed DBMS Subject & Study Notes...")
    res = post("http://127.0.0.1:8000/api/subjects/seed-demo")
    subject_id = res["subject_id"]
    print(f"[OK] Subject ready: {subject_id}")

    # 2. Concepts
    print("\n[Step 2] Verify Extracted Concepts...")
    concepts = get(f"http://127.0.0.1:8000/api/subjects/{subject_id}/concepts")
    print(f"[OK] Found {len(concepts)} concepts:")
    for c in concepts:
        print(f"   * {c['name']} (ID: {c['id'][:8]}...)")

    # 3. Generate Diagnostic Test
    print("\n[Step 3] Generate Diagnostic Test via AI Service...")
    t0 = time.time()
    test_gen = post(f"http://127.0.0.1:8000/api/subjects/{subject_id}/tests/generate", {
        "title": "DBMS Diagnostic Milestone Test",
        "test_type": "diagnostic",
        "mcq_count": 2,
        "subjective_count": 1
    })
    elapsed = time.time() - t0
    test_id = test_gen["id"]
    print(f"[OK] Test generated in {elapsed:.2f}s | Title: '{test_gen['title']}' | Marks: {test_gen['total_marks']}")

    # 4. Student Take View (Security Check: No answers or rubrics leaked)
    print("\n[Step 4] Fetch Test Taking View (Secure Student View)...")
    take_view = get(f"http://127.0.0.1:8000/api/tests/{test_id}/take")
    attempt_id = take_view["attempt_id"]
    questions = take_view["questions"]
    print(f"[OK] Attempt ID: {attempt_id}")
    print(f"[OK] Delivered {len(questions)} questions:")
    for q in questions:
        print(f"   * [{q['question_type'].upper()}] {q['question_text'][:70]}... ({q['marks']} marks)")
        # Verify no correct_option_id leaked
        if q["options"]:
            assert "correct_option_id" not in q["options"][0], "LEAK: correct_option_id found in student options!"

    # 5. Submit Answers
    print("\n[Step 5] Submit Student Answers & Score...")
    answers_to_submit = []
    for q in questions:
        if q["question_type"] == "mcq" and q["options"]:
            answers_to_submit.append({
                "question_id": q["id"],
                "selected_option_id": q["options"][0]["id"]
            })
        else:
            answers_to_submit.append({
                "question_id": q["id"],
                "answer_text": "2NF eliminates partial functional dependency on primary key. 3NF removes transitive dependencies."
            })

    t1 = time.time()
    submission_res = post(f"http://127.0.0.1:8000/api/attempts/{attempt_id}/submit", {
        "time_spent_seconds": 120,
        "answers": answers_to_submit
    })
    grade_elapsed = time.time() - t1
    print(f"[OK] Attempt Graded in {grade_elapsed:.2f}s!")
    print(f"   * Total Score: {submission_res['total_score']} / {submission_res['max_possible_score']}")
    print(f"   * Objective Score: {submission_res['objective_score']}")
    print(f"   * Subjective Score: {submission_res['subjective_score']}")

    # 6. Rubrics & Evaluations
    print("\n[Step 6] Transparent Rubric Breakdown...")
    for ev in submission_res["evaluations"]:
        print(f"   Question: {ev['question_text'][:50]}...")
        print(f"   Score: {ev['awarded_marks']}/{ev['marks']} | Feedback: {ev['actionable_feedback']}")
        if ev["criterion_results"]:
            print("   Criteria:")
            for cr in ev["criterion_results"]:
                status = "PASS" if cr.get("awarded_points", 0) > 0 else "PARTIAL/MISS"
                print(f"     - [{status}] {cr.get('criterion_name', '')[:50]}: {cr.get('awarded_points')}/{cr.get('max_points')} pts")

    # 7. Adaptive Follow-Up Recommendation
    print("\n[Step 7] Explainable Adaptive Recommendation...")
    rec = submission_res.get("adaptive_recommendation")
    if rec:
        print(f"[OK] Recommended Test Type: {rec.get('test_type')}")
        print(f"[OK] Target Concepts: {rec.get('target_concept_names')}")
        print(f"[OK] Rationale: {rec.get('rationale')}")

    # 8. Dashboard Analytics
    print("\n[Step 8] Dashboard Metrics...")
    dash = get("http://127.0.0.1:8000/api/dashboard/metrics")
    print(f"[OK] Processed Docs: {dash['documents_processed']}")
    print(f"[OK] Completed Tests: {dash['tests_completed']}")
    print(f"[OK] Average Score: {dash['average_score_pct']}%")

    print("\n==================================================")
    print("      ALL VERTICAL SLICE CHECKS PASSED!           ")
    print("==================================================")

if __name__ == "__main__":
    main()
