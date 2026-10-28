#!/usr/bin/env python3
"""site.py — build a single white page. No deps, no framework.

  python3 tools/site.py            -> site/index.html
  python3 -m http.server -d site   (or just open the file)
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "index.html"


def raw(src: str) -> str:
    # Exactly what was written, in a <pre>. Only three inline markers
    # render: **bold**, __underline__, *italic*. Everything else literal.
    return "<pre>" + inline3(html.escape(src)) + "</pre>"


def inline3(s: str) -> str:
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"__(.+?)__", r"<u>\1</u>", s)
    s = re.sub(r"\*([^*\n]+)\*", r"<em>\1</em>", s)
    return s


def header(p: Path) -> dict:
    text = p.read_text()
    head = text.split("---")[0] if "---" in text else ""
    out = {}
    for k in ("day", "visibility", "voice", "audio", "id", "status",
              "summary"):
        m = re.search(rf"^{k}:\s*(.+)$", head, re.M)
        if m:
            out[k] = m.group(1).strip()
    body = text.split("---", 1)[1] if "---" in text else text
    return out, body.strip()


def card(title, meta, body_html):
    return (f'<article><h2>{html.escape(title)}</h2>'
            f'<div class="meta">{meta}</div>{body_html}</article>')


def main():
    days = {}
    for pattern in ("entries/*.md", "essays/*.md"):
        for p in sorted((ROOT).glob(pattern)):
            if p.name.startswith("_"):
                continue
            h, body = header(p)
            if "day" not in h:
                continue
            days.setdefault(h["day"], []).append((p, h, body))
    tensions = []
    for p in sorted((ROOT / "tensions").glob("*.md")):
        h, body = header(p)
        tensions.append((p, h, body))

    parts = []
    for day in sorted(days, key=int):
        secs = [f"<p>day {day}</p>"]
        for p, h, body in days[day]:
            secs.append(f"<p>{p.stem}</p>" + raw(body))
        parts.append("\n".join(secs))
    tsec = ["<p>open tensions</p>"]
    for p, h, body in tensions:
        if h.get("status") != "open":
            continue
        tsec.append(f"<p>{h.get('id', p.stem)}</p>" + raw(body))
    parts.append("\n".join(tsec))
    man = ROOT / "uploads" / "manifest.json"
    if man.is_file():
        try:
            rows = json.loads(man.read_text())
        except json.JSONDecodeError:
            rows = []
        if rows:
            usec = ["<p>uploaded</p>"]
            for r in rows:
                flag = " [backfill]" if r.get("backfill") else ""
                usec.append(f"<p><a href=\"/files/{r['file']}\">{r['file']}"
                            f"</a>{flag} {r['uploaded_at']}</p>")
            parts.append("\n".join(usec))

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>nibbanahelp</title>
<style>
  body {{ background: #fff; color: #000;
         font-family: monospace;
         margin: 0; padding: 0 1rem; }}
  a {{ color: #000; }}
  pre {{ white-space: pre-wrap; font-family: monospace; }}
</style>
</head>
<body>
{''.join(parts)}
</body>
</html>
""")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
