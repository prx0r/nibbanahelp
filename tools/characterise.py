#!/usr/bin/env python3
"""characterise.py — auto-kind for uploads: diary | essay | poem | note |
audio | video | image. Text goes through the free-tier chat model as a
one-word choice; deterministic heuristics as fallback. Stdlib + ai.py."""
import re
from pathlib import Path

CHOICE = ("Classify this document. Reply with exactly one word from: "
          "diary, essay, poem, note. diary = dated first-person entries or "
          "stream logs; essay = structured prose argument; poem = verse "
          "(short lines, line-breaks carry meaning); note = anything else.")


def classify_text(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return "note"
    try:
        from ai import chat
        w = chat([{"role": "system", "content": CHOICE},
                  {"role": "user", "content": t[:1500]}],
                 max_tokens=8).strip().lower()
        for k in ("diary", "essay", "poem", "note"):
            if k in w:
                return k
    except Exception:
        pass
    lines = [l for l in t.splitlines() if l.strip()]
    words = t.split()
    if len(lines) >= 5 and sum(1 for l in lines if len(l) < 60) / len(lines) > 0.7:
        return "poem"
    if re.search(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|"
                 r"sunday|day\s*\d|date:)\b", t[:600], re.I) or \
            (t.lower().count(" i ") + (1 if t.lower().startswith("i ") else 0)) >= 2:
        return "diary"
    return "essay" if len(t) > 400 else "note"


def classify_bytes(data: bytes, name: str) -> str:
    ext = Path(name).suffix.lower()
    if ext in (".mp3", ".wav", ".m4a", ".ogg"):
        return "audio"
    if ext in (".mp4", ".mov", ".webm"):
        return "video"
    if ext in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
        return "image"
    try:
        return classify_text(data.decode("utf-8", "ignore"))
    except Exception:
        return "note"


if __name__ == "__main__":
    for s in ["Day 3\n\nI sat twice today. The pull was less.",
              "The argument holds because the premise dissolves under "
              "examination, as Nagarjuna shows…",
              "the kettle boils\nsteam leaves the cup\nwant leaves the mind",
              "xkcd 1234 notes"]:
        print(classify_text(s), "|", s[:40])
