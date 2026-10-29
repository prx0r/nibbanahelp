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
function up(day){
  var i=document.createElement('input');
  i.type='file';
  i.onchange=function(){
    if(!this.files.length)return;
    var f=this.files[0];
    var isText=/\.(md|txt)$/i.test(f.name);
    var box=document.createElement('div');
    var lab=document.createElement('p');
    lab.textContent=f.name+(isText?' — pick a kind:':'');
    box.appendChild(lab);
    var sel=null;
    if(isText){
      sel=document.createElement('select');
      ['diary','essay','poem'].forEach(function(k){
        var o=document.createElement('option');o.value=k;o.textContent=k;
        sel.appendChild(o);});
      box.appendChild(sel);
    }
    var btn=document.createElement('button');
    btn.textContent='upload';
    var st=document.createElement('span');
    box.appendChild(btn);
    box.appendChild(document.createTextNode(' '));
    box.appendChild(st);
    btn.onclick=function(){
      var fd=new FormData();
      fd.append('file',f);
      fd.append('day',String(day));
      var today=parseInt(document.body.getAttribute('data-today')||'1',10);
      if(day<today)fd.append('backfill','1');
      if(sel)fd.append('kind',sel.value);
      st.textContent='uploading\u2026';
      fetch('upload',{method:'POST',body:fd}).then(function(r){
        if(!r.ok)throw 0;
        return r.text();
      }).then(function(){
        st.textContent='uploaded'+(sel?' ('+sel.value+')':'')+' \u2014 reloading\u2026';
        setTimeout(function(){location.reload();},1200);
      }).catch(function(){st.textContent='upload failed, try again';});
    };
    document.getElementById('nav').appendChild(box);
  };
  i.click();
}

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
    for key in ("roots", "factors", "factors_growing"):
        m = re.search(rf"^{key}:\s*\[(.+?)\]\s*$", head, re.M)
        if m:
            out[key] = [x.strip() for x in m.group(1).split(",") if x.strip()]
    body = text.split("---", 1)[1] if "---" in text else text
    return out, body.strip()


def card(title, meta, body_html):
    return (f'<article><h2>{html.escape(title)}</h2>'
            f'<div class="meta">{meta}</div>{body_html}</article>')


UKIND = {".mp3": "audio", ".wav": "audio", ".m4a": "audio",
         ".ogg": "audio", ".mp4": "video", ".mov": "video",
         ".webm": "video", ".md": "essay", ".txt": "essay"}


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
            tensions.append({"id": h.get("id", p.stem),
                             "summary": h.get("summary", ""),
                             "status": h.get("status"),
                             "roots": h.get("roots", []),
                             "factors": h.get("factors", []),
                             "factors_growing": h.get("factors_growing", []),
                             "body": body})
    return days, tensions


def sidebar(days, link_uploads):
    s = ["<div id=nav>",
         "<a href=\"/chat\">chat</a><br><a href=\"/vis\">vis</a><br><br>"]
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
            kind = r.get("kind") or ukind(r["file"])
            kids.append(f"{kind} "
                        f"<a href=\"{link_uploads(r['file'])}\">"
                        f"{r['file']}</a>")
        s.append(f"<button class=daybox onclick=\"t('k{day}')\">{day}</button>"
                 f"<div id=\"k{day}\">"
                 + "<br>".join(kids) + "</div>"
                 + f"<p><a href=\"#\" onclick=\"up({day});return false\">+</a></p>")
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
    for i, t in enumerate(tensions):
        out.append(block(f"t{i}", f"tensions/{t['id']}.md", t["body"],
                         viewer=False))
    return "\n".join(out)


ROOTS = [("lobha", "greed"), ("dosa", "hate"), ("moha", "delusion")]


def chat_counts():
    """sessions/chat-*.json relayed tension ids -> count per tension stem."""
    out = {}
    for p in sorted((ROOT / "sessions").glob("chat-*.json")):
        try:
            rec = json.loads(p.read_text())
        except (ValueError, OSError):
            continue
        for rid in rec.get("relayed", []):
            s = str(rid).split(":")[-1].replace("tension-", "")
            s = s.replace(".md", "").rsplit("/", 1)[-1]
            out[s] = out.get(s, 0) + 1
    return out


