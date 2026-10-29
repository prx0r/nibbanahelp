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
import html
import json
import re
import subprocess
import sys
from datetime import date, datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import quote, unquote

import importlib.util as _ilu

_site_spec = _ilu.spec_from_file_location(
    "nibsite", Path(__file__).resolve().parent / "site.py")
_nibsite = _ilu.module_from_spec(_site_spec)
_site_spec.loader.exec_module(_nibsite)
header, raw, collect, sidebar, content, tension_blocks, JS, motto_block, GAP, build_vis, CHAT_PAGE = (
    _nibsite.header, _nibsite.raw, _nibsite.collect, _nibsite.sidebar,
    _nibsite.content, _nibsite.tension_blocks, _nibsite.JS,
    _nibsite.motto_block, _nibsite.GAP, _nibsite.build_vis,
    _nibsite.CHAT_PAGE)

ROOT = Path(__file__).resolve().parent.parent
UPLOADS = ROOT / "uploads"
MANIFEST = UPLOADS / "manifest.json"
MAX_UPLOAD = 50 * 1024 * 1024
DAY1 = date(2026, 10, 28)

CSS = ("body{background:#fff;color:#000;"
       "font-family:monospace;"
       "margin:0;padding:0 " + GAP + "}"
       "a{color:#000}"
       "pre{white-space:pre-wrap;font-family:monospace}"
       "pre.blk{width:fit-content;max-width:100%;cursor:text}"
       ".motto-blk{text-align:center;cursor:default}"
       ".motto-line{text-align:center}"
       ".motto{display:inline-block;font-style:italic;text-align:center;cursor:text}"
       "#wrap{display:flex}"
       "#nav{flex-shrink:0;padding-top:1rem;padding-right:" + GAP + ";"
       "font-size:.8rem}"
       "#nav .daybox{display:flex;align-items:center;justify-content:center;width:2.2rem;height:2.2rem;"
       "background:#fff;color:#000;border:1px solid #000;"
       "font-family:monospace;font-size:1rem;"
       "margin-bottom:.3rem}"
       "#nav div{margin-bottom:.6rem}"
       "#nav div a{display:block;padding:.15rem 0}"
       "body{touch-action:manipulation}"
       "#main{flex:1;min-width:0}"
       
       "input[type=text]{width:100%;font-family:monospace;font-size:1rem;"
       "border:1px solid #000;padding:.5rem;background:#fff;color:#000}"
       "textarea{width:100%;box-sizing:border-box;font-family:monospace;"
       "font-size:1rem;border:1px solid #000;padding:.5rem;background:#fff;"
       "color:#000}"
       "button{background:#000;color:#fff;border:0;padding:.6rem 1.2rem;"
       "font-size:1rem;cursor:pointer}form{margin:2rem 0}"
       "label{display:block;margin:1rem 0 .3rem}")


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


def entry_files():
    out = []
    for p in sorted(ROOT.glob("entries/*.md")):
        if p.name.startswith("_"):
            continue
        h, _ = header(p)
        if h.get("day", "").isdigit():
            out.append((int(h["day"]), p))
    return sorted(out)


