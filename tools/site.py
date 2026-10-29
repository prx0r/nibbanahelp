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

# Proportions: left screen edge to squares == squares to main body.
# One value. Everything derives from it.
GAP = "1rem"


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


SHADES = ["#333", "#555", "#777", "#999", "#bbb"]
MAX_MOTTO = 5


def motto_html(text: str) -> str:
    lines = [l for l in text.splitlines() if l.strip()][:MAX_MOTTO]
    n = len(lines)
    out = []
    for i, ln in enumerate(lines):
        c = SHADES[min(n - 1 - i, 4)]
        out.append(f"<div class=motto-line><p class=motto "
                   f"style=\"color:{c}\">\"{inline3(html.escape(ln))}\"</p>"
                   f"</div>")
    return "\n".join(out)


def motto_block() -> str:
    mp = ROOT / "motto.txt"
    if not mp.is_file():
        return ""
    text = mp.read_text().strip()
    return (f'<div class="motto-blk" data-f="motto.txt" data-kind="motto" '
            f'data-raw="{html.escape(text, quote=True)}">'
            + motto_html(text) + "</div>")


def block(anchor: str, fpath: str, body: str, viewer: bool = True) -> str:
    pre = (f"<pre class=\"blk\" data-f=\"{fpath}\" "
           f"data-raw=\"{html.escape(body, quote=True)}\">"
           f"{render(body)}</pre>")
    if not viewer:
        return pre
    return (f"<div data-blk=\"{anchor}\">"
            f"<span id=\"{anchor}\"></span>{pre}</div>")


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
function renderMotto(src) {
  var shades = ['#333', '#555', '#777', '#999', '#bbb'];
  var lines = esc(src).split('\n').filter(function (l) { return l.trim() !== ''; }).slice(0, 5);
  var n = lines.length;
  return lines.map(function (ln, i) {
    var c = shades[Math.min(n - 1 - i, 4)];
    return '<div class=motto-line><p class=motto style="color:' + c + '">"' + inline3(ln) + '"</p></div>';
  }).join('\n');
}
function renderFor(el, text) {
  return el.dataset.kind === 'motto' ? renderMotto(text) : render(text);
}
function show(id) {
  if (window.__editing) {
    var ae = document.activeElement;
    if (ae && ae.tagName === 'TEXTAREA') ae.blur();
    if (window.__editing) return;
  }
  var blocks = document.querySelectorAll('#main [data-blk]');
  for (var i = 0; i < blocks.length; i++) {
    blocks[i].style.display = blocks[i].dataset.blk === id ? '' : 'none';
  }
  try { localStorage.setItem('nib-last', id); } catch (e) {}
}
document.addEventListener('click', function (e) {
  var sh = e.target.closest ? e.target.closest('[data-show]') : null;
  if (sh) { e.preventDefault(); show(sh.dataset.show); return; }
  var el = e.target.closest ? e.target.closest('[data-f]') : null;
  if (!el || el.dataset.open) return;
  e.preventDefault();
  if (e.stopPropagation) e.stopPropagation();
  window.__editing = true;
  el.dataset.open = '1';
  var raw = el.dataset.raw;
  var cs = window.getComputedStyle(el);
  var prevPos = el.style.position;
  if (cs.position === 'static') el.style.position = 'relative';
  var ta = document.createElement('textarea');
  ta.value = raw;
  ta.style.position = 'absolute';
  ta.style.top = '0';
  ta.style.left = '0';
  ta.style.width = '100%';
  ta.style.height = '100%';
  ta.style.boxSizing = 'border-box';
  ta.style.margin = '0';
  ta.style.padding = '0';
  ta.style.border = '0';
  ta.style.outline = 'none';
  ta.style.background = 'transparent';
  ta.style.resize = 'none';
  ta.style.overflow = 'auto';
  ta.style.visibility = 'visible';
  ta.style.whiteSpace = 'pre-wrap';
  ta.style.fontFamily = cs.fontFamily;
  ta.style.fontSize = cs.fontSize;
  ta.style.lineHeight = cs.lineHeight;
  ta.style.fontStyle = cs.fontStyle;
  ta.style.fontWeight = cs.fontWeight;
  ta.style.visibility = 'visible';
  var timer = null, dirty = false, lastOk = true, closed = false;
  function swapBack() {
    el.innerHTML = renderFor(el, el.dataset.raw);
    delete el.dataset.open;
    window.__editing = false;
    el.style.visibility = '';
    el.style.position = prevPos;
    ta.remove();
  }
  function save() {
    var body = new URLSearchParams({ f: el.dataset.f, body: ta.value });
    fetch('save', { method: 'POST', body: body }).then(function (r) {
      if (!r.ok) throw 0;
      el.dataset.raw = ta.value;
      lastOk = true;
      ta.style.outline = 'none';
      if (closed) swapBack();
    }).catch(function () { lastOk = false; ta.style.outline = '1px solid red'; });
  }
  ta.addEventListener('input', function () {
    dirty = true; lastOk = true; ta.style.outline = 'none';
    clearTimeout(timer);
    timer = setTimeout(function () { if (dirty) { dirty = false; save(); } }, 1200);
  });
  ta.addEventListener('blur', function () {
    clearTimeout(timer);
    if (dirty) { dirty = false; closed = true; save(); }
    else if (lastOk) { swapBack(); }
  });
  el.style.visibility = 'hidden';
  el.appendChild(ta);
  try { ta.focus({ preventScroll: true }); } catch (e) { ta.focus(); }
});
(function initViewer() {
  var blocks = document.querySelectorAll('#main [data-blk]');
  if (!blocks.length) return;
  var last = null;
  try { last = localStorage.getItem('nib-last'); } catch (e) {}
  var ok = false;
  for (var i = 0; i < blocks.length; i++) {
    if (blocks[i].dataset.blk === last) { ok = true; break; }
  }
  show(ok ? last : blocks[blocks.length - 1].dataset.blk);
})();
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
              "summary", "kind"):
        m = re.search(rf"^{k}:\s*(.+)$", head, re.M)
        if m:
            out[k] = m.group(1).strip()
    body = text.split("---", 1)[1] if "---" in text else text
    return out, body.strip()


