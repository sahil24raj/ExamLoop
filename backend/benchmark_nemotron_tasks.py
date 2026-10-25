import os
import time
import json
import httpx

API_KEY = os.getenv("OPENROUTER_API_KEY", "")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

MODELS = [
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "nvidia/nemotron-3.5-lightning:free",
]

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "HTTP-Referer": "https://examloop.local",
    "X-Title": "ExamLoop Nemotron Evaluation",
    "Content-Type": "application/json"
}

SAMPLE_DOC_TEXT = """
Database Management Systems - Unit 4: Concurrency Control and Transactions
A transaction is a logical unit of database processing that includes one or more access operations (read, write, update).
To preserve the integrity of the data, the database system must ensure ACID properties:
1. Atomicity: Either all operations of the transaction are completed successfully, or none are. Handled by recovery management (undo/redo logs).
2. Consistency: Execution of a transaction in isolation preserves database consistency constraints.
3. Isolation: The execution of a transaction is unaware of concurrently executing transactions. Serializability is the gold standard of isolation. SQL defines four isolation levels: Read Uncommitted, Read Committed, Repeatable Read, and Serializable.
4. Durability: Once a transaction commits, the changes persist even in the event of system crashes.
Repeatable Read prevents Dirty Reads and Non-Repeatable Reads, but allows Phantom Reads where newly inserted rows satisfy a search predicate.
"""

def test_concept_extraction(model):
    prompt = f"""You are an examination expert. Analyze the following study material and extract 3 core examination concepts.
Return ONLY valid JSON matching this schema:
{{
  "concepts": [
    {{"name": "...", "description": "...", "keywords": ["..."]}}
  ]
}}

Study material:
{SAMPLE_DOC_TEXT}
"""
    t0 = time.time()
    try:
        resp = httpx.post(
            f"{BASE_URL}/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1200,
                "temperature": 0.2
            },
            timeout=40.0
        )
        elapsed = time.time() - t0
        if resp.status_code != 200:
            return {"status": "FAIL", "latency": elapsed, "error": resp.text[:150]}
        data = resp.json()
        choice = data["choices"][0]["message"]
        content = choice.get("content") or choice.get("reasoning", "")
        # Clean markdown
        c = content.strip()
        if "```" in c:
            lines = c.splitlines()
            cleaned = []
            inside = False
            for line in lines:
                if line.startswith("```"):
                    inside = not inside
                    continue
                if inside:
                    cleaned.append(line)
            if cleaned:
                c = "\n".join(cleaned).strip()
            else:
                c = "\n".join([l for l in lines if not l.startswith("```")]).strip()
        
        # Outermost braces
        s = c.find("{")
        e = c.rfind("}")
        if s != -1 and e > s:
            c = c[s:e+1]
        
        parsed = json.loads(c)
        concepts = parsed.get("concepts", [])
        return {"status": "PASS", "latency": round(elapsed, 2), "count": len(concepts), "sample": [x.get("name") for x in concepts]}
    except Exception as err:
        return {"status": "ERROR", "latency": round(time.time() - t0, 2), "error": str(err)}

