#!/usr/bin/env python3
"""ingest_hxrmxs.py — dialogue corpus -> relay items.

Parses the messy hxrmxs JSON dialogue files (tolerant brace-matcher +
strict=False), dedupes by episode_id (9* copies, uno, etc. collapse
automatically), chunks long episodes at turn boundaries. Used by
tools/build_index.py as the 5th corpus source.
"""
import json
import os
import re
from pathlib import Path

HX = Path("/home/box/repos/tomnotes/hxrmxs")


def extract_episodes(path: Path):
    raw = path.read_text(encoding="utf-8", errors="replace")
    out = []
    for m in re.finditer(r'\{\s*"episode_id"', raw):
        start = m.start()
        i, n, depth, instr, esc = start, len(raw), 0, False, False
        while i < n:
            c = raw[i]
            if instr:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    instr = False
            else:
                if c == '"':
                    instr = True
                elif c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        break
            i += 1
        if depth != 0:
            continue
        try:
            o = json.loads(raw[start:i + 1], strict=False)
            if isinstance(o, dict) and o.get("episode_id"):
                out.append(o)
        except Exception:
            continue
    return out


def episode_text(ep: dict) -> str:
    parts = []
    for key in ("messages", "student_turns", "teacher_turns", "turns"):
        turns = ep.get(key)
        if not isinstance(turns, list):
            continue
        for m in turns:
            if not isinstance(m, dict):
                continue
            who = m.get("role") or m.get("speaker") or m.get("speaker_name") or "?"
            t = m.get("content", m.get("text", ""))
            if isinstance(t, str) and t.strip() and who != "system":
                if who in ("system", "developer"):
                    continue
                parts.append(f"{who}: {t.strip()}")
    return "\n".join(parts)


def slug(eid: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", str(eid).lower()).strip("_")
    return s[:80] or "ep"


def collect_hxrmxs(max_chars: int = 1500) -> list:
    seen = set()
    items = []
    if not HX.is_dir():
        return items
    for f in sorted(HX.glob("*.txt")):
        if f.stat().st_size < 200:
            continue
        try:
            eps = extract_episodes(f)
        except OSError:
            continue
        for e in eps:
            eid = str(e.get("episode_id", "")).strip()
            if not eid or eid in seen or len(eid) < 4 or set(eid) == {"."}:
                continue
            seen.add(eid)
            lineage = str(e.get("lineage", "") or "?")
            text = episode_text(e).strip()
            if len(text) < 200:
                continue
            # chunk at turn boundaries (~2 lines per turn)
            lines = text.split("\n")
            cur, chunks, n = [], [], 0
            for ln in lines:
                cur.append(ln)
                n += 1
                if sum(len(x) for x in cur) >= max_chars and n % 2 == 0:
                    chunks.append("\n".join(cur))
                    cur = []
            if cur:
                chunks.append("\n".join(cur))
            for i, ch in enumerate(chunks):
                if len(ch.strip()) < 120:
                    continue
                items.append({"id": f"hx:{slug(eid)}" + (f":{i}" if len(chunks) > 1 else ""),
                              "kind": "dialogue",
                              "label": f"dialogue {eid[:60]} ({lineage})",
                              "url": f"tomnotes/hxrmxs/{f.name}",
                              "themes": [lineage],
                              "text": ch[:2000]})
    return items


if __name__ == "__main__":
    from collections import Counter
    items = collect_hxrmxs()
    print(f"{len(items)} hxrmxs items")
    kinds = Counter()
    for it in items:
        kinds[it["label"].split(" (")[-1].rstrip(")")] += 1
    print(dict(kinds))
    for it in items[:2]:
        print("---", it["id"], len(it["text"]))
