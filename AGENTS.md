# nibbanahelp — agent instructions

> **Read `HANDOVER.md` first** — orientation, file map, live ops, gotchas.
> This file is the rules; that file is the state of the world.

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
- VOICE RULE (absolute, user-set): the diarist's words are ONLY entries/*,
  essays/*, tensions/* bodies, motto.txt, advice to_friend, chat user-turns.
  Summaries, labels, schema text, graph descriptions, templates, and anything
  generated are NEVER presented as theirs. When in doubt about a line's
  origin, remove it and ask — never cement it.
- Relay index: `tools/build_index.py` embeds with bge-m3 into
  `corpus/vectors.json` + `index.json`, then upload both to R2 under
  `relay/` (the live chat reads them from there). Re-run on corpus change.
  Index is incremental (new ids only; model change forces a full rebuild).
- Chat is retrieval-first: embed query → cosine top-20 → bge-reranker
  top-5 → relay with sources. Zero generated advice, always.
  Only own-tension gets a boost (×1.35, the anchor); all other kinds
  score flat so the slot composer does the balancing — same weights
  in serve, worker, tension.py.
- Composition is tiered, gated on true relevance (raw cosine floor 0.28,
  0.22 for own-tension anchor): anchor own tension → up to 3 lived →
  1 lineage → 1 own-past. Empty tiers are skipped, never filled.
- dharma-tech's GraphRAG runs unmodified against corpus/dharma_graph/
  (exported by tools/export_dharma_graph.py); tools/dharma_engine.py
  is the bridge. Concept matches join the relay pool before rerank.
- tomnotes/ (NOT in repo — /home/box/repos/tomnotes, owner's box) feeds
  own-notes + own-chat items via build_index. hxrmxs bulk stays out of
  the worker index until the Vectorize migration (free tier math:
  ~11k chunks need Vectorize; R2 JSON too fat to ship per request).
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
