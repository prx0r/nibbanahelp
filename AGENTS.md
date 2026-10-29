# nibbanahelp — agent instructions

Shared second brain of diaries from people attaining nibbana. Markdown +
git, white page frontend, Cloudflare worker. Public by practice.

## Layout (do not restructure without asking)

- `entries/` — dated diary entries (`day: N`, `visibility:` header)
- `essays/` — speakable distillations, pinned to days (`day:`, `voice:`, `audio:`)
- `tensions/` — one file per tension (`id, status, domain, summary` + body)
- `advice/` — self-advice captures (JSON, verbatim, never edit after capture)
- `sessions/` — untangling records (tension + embedding + matches + chat, verbatim)
- `roots/` — the dependency graph: lobha/dosa/moha profiles + `graph.yaml`
  (machine-readable) + `antidotes.md` + `sources.md`
- `research/` — web research notes (lived lineage, datasets, embeddings)
- `corpus/` — imported relay material (canon JSON, practice-logs, compilations)
  + `vectors.json`/`index.json` (built by `tools/build_index.py`)
- `specs/` — future architecture (profile bridge to satsang)
- `uploads/` + `manifest.json` — inbox. Upload time IS the timestamp.
  Old material flagged `backfill: true`, never re-dated.
- `site/` — built white page (`tools/site.py`). `worker/` — Cloudflare host.

## Conventions

- Header blocks (`key: value` + `---`) are the schema. Keep keys stable:
  entries/essays use `day, visibility, voice, audio`; tensions use
  `id, visibility, diarist, opened, status, domain, summary`.
- `visibility: public` is the norm. Never flip anyone's item to private
  without asking; never publish a `private` item anywhere.
- Advice records and session transcripts are verbatim and immutable.
- The relay never generates advice: match + relay with provenance.
  Abhayagiri material is link-first only (see `corpus/abhayagiri-links.md`).
- `uploads/` is the inbox. When notebook pages get transcribed into
  entries/tensions, link back to the source upload. Process oldest first.
- Frontend renders raw: no markdown conversion, no font loads, no meta
  chrome. Content in `<pre>`, monospace, white. Never add styling.
- `motto.txt`: max 5 lines, newest last (darkest). Editable like everything.
- Proportions are structural: `GAP` in `tools/site.py` is the single value
  for left-edge margin AND nav-to-body gap. serve.py imports it; the worker
  bundle generates `theme.js` from it at build. Never hardcode spacing.
- `site/index.html` and `worker/src/page.js` (+`files.js`, `anchors.js`) are
  GENERATED. Never commit them stale: after any content edit run
  `python3 tools/site.py` first, and `cd worker && node build.mjs` before
  every deploy. Stale bundles are silent — verify with grep, not trust.
- Tools are stdlib (+numpy/sklearn where noted). No new deps without asking.
- Commit messages: lowercase, short. Push to origin main when asked or when
  a unit of work completes.

## Commands

- `python3 tools/site.py` — rebuild the white page
- `python3 tools/day.py N` — bundle day N
- `python3 tools/tension.py match --tension ID` — similar passages
- `python3 tools/build_index.py` — re-embed corpora (free tier CF API)
- `python3 tools/serve.py --port 18899` — local dropbox (no auth, localhost)
- worker: `node worker/build.mjs && wrangler deploy` (from `worker/`)
