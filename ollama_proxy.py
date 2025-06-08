import json
import httpx
import logging
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
from urllib.parse import urlparse

OLLAMA_URL = "http://localhost:11434/api/generate"
PORT = 11435
PREFERRED_DOMAINS = ["wowhead.com", "warcraft.wiki.gg", "wowpedia.fandom.com"]

app = Flask(__name__)

cache = {}
stats = {
    "total_requests": 0,
    "lookup_attempts": 0,
    "preferred_domain_matches": 0,
    "cache_hits": 0
}

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s'
)

def extract_results(html_doc):
    soup = BeautifulSoup(html_doc, "html.parser")
    results = []
    for result in soup.select(".w-gl__result")[:6]:
        try:
            anchor = result.select_one(".w-gl__result-title")
            snippet_tag = result.select_one(".w-gl__description")
            title = anchor.get_text(strip=True) if anchor else ""
            url = anchor.get("href") if anchor else ""
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
            if title and url:
                results.append((url, f"{title} - {snippet}"))
        except Exception as e:
            logging.warning(f"[PARSE] Error parsing result: {e}")
    return results

def summarize_results(results):
    output = []
    for link, title_snippet in results:
        output.append(f"{title_snippet} (Source: {link})")
    return "\n".join(output)

def domain_matches(url, preferred_domains):
    try:
        netloc = urlparse(url).netloc.lower()
        for pd in preferred_domains:
            pd = pd.lower()
            if netloc == pd or netloc.endswith("." + pd):
                return True
        return False
    except Exception:
        return False

@app.route("/api/generate", methods=["POST"])
def generate():
    stats["total_requests"] += 1
    json_data = request.get_json()
    prompt = json_data.get("prompt", "").strip()
    model = json_data.get("model", "").strip()

    if not prompt:
        return jsonify({"error": "Prompt missing"}), 400

    if prompt in cache:
        stats["cache_hits"] += 1
        logging.info(f"[CACHE HIT] {prompt}")
        return jsonify({"context": cache[prompt][0], "response": cache[prompt][1]})

    stats["lookup_attempts"] += 1
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    try:
        res = httpx.post(
            url="https://www.startpage.com/sp/search",
            data={"query": prompt},
            headers=headers,
            timeout=10
        )
        res.raise_for_status()
        with open("last_search.html", "w", encoding="utf-8") as f:
            f.write(res.text)
        raw_results = extract_results(res.text)
    except Exception as e:
        logging.warning(f"[LOOKUP] Failed search: {e}")
        raw_results = []

    context = ""
    preferred_results = [r for r in raw_results if domain_matches(r[0], PREFERRED_DOMAINS)]
    if preferred_results:
        context = summarize_results(preferred_results)
        stats["preferred_domain_matches"] += 1
    elif raw_results:
        context = summarize_results(raw_results)

    full_prompt = f"You are a helpful World of Warcraft assistant.\nUse the following context to answer the question.\n\nContext:\n{context}\n\nQuestion: {prompt}\nAnswer:"

    payload = {"prompt": full_prompt}
    if model:
        payload["model"] = model
    logging.info(f"[LLM] Using model: {model or 'default'}")
    logging.info(f"[LLM] Sending prompt: {full_prompt}")

    try:
        res = httpx.post(OLLAMA_URL, json=payload, timeout=60)
        response = ""
        try:
            for line in res.text.strip().splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    if "response" in chunk:
                        response += chunk["response"]
                except json.JSONDecodeError:
                    continue
            response = response.strip()
            if not response:
                raise ValueError("Empty response field")
        except Exception as e:
            logging.warning(f"[LLM JSON ERROR] {e}, raw: {res.text.strip()}")
            response = f"[LLM Failure] {e}"
    except Exception as e:
        response = f"[LLM Failure] {e}"

    cache[prompt] = (context, response)
    return jsonify({"context": context, "response": response})

@app.route("/stats", methods=["GET"])
def get_stats():
    return jsonify(stats)

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, threaded=True)
