#!/usr/bin/env python3
"""build_index.py — embed the relay corpora into corpus/vectors.json.

Sources: practice-logs summaries, canon suttas, tensions/, sessions/ chats.
Re-run after adding tensions or corpora. Incremental: only new ids are
embedded (model recorded in corpus/index_meta.json — mismatch forces full).
Stdlib + numpy.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ai import embed_batch, EMBED_MODEL

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"


def canon_text(path: Path) -> str:
    d = json.loads(path.read_text())
    out = []

    def walk(x):
        if isinstance(x, str) and len(x.strip()) > 25:
            out.append(x.strip())
        elif isinstance(x, dict):
            walk(list(x.values()))
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(d)
    return " ".join(out)


def collect():
    items = []
    # 1. practice logs (the lived-tension side)
    for r in json.loads((CORPUS / "practice-logs" / "logs.json").read_text()):
        text = (r.get("summary", "") + " Keywords: " +
                ", ".join(r.get("key_words", [])))
        if r.get("helpful_sentence"):
            text += " Helpful: " + r["helpful_sentence"]
        items.append({"id": f"plog:{r.get('url', '')}",
                      "kind": "lived-log",
                      "label": f"{r.get('source')}: {r.get('log', '')}",
                      "url": r.get("url", ""),
                      "themes": r.get("predefined_themes", []),
                      "text": text})
    # 2. canon (the teacher side, quotable)
    for p in sorted((CORPUS / "canon").glob("*.json")):
        uid = p.stem.rsplit("_", 1)[0]
        items.append({"id": f"canon:{uid}",
                      "kind": "canon",
                      "label": f"SuttaCentral {uid}",
                      "url": f"https://suttacentral.net/{uid}/en/sujato",
                      "themes": [],
                      "text": canon_text(p)[:4000]})
    # 3. own tensions (match yourself first)
    for p in sorted((ROOT / "tensions").glob("*.md")):
        text = p.read_text()
        body = text.split("---", 1)[1] if "---" in text else text
        items.append({"id": f"tension:{p.stem}",
                      "kind": "own-tension",
                      "label": f"tension {p.stem}",
                      "url": f"tensions/{p.name}",
                      "themes": [],
                      "text": body.strip()[:2000]})
    # 4. own chats (your words guiding you — match yourself first)
    for p in sorted((ROOT / "sessions").glob("chat-*.json")):
        try:
            rec = json.loads(p.read_text())
        except (ValueError, OSError):
            continue
        turns = [m.get("content", "") for m in rec.get("messages", [])
                 if isinstance(m, dict) and m.get("role") in ("user", "assistant")]
        if not turns:
            continue
        first = next((t for t in rec.get("messages", [])
                      if isinstance(t, dict) and t.get("role") == "user"), {})
        items.append({"id": f"chat:{p.stem}",
                      "kind": "own-chat",
                      "label": f"chat {rec.get('date', '')}: "
                               f"{first.get('content', '')[:60]}",
                      "url": f"sessions/{p.name}",
                      "themes": [],
                      "text": "\n".join(turns)[:2000]})
    return [i for i in items if i["text"].strip()]


def main():
    items = collect()
    print(f"{len(items)} items", flush=True)
    meta_path = CORPUS / "index_meta.json"
    vecs = {}
    try:
        meta = json.loads(meta_path.read_text())
        if meta.get("model") == EMBED_MODEL:
            old = json.loads((CORPUS / "vectors.json").read_text())
            if old:
                dim = len(next(iter(old.values())))
                vecs = old
                print(f"reusing {len(vecs)} vectors (dim {dim})", flush=True)
    except (ValueError, OSError, StopIteration):
        pass
    todo = [i for i in items if i["id"] not in vecs]
    print(f"{len(todo)} new to embed", flush=True)
    stale = [k for k in vecs if k not in {i["id"] for i in items}]
    for k in stale:
        del vecs[k]
    if stale:
        print(f"pruned {len(stale)} stale vectors", flush=True)
    B = 64
    dim = None
    for a in range(0, len(todo), B):
        batch = todo[a:a + B]
        for item, v in zip(batch, embed_batch([i["text"][:2000]
                                               for i in batch])):
            vecs[item["id"]] = v
            dim = dim or len(v)
        print(f"embedded {min(a + B, len(todo))}/{len(todo)}", flush=True)
    if dim is None and vecs:
        dim = len(next(iter(vecs.values())))
    (CORPUS / "vectors.json").write_text(json.dumps(vecs))
    (CORPUS / "index.json").write_text(json.dumps(items, ensure_ascii=False))
    meta_path.write_text(json.dumps({"model": EMBED_MODEL, "dim": dim,
                                     "n": len(items)}))
    print("wrote corpus/vectors.json + corpus/index.json + index_meta.json")


if __name__ == "__main__":
    main()