def page():
    days, tensions = collect()
    motto = motto_block()
    forms = ["<form method=post action=/upload enctype=multipart/form-data>"
             "<input type=file name=file><br>"
             "<label><input type=checkbox name=backfill value=1> "
             "backfill</label>"
             "<label>note <input type=text name=note></label><br>"
             "<button>upload</button></form>",
             "<form method=post action=/new-day>"
             "<button>submit — start a new day</button></form>"]
    nav = sidebar(days, lambda fn: f"/files/{fn}")
    body = content(days) + tension_blocks(tensions)
    main = motto + "\n".join(forms) + body
    return ("<!doctype html><html><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>nibbanahelp</title><style>{CSS}</style></head><body>"
            f"<div id=wrap>{nav}<div id=main>{main}</div></div>"
            f"<script>{JS}</script></body></html>")


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

    def safe_file(self, f: str):
        if ".." in f or f.startswith("/") or not f.endswith(".md"):            return None
        if not (f.startswith("entries/") or f.startswith("essays/") or
                f.startswith("tensions/") or f == "motto.txt"):
            return None
        p = ROOT / f
        return p if p.is_file() else None

    def do_GET(self):
        if self.path == "/":
            self._send(page())
        elif self.path == "/vis":
            days, tensions = collect()
            self._send("<!doctype html><html><head><meta charset=utf-8>"
                       "<meta name=viewport content='width=device-width,"
                       "initial-scale=1'>"
                       "<title>nibbanahelp vis</title><style>"
                       "body{background:#fff;color:#000;font-family:monospace;"
                       "margin:0;padding:0 1rem;max-width:60rem}"
                       "a{color:#000}</style></head><body>"
                       "<p><a href='/'>diary</a> · <a href='/chat'>chat</a></p>"
                       + build_vis(days, tensions) + "</body></html>")
        elif self.path == "/chat":
            self._send(CHAT_PAGE, 200, "text/html")
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
        if self.path == "/chat" and n and "json" in ctype:
            import json as _json
            try:
                data = _json.loads(raw.decode())
            except ValueError:
                return self._send("bad json", 400)
            msgs = data.get("messages", [])[-12:]
            if not msgs or not isinstance(msgs, list):
                return self._send("no messages", 400)
            clean = [m for m in msgs if m.get("role") in ("user", "assistant")]
            if not clean or clean[-1].get("role") != "user":
                return self._send("no question", 400)
            relay, sources = [], []
            try:
                from ai import (chat as _aichat, embed_batch as _emb,
                                rerank as _rr, CHAT_SYSTEM)
                import numpy as _np
                global _RELAY
                try:
                    _RELAY
                except NameError:
                    _RELAY = None
                if _RELAY is None:
                    _items = _json.loads((ROOT / "corpus" / "index.json").read_text())
                    _vecs = _json.loads((ROOT / "corpus" / "vectors.json").read_text())
                    _mat = _np.array([_vecs[i["id"]] for i in _items], dtype=_np.float32)
                    _mat = _mat / (_np.linalg.norm(_mat, axis=1, keepdims=True) + 1e-9)
                    _RELAY = (_items, _mat)
                _items, _mat = _RELAY
                _q = _np.array(_emb([clean[-1]["content"][:2000]])[0], dtype=_np.float32)
                _q = _q / (_np.linalg.norm(_q) + 1e-9)
                _order = _np.argsort(-(_mat @ _q))[:20]
                _cands = [_items[int(i)] for i in _order]
                for _i in _rr(clean[-1]["content"], [c["text"][:1000] for c in _cands])[:5]:
                    relay.append(_cands[_i])
                sources = [{"label": r["label"], "url": r["url"]} for r in relay]
            except Exception as e:
                print("relay unavailable:", str(e)[:200])
            try:
                from ai import chat as _aichat, CHAT_SYSTEM
                rb = ("\n\nSIMILAR LIVED PASSAGES (relay these with their "
                      "sources, never invent advice):\n" + "\n".join(
                      f"- [{r['kind']}] {r['label']} :: {r['url']}\n"
                      f"  {r['text'][:600]}" for r in relay)) if relay else ""
                reply = _aichat([{"role": "system",
                                   "content": CHAT_SYSTEM + rb}] + clean,
                                max_tokens=400)
            except Exception:
                return self._send("ai error", 502)
            import datetime as _dt, random as _r
            (ROOT / "sessions").mkdir(exist_ok=True)
            fn = (f"chat-{_dt.date.today().isoformat()}-"
                  f"{_r.randrange(1 << 30):08x}.json")
            (ROOT / "sessions" / fn).write_text(_json.dumps(
                {"date": str(_dt.date.today()), "via": "serve",
                 "messages": msgs + [{"role": "assistant",
                                       "content": reply}],
                 "relayed": [r["id"] for r in relay]},
                ensure_ascii=False, indent=1))
            git("add", f"sessions/{fn}")
            git("commit", "-q", "-m", f"chat: {fn}")
            git("push", "-q", "origin", "main")
            self._send(_json.dumps({"reply": reply, "sources": sources}),
                       200, "application/json")
            return
        if self.path == "/save" and n and "urlencoded" in ctype:
            from urllib.parse import parse_qs as _pq
            f = _pq(raw.decode())
            p = self.safe_file((f.get("f", [""])[0] or ""))
            body = (f.get("body", [""])[0] or "").rstrip() + "\n"
            if p is None:
                return self._send("no such file", 400)
            if p.name == "motto.txt" and len(
                    [l for l in body.splitlines() if l.strip()]) > 5:
                return self._send("max 5 lines", 400)
            text = p.read_text()
            head = text.split("---", 1)[0] + "---\n" if "---" in text else ""
            p.write_text(head + body)
            git("add", str(p.relative_to(ROOT)))
            git("commit", "-q", "-m", f"edit: {p.relative_to(ROOT)}")
            code, _ = git("push", "-q", "origin", "main")
            if code != 0:
                return self._send("saved locally", 200, "text/plain")
            return self._send("ok", 200, "text/plain")
        if self.path == "/new-day" and (not n or "urlencoded" in ctype):
            files = entry_files()
            nxt = max([d for d, _ in files] + [0]) + 1
            dest = ROOT / "entries" / f"day-{nxt:02d}.md"
            dest.write_text(f"day: {nxt}\nvisibility: public\n---\n")
            git("add", str(dest.relative_to(ROOT)))
            git("commit", "-q", "-m", f"new day {nxt}")
            code, _ = git("push", "-q", "origin", "main")
            extra = "" if code == 0 else " (committed locally)"
            self._send(f"<p>day {nxt} open{extra}</p>"
                       "<p><a href='/'>back</a></p>")
            return
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
