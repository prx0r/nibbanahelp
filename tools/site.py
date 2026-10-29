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


def render(src: str) -> str:
    # Exactly what was written. Only four things render:
    # **bold**, __underline__, *italic*, and # headings as bold.
    # Everything else literal.
    lines = []
    for line in html.escape(src).splitlines():
        m = re.match(r"^#{1,6}\s+(.*)", line)
        if m:
            lines.append(f"<strong>{inline3(m.group(1))}</strong>")
        else:
            lines.append(inline3(line))
    return "\n".join(lines)


def raw(src: str) -> str:
    return "<pre>" + render(src) + "</pre>"


def block(anchor: str, fpath: str, body: str) -> str:
    return (f"<span id=\"{anchor}\"></span>"
            f"<pre class=\"blk\" data-f=\"{fpath}\" "
            f"data-raw=\"{html.escape(body, quote=True)}\">"
            f"{render(body)}</pre>")


JS = r"""
function t(id) {
  var e = document.getElementById(id);
  e.style.display = e.style.display === 'none' ? 'block' : 'none';
}
function esc(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
function inline3(s) {
  s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/__(.+?)__/g, '<u>$1</u>');
  s = s.replace(/\*([^\*\n]+)\*/g, '<em>$1</em>');
  return s;
}
function render(src) {
  return esc(src).split('\n').map(function (line) {
    var m = line.match(/^(#{1,6})\s+(.*)$/);
    if (m) return '<strong>' + inline3(m[2]) + '</strong>';
    return inline3(line);
  }).join('\n');
}
document.addEventListener('click', function (e) {
  var pre = e.target.closest ? e.target.closest('pre.blk') : null;
  if (!pre || pre.dataset.open) return;
  pre.dataset.open = '1';
  var ta = document.createElement('textarea');
  ta.rows = Math.max(4, pre.dataset.raw.split('\n').length + 1);
  ta.value = pre.dataset.raw;
  ta.style.width = '100%';
  ta.style.boxSizing = 'border-box';
  var timer = null, dirty = false, lastOk = true, closed = false;
  function swapBack() {
    pre.innerHTML = render(pre.dataset.raw);
    delete pre.dataset.open;
    pre.style.display = '';
    ta.remove();
  }
  function save() {
    var body = new URLSearchParams({ f: pre.dataset.f, body: ta.value });
    fetch('save', { method: 'POST', body: body }).then(function (r) {
      if (!r.ok) throw 0;
      pre.dataset.raw = ta.value;
      lastOk = true;
      ta.style.border = '';
      if (closed) swapBack();
    }).catch(function () { lastOk = false; ta.style.border = '1px solid red'; });
  }
  ta.addEventListener('input', function () {
    dirty = true; lastOk = true; ta.style.border = '';
    clearTimeout(timer);
    timer = setTimeout(function () { if (dirty) { dirty = false; save(); } }, 1200);
  });
  ta.addEventListener('blur', function () {
    clearTimeout(timer);
    if (dirty) { dirty = false; closed = true; save(); }
    else if (lastOk) { swapBack(); }
  });
  pre.style.display = 'none';
  pre.parentNode.insertBefore(ta, pre.nextSibling);
  ta.focus();
});
"""


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


UKIND = {".mp3": "voice", ".wav": "voice", ".m4a": "voice",
         ".ogg": "voice", ".mp4": "video", ".mov": "video",
         ".webm": "video", ".md": "note", ".txt": "note"}


def ukind(name):
    return UKIND.get(Path(name).suffix.lower(), "file")


def daykey(d):
    return int(d) if str(d).isdigit() else 0


def collect():
    days = {}
    for pattern in ("entries/*.md", "essays/*.md"):
        for p in sorted(ROOT.glob(pattern)):
            if p.name.startswith("_"):
                continue
            h, body = header(p)
            if "day" not in h:
                continue
            d = days.setdefault(h["day"], {"entries": [], "essays": [],
                                           "uploads": []})
            kind = "essays" if p.parent.name == "essays" else "entries"
            d[kind].append((p.stem, body, p.relative_to(ROOT).as_posix()))
    man = ROOT / "uploads" / "manifest.json"
    if man.is_file():
        try:
            rows = json.loads(man.read_text())
        except json.JSONDecodeError:
            rows = []
        for r in rows:
            days.setdefault(str(r.get("day", "?")),
                            {"entries": [], "essays": [],
                             "uploads": []})["uploads"].append(r)
    tensions = []
    for p in sorted((ROOT / "tensions").glob("*.md")):
        h, body = header(p)
        if h.get("status") in ("open", "loosening"):
            tensions.append((h.get("id", p.stem), body))
    return days, tensions


