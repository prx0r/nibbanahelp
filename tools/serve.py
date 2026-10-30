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
            f"<title>nibbanahelp</title><style>{CSS}</style></head>"
            f"<body data-today=\"{max((int(d) for d in days if str(d).isdigit()), default=0)+1}\">"
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
                                _post as _post_ai, CHAT_SYSTEM)
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
                _msg = clean[-1]["content"][:2000]
                _stop = {"the", "and", "for", "that", "this", "with", "have",
                         "you", "are", "not", "but", "can", "its", "was",
                         "just", "like", "what", "when", "your", "about"}
                _kw = [w for w in re.findall(r"[a-z']{4,}", _msg.lower())
                       if w not in _stop]
                _views = [_msg] + ([" ".join(_kw[:6])] if _kw else [])
                _embs = _emb(_views)
                _q = _np.zeros(len(_embs[0]), dtype=_np.float32)
                for _e in _embs:
                    _e = _np.array(_e, dtype=_np.float32)
                    _q += _e / (_np.linalg.norm(_e) + 1e-9)
                _q = _q / (_np.linalg.norm(_q) + 1e-9)
                _raw = (_mat @ _q).astype(float)
                _rawmap = { _items[int(_i)]["id"]: float(_raw[int(_i)]) for _i in range(len(_items)) }
                # own words first: diary, then past chats/notes, then others
                _BOOST = {"own-tension": 1.35, "own-diary": 1.35,
                          "canon": 1.2, "trika": 1.2,
                          "teacher-answer": 1.2, "forum-answer": 1.15}
                _sc = _raw.copy()
                for _ii, _it in enumerate(_items):
                    _sc[_ii] *= _BOOST.get(_it.get("kind"), 1.0)
                _order = _np.argsort(-_sc)[:30]
                # quota pool (red-team rt03 round 3): the hxrmxs dialogue corpus
                # floods the top-30 — guarantee lived/canon/trika representation
                _top = [_items[int(i)] for i in _order
                        if not (_items[int(i)].get("kind") == "own-chat"
                                and clean[-1]["content"][:120] in
                                (_items[int(i)].get("text") or "")[:300])]
                _have = {i.get("id") for i in _top}
                _srt = _np.argsort(-_sc)
                for _kind, _n, _fl in (("lived-log", 4, 0.45),
                                       ("canon", 3, 0.40),
                                       ("trika", 4, 0.40)):
                    for _ix in _srt:
                        if _n <= 0:
                            break
                        _it = _items[int(_ix)]
                        if (_it.get("kind") != _kind
                                or _it.get("id") in _have
                                or float(_sc[int(_ix)]) < _fl):
                            continue
                        _top.append(_it)
                        _have.add(_it.get("id"))
                        _n -= 1
                _cands = _top
                # graph stage: roots of any matched tensions -> dharma-tech concept retrieval
                try:
                    sys.path.insert(0, str(ROOT / "tools"))
                    from dharma_engine import relay_for_roots as _grr
                    _tids = set()
                    for _c in _cands:
                        _cid = _c.get("id", "")
                        if _cid.startswith("tension:") and \
                                _rawmap.get(_cid, 0) >= 0.45:
                            _tids.add(_cid.split(":", 1)[1])
                        elif (_c.get("url", "").startswith("tensions/")
                              and _rawmap.get(_cid, 0) >= 0.45):
                            _tids.add(Path(_c["url"]).stem)
                    _groots = set()
                    for _tp in (ROOT / "tensions").glob("*.md"):
                        _h, _ = header(_tp)
                        if _h.get("id") in _tids or _tp.stem in _tids:
                            _groots.update(_h.get("roots", []))
                    for _g in _grr(sorted(_groots), top_n=3):
                        _gk = _g["id"].split(":")[-1].replace("tension-", "")
                        if _gk not in {c["id"].split(":")[-1].replace("tension-", "") for c in _cands}:
                            _cands.append({"id": _g["id"], "kind": _g["kind"],
                                           "label": _g["label"], "url": _g["url"],
                                           "text": _g["text"]})
                            _rawmap[_g["id"]] = 0.5
                except Exception as e:
                    print("graph stage unavailable:", str(e)[:200])
                _rrpairs = []
                try:
                    for _b in range(0, len(_cands), 8):
                        _batch = _cands[_b:_b + 8]
                        _out = _post_ai("@cf/baai/bge-reranker-base",
                                        {"query": clean[-1]["content"],
                                         "contexts": [{"text": c["text"][:400]} for c in _batch]})
                        for _r in _out.get("result", {}).get("response", []):
                            _i = int(_r.get("id", -1))
                            if 0 <= _i < len(_batch):
                                _rrpairs.append((float(_r.get("score", 0)), _b + _i))
                    _rrpairs.sort(reverse=True)
                except Exception:
                    _rrpairs = [(1.0, i) for i in range(len(_cands))]
                # dynamic composition, only if truly relevant (raw cosine floor):
                # anchor own tension -> lived others -> one lineage -> one own-past
                def _tier(c):
                    k = c.get("kind", "")
                    if k == "own-tension":
                        return "anchor"
                    if k in ("lived-log", "forum-answer"):
                        return "lived"
                    if k == "dialogue":
                        return "dialogue"
                    if k in ("canon", "trika", "roots-doc", "teacher-answer"):
                        return "lineage"
                    return "ownpast"
                _ranked = sorted(
                    ((_s * _BOOST.get(_cands[i].get("kind"), 1.0),
                      0 if _BOOST.get(_cands[i].get("kind"), 1.0) > 1 else 1,
                      _cands[i]) for _s, i in _rrpairs),
                    key=lambda x: (x[1], -x[0]))
                _slots = {"anchor": 1, "lived": 3, "lineage": 2, "ownpast": 1,
                             "dialogue": 2}
                _seen, relay, sources = set(), [], []
                for _rrs, _pri, _c in _ranked:
                    _t = _tier(_c)
                    if _slots.get(_t, 0) <= 0:
                        continue
                    # red-team floors: anchor .45 / lived .45 / ownpast .35 / shared .40
                    _floor = (0.45 if _t == "anchor"
                              else (0.45 if _c.get("kind") == "lived-log"
                              else (0.35 if _t == "ownpast" else 0.40)))
                    if _rawmap.get(_c["id"], 0) < _floor:
                        continue
                    _curated = (str(_c.get("id", "")).startswith("curated:")
                                and _rawmap.get(_c["id"], 0) >= 0.5)
                    _key = _c["id"].split(":")[-1].replace("tension-", "")
                    if _key in _seen:
                        continue
                    _seen.add(_key)
                    _slots[_t] -= 1
                    relay.append(_c)
                    if len(relay) >= 7:
                        break
                _TIER_ORDER = {"canon": 0, "lineage": 1, "roots-doc": 1,
                               "graph": 1, "anchor": 2, "ownpast": 3,
                               "lived": 4, "dialogue": 5}
                relay.sort(key=lambda c: _TIER_ORDER.get(_tier(c), 9))
                sources = [{"label": r["label"], "url": r["url"],
                            "excerpt": r["text"][:280]} for r in relay]
            except Exception as e:
                print("relay unavailable:", str(e)[:200])
            # video tier: satsang clip moments (YouTube id @ second), fail-open.
            # only when real passages matched — never pad an empty relay (F4)
            try:
                if not relay:
                    raise RuntimeError("no passages matched")
                from urllib.request import Request as _Req, urlopen as _ul
                _stop = {"the", "and", "for", "that", "this", "with", "have",
                         "you", "are", "not", "but", "can", "its", "was",
                         "one", "more", "just", "like", "what", "when",
                         "your", "about", "how", "deal", "going", "keep",
                         "really", "want", "feel", "feeling"}
                _kw = [w for w in re.findall(r"[a-z']{4,}",
                                             clean[-1]["content"].lower())
                       if w not in _stop]
                _plans = ([_kw[:3]] if len(_kw) >= 3 else []) + [
                    [w] for w in _kw[:4]]
                _hits = []
                for _plan in _plans:
                    if not _plan or _hits:
                        continue
                    _req = _Req(
                        "https://mcp.tantrafiles.xyz/api/search?q=" +
                        quote(" ".join(_plan)) + "&kinds=clip&limit=4",
                        headers={"User-Agent": "Mozilla/5.0 (Linux; Android 10) "
                                 "AppleWebKit/537.36 Chrome/120 Mobile "
                                 "Safari/537.36"})
                    with _ul(_req, timeout=10) as _r:
                        _hits = _json.load(_r).get("results", [])[
                            :max(0, 7 - len(relay))]
                for _res in _hits:
                    _m = re.match(r"clip/([A-Za-z0-9_-]{6,})(?:@(\d+))?",
                                  _res.get("id", ""))
                    if not _m:
                        continue
                    _v = {"id": _res.get("id", ""), "kind": "video",
                          "label": _res.get("title", "")[:90],
                          "url": _res.get("url") or "",
                          "text": _res.get("title", ""),
                          "youtube": _m.group(1),
                          "start": int(_m.group(2) or 0)}
                    relay.append(_v)
                    sources.append({"label": _v["label"],
                                    "url": _v["url"],
                                    "excerpt": _v["text"][:280],
                                    "youtube": _v["youtube"],
                                    "start": _v["start"]})
            except Exception as e:
                print("satsang video tier unavailable:", str(e)[:150])
            try:
                from ai import chat as _aichat, CHAT_SYSTEM
                rb = ("\n\nSIMILAR LIVED PASSAGES (relay these with their "
                      "sources, never invent advice):\n" + "\n".join(
                      f"- [{r['kind']}] {r['label']} :: {r['url']}\n"
                      f"  {r['text'][:600]}" for r in relay)) if relay else ""
                reply = _aichat([{"role": "system",
                        "content": CHAT_SYSTEM + rb}] + clean,
                        max_tokens=800)
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
            self._send(_json.dumps({"reply": reply,
                                    "sources": [{"label": r["label"],
                                                 "url": r["url"],
                                                 "excerpt": r["text"][:280]}
                                                for r in relay]}),
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
        try:
            sys.path.insert(0, str(ROOT / "tools"))
            from characterise import classify_bytes
            kind = classify_bytes(blob, dest.name)
        except Exception:
            kind = None
        posted_day = None
        posted_kind = None
        for _ch in raw.split(bound):
            if b'name="day"' in _ch:
                _b = _ch.split(b"\r\n\r\n", 1)[-1].rstrip(b"\r\n--")
                _v = _b.decode("utf-8", "ignore").strip()
                if _v.isdigit():
                    posted_day = int(_v)
            if b'name="kind"' in _ch:
                _b = _ch.split(b"\r\n\r\n", 1)[-1].rstrip(b"\r\n--")
                _v = _b.decode("utf-8", "ignore").strip()
                if _v in ("diary", "essay", "poem"):
                    posted_kind = _v
        day_val = posted_day or day_of(now.date())
        backfill = bool(backfill) or day_val < day_of(now.date())
        if posted_kind == "diary":
            entry = None
            for ep in sorted((ROOT / "entries").glob("*.md")):
                if ep.name.startswith("_"):
                    continue
                et = ep.read_text()
                m = re.search(r"^day:\s*(\S+)", et.split("---")[0], re.M)
                if m and m.group(1) == str(day_val):
                    entry = ep
                    break
            if entry is None:
                entry = ROOT / "entries" / f"day-{day_val:02d}.md"
                head_new = f"day: {day_val}\nvisibility: public\n---\n"
            else:
                et = entry.read_text()
                head_new = et.split("---", 1)[0] + "---\n" if "---" in et else ""
            body_txt = blob.decode("utf-8", "ignore")
            if body_txt.startswith("---"):
                body_txt = body_txt.split("---", 1)[1].lstrip("\n")
            entry.write_text(head_new + body_txt.rstrip() + "\n")
            git("add", str(entry.relative_to(ROOT)))
            git("commit", "-q", "-m", f"diary upload day {day_val}")
            code, _ = git("push", "-q", "origin", "main")
            extra = "" if code == 0 else " (committed locally)"
            self._send(f"<p>diary saved for day {day_val}{extra}</p>"
                       "<p><a href='/'>back</a></p>")
            return
        kind = posted_kind or kind
        rows = manifest()
        rows.append({"file": dest.name,
                     "uploaded_at": now.isoformat(timespec="seconds"),
                     "backfill": backfill, "note": note,
                     "day": day_val, "kind": kind})
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
