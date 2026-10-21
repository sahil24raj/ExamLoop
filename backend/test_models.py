import os
import time
import json
import httpx

API_KEY = os.getenv("OPENROUTER_API_KEY", "your_openrouter_api_key_here")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# Candidate models to evaluate
CANDIDATES = [
    # NVIDIA Nemotron models
    "nvidia/llama-3.1-nemotron-70b-instruct:free",
    "nvidia/llama-3.1-nemotron-70b-instruct",
    "nvidia/nemotron-4-340b-instruct",
    # DeepSeek models
    "deepseek/deepseek-chat:free",
    "deepseek/deepseek-chat",
    "deepseek/deepseek-r1:free",
    "deepseek/deepseek-r1-distill-llama-70b",
    # Qwen models
    "qwen/qwen-2.5-72b-instruct:free",
    "qwen/qwen-2.5-72b-instruct",
    # Meta Llama fallback
    "meta-llama/llama-3.3-70b-instruct:free",
    "meta-llama/llama-3.3-70b-instruct"
]

TEST_PROMPT = """You are an examination question generator. Given the following excerpt:
'A transaction is a logical unit of database processing. Repeatable Read prevents Dirty Reads and Non-Repeatable Reads, but permits Phantom Reads where newly inserted rows satisfy the query predicate.'

Generate exactly 1 MCQ in valid JSON format:
{
  "question_text": "...",
  "options": [{"id": "A", "text": "..."}, {"id": "B", "text": "..."}],
  "correct_option_id": "A",
  "explanation": "..."
}
Return only JSON.
"""

def test_model(model_name):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": "https://examloop.local",
        "X-Title": "ExamLoop Benchmark",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": TEST_PROMPT}
        ],
        "temperature": 0.1,
        "max_tokens": 500
    }
    start = time.time()
    try:
        with httpx.Client(timeout=25.0) as client:
            resp = client.post(f"{BASE_URL}/chat/completions", headers=headers, json=payload)
            elapsed = time.time() - start
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                # Try parsing JSON
                cleaned = content.strip()
                if cleaned.startswith("```"):
                    lines = cleaned.splitlines()
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    cleaned = "\n".join(lines).strip()
                try:
                    parsed = json.loads(cleaned)
                    valid_json = "question_text" in parsed and "correct_option_id" in parsed
                except:
                    valid_json = False
                return {
                    "model": model_name,
                    "status": "SUCCESS",
                    "latency_sec": round(elapsed, 2),
                    "valid_json": valid_json,
                    "response_preview": cleaned[:120]
                }
            else:
                return {
                    "model": model_name,
                    "status": f"HTTP {resp.status_code}",
                    "latency_sec": round(elapsed, 2),
                    "error": resp.text[:200]
                }
    except Exception as e:
        return {
            "model": model_name,
            "status": "ERROR",
            "latency_sec": round(time.time() - start, 2),
            "error": str(e)
        }

if __name__ == "__main__":
    print("Starting OpenRouter Model Benchmark for ExamLoop...")
    results = []
    for model in CANDIDATES:
        print(f"Testing {model}...", flush=True)
        res = test_model(model)
        results.append(res)
        print(f" -> {res['status']} ({res.get('latency_sec')}s) - Valid JSON: {res.get('valid_json', False)}")
        time.sleep(0.5)

    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nBenchmark complete! Results saved to benchmark_results.json")
