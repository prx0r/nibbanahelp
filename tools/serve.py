#!/usr/bin/env python3
"""serve.py — shared nibbanahelp dropbox. Stdlib only, white page.

Writing happens in your notebook. This is just the way in: upload files,
each timestamped at upload time. No backfilling the timeline — old material
is welcome but must be flagged backfill (with an optional note on when it's
from), so the "now" sequence stays honest.

  python3 tools/serve.py                 # http://127.0.0.1:18899
  python3 tools/serve.py --port 18899 --host 127.0.0.1

Uploads live in uploads/, tracked in uploads/manifest.json:
  [{file, uploaded_at (UTC), backfill: bool, note, day}]
day = days since DAY1 (2026-10-28). Backfill keeps its upload day but is
flagged, so readers know the content is older than its position.

WARNING: no auth. Localhost only unless behind login. Anyone with the URL
can upload to the repo.
"""
import json
import re
import subprocess
import sys
from datetime import date, datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import unquote

import importlib.util as _ilu

_site_spec = _ilu.spec_from_file_location(
    "nibsite", Path(__file__).resolve().parent / "site.py")
_nibsite = _ilu.module_from_spec(_site_spec)
_site_spec.loader.exec_module(_nibsite)
header, md = _nibsite.header, _nibsite.md

ROOT = Path(__file__).resolve().parent.parent
UPLOADS = ROOT / "uploads"
MANIFEST = UPLOADS / "manifest.json"
MAX_UPLOAD = 50 * 1024 * 1024
DAY1 = date(2026, 10, 28)

CSS = ("body{background:#fff;color:#000;"
       "font-family:'Cormorant Garamond','Tiro Devanagari Sanskrit',Georgia,serif;"
       "font-size:1.2rem;"
       "max-width:38rem;margin:3rem auto;padding:0 1.2rem;line-height:1.8}"
       "h1{font-size:1.1rem;letter-spacing:.15em;text-transform:uppercase;"
       "border-bottom:1px solid #000;padding-bottom:.4rem;margin-top:3rem}"
       "h2{font-weight:500}"
       "article{margin:2rem 0}.meta{font-size:.8rem;opacity:.6;"
       "font-family:monospace}a{color:#000}"
       "input[type=text]{width:100%;font-family:Georgia,serif;font-size:1rem;"
       "border:1px solid #000;padding:.5rem;background:#fff;color:#000}"
       "button{background:#000;color:#fff;border:0;padding:.6rem 1.2rem;"
       "font-size:1rem;cursor:pointer}form{margin:2rem 0}"
       "label{display:block;margin:1rem 0 .3rem}.backfill{color:#000;"
       "border:1px solid #000;padding:0 .4rem;font-size:.75rem}")


def manifest() -> list:
    if MANIFEST.is_file():
        try:
            return json.loads(MANIFEST.read_text())
        except json.JSONDecodeError:
            return []
    return []


def save_manifest(rows: list):
    UPLOADS.mkdir(exist_ok=True)
    MANIFEST.write_text(json.dumps(rows, indent=1) + "\n")


def day_of(when: date) -> int:
    return max(1, (when - DAY1).days + 1)