def card(title, meta, body_html):
    return (f'<article><h2>{html.escape(title)}</h2>'
            f'<div class="meta">{meta}</div>{body_html}</article>')


UKIND = {".mp3": "audio", ".wav": "audio", ".m4a": "audio",
         ".ogg": "audio", ".mp4": "video", ".mov": "video",
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
            ek = h.get("kind", "essay") if kind == "essays" else ""
            d[kind].append((p.stem, body, p.relative_to(ROOT).as_posix(),
                            ek))
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


def sidebar(days, link_uploads):
    s = ["<div id=nav>"]
    order = sorted(days, key=daykey)
    for i, day in enumerate(order):
        d = days[day]
        kids = []
        for n, (_stem, _body, _rp, _ek) in enumerate(d["entries"]):
            kids.append(f"<a href=\"#\" data-show=\"d{day}-e{n}\">diary</a>")
        for n, (_stem, _body, _rp, ek) in enumerate(d["essays"]):
            kids.append(f"<a href=\"#\" data-show=\"d{day}-s{n}\">"
                        f"{ek or 'essay'}</a>")
        for r in d["uploads"]:
            kids.append(f"<a href=\"{link_uploads(r['file'])}\">"
                        f"{ukind(r['file'])}</a>")
        s.append(f"<button class=daybox onclick=\"t('k{day}')\">{day}</button>"
                 f"<div id=\"k{day}\">"
                 + "<br>".join(kids) + "</div>")
    s.append("</div>")
    return "\n".join(s)


def content(days):
    out = []
    for day in sorted(days, key=daykey):
        d = days[day]
        for n, (_stem, body, rp, _ek) in enumerate(d["entries"]):
            out.append(block(f"d{day}-e{n}", rp, body))
        for n, (_stem, body, rp, _ek) in enumerate(d["essays"]):
            out.append(block(f"d{day}-s{n}", rp, body))
    return "\n".join(out)


def tension_blocks(tensions):
    out = []
    for i, (tid, body) in enumerate(tensions):
        out.append(block(f"t{i}", f"tensions/{tid}.md", body, viewer=False))
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
    motto = motto_block()

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(PAGE.format(nav=nav, body=body, motto=motto, js=JS,
                               gap=GAP))
    print(f"wrote {OUT.relative_to(ROOT)}")


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>nibbanahelp</title>
<style>
  body {{ background: #fff; color: #000; font-family: monospace;
         margin: 0; padding: 0 {gap}; }}
  a {{ color: #000; }}
  pre {{ white-space: pre-wrap; font-family: monospace; }}
  #wrap {{ display: flex; }}
  #nav {{ flex-shrink: 0; padding-top: 1rem; padding-right: {gap};
    font-size: .8rem; }}
  #nav .daybox {{ display: flex; align-items: center; justify-content: center;
    width: 2.2rem; height: 2.2rem;
    background: #fff; color: #000; border: 1px solid #000;
    font-family: monospace; font-size: 1rem; cursor: pointer;
    margin-bottom: .3rem; padding: 0; }}
  #nav div {{ margin-bottom: .6rem; }}
  #nav div a {{ display: block; padding: .15rem 0; }}
  body {{ touch-action: manipulation; }}
  #main {{ flex: 1; min-width: 0; }}
  pre.blk {{ width: fit-content; max-width: 100%; cursor: text; }}
  .motto-blk {{ text-align: center; cursor: default; }}
  .motto-line {{ text-align: center; }}
  .motto {{ display: inline-block; font-style: italic; text-align: center;
    cursor: text; }}
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
