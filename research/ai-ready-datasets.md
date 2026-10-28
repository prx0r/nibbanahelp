# AI-ready datasets for the relay (+ the ethics that shape it)

Goal (owner's design): the AI does **zero generation**. It matches your
tension to real tensions others lived, then relays what actual teachers
said — verbatim, with provenance. A smart friend passing notes, never
advising. Searched 2026-10-28.

## The relay architecture

```
your tension (text + root tags from roots/graph.yaml)
   → embed + tag-match against corpus index
   → relay: lived tension + teacher's actual words + source link
   → NOTHING generated. Match rationale is extractive
      (shared tags, shared words), never advice.
```

The join key is `roots/graph.yaml`: every corpus item gets tagged
lobha/dosa/moha + tension-domain. Matching is tags first, embeddings
second, teacher-words only.

## Corpora (ranked by relay-suitability)

### 1. SuttaCentral — canon API (link-first, openly licensed)
- Segmented JSON for every sutta: `https://github.com/suttacentral/bilara-data`
  (e.g. `translation/en/sujato/sutta/mn/mn11_translation-en-sujato.json`)
- Live API: `https://suttacentral.net/api/bilarasuttas/<uid>/<translator>`
  (example: `.../api/bilarasuttas/sn7.5/sujato`), docs at
  `https://suttacentral.net/api/docs/`
- Relay use: quote-by-reference. We already reach this via the fojin MCP;
  SC is the bulk-fetch counterpart.

### 2. johnduality/practice-logs — lived tensions, AI-labelled, remixable
- https://github.com/johnduality/practice-logs (site: johnduality.net/practice-logs)
- DhO + KFD logs in one filterable table: attainment stage, techniques,
  themes, quality grades — labelled with Claude, updated July 2026.
- Respects author opt-outs (excludes logs where authors refuse AI
  processing). Check repo license before redistributing; link-first by default.
- Relay use: the tension side of the pair. Your "£1500 debt + dharma work"
  matches against hundreds of real householder-practice collisions.

### 3. Abhayagiri Q&A archive — teacher advice, structured, PERMISSION REQUIRED
- Thousands of questions, tagged + clustered (everyday-life, work, anger,
  doubt…), each with audio excerpt + transcript + teacher:
  https://www.abhayagiri.org/questions/
- Structured backend: JSON database + Google Sheet + CC0 site engine
  ("material on github"). BUT the teachings themselves: non-commercial,
  unified-whole-only, **no subsections**.
- **Hard constraint** (license page, archivist + Ajahn Pasanno, June 2023):
  they explicitly ask people NOT to build AI that recreates his responses.
  "An AI simulacrum of Ajahn Pasanno seems distinctly creepy… Please don't."
- Relay use: **link-first only** — relay the question title, tags, teacher,
  and deep link (page + audio timestamp). NO excerpt hosting, NO paraphrase
  that stands in for the teacher, until/unless
  questionsandstories@abhayagiri.org grants permission.
- Why this still works: the relay never speaks *as* the teacher. It says
  "Pasanno answered this exact situation here → [link]". That is a
  librarian, not a simulacrum — the distinction the license is asking for.

### 4. Pragmatic teacher compilations (link-first)
- **Daniel Ingram posts** (~320 numbered posts, TOC-structured):
  https://danielpostscompilation.blogspot.com/p/blog-page.html
- **Shargrol posts** (technique-level answers): https://shargrolpostscompilation.blogspot.com/p/blog-page.html
- Relay use: both are already Q→A structured. Tag entries by root,
  deep-link answers. Authors are alive — ask before bulk reuse.

### 5. Dharma Overground forums (live, RSS available)
- Per-thread RSS feeds exist (seen in the wild). RSS = sanctioned
  machine-readable access; prefer it over scraping. Check ToS before bulk
  fetch. Link-first always; authors opted into a forum, not a dataset.

### 6. HuggingFace (mostly WRONG epistemology for relay — flagged)
- `sweatSmile/buddha-taught-qa` (699 QA from Rahula's *What the Buddha
  Taught*): generated pairs, textbook not lived. Usable for concept
  lookup, NOT as "real tension → teacher advice".
- `11-47/high_priest_Buddhism_100k`: synthetic persona commentary. This is
  generated advice wearing robes — the exact thing the relay refuses to be.
  Exclude.
- `DharmaBench` (Sanskrit/Tibetan eval): academic, not advice. Exclude.

### 7. DharmaSeed / talks archives (link-first, unverified bulk access)
- Teacher pages (Upton, Tejaniya, Chah lineage teachers all present) with
  streamable talks. No bulk API confirmed — do not assume one. Deep-link
  per talk.

## Relay principles (binding)

1. **Zero generation of advice.** The AI matches and relays. Wrapping text
   is extractive (titles, tags, shared words) — never counsel.
2. **Link-first.** Quote only where the license clearly allows (SC/bilara,
   public domain). Otherwise: title + teacher + tags + deep link.
3. **Permission-required list:** Abhayagiri excerpts, DhO bulk, living
   teachers' compilations. Ask in writing; record grants in this file.
4. **Opt-outs are data.** johnduality's exclusion rule is the model: any
   author refusal propagates to every index we build.
5. **Own diary first.** `advice/` (your words) and `tensions/` outrank all
   external corpora in playback order. The relay prefers your past self,
   then lived others, then teachers, then canon.