def page():
    days = {}
    for pat in ("entries/*.md", "essays/*.md"):
        for p in sorted(ROOT.glob(pat)):
            if p.name.startswith("_"):
                continue
            h, body = header(p)
            if "day" in h:
                days.setdefault(h["day"], []).append((p, h, body))
    out = ["<h1>nibbanahelp — day by day</h1>",
           "<p class=meta>shared second brain of diaries. public by "
           "practice. upload time is the timestamp — old material flagged "
           "backfill.</p>",
           "<h1>Upload</h1>",
           "<form method=post action=/upload enctype=multipart/form-data>"
           "<input type=file name=file><br>"
           "<label><input type=checkbox name=backfill value=1> "
           "backfill — older material (diary notes from before)</label>"
           "<label>Note (optional: when is it from?)"
           " <input type=text name=note></label><br>"
           "<button>upload</button></form>"]
    up_by_day = {}
    for r in manifest():
        up_by_day.setdefault(str(r.get("day", "?")), []).append(r)
    if up_by_day:
        out.append("<h1>Uploaded</h1>")
        for d in sorted(up_by_day, key=lambda x: int(x) if x.isdigit() else 0):
            out.append(f"<h1>Day {d}</h1><ul>")
            for r in up_by_day[d]:
                flag = (" <span class=backfill>backfill</span>"
                        if r.get("backfill") else "")
                note = f" — {r['note']}" if r.get("note") else ""
                out.append(f"<li><a href=\"/files/{r['file']}\">{r['file']}"
                           f"</a>{flag} <span class=meta>{r['uploaded_at']}"
                           f"{note}</span></li>")
            out.append("</ul>")
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
    return ("<!doctype html><html><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            "<link href='https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;1,400&family=Tiro+Devanagari+Sanskrit&display=swap' rel=stylesheet>"
            f"<title>nibbanahelp</title><style>{CSS}</style></head><body>"
            + "".join(out) + "</body></html>")


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
        if self.path != "/upload" or not n or "multipart" not in ctype:
            return self._send("nothing here", 404, "text/plain")
        bm = re.search(r"boundary=([^\s;]+)", ctype)
        if not bm:
            return self._send("no boundary", 400)
        bound = ("--" + bm.group(1)).encode()
        blob, filename, backfill, note = None, None, False, ""
        for ch in raw.split(bound):
            if b"\r\n\r\n" not in ch:
                continue
            head, _, content = ch.partition(b"\r\n\r\n")
            content = content[:-2] if content.endswith(b"\r\n") else content
            nm = re.search(rb'name="([^"]+)"', head)
            if not nm:
                continue
            field = nm.group(1).decode()
            if field == "file":
                fm = re.search(rb'filename="([^"]+)"', head)
                if fm:
                    filename = Path(fm.group(1).decode("utf-8",
                                                       "ignore")).name
                    blob = content
            elif field == "backfill":
                backfill = content.strip() == b"1"
            elif field == "note":
                note = content.decode("utf-8", "ignore").strip()[:200]
        if not filename or filename.startswith(".") or not blob:
            return self._send("no file", 400)
        if len(blob) > MAX_UPLOAD:
            return self._send("too big", 400)
        UPLOADS.mkdir(exist_ok=True)
        dest = UPLOADS / filename
        i = 2
        while dest.exists():
            dest = UPLOADS / f"{dest.stem}-{i}{dest.suffix}"
            i += 1
        dest.write_bytes(blob)
        now = datetime.now(timezone.utc)
        rows = manifest()
        rows.append({"file": dest.name,
                     "uploaded_at": now.isoformat(timespec="seconds"),
                     "backfill": backfill, "note": note,
                     "day": day_of(now.date())})
        save_manifest(rows)
        git("add", f"uploads/{dest.name}", "uploads/manifest.json")
        git("commit", "-q", "-m", f"upload: {dest.name}")
        code, _ = git("push", "-q", "origin", "main")
        extra = "" if code == 0 else " (committed locally, push failed)"
        self._send(f"<p>uploaded: {dest.name} — timestamped "
                   f"{now.isoformat(timespec='seconds')}"
                   f"{' [backfill]' if backfill else ''}{extra}</p>"
                   "<p><a href='/'>back</a></p>")


if __name__ == "__main__":
    host, port = "127.0.0.1", 18899
    for i, a in enumerate(sys.argv[1:]):
        if a == "--port":
            port = int(sys.argv[2 + i])
        if a == "--host":
            host = sys.argv[2 + i]
    print(f"nibbanahelp dropbox on http://{host}:{port} (no auth — "
          f"keep it local)")
    HTTPServer((host, port), H).serve_forever()
