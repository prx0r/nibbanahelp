#!/usr/bin/env python3
"""tension.py — the untangling loop. Stdlib + numpy.

  python3 tools/tension.py match --tension coffee-addiction
  python3 tools/tension.py match --text "I keep ordering coffee..."
  python3 tools/tension.py new --tension coffee-addiction   # interactive

`new`: embeds the tension, shows similar lived logs + canon, then chats —
the AI asks, relays, never advises. Everything saved verbatim to
sessions/YYYY-MM-DD-<id>.json: tension, embedding, matches, full chat.
"""
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ai import chat, embed_batch

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"
SESSIONS = ROOT / "sessions"

SYSTEM = (
    "You are a smart friend helping someone untangle a meditation/life "
    "tension. STRICT RULES: never give advice, recommendations, or "
    "instructions. Only (1) ask questions that help them articulate what is "
    "in their mind, and (2) relay relevant passages from the provided "
    "context, always with their source. If they ask what to do, reflect the "
    "question back with a sharper question plus the most relevant relayed "
    "passage. Short replies. One question at a time.")


def load():
    items = json.loads((CORPUS / "index.json").read_text())
    vecs = json.loads((CORPUS / "vectors.json").read_text())
    mat = np.array([vecs[i["id"]] for i in items], dtype=np.float32)
    mat = mat / (np.linalg.norm(mat, axis=1, keepdims=True) + 1e-9)
    return items, mat


def similar(qvec, items, mat, k=5, skip_id=None):
    q = np.array(qvec, dtype=np.float32)
    q = q / (np.linalg.norm(q) + 1e-9)
    scores = mat @ q
    boost = {"own-tension": 1.35, "own-chat": 1.25, "canon": 1.1}
    order = np.argsort(-scores)
    scored = sorted(((float(scores[int(i)]) * boost.get(items[int(i)].get("kind"), 1.0), int(i)) for i in order), reverse=True)
    out = []
    for s, i in scored:
        if items[i]["id"] == skip_id:
            continue
        out.append((items[i], s))
        if len(out) == k:
            break
    return out


def tension_text(tid: str) -> str:
    p = ROOT / "tensions" / f"{tid}.md"
    text = p.read_text()
    return (text.split("---", 1)[1] if "---" in text else text).strip()


def cmd_match(tid=None, text=None, k=5):
    items, mat = load()
    if tid:
        qtext = tension_text(tid)
        skip = f"tension:{tid}"
    else:
        qtext, skip = text, None
    qvec = embed_batch([qtext[:2000]])[0]
    for item, s in similar(qvec, items, mat, k=k, skip_id=skip):
        print(f"\n[{s:.3f}] {item['kind']} — {item['label']}")
        if item.get("themes"):
            print(f"  themes: {', '.join(item['themes'][:5])}")
        print(f"  {item['url']}")
        print(f"  {item['text'][:400]}")


def cmd_new(tid: str):
    items, mat = load()
    qtext = tension_text(tid)
    qvec = embed_batch([qtext[:2000]])[0]
    matches = similar(qvec, items, mat, k=5, skip_id=f"tension:{tid}")
    print(f"=== untangling: {tid} ===\n")
    ctx_bits = []
    for item, s in matches:
        print(f"--- [{s:.3f}] {item['label']}\n{item['url']}\n"
              f"{item['text'][:600]}\n")
        ctx_bits.append(f"[{item['label']}] {item['url']}: "
                        f"{item['text'][:800]}")
    context = "\n\n".join(ctx_bits)
    history = [{"role": "system", "content": SYSTEM + "\n\nTension:\n" +
                qtext[:1500] + "\n\nRelated passages:\n" + context}]
    transcript = []
    print("Talk it through. The AI asks + relays, never advises. "
          "Type /done to save and exit.\n")
    while True:
        try:
            user = input("you> ").strip()
        except EOFError:
            user = "/done"
        if user == "/done":
            break
        if not user:
            continue
        history.append({"role": "user", "content": user})
        reply = chat(history, max_tokens=300)
        print(f"\nai> {reply}\n")
        history.append({"role": "assistant", "content": reply})
        transcript.append({"you": user, "ai": reply})
    SESSIONS.mkdir(exist_ok=True)
    rec = {"date": date.today().isoformat(), "tension": tid,
           "tension_text": qtext,
           "embedding": qvec,
           "matches": [{"id": m["id"], "label": m["label"], "url": m["url"],
                         "score": s} for m, s in matches],
           "chat": transcript}
    dest = SESSIONS / f"{date.today().isoformat()}-{tid}.json"
    dest.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    print(f"saved → {dest.relative_to(ROOT)} "
          f"({len(transcript)} exchanges, embedding stored)")


def main(argv):
    if not argv or argv[0] not in ("match", "new"):
        print(__doc__)
        return 1
    if argv[0] == "match":
        k = 5
        if "--k" in argv:
            k = int(argv[argv.index("--k") + 1])
        if "--tension" in argv:
            cmd_match(tid=argv[argv.index("--tension") + 1], k=k)
        elif "--text" in argv:
            cmd_match(text=argv[argv.index("--text") + 1], k=k)
        else:
            print("need --tension ID or --text '...'");
            return 1
    else:
        if "--tension" not in argv:
            print("need --tension ID");
            return 1
        cmd_new(argv[argv.index("--tension") + 1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
