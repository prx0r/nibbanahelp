# HANDOVER — nibbanahelp (read this first, then AGENTS.md for rules)

Orientation for the next agent. Written 2026-10-29. Project repo:
`/home/box/repos/nibbanahelp` (github.com/prx0r/nibbanahelp, public).
Host: Cloudflare Worker `nibbanahelp` → **https://nibbana.stonedoorway.com**
(also served at nibbanahelp.tradesprior.workers.dev). Box: debz.

## What this is (one breath)

A shared second brain of diaries from people attaining nibbana. You write
raw (notebook → upload), tensions get tracked as persistent entities with
root/factor decodes, and a chat that **never gives advice** — it embeds your
question, finds similar lived experience + teacher material, and relays it
verbatim with sources. A vis shows the afflictions live. Everything is your
own words first (VOICE RULE in AGENTS.md — read it).

## The loop, end to end

```
upload (nav "+", diary/essay/poem picker) ──► worker /upload → R2 pending/upload
   diary-kind → overwrites that day's entry body (1 diary/day law)
   essay/poem → uploads/ + manifest{kind,day,backfill} on sync
local dropbox (tools/serve.py --port 18888+) does the same directly + git commits
cron */3 runs tools/sync_r2.py → applies R2 pending → commits → rebuilds → redeploys
chat: embed query (bge-m3, 2 views: raw + keywords) → cosine top-30
   → dharma-tech GraphRAG adds root-linked passages
   → bge-reranker in batches of 8 (400 chars each — NEVER one big call)
   → tier composer: anchor(own-tension) → lineage(canon/Upton/teacher-answer)
     → lived(+forum) → dialogue → own-past; floors: cosine .28 (.22 anchor),
     rerank .12; curated:* with cosine≥.5 bypass floor; boosted kinds (boost>1)
     sort before flat kinds
   → deepseek-v4-flash drafts (fallback llama-3.3-70b on empty), prompt:
     relay-only, quote ONLY the relay block, one question, probe factors
   → session JSON committed to sessions/; live side → R2 pending/chat → cron
vis: roots sized by tension status+chat counts; per-tension factors chips;
   14-unwholesome grid lit by counts; decode key = roots/cetasikas-decode.md
self-advice: tools/echo.py capture/playback (to_friend verbatim, immutable)
stacking: tools/stack.py → sessions/*.analysis.json (verbatim gold)
watch queue: tools/me.py + tools/watch_queue.py → satsang REST (tantrafiles.xyz)
```

## Where everything is

| Path | What |
|---|---|
| `entries/`, `essays/`, `tensions/`, `motto.txt`, `advice/`, `sessions/` | content (yours; voice rules apply) |
| `roots/` | dependency graph (graph.yaml, cetasikas-decode.md, abhidhamma.md, lobha/dosa/moha profiles, antidotes, sources) |
| `corpus/` | index (vectors.json+index.json+index_meta.json — 1783 items), canon JSON, practice-logs (932), hxrmxs dialogues (575), curated/ (night-practice.json etc), dharma_graph/ (exported for dharma-tech) |
| `tools/` | ai.py (models+CHAT_SYSTEM), build_index.py, serve.py (dropbox+chat), tension.py, echo.py, day.py, stack.py, site.py (page+vis+shared JS), characterise.py (diary/essay/poem lock), sync_r2.py (cron), me.py, watch_queue.py, ingest_hxrmxs.py, export_dharma_graph.py, dharma_engine.py |
| `worker/` | Cloudflare Worker (src/index.js = routes+chat+upload; build.mjs inlines site+files; wrangler.toml has R2 binding `BRAIN`→bucket `nibbanahelp-live`, AI binding, custom_domain nibbana.stonedoorway.com) |
| `specs/` | jev-register-gate.md (LATER), trajectory-endgame.md (NOT BUILT) |
| `research/`, `PROCESS-NOTES.md`, `AGENTS.md` | prior art, mistakes, rules |

## External dependencies (NOT in this repo)

- `/home/box/repos/tomnotes` — owner's word bank (day-files, essays,
  `diary training data.txt` 102 convos, `hxrmxs/` dialogue corpus). Indexed
  by build_index; hxrmxs bulk still OUT of worker index (too fat for R2
  JSON path — Vectorize note below).
- `/home/box/repos/abhidhamma` — 2 Beth Upton interview transcripts
  (indexed as canon tier). Its audio/segments unused by us.
- `/home/box/repos/dharma-tech` — GraphRAG engine, used UNMODIFIED via
  `tools/dharma_engine.py` (sys.path hack) + `corpus/dharma_graph/` export.
- Satsang REST: `https://mcp.tantrafiles.xyz/api/search?q=&kinds=clip`
  (needs browser User-Agent header — edge 403s default agents). satsang.digital
  domain pending; links use tantrafiles.xyz.
