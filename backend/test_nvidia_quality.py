import os
import httpx
import json

API_KEY = os.getenv("OPENROUTER_API_KEY", "your_openrouter_api_key_here")
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "HTTP-Referer": "https://examloop.local",
    "X-Title": "ExamLoop"
}

prompt = (
    "You are an examination question generator. Given the excerpt:\n"
    "'Repeatable Read prevents Dirty Reads and Non-Repeatable Reads, but permits Phantom Reads where newly inserted rows satisfy the query predicate. "
    "Serializable isolation eliminates Phantom Reads by employing index-range locking or MVCC serialization.'\n\n"
    "Generate 1 subjective question with max_marks=5 and rubric_criteria (summing to 5.0).\n"
    "Return JSON format:\n"
    "{\n"
    '  "question_text": "...",\n'
    '  "max_marks": 5,\n'
    '  "expected_key_points": ["..."],\n'
    '  "reference_answer": "...",\n'
    '  "rubric_criteria": [{"criterion_id": "c1", "description": "...", "max_marks": 2.5}, {"criterion_id": "c2", "description": "...", "max_marks": 2.5}]\n'
    "}\n"
    "Return ONLY valid JSON."
)

models = ["nvidia/nemotron-3.5-lightning:free", "nvidia/nemotron-3.5-lightning"]
for m in models:
    print(f"\n--- Testing {m} ---")
    resp = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json={"model": m, "messages": [{"role": "user", "content": prompt}], "max_tokens": 600},
        timeout=30.0
    )
    if resp.status_code == 200:
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        print("Success! Response:")
        print(content)
        # Parse test
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = "\n".join(cleaned.splitlines()[1:-1])
        try:
            parsed = json.loads(cleaned)
            print("Parsed successfully. Rubric sum:", sum(c["max_marks"] for c in parsed.get("rubric_criteria", [])))
        except Exception as e:
            print("JSON parse error:", e)
    else:
        print("Error:", resp.status_code, resp.text)
