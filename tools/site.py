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


def md(src: str) -> str:
    out = []
    para = []
    def flush():
        if para:
            out.append("<p>" + " ".join(para) + "</p>")
            para.clear()
    for line in src.splitlines():
        line = line.rstrip()
        if not line.strip() or line.strip() == "---":
            flush()
            continue
        m = re.match(r"^(#{1,3})\s+(.*)", line)
        if m:
            flush()
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            continue
        if re.match(r"^[-*]\s+", line):
            flush()
            bullet = re.sub(r"^[-*]\s+", "", line)
            out.append(f"<li>{inline(bullet)}</li>")
            continue
        if re.match(r"^\d+\.\s+", line):
            flush()
            numbered = re.sub(r"^\d+\.\s+", "", line)
            out.append(f"<li>{inline(numbered)}</li>")
            continue
        para.append(inline(line))
    flush()
    return "\n".join(out)


def inline(s: str) -> str:
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    s = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', s)
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
        secs = [f"<h1>Day {day}</h1>"]
        for p, h, body in days[day]:
            kind = "essay" if p.parent.name == "essays" else "entry"
            vis = h.get("visibility", "private")
            au = f' · <a href="#">spoken</a>' if h.get("audio",
                                                      "-") != "-" else ""
            secs.append(card(f"{p.stem} ({kind}, {vis})",
                             f"{p.relative_to(ROOT)}{au}", md(body)))
        parts.append("\n".join(secs))
    tsec = ["<h1>Open tensions</h1>"]
    for p, h, body in tensions:
        if h.get("status") != "open":
            continue
        tsec.append(card(f"{h.get('id', p.stem)}",
                         f"{h.get('summary', '')} · {p.relative_to(ROOT)}",
                         md(body)))
    parts.append("\n".join(tsec))
    man = ROOT / "uploads" / "manifest.json"
    if man.is_file():
        try:
            rows = json.loads(man.read_text())
        except json.JSONDecodeError:
            rows = []
        if rows:
            usec = ["<h1>Uploaded (upload time is the timestamp)</h1><ul>"]
            for r in rows:
                flag = " [backfill]" if r.get("backfill") else ""
                note = f" — {r['note']}" if r.get("note") else ""
                usec.append(f"<li>day {r.get('day', '?')}: {r['file']}"
                            f"{flag} <span class=meta>{r['uploaded_at']}"
                            f"{note}</span></li>")
            usec.append("</ul>")
            parts.append("\n".join(usec))

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>nibbanahelp — day by day</title>
<style>
  body {{ background: #fff; color: #000; font-family: Georgia, serif;
         max-width: 38rem; margin: 3rem auto; padding: 0 1.2rem;
         line-height: 1.7; }}
  h1 {{ font-size: 1.1rem; letter-spacing: .15em; text-transform: uppercase;
       border-bottom: 1px solid #000; padding-bottom: .4rem; margin-top: 3rem; }}
  article {{ margin: 2rem 0; }}
  .meta {{ font-size: .8rem; opacity: .6; font-family: monospace; }}
  a {{ color: #000; }}
  code {{ font-size: .85em; }}
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
