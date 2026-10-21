import urllib.request
import json
import time

BASE = "http://127.0.0.1:8000"

def run_e2e():
    print("--- Starting ExamLoop Syllabus-First E2E Verification ---")

    # 1. Create a subject
    req = urllib.request.Request(
        f"{BASE}/api/subjects",
        data=json.dumps({"name": "Distributed Operating Systems"}).encode(),
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req)
    subj = json.loads(resp.read().decode())
    subj_id = subj["id"]
    print("1. Created Subject:", subj["name"], subj_id)

    # 2. Ingest Syllabus Document
    syllabus_payload = {
        "title": "Operating Systems Syllabus 2026",
        "document_role": "syllabus",
        "content": """UNIT 1: Process Synchronization & Concurrency
- Critical section problem and Peterson solution
- Semaphores, Mutexes, and Monitors
- Classical synchronization problems: Dining Philosophers, Producer-Consumer

UNIT 2: Deadlocks & Resource Allocation
- Deadlock characterization (4 Coffman conditions)
- Resource Allocation Graphs (RAG)
- Banker Algorithm for deadlock avoidance
"""
    }
    req = urllib.request.Request(
        f"{BASE}/api/subjects/{subj_id}/documents/paste-text",
        data=json.dumps(syllabus_payload).encode(),
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req)
    doc = json.loads(resp.read().decode())
    print("2. Ingested Syllabus Document:", doc["filename"], "Role:", doc["document_role"])

    # 3. Analyze Syllabus Hierarchy
    req = urllib.request.Request(
        f"{BASE}/api/subjects/{subj_id}/syllabus/analyze",
        data=b"{}",
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req)
    units = json.loads(resp.read().decode())
    print(f"3. Extracted {len(units)} Units & Topics:")
    topic_ids = []
    for u in units:
        unit_num = u.get("unit_number", 1)
        unit_title = u.get("title", "")
        t_count = len(u.get("topics", []))
        print(f"   - Unit {unit_num}: {unit_title} ({t_count} topics)")
        for t in u.get("topics", []):
            topic_ids.append(t["id"])
            prio = t.get("practice_priority", "normal").upper()
            inf = t.get("is_inferred", False)
            reason = (t.get("priority_reason") or "")[:45]
            print(f"     * [{prio}] {t['name']} (Inferred={inf}) -> {reason}...")

    # 4. Generate Custom Test (MCQ + Very Short + Short + Long)
    custom_req = {
        "title": "Midterm Practice Sprint",
        "mode": "mixed",
        "global_difficulty": "medium",
        "target_topic_ids": topic_ids[:3] if topic_ids else [],
        "mcq_count": 2,
        "mcq_difficulty": "medium",
        "very_short_count": 1,
        "very_short_difficulty": "easy",
        "short_count": 1,
        "short_difficulty": "medium",
        "long_count": 1,
        "long_difficulty": "hard",
        "is_timed": True,
        "duration_minutes": 40
    }
    req = urllib.request.Request(
        f"{BASE}/api/subjects/{subj_id}/tests/custom",
        data=json.dumps(custom_req).encode(),
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req)
    test = json.loads(resp.read().decode())
    print("4. Custom Test Created:", test["title"])
    print(f"   Questions: {test.get('question_count')}, Raw marks: {test.get('total_raw_marks')}, Max norm: {test.get('normalized_max_score')}, Mode: {test.get('source_mode')}")

    # 5. Get Test-Taking View (Confirm answer key & rubrics are securely hidden)
    req = urllib.request.Request(f"{BASE}/api/tests/{test['id']}/take")
    resp = urllib.request.urlopen(req)
    test_taking = json.loads(resp.read().decode())
    print("5. Test-Taking View loaded. Attempt ID:", test_taking["attempt_id"])
    for q in test_taking["questions"]:
        assert "correct_option_id" not in q, "Security breach: correct_option_id exposed!"
        assert "reference_answer" not in q, "Security breach: reference_answer exposed!"
        assert "rubric_criteria" not in q, "Security breach: rubric_criteria exposed!"
        q_type = q.get("question_type")
        subtype = q.get("subjective_subtype")
        marks = q.get("marks")
        text = q.get("question_text", "")[:45]
        print(f"   Item: [{q_type}/{subtype}] {text}... ({marks} marks)")

    # 6. Submit Attempt
    attempt_id = test_taking["attempt_id"]
    answers = []
    for q in test_taking["questions"]:
        if q["question_type"] == "mcq":
            opt = q["options"][0]["id"] if q.get("options") else "A"
            answers.append({"question_id": q["id"], "selected_option_id": opt})
        else:
            answers.append({
                "question_id": q["id"],
                "answer_text": "Deadlock requires 4 conditions: mutual exclusion, hold and wait, no preemption, and circular wait. Banker algorithm safely avoids it via safe state vector evaluation."
            })

    submit_payload = {"time_spent_seconds": 720, "answers": answers}
    req = urllib.request.Request(
        f"{BASE}/api/attempts/{attempt_id}/submit",
        data=json.dumps(submit_payload).encode(),
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req)
    results = json.loads(resp.read().decode())
    print("6. Attempt Evaluated & Graded:")
    print(f"   Score Display: {results.get('score_display')}")
    print(f"   Normalized /10: {results.get('normalized_score_10')}")
    print(f"   Raw Marks: {results.get('raw_score')} / {results.get('max_raw_marks')}")
    print(f"   Objective MCQ Score: {results.get('objective_score')}, Subjective Score: {results.get('subjective_score')}")
    print("--- SUCCESS: ALL 6 PIPELINE STAGES VERIFIED AGAINST LIVE SERVER ---")

if __name__ == "__main__":
    run_e2e()
