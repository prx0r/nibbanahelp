#!/usr/bin/env python3
"""echo.py — self-advice loop for nibbanahelp. Stdlib only.

  python3 tools/echo.py capture              ask the question per open tension
  python3 tools/echo.py playback             your words back, for open tensions
  python3 tools/echo.py playback --tension ID filter to one tension

Advice records live in advice/ as JSON, one file per capture:
  advice/YYYY-MM-DD-<tension-id>.json
  {date, tension, situation, to_friend, from_future_self}
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TENSIONS = ROOT / "tensions"
ADVICE = ROOT / "advice"


def parse_tension(path: Path) -> dict:
    text = path.read_text()
    head = text.split("---")[0] if "---" in text else text
    get = lambda k: (re.search(rf"^{k}:\s*(.+)$", head, re.M).group(1).strip()
                     if re.search(rf"^{k}:\s*(.+)$", head, re.M) else "")
    body = text.split("---", 1)[1].strip() if "---" in text else ""
    return {"id": get("id") or path.stem, "status": get("status"),
            "summary": get("summary"), "body": body}


def open_tensions():
    out = []
    for p in sorted(TENSIONS.glob("*.md")):
        t = parse_tension(p)
        if t["status"] in ("open", "loosening"):
            out.append(t)
    return out


def cmd_capture():
    tensions = open_tensions()
    if not tensions:
        print("No open tensions. Nothing to ask.")
        return
    ADVICE.mkdir(exist_ok=True)
    today = date.today().isoformat()
    for t in tensions:
        print(f"\n=== {t['id']} ===")
        print(f"{t['summary']}\n")
        to_friend = input(
            "What would YOU say to a dear friend in exactly this "
            "situation?\n> ").strip()
        if not to_friend:
            print("(skipped — nothing saved)")
            continue
        future = input(
            "And what would future-you, one month past this, say?\n> "
        ).strip()
        rec = {"date": today, "tension": t["id"],
               "situation": t["summary"], "to_friend": to_friend,
               "from_future_self": future}
        dest = ADVICE / f"{today}-{t['id']}.json"
        dest.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n")
        print(f"saved → {dest.relative_to(ROOT)}")


def load_advice():
    recs = []
    if ADVICE.is_dir():
        for p in sorted(ADVICE.glob("*.json")):
            try:
                recs.append(json.loads(p.read_text()))
            except json.JSONDecodeError:
                print(f"warn: unreadable {p.name}, skipping")
    return recs


def cmd_playback(only=None):
    tensions = {t["id"]: t for t in open_tensions()}
    recs = [r for r in load_advice()
            if r.get("tension") in tensions
            and (only is None or r.get("tension") == only)]
    if not recs:
        print("Nothing to echo back yet. Run `capture` first — "
              "your future self needs material.")
        return
    latest = {}
    for r in recs:
        latest[r["tension"]] = r  # sorted by filename = chronological
    for tid, r in latest.items():
        print(f"\n=== {tid} (you, on {r['date']}) ===")
        print(f"Situation was: {r['situation']}\n")
        print(f'You said to a friend:\n  "{r["to_friend"]}"')
        if r.get("from_future_self"):
            print(f'\nFuture-you said:\n  "{r["from_future_self"]}"')


def main(argv):
    if not argv or argv[0] not in ("capture", "playback"):
        print(__doc__)
        return 1
    if argv[0] == "capture":
        cmd_capture()
    else:
        only = None
        if "--tension" in argv:
            only = argv[argv.index("--tension") + 1]
        cmd_playback(only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