- Cloudflare: token+account in `/root/.r2-env` (never print), API token also
  `/root/.cf-api-token` for wrangler. Bucket `nibbanahelp-live` layout:
  `relay/` (vectors+index+dharma jsonl), `pending/` (entry|essay|tension|motto.md,
  chat/<sid>/*.json, upload/<ts>-<name> + uploadmeta/<same>.json).

## Live ops

- Redeploy worker: `cd worker && node build.mjs && CLOUDFLARE_API_TOKEN=$(cat /root/.cf-api-token) wrangler deploy`
  (ALWAYS `node build.mjs` first — site/index.html + worker/src/{page,files,anchors,context,tension_roots}.js are GENERATED).
- Rebuild index: `python3 tools/build_index.py` (incremental; model pinned in
  index_meta.json — change model ⇒ full rebuild) then upload
  corpus/{vectors,index}.json → R2 `relay/`.
- Local dropbox: `python3 tools/serve.py --port 18888` — localhost only, no auth.
  Use a FRESH port every time (stale servers on reused ports caused 3 debugging
  spirals). Kill by exact PID: `for pid in $(ps -eo pid,args | grep "[s]erve.py --port 18888" | awk '{print $1}'); do kill $pid; done` — NEVER `pkill -f serve.py` (kills your own shell group on this box).
- Cron: `*/3 * * * * cd /home/box/repos/nibbanahelp && /usr/bin/python3 tools/sync_r2.py >> /tmp/nib-sync.log 2>&1`
- Headless browser (VERIFY UI before shipping — this box HAS one):
  `/root/.cache/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-linux64/chrome-headless-shell`,
  python playwright installed. Screenshot → read the PNG. Non-negotiable for
  frontend changes (owner checks by tapping).

## Gotchas that already burned us (see PROCESS-NOTES.md for the full log)

1. **Never name a tools/ file after a stdlib module.** `tools/queue.py`
   shadowed `queue` and silently killed the sync (urllib3 broke). Renamed
   watch_queue.py.
2. **Reranker token window**: ≤8 contexts per call, ≤400 chars each. One
   fat call fails silently → empty relay → only video sources appear.
3. **JS `in` operator does not substring-search strings** — use `.includes`.
4. **Shell timeouts kill process groups here** — `setsid nohup … < /dev/null &`
   to detach, and never chain long tests with server starts in one command.
5. **Voice rule**: only entries/essays/tension-bodies/motto/chat-user-turns
   are the diarist's words. Never cement a line you invented — ask.
6. **One diary per day**: diary-kind uploads overwrite that day's entry body.
   Kinds locked to diary|essay|poem (characterise.py — deterministic
   heuristics first, model tiebreak; never "note").
7. Tier keys in composer TIER maps: canon/lineage first. If you add a new
   `kind`, map it in `_tier` (serve) + `tierOf` (worker) + boost tables —
   three places, all must match.
8. Test artifacts: live chats auto-commit/auto-sync. Clean `sessions/chat-*`,
   R2 `pending/chat/*` test keys, and any test entries/files after verifying,
   BEFORE the final push. Git history is public — force-push only on clean trees.
9. `.git` is public: never commit `/root/.r2-env` contents, keys, or owner's
   private notes from other repos.

## Current state snapshot

- Content: day-01 public (debt/coffee/shame tensions; coffee+debt loosening),
  motto = 2 owner lines, sessions/ empty (test transcripts scrubbed).
- Index: 1783 items (932 lived logs, 575 hxrmxs dialogues, 147+ own-notes,
  ~102 own-chat, 17 canon incl. Upton, 4 curated night-practice).
- Chat: tiered relay verified live on the night-practice query (teacher-answer
  first, streamentry threads in, videos tail, echo-filtered).
- Vis: decode map live (14-grid + factor chips + growing beautfuls).
- Upload: picker + visible feedback + diary-overwrite live (local tested;
  live POST path identical via R2 sync).
- Deployed worker includes `relayErr` in chat JSON (debug echo — keep or
  remove at leisure).

## Next-up queue (owner's words, priority order)

1. Play with it — real usage is the next data. Fix what annoys.
2. Parked/unverified: chat video tier (click-to-play embeds, code shipped,
   e2e unverified — verify with the phone harness).
3. JEV register gate (`specs/jev-register-gate.md`) — build when owner says go.
4. Trajectory endgame (`specs/trajectory-endgame.md`) — NOT built, needs
   register gate first.
5. hxrmxs bulk into worker index → Vectorize migration (research the numbers
   in AGENTS.md note; ~11k chunks needs 768-dim Vectorize).
6. Upton talk captions: owner runs yt-dlp on his machine (S6 pattern),
   then index. Dharma Seed stays link-first (CC-BY-NC-ND).
7. Profile bridge to satsang (`specs/profile-bridge.md`) — paste-import first.