def build_vis(days, tensions):
    chats = chat_counts()
    w = {r: 0.0 for r, _ in ROOTS}
    for t in tensions:
        wt = 1.0 if t["status"] == "open" else 0.6
        wt += 0.15 * chats.get(t["id"], 0)
        for r in t["roots"]:
            if r in w:
                w[r] += wt
    xs = {"lobha": 150, "dosa": 400, "moha": 650}
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 560"'
             ' style="max-width:100%;height:auto" font-family="monospace">']
    parts.append("<text x=\"400\" y=\"24\" text-anchor=\"middle\" "
                 "font-size=\"14\">afflictions, live</text>")
    n_live = sum(1 for t in tensions if t["status"] == "open")
    parts.append(f"<text x=\"400\" y=\"42\" text-anchor=\"middle\" "
                 f"font-size=\"11\">{n_live} open threads, "
                 f"{len(tensions) - n_live} loosening</text>")
    for r, en in ROOTS:
        rad = 30 + 18 * w[r]
        parts.append(f"<circle cx=\"{xs[r]}\" cy=\"130\" r=\"{rad:.0f}\" "
                     f"fill=\"none\" stroke=\"black\" stroke-width=\"2\"/>")
        parts.append(f"<text x=\"{xs[r]}\" y=\"126\" text-anchor=\"middle\" "
                     f"font-size=\"13\">{r}</text>")
        parts.append(f"<text x=\"{xs[r]}\" y=\"142\" text-anchor=\"middle\" "
                     f"font-size=\"10\">{en} · {w[r]:.1f}</text>")
    groups = {}
    for t in tensions:
        primary = next((r for r in t["roots"] if r in xs), None) or "moha"
        groups.setdefault(primary, []).append(t)
    for r, ts in groups.items():
        for i, t in enumerate(ts):
            x = xs[r] + (i - (len(ts) - 1) / 2) * 120
            y = 300
            for pr in t["roots"]:
                if pr not in xs:
                    continue
                dash = "" if pr == r else ' stroke-dasharray="4,3"'
                parts.append(f"<line x1=\"{xs[pr]}\" "
                             f"y1=\"{130 + 30 + 18 * w[pr]:.0f}\" "
                             f"x2=\"{x}\" y2=\"{y - 8}\"{dash} "
                             f"stroke=\"black\" stroke-width=\"1\"/>")
        parts.append(f"<circle cx=\"{x}\" cy=\"{y}\" r=\"9\" "
                     f"fill=\"black\"/>")
        parts.append(f"<text x=\"{x}\" y=\"{y + 26}\" text-anchor=\"middle\" "
                     f"font-size=\"10\">{html.escape(t['id'])}</text>")
        sub = t["status"] + (f" · {chats.get(t['id'], 0)} chats" if chats.get(t["id"]) else "")
        parts.append(f"<text x=\"{x}\" y=\"{y + 38}\" text-anchor=\"middle\" "
                     f"font-size=\"9\">{html.escape(sub)}</text>")
        fac = ", ".join(t.get("factors", []))
        if fac:
            parts.append(f"<text x=\"{x}\" y=\"{y + 50}\" text-anchor=\"middle\" "
                         f"font-size=\"8\">{html.escape(fac[:44])}</text>")
            if len(fac) > 44:
                parts.append(f"<text x=\"{x}\" y=\"{y + 60}\" text-anchor=\"middle\" "
                             f"font-size=\"8\">{html.escape(fac[44:88])}</text>")
    # decode strip: the 14 unwholesome, lit where present across live tensions
    ALL14 = [("moha", "moha"), ("ahirika", "ahir"), ("anottappa", "anot"),
             ("uddhacca", "uddh"), ("lobha", "lobha"), ("diṭṭhi", "ditthi"),
             ("māna", "mana"), ("dosa", "dosa"), ("issā", "issa"),
             ("macchariya", "macch"), ("kukkucca", "kukk"),
             ("thīna", "thina"), ("middha", "midd"), ("vicikicchā", "vici")]
    counts, grow = {}, {}
    for t in tensions:
        for f in t.get("factors", []):
            counts[f] = counts.get(f, 0) + 1
        for f in t.get("factors_growing", []):
            grow[f] = grow.get(f, 0) + 1
    parts.append("<text x=\"400\" y=\"430\" text-anchor=\"middle\" "
                 "font-size=\"11\">the 14 unwholesome — lit where present "
                 "(decode, roots/cetasikas-decode.md)</text>")
    for i, (fac, ab) in enumerate(ALL14):
        cx = 20 + (i % 7) * 110
        cy = 448 + (i // 7) * 44
        n = counts.get(fac, 0)
        parts.append(f"<rect x=\"{cx}\" y=\"{cy}\" width=\"100\" height=\"26\" "
                     f"fill=\"{'black' if n else 'white'}\" stroke=\"black\"/>")
        parts.append(f"<text x=\"{cx + 50}\" y=\"{cy + 16}\" "
                     f"text-anchor=\"middle\" font-size=\"10\" "
                     f"fill=\"{'white' if n else 'black'}\">"
                     f"{html.escape(ab)} ×{n}</text>")
    gl = ", ".join(f"{k}×{v}" for k, v in sorted(grow.items()))
    parts.append(f"<text x=\"400\" y=\"548\" text-anchor=\"middle\" "
                 f"font-size=\"9\">growing: {html.escape(gl or '—')}</text>")
    parts.append("</svg>")
    return "\n".join(parts)


CHAT_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>nibbanahelp chat</title>
<style>
  body { background: #fff; color: #000; font-family: monospace;
         margin: 0; padding: 0 1rem; max-width: 44rem; }
  a { color: #000; }
  #log p { white-space: pre-wrap; }
  .you { color: #555; }
  form { display: flex; gap: .5rem; margin: 1rem 0; }
  input { flex: 1; font-family: monospace; font-size: 1rem;
    border: 1px solid #000; padding: .5rem; }
  button { background: #000; color: #fff; border: 0; padding: .5rem 1rem;
    font-size: 1rem; cursor: pointer; }
</style>
</head>
<body>
<p><a href="/">diary</a> · <a href="/vis">vis</a></p>
<div id=log></div>
<form id=f><input id=q autocomplete=off placeholder="what is on your mind?"><button>send</button></form>
<script>
var transcript = [];
var log = document.getElementById('log');
var sid = Math.random().toString(36).slice(2, 10);
function say(who, text) {
  var p = document.createElement('p');
  if (who === 'you') p.className = 'you';
  p.textContent = (who === 'you' ? '> ' : '') + text;
  log.appendChild(p);
  window.scrollTo(0, document.body.scrollHeight);
}
document.getElementById('f').addEventListener('submit', function (e) {
  e.preventDefault();
  var box = document.getElementById('q');
  var text = box.value.trim();
  if (!text) return;
  box.value = '';
  say('you', text);
  transcript.push({ role: 'user', content: text });
  fetch('chat', { method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sid: sid, messages: transcript.slice(-12) }) }).then(function (r) {
    if (!r.ok) throw 0;
    return r.json();
  }).then(function (d) {
    (d.sources || []).forEach(function (s) {
      var p = document.createElement('p');
      p.textContent = 'similar: ' + s.label;
      log.appendChild(p);
      if (s.excerpt) {
        var q = document.createElement('p');
        q.textContent = '\u201c' + s.excerpt + '\u201d' + (s.url ? ' — ' + s.url : '');
        log.appendChild(q);
      }
      if (s.youtube && /^[A-Za-z0-9_-]{6,}$/.test(s.youtube)) {
        var start = s.start || 0;
        var mm = Math.floor(start / 60), ss = ('0' + (start % 60)).slice(-2);
        var wbtn = document.createElement('button');
        wbtn.textContent = '\u25b6 watch from ' + mm + ':' + ss;
        wbtn.style.cssText = 'background:#000;color:#fff;border:0;padding:.3rem .8rem;font-size:.85rem;cursor:pointer;margin:.2rem 0';
        var wp = document.createElement('p');
        wp.appendChild(wbtn);
        log.appendChild(wp);
        wbtn.addEventListener('click', function () {
          if (window.__vid) window.__vid.remove();
          var holder = document.createElement('div');
          var f = document.createElement('iframe');
          f.width = '100%'; f.height = '220'; f.allowFullscreen = true;
          f.src = 'https://www.youtube-nocookie.com/embed/' + s.youtube +
                  '?start=' + start + '&rel=0';
          holder.appendChild(f);
          wp.appendChild(holder);
          window.__vid = holder;
          wbtn.remove();
        });
        return;
      }
      if (s.url && s.url.indexOf('http') === 0) {
        var a = document.createElement('a');
        a.href = s.url; a.textContent = '→ ' + s.label;
        a.target = '_blank'; a.rel = 'noopener';
        var w = document.createElement('p');
        w.appendChild(a); log.appendChild(w);
      }
    });
    say('ai', d.reply);
    transcript.push({ role: 'assistant', content: d.reply });
    window.scrollTo(0, document.body.scrollHeight);
  }).catch(function () { say('ai', '[offline mirror — connect to talk]'); });
});
</script>
</body>
</html>"""


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
    today = (max((int(d) for d in days if str(d).isdigit()), default=0) + 1)
    OUT.write_text(PAGE.format(nav=nav, body=body, motto=motto, js=JS,
                               gap=GAP, today=today))
    print(f"wrote {OUT.relative_to(ROOT)}")
    (OUT.parent / "chat.html").write_text(CHAT_PAGE)
    print("wrote site/chat.html")
    vis_body = build_vis(days, tensions)
    (OUT.parent / "vis.html").write_text(
        "<!doctype html><html><head><meta charset=utf-8>"
        "<meta name=viewport content='width=device-width,initial-scale=1'>"
        "<title>nibbanahelp vis</title><style>"
        "body{background:#fff;color:#000;font-family:monospace;"
        "margin:0 auto;padding:0 1rem;max-width:60rem;text-align:center}"
        "a{color:#000}svg{display:inline-block}</style></head><body>"
        "<p><a href='/'>diary</a> · <a href='/chat'>chat</a></p>"
        + vis_body + "</body></html>")
    print("wrote site/vis.html")


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
<body data-today="{today}">
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
