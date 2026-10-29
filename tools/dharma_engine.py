#!/usr/bin/env python3
"""dharma_engine.py — dharma-tech's GraphRAG running on OUR lived corpus.

No fork, no copy: imports dharma-tech's engine unmodified and points it
at nibbanahelp's exported graph (tools/export_dharma_graph.py).
Falls back to local-only operation — no Ollama, no FalkorDB needed.
"""
import sys
from pathlib import Path

sys.path.insert(0, "/home/box/repos/dharma-tech")

_NIB_GRAPH = Path(__file__).resolve().parent.parent / "corpus" / "dharma_graph"

import core.rag as _rag

_rag.DATA_DIR = _NIB_GRAPH

_ENGINE = None


def engine():
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = _rag.GraphRAG()
    return _ENGINE


def relay_for_roots(roots: list, top_n: int = 3) -> list:
    """Concept-constrained retrieval: passages the graph links to `roots`.

    Returns nibbanahelp-style relay items: {id, kind, label, url, text}.
    Deterministic — no embeddings, no generation.
    """
    eng = engine()
    seen, out = set(), []
    for root in roots:
        for p in eng.retrieve(root, top_n=top_n):
            if p["id"] in seen:
                continue
            seen.add(p["id"])
            tid = p.get("text_id", "")
            if tid.startswith("tensions/"):
                url, kind, label = tid, "tension", p.get("summary", tid)
            elif tid.startswith("roots/"):
                url, kind, label = tid, "roots-doc", p.get("summary", tid) or tid
            else:
                url, kind, label = tid, "passage", tid
            out.append({"id": p["id"], "kind": kind, "label": label,
                        "url": url, "text": p.get("text", "")})
    return out


if __name__ == "__main__":
    import json
    roots = sys.argv[1:] or ["lobha"]
    print(json.dumps(relay_for_roots(roots), ensure_ascii=False, indent=1)[:2000])
