#!/usr/bin/env python3
"""characterise.py — auto-kind for text uploads: locked to diary | essay |
poem (never anything else; audio/video/image by extension). Heuristics are
deterministic-first; the free-tier model only breaks ties. Stdlib + ai.py."""
import re
from pathlib import Path

CHOICE = ("Classify this document. Reply with exactly one word: "
          "diary, essay, or poem. diary = dated first-person entries or "
          "stream logs; essay = prose argument or notes in sentences; "
          "poem = verse (short lines, line-breaks carry meaning). "
          "Never answer note or any other word.")


def classify_text(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return "essay"
    lines = [l for l in t.splitlines() if l.strip()]
    words = t.split()
    # deterministic verse checks first
    if len(lines) >= 4 and \
            sum(1 for l in lines if len(l) < 60) / len(lines) > 0.7:
        return "poem"
    if len(lines) >= 3 and len(words) / len(lines) < 6 and len(t) < 400:
        return "poem"
    # deterministic diary markers
    if re.search(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|"
                 r"sunday|day\s*\d|date:)\b", t[:600], re.I):
        return "diary"
    # ambiguous prose: one model call breaks the diary/essay tie
    try:
        from ai import chat
        w = chat([{"role": "system", "content": CHOICE},
                  {"role": "user", "content": t[:1500]}],
                 max_tokens=64).strip().lower()
        for k in ("diary", "essay", "poem"):
            if re.search(rf"\b{k}\b", w):
                return k
    except Exception:
        pass
    return "essay"


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
        return "essay"


if __name__ == "__main__":
    for s in ["Day 3\n\nI sat twice today. The pull was less.",
              "The argument holds because the premise dissolves under "
              "examination, as Nagarjuna shows…",
              "the kettle boils\nsteam leaves the cup\nwant leaves the mind",
              "xkcd 1234 notes"]:
        print(classify_text(s), "|", s[:40])
