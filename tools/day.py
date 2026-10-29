#!/usr/bin/env python3
"""day.py — bundle everything assigned to a day. Stdlib only.

  python3 tools/day.py 1                 day 1's entries + essays,
                                         plus open tensions + their advice
  python3 tools/day.py 1 --public-only   hide private items
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def header(path: Path) -> dict:
    text = path.read_text()
    head = text.split("---")[0] if "---" in text else ""
    out = {}
    for k in ("day", "visibility", "voice", "audio", "id", "status",
              "summary"):
        m = re.search(rf"^{k}:\s*(.+)$", head, re.M)
        if m:
            out[k] = m.group(1).strip()
    return out


def main(argv):
    if not argv or not argv[0].isdigit():
        print(__doc__)
        return 1
    day = argv[0]
    public_only = "--public-only" in argv
    hide = lambda h: public_only and h.get("visibility", "private") != "public"

    print(f"# Day {day} bundle\n")
    for section, pattern in (("entries", "entries/*.md"),
                             ("essays", "essays/*.md")):
        print(f"## {section}")
        found = False
        for p in sorted(ROOT.glob(pattern)):
            if p.name.startswith("_"):
                continue
            h = header(p)
            if h.get("day") != day or hide(h):
                continue
            found = True
            extra = (f" [audio: {h['audio']}]"
                     if h.get("audio", "-") != "-" else "")
            v = h.get("visibility", "private")
            print(f"- {p.relative_to(ROOT)} ({v}){extra}")
        if not found:
            print("- (none)")
        print()

    print("## open tensions (alive this day until resolved)")
    open_ids = []
    for p in sorted((ROOT / "tensions").glob("*.md")):
        h = header(p)
        if h.get("status") in ("open", "loosening") and not hide(h):
            open_ids.append(h.get("id") or p.stem)
            print(f"- tensions/{p.name} ({h.get('visibility', 'private')}): "
                  f"{h.get('summary', '')}")
    if not open_ids:
        print("- (none)")
    print()

    print("## advice echoed (for open tensions)")
    adv = ROOT / "advice"
    found = False
    if adv.is_dir():
        for p in sorted(adv.glob("*.json")):
            try:
                r = json.loads(p.read_text())
            except json.JSONDecodeError:
                continue
            if r.get("tension") in open_ids:
                found = True
                print(f"- advice/{p.name} → {r['tension']} ({r['date']}): "
                      f"\"{r['to_friend'][:80]}...\"")
    if not found:
        print("- (none)")
    print()

    print("## uploads (upload time is the timestamp)")
    man = ROOT / "uploads" / "manifest.json"
    ufound = False
    if man.is_file():
        try:
            rows = json.loads(man.read_text())
        except json.JSONDecodeError:
            rows = []
        for r in rows:
            if str(r.get("day")) != day:
                continue
            ufound = True
            flag = " [backfill — older material]" if r.get("backfill") else ""
            note = f" ({r['note']})" if r.get("note") else ""
            print(f"- uploads/{r['file']}{flag} @ {r['uploaded_at']}{note}")
    if not ufound:
        print("- (none)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
