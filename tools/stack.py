#!/usr/bin/env python3
"""stack.py — log + tag + analyse new chat sessions.

For every sessions/chat-*.json WITHOUT a matching .analysis.json sidecar,
asks the model (free tier) to extract: tensions mentioned, the diarist's
own verbatim insights (self-answers are the gold), roots tags, and
suggested tension updates. Writes sessions/chat-<id>.analysis.json.
Nothing is auto-filed into tensions/ — the diarist confirms first.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ai import chat

ROOT = Path(__file__).resolve().parent.parent

EXTRACT = """You log and tag a dharma-journal chat. Read it and return ONLY JSON:
{"tensions_mentioned": [{"id_or_slug": str, "status": "known|new"}],
 "own_insights": ["verbatim quotes where the diarist answered their own question or stated a resolution - exact words, no paraphrase"],
 "roots": ["lobha|dosa|moha present, with one-line why each"],
 "suggested_tension_updates": [{"tension": "id or NEW:name", "action": "append-progress|new-tension|status-change", "note": "verbatim or near-verbatim material to file"}]}
Be conservative: only quote what was actually said. Empty lists allowed."""


def main():
    sessions = ROOT / "sessions"
    new = 0
    for p in sorted(sessions.glob("chat-*.json")):
        if p.name.endswith(".analysis.json"):
            continue
        sidecar = p.parent / (p.stem + ".analysis.json")
        if sidecar.exists():
            continue
        try:
            rec = json.loads(p.read_text())
        except (ValueError, OSError):
            continue
        convo = "\n".join(
            f"{m.get('role', '')}: {m.get('content', '')}"
            for m in rec.get("messages", []) if isinstance(m, dict))
        if not convo.strip():
            continue
        print(f"analysing {p.name}...", flush=True)
        try:
            out = chat([{"role": "system", "content": EXTRACT},
                        {"role": "user", "content": convo[:6000]}],
                       max_tokens=600)
        except Exception as e:
            print(f"  ai error: {e}")
            continue
        txt = out.strip()
        if txt.startswith("```"):
            txt = txt.strip("`").split("\n", 1)[-1].rsplit("```", 1)[0]
        try:
            data = json.loads(txt[txt.index("{"):txt.rindex("}") + 1])
        except (ValueError, IndexError):
            print("  unparseable, saving raw")
            data = {"raw": out}
        sidecar.write_text(json.dumps({"source": p.name, "analysis": data},
                                      ensure_ascii=False, indent=1) + "\n")
        print(f"  wrote {sidecar.name}")
        new += 1
    print(f"done, {new} new analyses")


if __name__ == "__main__":
    main()
