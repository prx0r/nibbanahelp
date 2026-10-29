#!/usr/bin/env python3
"""me.py — the model of me, from my own words only.

Reads tensions/ (roots + summaries + progress), entries/, essays/, motto,
sessions/, tomnotes top-level notes. Emits profile/me.json (query themes,
roots, live concerns — everything derived verbatim or from schema) and
profile/me.md (readable). Feeds tools/queue.py.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOMNOTES = Path("/home/box/repos/tomnotes")
PROFILE = ROOT / "profile"

# theme -> satsang search terms, seeded from the tensions themselves
THEME_QUERIES = {
    "coffee-addiction": ["craving", "addiction", "habit"],
    "debt-1500": ["money", "livelihood", "renunciation"],
    "hidden-sexuality-shame": ["self-judgment", "shame", "conceit"],
}


def header(p: Path) -> dict:
    text = p.read_text()
    head = text.split("---")[0] if "---" in text else ""
    out = {}
    for k in ("day", "id", "status", "domain", "roots", "summary"):
        m = re.search(rf"^{k}:\s*(.+)$", head, re.M)
        if m:
            out[k] = m.group(1).strip()
    m = re.search(r"^roots:\s*\[(.+?)\]\s*$", head, re.M)
    if m:
        out["roots"] = [x.strip() for x in m.group(1).split(",")]
    body = text.split("---", 1)[1] if "---" in text else text
    out["_body"] = body.strip()
    return out


def main():
    concerns = []
    for p in sorted((ROOT / "tensions").glob("*.md")):
        h = header(p)
        if h.get("status") not in ("open", "loosening"):
            continue
        concerns.append({
            "id": h.get("id", p.stem),
            "status": h.get("status"),
            "domain": h.get("domain", ""),
            "roots": h.get("roots", []),
            "summary": h.get("summary", ""),
            "verbatim": h["_body"][:400],
            "queries": THEME_QUERIES.get(h.get("id", p.stem), []),
        })
    motto = []
    mp = ROOT / "motto.txt"
    if mp.is_file():
        motto = [l for l in mp.read_text().splitlines() if l.strip()]
    notes = []
    for name in ["day1", "day2", "day 6", "fasgrabby",
                 "enlightenment is simply a choice"]:
        p = TOMNOTES / name
        if p.is_file():
            t = p.read_text(errors="ignore").strip()
            if t:
                notes.append({"name": name, "excerpt": t[:300]})
    sess_count = len(list((ROOT / "sessions").glob("chat-*.json")))
    me = {
        "generated": "2026-10-29",
        "live_tensions": concerns,
        "roots_active": sorted({r for c in concerns for r in c["roots"]}),
        "motto": motto,
        "notes_excerpts": notes,
        "sessions_logged": sess_count,
        "voice": "notes/essays/chats of prx0r; nothing here is inferred "
                 "beyond schema fields",
    }
    PROFILE.mkdir(exist_ok=True)
    (PROFILE / "me.json").write_text(json.dumps(me, indent=1) + "\n")
    lines = ["# me (model from my own words)", ""]
    lines.append("## live tensions")
    for c in concerns:
        lines.append(f"- {c['id']} [{c['status']}] roots={','.join(c['roots'])}"
                     f" :: {c['summary']}")
        lines.append(f"  verbatim: {c['verbatim'][:180]}")
    lines.append("\n## motto")
    lines.extend(f"- {m}" for m in motto)
    lines.append(f"\n## sessions logged: {sess_count}")
    (PROFILE / "me.md").write_text("\n".join(lines) + "\n")
    print(f"wrote profile/me.json + me.md ({len(concerns)} live tensions)")


if __name__ == "__main__":
    main()
