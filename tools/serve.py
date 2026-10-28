#!/usr/bin/env python3
"""serve.py — shared nibbanahelp blog. Stdlib only, white page, black text.

  python3 tools/serve.py                 # http://127.0.0.1:8799
  python3 tools/serve.py --port 8800 --host 127.0.0.1

Read: days, essays, tensions, uploads. Write: form posts a new entry
(entries/day-N-slug.md, visibility public, handle optional) and commits it.
Upload: multipart file form -> uploads/ (basename only, 50 MB cap).

WARNING: no auth. Bind to localhost or put it behind auth. Never expose
openly — anyone with the URL can write to the repo.
"""
import re
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote

import importlib.util as _ilu

_site_spec = _ilu.spec_from_file_location(
    "nibsite", Path(__file__).resolve().parent / "site.py")
_nibsite = _ilu.module_from_spec(_site_spec)
_site_spec.loader.exec_module(_nibsite)
header, md = _nibsite.header, _nibsite.md

ROOT = Path(__file__).resolve().parent.parent
UPLOADS = ROOT / "uploads"
MAX_UPLOAD = 50 * 1024 * 1024

CSS = ("body{background:#fff;color:#000;font-family:Georgia,serif;"
       "max-width:38rem;margin:3rem auto;padding:0 1.2rem;line-height:1.7}"
       "h1{font-size:1.1rem;letter-spacing:.15em;text-transform:uppercase;"
       "border-bottom:1px solid #000;padding-bottom:.4rem;margin-top:3rem}"
       "article{margin:2rem 0}.meta{font-size:.8rem;opacity:.6;"
       "font-family:monospace}a{color:#000}"
       "textarea,input[type=text]{width:100%;font-family:Georgia,serif;"
       "font-size:1rem;border:1px solid #000;padding:.5rem;background:#fff;"
       "color:#000}textarea{min-height:12rem}"
       "button{background:#000;color:#fff;border:0;padding:.6rem 1.2rem;"
       "font-size:1rem;cursor:pointer}form{margin:2rem 0}"
       "label{display:block;margin:1rem 0 .3rem}")


def slug(s: str) -> str:
    s = s.lower().strip().replace(" ", "-")
    s = re.sub(r"[^a-z0-9-]", "", s)[:60] or "untitled"
    return s


def next_day() -> int:
    top = 0
    for pat in ("entries/*.md", "essays/*.md"):
        for p in ROOT.glob(pat):
            if p.name.startswith("_"):
                continue
            h, _ = header(p)
            if h.get("day", "").isdigit():
                top = max(top, int(h["day"]))
    return top + 1


def page():
    days = {}
    for pat in ("entries/*.md", "essays/*.md"):
        for p in sorted(ROOT.glob(pat)):
            if p.name.startswith("_"):
                continue
            h, body = header(p)
            if "day" in h:
                days.setdefault(h["day"], []).append((p, h, body))
    out = []
    for day in sorted(days, key=int):
        out.append(f"<h1>Day {day}</h1>")
        for p, h, body in days[day]:
            kind = "essay" if p.parent.name == "essays" else "entry"
            au = (f' · <a href="/files/{h["audio"]}">spoken</a>'
                  if h.get("audio", "-") not in ("-", "") else "")
            out.append(f"<article><h2>{p.stem}</h2>"
                       f"<div class=meta>{kind} · {h.get('visibility')}{au}"
                       f"</div>{md(body)}</article>")
    out.append("<h1>Open tensions</h1>")
    for p in sorted((ROOT / "tensions").glob("*.md")):
        h, body = header(p)
        if h.get("status") == "open":
            out.append(f"<article><h2>{h.get('id', p.stem)}</h2>"
                       f"<div class=meta>{h.get('summary', '')}</div>"
                       f"{md(body)}</article>")
    files = ""
    if UPLOADS.is_dir():
        names = sorted(p.name for p in UPLOADS.iterdir() if p.is_file())
        if names:
            files = ("<h1>Uploads</h1><ul>" + "".join(
                f'<li><a href="/files/{n}">{n}</a></li>' for n in names)
                + "</ul>")
    nd = next_day()
    return ("<!doctype html><html><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>nibbanahelp</title><style>{CSS}</style></head><body>"
            "<h1>nibbanahelp — day by day</h1>"
            f"<p class=meta>shared repo, public by practice. day {nd} is open."
            "</p>"
            "<h1>Write</h1>"
            "<form method=post action=/save>"
            f"<label>Day <input type=text name=day value='{nd}'></label>"
            "<label>Title <input type=text name=title></label>"
            "<label>Handle (optional, blank = anonymous)"
            " <input type=text name=handle></label>"
            "<label>Entry <textarea name=body></textarea></label>"
            "<button>save to the diary</button></form>"
            "<h1>Upload</h1>"
            "<form method=post action=/upload enctype=multipart/form-data>"
            "<input type=file name=file><br><br>"
            "<button>upload</button></form>"
            + "".join(out) + files + "</body></html>")