def etitle(body):
    m = re.search(r"^#\s+(.+)$", body, re.M)
    return m.group(1).strip() if m else None


def sidebar(days, link_uploads):
    s = ["<div id=nav>"]
    order = sorted(days, key=daykey)
    for i, day in enumerate(order):
        d = days[day]
        kids = []
        for n, (_stem, _body, _rp) in enumerate(d["entries"]):
            label = "notes" if len(d["entries"]) == 1 else f"notes {n + 1}"
            kids.append(f"<a href=\"#d{day}-e{n}\">{label}</a>")
        for n, (_stem, body, _rp) in enumerate(d["essays"]):
            kids.append(f"<a href=\"#d{day}-s{n}\">"
                        f"{etitle(body) or _stem}</a>")
        for r in d["uploads"]:
            kids.append(f"<a href=\"{link_uploads(r['file'])}\">"
                        f"{r['file']}</a>")
        open_style = "" if i == len(order) - 1 else " style='display:none'"
        s.append(f"<button onclick=\"t('k{day}')\">{day}</button>"
                 f"<div id=\"k{day}\"{open_style}>"
                 + "<br>".join(kids) + "</div>")
    s.append("</div>")
    return "\n".join(s)


def content(days):
    out = []
    for day in sorted(days, key=daykey):
        d = days[day]
        for n, (_stem, body, rp) in enumerate(d["entries"]):
            out.append(block(f"d{day}-e{n}", rp, body))
        for n, (_stem, body, rp) in enumerate(d["essays"]):
            out.append(block(f"d{day}-s{n}", rp, body))
    return "\n".join(out)


def tension_blocks(tensions):
    out = []
    for i, (tid, body) in enumerate(tensions):
        out.append(block(f"t{i}", f"tensions/{tid}.md", body))
    return "\n".join(out)


def main():
    import shutil
    days, tensions = collect()
    updir = OUT.parent / "uploads"
    updir.mkdir(exist_ok=True)
    for f in (ROOT / "uploads").glob("*"):
        if f.is_file() and f.name != "manifest.json":
            shutil.copy(f, updir / f.name)
    nav = sidebar(days, lambda fn: f"uploads/{fn}")
    body = content(days) + tension_blocks(tensions)
    motto = ""
    mp = ROOT / "motto.txt"
    if mp.is_file():
        motto = "".join(f"<p class=motto>{html.escape(line)}</p>"
                         for line in mp.read_text().splitlines()
                         if line.strip())

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(PAGE.format(nav=nav, body=body, motto=motto, js=JS))
    print(f"wrote {OUT.relative_to(ROOT)}")


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>nibbanahelp</title>
<style>
  body {{ background: #fff; color: #000; font-family: monospace;
         margin: 0; padding: 0 1rem; }}
  a {{ color: #000; }}
  pre {{ white-space: pre-wrap; font-family: monospace; }}
  #wrap {{ display: flex; }}
  #nav {{ width: 12rem; flex-shrink: 0; padding-top: 1rem; }}
  #nav button {{ display: block; width: 2.2rem; height: 2.2rem;
    background: #fff; color: #000; border: 1px solid #000;
    font-family: monospace; font-size: 1rem; cursor: pointer;
    margin-bottom: .3rem; }}
  #nav div {{ font-size: .8rem; margin-bottom: .6rem; }}
  #main {{ flex: 1; min-width: 0; }}
  .motto {{ color: #888; font-style: italic; }}
  pre.blk {{ cursor: text; }}
  textarea {{ width: 100%; box-sizing: border-box; font-family: monospace;
    font-size: 1rem; }}
</style>
</head>
<body>
{motto}
<div id=wrap>{nav}<div id=main>{body}</div></div>
<script>
{js}
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
