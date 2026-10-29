# hxrmxs ingestion plan

Census 2026-10-29 (`/home/box/repos/tomnotes/hxrmxs/`, 68 files, 12.7MB).
Parser: tolerant brace-matcher + strict=False (files contain raw newlines
in strings and concatenated top-level values). Repro: see /tmp/hx_parse3.py
pattern; rerun counts with the same recipe.

## What it actually is

~425 unique dialogue episodes (Socratic/Platonic men, Buddha suttas,
Gurdjieff, Nisargadatta/"I Am That", Zen, Theravada therapy dialogues,
Milinda, Stoics, Madhyamaka...). Each episode: lineage tag + turns with
speaker/text + rich annotation (behavior_tags, trap_ids, mechanism,
phase, registers). This is the "similar conversations" corpus: someone
describes a situation, a teacher-figure responds.

## Deduplication map (verified by md5 + episode-id sets)

- The whole `9 *` series adds NOTHING — byte-exact copies:
  `9 buddha.txt`=`3 buddha.txt`, `9 gurdjeff.txt`=`4 GURDJEFF.txt`,
  `9 socratic.txt`=`5 socratic.txt`, `9 therapy.txt`=`1 therapytinker.txt`,
  `9 realist.txt`=`2 real realist tinker.txt`. Exclude the `9 *` copies.
- `uno.txt` (274 eps) ⊆ `finale.txt`+`finale 2.txt` (343 unique). Exclude uno.
- `finale` does NOT contain it all: **80 unique episodes live only outside
  it** (15 files), heaviest in `4 buddha mn pass1.txt` (19, incl. SN suttas),
  `5 gurdjeff pass1.txt` (15), `2 realist tinker.txt` (14). Missing Buddhist
  28, Gurdjieffian 15, Realist 14, Advaita 7, Socratic 7, rest scattered.
- Exclude ~24 non-dialogue files: plans, keys (`tinker api key.txt`),
  junk (`PRACTISE.txt` is a CompTIA transcript, `burp.txt`, `chutee.txt`,
  `deceiveapi.txt`, zero-byte stubs), `budda source of t.txt` (gap-filler
  doc for budda.txt, not dialogues), `SYSTEM MESSAGE (GENERATOR).txt`,
  `pass1 script.txt`, MAGNUM OPUS notes, `my thoughts.txt`, taxonomies.
- `diary training data.txt` + `xpreniex.txt` inside hxrmxs are byte-identical
  to the top-level tomnotes copies — already ingested as own-chat/own-notes.
  Do not double-ingest.

## Chunking spec

- Unit: one episode if ≤1800 chars, else split at turn boundaries into
  ~1500-char chunks (never split mid-turn).
- Fields per item: `id: hx:<episode_id>[:<n>]`, `kind: dialogue`,
  `themes: [lineage]`, `label: "dialogue <episode_id> (<lineage>)"`,
  `url: tomnotes/hxrmxs/<file>` (local ref, no public link),
  `text`: `Speaker: text` lines joined.
- Estimated volume: ~0.6–1.0M unique chars → **~400–650 chunks**.

## Where it lives (decision, with numbers)

NO new infrastructure. At ~600 chunks × 1024 dims the whole hxrmxs set is
~5MB as JSON — the existing R2 `relay/vectors.json` + `index.json` path
absorbs it with one rebuild. Vectorize is the wrong tool here: free tier
covers it trivially either way, and a second retrieval system doubles every
future change (boost tables, graph links, dedup). Revisit Vectorize only
if the corpus passes ~50k vectors (video/audio transcripts would do it).
Worker code unchanged — same cosine top-20 → graph → rerank → compose path.

## Relay integration

- `kind: dialogue`, boost **1.0 (neutral)** — below lived-logs. These are
  constructed dialogues, not lived experience; they lose ties. Own words
  keep priority (own-tension 1.35, own-notes 1.3, own-chat 1.25).
- Composition slots: lived (incl. dialogue? no — keep dialogue in its own
  lane): lived-log up to 3, lineage up to 1, own-past up to 1, **dialogue
  up to 2** (they read like the answer format the user wants: situation →
  teacher response).
- Graph: tag dialogue items with roots? No — leave untagged; they match
  by embedding only. The dharma_graph stays roots×tensions×roots-docs.

## Steps

1. `tools/ingest_hxrmxs.py`: parse (tolerant), dedupe (drop 9* set, uno),
   exclude non-dialogue list, chunk, emit items (do NOT write corpus yet —
   print counts + 3 samples).
2. Eyeball samples, then append into `build_index.py` as a 5th source.
3. Full `build_index` run, verify counts, upload relay/* to R2.
4. Live chat test with a "how do i deal with X" query; confirm a dialogue
   surfaces with label + excerpt and correct (non-)attribution.
5. Commit, push, deploy.
