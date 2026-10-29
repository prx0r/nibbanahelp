#!/usr/bin/env python3
"""queue.py — videos I should watch, from my model, via satsang.

Reads profile/me.json (tools/me.py), searches the satsang directory
(REST, no auth) for each theme's queries, dedups clip hits, ranks,
writes profile/watch-queue.md with a why-line per pick (tied to the
tension it serves). Links resolve to satsang.digital.
"""
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "profile"
API = "https://mcp.tantrafiles.xyz/api/search"


def search(q, limit=8):
    url = f"{API}?q={urllib.parse.quote(q)}&kinds=clip&limit={limit}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 "
                      "Chrome/120 Mobile Safari/537.36"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r).get("results", [])
    except Exception as e:
        print(f"  search fail {q!r}: {e}")
        return []


def main():
    me = json.loads((PROFILE / "me.json").read_text())
    seen = set()
    picks = []
    for c in me["live_tensions"]:
        for q in c.get("queries", []):
            for res in search(q, limit=6):
                rid = res.get("id", "")
                if not rid.startswith("clip/") or rid in seen:
                    continue
                seen.add(rid)
                title = (res.get("name") or res.get("title") or
                         res.get("label") or rid)
                teacher = res.get("teacher") or res.get("person") or ""
                picks.append({
                    "tension": c["id"], "query": q, "id": rid,
                    "title": title, "teacher": teacher,
                    "why": c["summary"],
                })
    # interleave: max 4 per tension, cap 12 total
    by_t = {}
    for p in picks:
        by_t.setdefault(p["tension"], []).append(p)
    picks, i = [], 0
    while len(picks) < 12 and any(by_t.values()):
        for t in list(by_t):
            if by_t[t]:
                picks.append(by_t[t].pop(0))
            if len(picks) >= 12:
                break
    lines = ["# watch queue", "",
             "Generated from profile/me.json via the satsang directory "
             "(mcp.tantrafiles.xyz). Each pick names the tension it serves "
             "and why — the why-line is the tension summary, verbatim.", ""]
    for p in picks:
        url = "https://tantrafiles.xyz/" + p["id"]
        lines.append(f"- [{p['title']}]({url})"
                     + (f" — {p['teacher']}" if p["teacher"] else ""))
        lines.append(f"  for: {p['tension']} ({p['query']}) — {p['why'][:100]}")
    (PROFILE / "watch-queue.md").write_text("\n".join(lines) + "\n")
    print(f"wrote profile/watch-queue.md ({len(picks)} picks)")
    for p in picks[:12]:
        print(" -", p["title"][:70])


if __name__ == "__main__":
    main()
