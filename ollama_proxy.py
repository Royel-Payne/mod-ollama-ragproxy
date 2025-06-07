import json
import logging
import re
from flask import Flask, request, jsonify
import httpx
from bs4 import BeautifulSoup
from collections import Counter

app = Flask(__name__)

# Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
SEARCH_ENGINE_URL = "https://www.startpage.com/sp/search"
PREFERRED_DOMAINS = ["wowhead.com", "warcraft.wiki.gg", "warcraftpets.com"]
OLLAMA_MODEL = "llama3"

# Stats
stats = {
    "total_requests": 0,
    "cache_hits": 0,
    "lookup_attempts": 0,
    "preferred_domain_matches": 0
}

# Cache
cache = {}

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
)

def extract_results(html):
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for result in soup.select(".w-gl__result")[:6]:
        anchor = result.select_one("a")
        if anchor and anchor["href"]:
            title = anchor.get_text(strip=True)
            snippet_tag = result.select_one(".w-gl__description")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
            results.append((anchor["href"], title, snippet))
    return results

def summarize_results(results):
    output = []
    for link, title, snippet in results:
        output.append(f"{link}: {title} - {snippet}")
    return "\n\n".join(output)

@app.route("/api/generate", methods=["POST"])
def generate():
    stats["total_requests"] += 1
    prompt = request.json.get("prompt", "").strip()

    if prompt in cache:
        stats["cache_hits"] += 1
        logging.info(f"[CACHE] Hit: {prompt!r}")
        return jsonify(cache[prompt])

    logging.info(f"[PROMPT] {prompt}")

    # Search the web
    stats["lookup_attempts"] += 1
    try:
        res = httpx.post(SEARCH_ENGINE_URL, data={"query": prompt}, timeout=10)
        res.raise_for_status()
    except Exception as e:
        logging.warning(f"[LOOKUP] Failed search: {e}")
        res = None

    context = ""
    if res and res.text:
        results = extract_results(res.text)
        context = summarize_results(results)

        # Check for preferred domains
        matches = [r for r in results if any(domain in r[0] for domain in PREFERRED_DOMAINS)]
        if matches:
            stats["preferred_domain_matches"] += 1
            context = summarize_results(matches)

    # Call Ollama (streamed response)
    full_prompt = f"Context:\n{context}\n\nQuestion: {prompt}"
    try:
        ollama_response = httpx.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": full_prompt, "stream": True},
            timeout=60
        )
        response_text = ""
        for line in ollama_response.iter_lines():
            try:
                chunk = json.loads(line)
                if chunk.get("done"):
                    break
                response_text += chunk.get("response", "")
            except json.JSONDecodeError:
                continue
    except Exception as e:
        logging.error(f"[OLLAMA ERROR] {e}")
        response_text = "I'm having trouble understanding."

    logging.info(f"[RESULT] {response_text.strip()[:80]}...")
    result = {"context": context.strip(), "response": response_text.strip()}
    cache[prompt] = result
    return jsonify(result)

@app.route("/flush", methods=["POST"])
def flush():
    cache.clear()
    logging.info("[CACHE] Flushed manually.")
    return jsonify({"message": "Cache cleared successfully."})

@app.route("/stats", methods=["GET"])
def get_stats():
    return jsonify(stats)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=11435)
