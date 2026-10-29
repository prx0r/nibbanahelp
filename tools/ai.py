#!/usr/bin/env python3
"""ai.py — shared Cloudflare Workers AI backend (free tier). Stdlib only.

Embeddings: @cf/baai/bge-m3 (1024-dim). Chat: @cf/deepseek-ai/deepseek-v4-flash.
Rerank: @cf/baai/bge-reranker-base. All free tier, no spend, ever.
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

EMBED_MODEL = "@cf/baai/bge-m3"
CHAT_MODEL = "@cf/deepseek-ai/deepseek-v4-flash"
FALLBACK_MODEL = "@cf/meta/llama-3.3-70b-instruct-fp8-fast"


def _post(model: str, payload: dict, timeout: int = 120) -> dict:
    req = urllib.request.Request(
        f"{BASE}/{model}",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def embed_batch(texts: list, model: str = None) -> list:
    """texts: list[str] (batch up to ~64) -> list[vector]."""
    out = _post(model or EMBED_MODEL, {"text": texts})
    return out["result"]["data"]


def _chat_once(model, messages, max_tokens):
    out = _post(model, {"messages": messages, "max_tokens": max_tokens})
    ch = out["result"]["choices"][0]["message"]
    text = ch.get("content") or ""
    return text.strip()


def chat(messages: list, max_tokens: int = 800) -> str:
    try:
        text = _chat_once(CHAT_MODEL, messages, max_tokens)
        if text:
            return text
    except Exception:
        pass
    return _chat_once(FALLBACK_MODEL, messages, max_tokens)


def rerank(query: str, texts: list) -> list:
    """Cross-encoder rerank. Returns input indices, most relevant first."""
    out = _post("@cf/baai/bge-reranker-base",
                {"query": query,
                 "contexts": [{"text": t[:1000]} for t in texts]})
    res = out.get("result", {}).get("response", [])
    if isinstance(res, dict):
        res = res.get("response", [])
    order = sorted([r for r in res if isinstance(r, dict)],
                   key=lambda r: r.get("score", 0), reverse=True)
    ids = [r["id"] for r in order
           if isinstance(r.get("id"), int) and 0 <= r["id"] < len(texts)]
    return ids or list(range(len(texts)))


CHAT_SYSTEM = (
    "You are a dharma friend inside nibbanahelp, a shared diary of people "
    "attaining nibbana. STRICT RULES: never give advice, recommendations, "
    "or instructions. Only two moves: (1) ask questions — especially "
    "questions that help the diarist notice and name tensions (cravings, "
    "irritations, fog) in ordinary daily situations; (2) relay relevant "
    "passages from the provided context, always with their source. When "
    "you see a tension forming, name it plainly and map it to its root: "
    "lobha (greed, pulling), dosa (hate, pushing), moha (delusion, fog). "
    "If they ask what to do, reflect the question back with a sharper "
 "question plus the most relevant relayed passage. Short replies. "
 "One question at a time. Advanced mode: probe for specific mental "
 "factors, not just roots — restlessness? doubt? view? conceit? worry? "
 "aversion? Name the citta-class (e.g. doubt-rooted, worry-laden) rather "
 "than labelling whole life situations; a debt is not greed, a doubting "
 "mind-moment is delusion. Always separate the circumstance (real — e.g. "
 "debt owed, to be handled practically by sustaining oneself) from the "
 "affliction it incurs (mental states to discern, never to obey)."
 "When the diarist answers their own question or states their own "
 "insight, mirror their exact words back first — that verbatim record "
 "is the point; analysis second, always brief. VOICE RULE (absolute): "
 "the diarist's own words are ONLY entries/*, essays/*, tensions/* bodies, "
 "motto.txt, advice to_friend, and chat user-turns. Summaries, labels, "
 "schema text, graph descriptions, and anything the AI wrote are NEVER "
 "the diarist's words — quote those only as record/metadata, never as "
 "'you said'."
 "Lead with what you relayed — quoted passages with sources first, "
 "your own words minimal and interrogative. You are "
 "a finder, not a teacher.")
