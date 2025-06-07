# mod-ollama-ragproxy

A lightweight proxy for Ollama that augments prompts with context from real-time web search via DuckDuckGo HTML scraping. Designed to plug into mod-playerbots or any external system needing a smarter LLM.

**Based on:** https://github.com/DustinHendrickson/mod-ollama-chat

## Features
- Simple Flask API
- DuckDuckGo HTML search + preferred domain filtering
- Works with any local Ollama model
- Optional caching and stats tracking

## Usage
curl -X POST http://localhost:11435/api/generate
-H "Content-Type: application/json"
-d '{"prompt": "Where is Orgrimmar?"}'
