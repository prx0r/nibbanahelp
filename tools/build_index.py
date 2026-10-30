#!/usr/bin/env python3
"""build_index.py — embed the relay corpora into corpus/vectors.json.

Sources: practice-logs summaries, canon suttas, tensions/, sessions/ chats.
Re-run after adding tensions or corpora. Incremental: only new ids are
embedded (model recorded in corpus/index_meta.json — mismatch forces full).
Stdlib + numpy.
"""
import json
import os
import re
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


TOMNOTES = Path("/home/box/repos/tomnotes")


def chunk_text(text, size=1200):
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, cur = [], ""
    for p in paras:
        if len(cur) + len(p) + 2 <= size:
            cur = (cur + "\n\n" + p).strip()
        else:
            if cur:
                chunks.append(cur)
            while len(p) > size:
                chunks.append(p[:size])
                p = p[size:]
            cur = p
    if cur:
        chunks.append(cur)
    return chunks


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
    # 4b. curated link-first answers (forum threads, timing guidance)
    for cp in sorted((CORPUS / "curated").glob("*.json")):
        try:
            recs = json.loads(cp.read_text())
        except (ValueError, OSError):
            continue
        if isinstance(recs, dict):
            recs = [recs]
        for r in recs:
            if not isinstance(r, dict) or not r.get("text"):
                continue
            items.append({"id": str(r.get("id", f"curated:{cp.stem}")),
                          "kind": r.get("kind", "teacher-answer"),
                          "label": str(r.get("label", cp.stem))[:90],
                          "url": str(r.get("url", "")),
                          "themes": r.get("themes", []),
                          "text": str(r["text"])[:2000]})
    # 4c. Beth Upton interview transcripts (local, from the abhidhamma repo)
    UPTON = Path("/home/box/repos/abhidhamma/transcripts/pa-auk")
    if UPTON.is_dir():
        for tp in sorted(UPTON.glob("upton-*.txt")):
            text = tp.read_text(errors="ignore").strip()
            if len(text) < 400:
                continue
            for chi, ch in enumerate(chunk_text(text)[:12]):
                items.append({"id": f"canon:upton:{tp.stem}:{chi}",
                              "kind": "canon",
                              "label": f"Beth Upton interview ({tp.stem})",
                              "url": f"abhidhamma/transcripts/pa-auk/{tp.name}",
                              "themes": ["Beth Upton", "Pa Auk", "Abhidhamma"],
                              "text": ch[:2000]})
    # 5. own bank: tomnotes diaries, essays, prior chats (your words first)
    if TOMNOTES.is_dir():
        conv_file = TOMNOTES / "diary training data.txt"
        if conv_file.is_file():
            try:
                convos = json.loads(conv_file.read_text())
            except (ValueError, OSError):
                convos = []
            for ci, c in enumerate(convos):
                msgs = c.get("messages", []) if isinstance(c, dict) else []
                pairs, cur_q = [], None
                for m in msgs:
                    if not isinstance(m, dict):
                        continue
                    if m.get("role") == "user":
                        cur_q = m.get("content", "")
                    elif m.get("role") == "assistant" and cur_q:
                        pairs.append((cur_q, m.get("content", "")))
                        cur_q = None
                if not pairs and msgs:
                    pairs = [("diary", " ".join(
                        str(m.get("content", "")) for m in msgs
                        if isinstance(m, dict)))]
                for pi, (qq, aa) in enumerate(pairs):
                    text = f"Q: {qq}\nA: {aa}".strip()[:2000]
                    if len(text) < 40:
                        continue
                    items.append({"id": f"ownchat:tomnotes-diary-{ci}-{pi}",
                                  "kind": "own-chat",
                                  "label": f"diary {str(qq)[:60]}",
                                  "url": "tomnotes/diary training data.txt",
                                  "themes": [],
                                  "text": text})
        for name in sorted(os.listdir(TOMNOTES)):
            p = TOMNOTES / name
            if (not p.is_file() or p.suffix.lower() not in ("", ".txt", ".md")
                    or name in ("diary training data.txt",)):
                continue
            try:
                text = p.read_text(errors="ignore")
            except OSError:
                continue
            if len(text.strip()) < 40:
                continue
            for chi, ch in enumerate(chunk_text(text)):
                items.append({"id": f"ownnotes:{name}:{chi}",
                              "kind": "own-notes",
                              "label": f"notes: {name}",
                              "url": f"tomnotes/{name}",
                              "themes": [],
                              "text": ch[:2000]})
    # 4d. trika corpus (mantra-body texts; kind=trika -> lineage tier, see trika/README)
    TRIKA = ROOT / "trika" / "passages"
    if TRIKA.is_dir():
        for tp in sorted(TRIKA.glob("*.md")):
            text = tp.read_text(encoding="utf-8", errors="ignore").strip()
            if len(text) < 40:
                continue
            first = text.splitlines()[0].lstrip("# ").strip() if text else tp.stem
            first = first.replace("Trika passage: ", "")
            for chi, ch in enumerate(chunk_text(text)):
                items.append({"id": f"trika:{tp.stem}:{chi}",
                              "kind": "trika",
                              "label": f"Trika: {first}"[:90],
                              "url": "",
                              "themes": ["Trika", "Kashmir Shaivism"],
                              "text": ch[:2000]})
    # 5. own bank: tomnotes diaries, essays, prior chats (your words first)
    from ingest_hxrmxs import collect_hxrmxs
    for it in collect_hxrmxs():
        items.append(it)
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