def test_question_generation(model):
    prompt = f"""You are an examination question creator.
Based on the text:
{SAMPLE_DOC_TEXT}

Generate 1 Multiple Choice Question (MCQ) and 1 Subjective Question with marking rubric (max marks 5).
Return ONLY valid JSON matching this format:
{{
  "mcq": {{
    "question_text": "...",
    "options": [
      {{"id": "A", "text": "..."}},
      {{"id": "B", "text": "..."}},
      {{"id": "C", "text": "..."}},
      {{"id": "D", "text": "..."}}
    ],
    "correct_option_id": "A",
    "explanation": "..."
  }},
  "subjective": {{
    "question_text": "...",
    "max_marks": 5,
    "expected_key_points": ["..."],
    "rubric_criteria": [
      {{"criterion_id": "c1", "description": "...", "max_marks": 2.5}},
      {{"criterion_id": "c2", "description": "...", "max_marks": 2.5}}
    ]
  }}
}}
"""
    t0 = time.time()
    try:
        resp = httpx.post(
            f"{BASE_URL}/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1500,
                "temperature": 0.2
            },
            timeout=45.0
        )
        elapsed = time.time() - t0
        if resp.status_code != 200:
            return {"status": "FAIL", "latency": elapsed, "error": resp.text[:150]}
        data = resp.json()
        choice = data["choices"][0]["message"]
        content = choice.get("content") or choice.get("reasoning", "")
        c = content.strip()
        s = c.find("{")
        e = c.rfind("}")
        if s != -1 and e > s:
            c = c[s:e+1]
        parsed = json.loads(c)
        valid_mcq = "options" in parsed.get("mcq", {}) and len(parsed["mcq"]["options"]) == 4
        valid_subj = "rubric_criteria" in parsed.get("subjective", {})
        return {
            "status": "PASS" if (valid_mcq and valid_subj) else "INVALID_STRUCTURE",
            "latency": round(elapsed, 2),
            "mcq_q": parsed.get("mcq", {}).get("question_text", "")[:60],
            "subj_q": parsed.get("subjective", {}).get("question_text", "")[:60]
        }
    except Exception as err:
        return {"status": "ERROR", "latency": round(time.time() - t0, 2), "error": str(err)}

def test_answer_grading(model):
    prompt = """You are a strict academic evaluator.
Question: 'Explain Phantom Reads and why Repeatable Read isolation allows them.'
Max Marks: 5
Rubric:
- Criterion 1 (2.5 marks): Definition of phantom read as newly inserted rows appearing in subsequent queries.
- Criterion 2 (2.5 marks): Mechanism in Repeatable Read (locks existing rows but lacks range locks on non-existent records).

Student Answer:
'Phantom read happens when another transaction inserts new rows that match a range query while the first transaction is still running. Repeatable read locks existing rows so they cannot be modified or deleted, but it does not lock the gaps between records, allowing insertions.'

Evaluate the student answer and output JSON only:
{
  "total_score": 5.0,
  "max_score": 5.0,
  "percentage": 100.0,
  "overall_feedback": "...",
  "rubric_scores": [
    {"criterion_id": "c1", "score": 2.5, "feedback": "..."},
    {"criterion_id": "c2", "score": 2.5, "feedback": "..."}
  ]
}
"""
    t0 = time.time()
    try:
        resp = httpx.post(
            f"{BASE_URL}/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.1
            },
            timeout=40.0
        )
        elapsed = time.time() - t0
        if resp.status_code != 200:
            return {"status": "FAIL", "latency": elapsed, "error": resp.text[:150]}
        data = resp.json()
        choice = data["choices"][0]["message"]
        content = choice.get("content") or choice.get("reasoning", "")
        c = content.strip()
        s = c.find("{")
        e = c.rfind("}")
        if s != -1 and e > s:
            c = c[s:e+1]
        parsed = json.loads(c)
        score = parsed.get("total_score")
        return {
            "status": "PASS" if score is not None else "NO_SCORE",
            "latency": round(elapsed, 2),
            "score": score,
            "feedback": parsed.get("overall_feedback", "")[:80]
        }
    except Exception as err:
        return {"status": "ERROR", "latency": round(time.time() - t0, 2), "error": str(err)}

if __name__ == "__main__":
    results = {}
    for m in MODELS:
        print(f"\n=======================================================")
        print(f"Testing {m}...")
        print("1. Concept Extraction...")
        r_conc = test_concept_extraction(m)
        print("   ->", r_conc)
        time.sleep(1.5)

        print("2. Test Generation (MCQ + Subjective)...")
        r_qgen = test_question_generation(m)
        print("   ->", r_qgen)
        time.sleep(1.5)

        print("3. Answer Grading / Rubric Evaluation...")
        r_eval = test_answer_grading(m)
        print("   ->", r_eval)
        time.sleep(1.5)

        results[m] = {
            "extraction": r_conc,
            "generation": r_qgen,
            "grading": r_eval
        }

    with open("nemotron_benchmark_report.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nBenchmark Finished! Saved to nemotron_benchmark_report.json")
