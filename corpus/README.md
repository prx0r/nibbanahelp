# Corpus — imported relay material

Raw imports live here. Nothing generated. Each subdir notes source, license,
and how the relay may use it (see `research/ai-ready-datasets.md` for the
binding principles — link-first, zero generated advice).

## canon/ — SuttaCentral API pulls (openly licensed, quote-by-reference OK)

Segmented JSON via `https://suttacentral.net/api/bilarasuttas/<uid>/<author>`:

- `iti50_sujato.json` — Iti 50, the three unskillful roots
- `an3.69_sujato.json` — Akusalamūlasutta: roots → body/speech/mind acts →
  wholesome roots → parinibbāna in this very life
- `an10.174_sujato.json` — deeds threefold by greed/hate/delusion
- `sn3.23_sujato.json` — bamboo destroyed by its own fruit

Relay use: verbatim quotes with uid citation. Refresh/extend via the API.

## practice-logs/ — 932 labelled lived journals (link-first)

Clone of https://github.com/johnduality/practice-logs (nested git stripped;
upstream is the live copy, updated July 2026). 652 DhO + 280 KFD logs in
`logs.json`, one record per log:

`url, author, predefined_themes, key_words, summary, interesting_sentence,
helpful_sentence, attainment_claimed, likely_highest_attainment,
techniques_used, teachers_mentioned, practice_volume, ...`

Note `predefined_themes` includes **Work-Practice Balance** — the
householder-tension tag. That is our match surface: tension → themes +
keywords → the actual log URL.

Relay use: match only. Link out to the log; authors opted into a forum, not
a dataset (upstream respects opt-outs — re-sync before any bulk use).

## pragmatic/ — teacher answer compilations (link-first)

Single-page snapshots, fetched 2026-10-28 (format shifts over time; URLs
are canonical, local copies are convenience):

- `ingram-posts.html` (~320 numbered posts, TOC'd) —
  https://danielpostscompilation.blogspot.com/p/blog-page.html
- `shargrol-posts.html` (technique-level answers) —
  https://shargrolpostscompilation.blogspot.com/p/blog-page.html

Relay use: tag entries by root, deep-link answers. Living authors — ask
before bulk reuse.

## Abhayagiri Q&A — NOT imported (permission-gated)

Link index only: `abhayagiri-links.md`. License forbids hosting excerpts or
recreating teacher responses. Relay = title + tags + deep link.
