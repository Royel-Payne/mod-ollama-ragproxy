# Ollama RAG Proxy for mod-ollama-chat

This project provides a lightweight Flask-based proxy that adds retrieval-augmented generation (RAG) to [mod-ollama-chat](https://github.com/DustinHendrickson/mod-ollama-chat). It scrapes search results from Startpage, filters by domain preference, injects relevant snippets as context, and streams LLM responses from your local Ollama model.

## Features

-  Uses **Startpage** search (HTML form POST scraping)
-  Attempts to filter results to preferred domains (e.g., wowhead.com)
-  Injects contextual info before querying your Ollama model
-  Caches prompt-response pairs in memory
-  Designed for use with `mod-ollama-chat`

## Installation

### Pre-requisites

Make sure you have Python 3.8+ and `pip` installed. You can check with:

```bash
python3 --version
pip3 --version
```

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### Clone the repository

```bash
git clone https://github.com/Royel-Payne/mod-ollama-ragproxy
cd mod-ollama-ragproxy
```

### Install the dependencies

```bash
pip install -r requirements.txt
```

### Start the Flask server

```bash
python3 ollama_proxy.py
```

The proxy will run on port `11435`.

## Integration with mod-ollama-chat

Edit your `mod_ollama_chat.conf` to point to the proxy:

```
OllamaChat.Url = http://127.0.0.1:11435/api/generate
```

For remote servers or containers:

```
OllamaChat.Url = http://YOUR.IP.ADDR.HERE:11435/api/generate
```

## Stats Endpoint

Track usage metrics:

```bash
curl http://127.0.0.1:11435/stats | jq
```

Example:

```json
{
  "total_requests": 9,
  "lookup_attempts": 6,
  "preferred_domain_matches": 3,
  "cache_hits": 2
}
```

## Port Notice

This proxy runs on port `11435` (to avoid Ollama’s default port `11434`).

## Attribution

Inspired by and intended to work with:

https://github.com/DustinHendrickson/mod-ollama-chat
