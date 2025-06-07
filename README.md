# Ollama RAG Proxy for mod-ollama-chat

This project provides a lightweight Flask-based proxy that adds basic retrieval-augmented generation (RAG) to [mod-ollama-chat](https://github.com/DustinHendrickson/mod-ollama-chat) using DuckDuckGo Lite scraping. It injects relevant search snippets as context for the prompt before sending to Ollama.

## Features
- 🔍 Scrapes DuckDuckGo Lite HTML for lightweight search results
- 🧠 Injects context before querying your local Ollama model
- ⚡ Caches results in memory to reduce duplicate lookups
- 📈 Includes a `/stats` endpoint to track usage
- ✅ Designed for use with `mod-ollama-chat`

## Requirements
```bash
pip install flask httpx beautifulsoup4
```

## Usage
```bash
python3 ollama_proxy.py
```
The server will run on:
```
http://localhost:11435
```

## Integration with mod-ollama-chat
Edit your `mod_ollama_chat.conf` to point to this proxy:
```
OllamaChat.Url = http://127.0.0.1:11435/api/generate
```
Or if used from another container or VM:
```
OllamaChat.Url = http://YOUR.IP.ADDR.HERE:11435/api/generate
```

## Stats Endpoint
Check usage and caching stats:
```bash
curl -s http://127.0.0.1:11435/stats | jq
```
Example output:
```json
{
  "total_requests": 3,
  "lookup_attempts": 3,
  "preferred_domain_matches": 2,
  "cache_hits": 1
}
```

## Port Notice
This proxy runs on port `11435` to avoid conflict with Ollama’s default `11434`.

## Development Notes
- Searches are limited to preferred domains like `wowhead.com`, `warcraft.wiki.gg`, etc.
- The last DuckDuckGo search is saved to `last_search.html` for debugging.
- A `.gitignore` is recommended:
```gitignore
__pycache__/
*.pyc
.env
*.log
last_search.html
```

## Attribution
Inspired by and intended to work with:
- https://github.com/DustinHendrickson/mod-ollama-chat
