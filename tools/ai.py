#!/usr/bin/env python3
"""ai.py — shared Cloudflare Workers AI backend (free tier). Stdlib only.

Embeddings: @cf/baai/bge-base-en-v1.5
Chat: @cf/meta/llama-3.3-70b-instruct-fp8-fast
Creds: $CF_API_TOKEN / $CF_ACCOUNT_ID, else /root/.r2-env
"""
import json
import os
import urllib.request

ACCOUNT = os.environ.get("CF_ACCOUNT_ID", "954612afb5a97bb15dddcdc70176813d")
TOKEN = os.environ.get("CF_API_TOKEN", "")

if not TOKEN:
    try:
        with open("/root/.r2-env") as f:
            for line in f:
                line = line.strip()
                if line.startswith("CF_API_TOKEN="):
                    TOKEN = line.split("=", 1)[1]
    except OSError:
        pass

BASE = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/ai/run"


def _post(model: str, payload: dict, timeout: int = 120) -> dict:
    req = urllib.request.Request(
        f"{BASE}/{model}",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def embed_batch(texts: list) -> list:
    """texts: list[str] (batch up to ~64) -> list[vector]."""
    out = _post("@cf/baai/bge-base-en-v1.5", {"text": texts})
    return out["result"]["data"]


def chat(messages: list, max_tokens: int = 500) -> str:
    out = _post("@cf/meta/llama-3.3-70b-instruct-fp8-fast",
                {"messages": messages, "max_tokens": max_tokens})
    return out["result"]["choices"][0]["message"]["content"]