def git(*args):
    r = subprocess.run(["git", "-C", str(ROOT), *args],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr)[-500:]


class H(BaseHTTPRequestHandler):
    server_version = "nibbanahelp/0"
    def log_message(self, *a):
        pass

    def _send(self, body: str | bytes, code=200, ctype="text/html"):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self._send(page())
        elif self.path.startswith("/files/"):
            name = unquote(self.path[len("/files/"):])
            if "/" in name or name.startswith("."):
                return self._send("no", 400, "text/plain")
            p = UPLOADS / name
            if not p.is_file():
                return self._send("missing", 404, "text/plain")
            ctype = "application/octet-stream"
            if p.suffix == ".mp3":
                ctype = "audio/mpeg"
            elif p.suffix in (".md", ".txt"):
                ctype = "text/plain"
            self._send(p.read_bytes(), 200, ctype)
        else:
            self._send("nothing here", 404, "text/plain")

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        ctype = self.headers.get("Content-Type", "")
        raw = self.rfile.read(n) if n else b""
        if self.path == "/save" and n and "urlencoded" in ctype:
            f = parse_qs(raw.decode())
            title = (f.get("title", ["untitled"])[0] or "untitled").strip()
            day = (f.get("day", ["1"])[0] or "1").strip()
            if not day.isdigit():
                day = "1"
            handle = (f.get("handle", [""])[0] or "").strip() or "anonymous"
            body = (f.get("body", [""])[0] or "").strip()
            if not body:
                return self._send("empty — nothing saved", 400)
            dest = ROOT / "entries" / f"day-{day}-{slug(title)}.md"
            i = 2
            while dest.exists():
                dest = ROOT / "entries" / f"day-{day}-{slug(title)}-{i}.md"
                i += 1
            dest.write_text(f"day: {day}\nvisibility: public\n"
                            f"diarist: {handle}\n---\n# {title}\n\n{body}\n")
            git("add", dest.name if False else str(dest.relative_to(ROOT)))
            git("commit", "-q", "-m", f"diary: day {day} {dest.stem}")
            code, _ = git("push", "-q", "origin", "main")
            note = "" if code == 0 else " (push failed — committed locally)"
            self._send(f"<p>saved: {dest.name}{note}</p>"
                       "<p><a href='/'>back</a></p>")
        elif self.path == "/upload" and n and "multipart" in ctype:
            bm = re.search(r"boundary=([^\s;]+)", ctype)
            if not bm:
                return self._send("no boundary", 400)
            bound = ("--" + bm.group(1)).encode()
            saved = None
            for ch in raw.split(bound):
                if b'filename="' not in ch:
                    continue
                head, sep, blob = ch.partition(b"\r\n\r\n")
                if not sep:
                    continue
                m = re.search(rb'filename="([^"]+)"', head)
                if not m:
                    continue
                name = Path(m.group(1).decode("utf-8", "ignore")).name
                if not name or name.startswith("."):
                    continue
                blob = blob[:-2] if blob.endswith(b"\r\n") else blob
                if not blob or len(blob) > MAX_UPLOAD:
                    continue
                UPLOADS.mkdir(exist_ok=True)
                (UPLOADS / name).write_bytes(blob)
                saved = name
                break
            if not saved:
                return self._send("no file", 400)
            git("add", f"uploads/{saved}")
            git("commit", "-q", "-m", f"upload: {saved}")
            git("push", "-q", "origin", "main")
            self._send(f"<p>uploaded: {saved}</p><p><a href='/'>back</a></p>")
        else:
            self._send("nothing here", 404, "text/plain")


if __name__ == "__main__":
    host, port = "127.0.0.1", 8799
    for i, a in enumerate(sys.argv[1:]):
        if a == "--port":
            port = int(sys.argv[2 + i])
        if a == "--host":
            host = sys.argv[2 + i]
    print(f"nibbanahelp on http://{host}:{port} (localhost only unless "
          f"--host set — no auth, keep it private)")
    HTTPServer((host, port), H).serve_forever()
