# Practice Logs

A searchable, labelled database of meditation **practice logs** collected from two
long-running online communities — the [Dharma Overground](https://www.dharmaoverground.org/)
(DhO) forum and the [Kenneth Folk Dharma](https://www.kennethfolkdharma.com/) (KFD)
archive. Each log is a first-person account of someone's meditation practice; every
log is labelled (attainment stage, techniques, themes, quality grades, and more) and
published as a single filterable table.

**Live site:** https://johnduality.net/practice-logs/

---

## What's here

The published product is a self-contained web page (`index.html`) that embeds the
labelled dataset (`logs.json`) as an inline table you can search, sort, and filter —
by attainment level, technique, theme, practice volume, and so on. There is no server
and no build step to view it: open `index.html` in a browser.

As of the latest build the dataset holds **932 labelled logs** (652 from DhO, 280 from
KFD).

## Repository layout

```
.
├── index.html              # the published page — embeds the data as `const DATA = [...]`
├── logs.json               # canonical dataset: one labelled JSON record per log
├── RUNBOOK.md              # how to refresh the database and republish (full guide)
├── Tools/
│   ├── extract_snippet.js       # in-browser capture of a DhO thread
│   ├── extract_awakenetwork.js  # in-browser capture of awakenetwork.org articles
│   ├── combine_download.js      # bundle captured threads into one download
│   ├── process_payload.py       # captured payload  ->  formatted .txt log
│   ├── build_index.py           # logs.json  ->  embedded into index.html
│   └── subagent_prompt.md       # the labelling rubric + output schema (source of truth)
└── Data/                   # raw scraped .txt logs — NOT committed
```

## The pipeline

```
forum thread ──(browser capture)──► per-thread .txt ──(label)──► logs.json ──(embed)──► index.html
```

1. **Capture** — DhO sits behind Cloudflare and the awakenetwork.org articles are
   client-rendered, so pages are captured from a real signed-in browser rather than a
   server-side fetch. `extract_snippet.js` / `extract_awakenetwork.js` grab a thread's
   posts; `combine_download.js` hands them off as a single download.
2. **Convert** — `process_payload.py` turns the captured payload into one `.txt` per
   thread in a stable `Title:` / `URL:` / `User:` format.
3. **Label** — each `.txt` is read and turned into one structured JSON record
   following the rubric and schema in `Tools/subagent_prompt.md`.
4. **Publish** — records are merged into `logs.json` (keyed by URL), then
   `python3 Tools/build_index.py logs.json index.html` embeds them into the page.

`RUNBOOK.md` is the complete operating guide — folder conventions, selectors, the
incremental-update workflow, and the parallel-labelling approach for large batches.
It's written so the database can keep being refreshed as new logs appear on the
boards.

## Rebuilding / republishing

```bash
python3 Tools/build_index.py logs.json index.html
```

This is the only build step. It rewrites the `const DATA = [...]` block inside
`index.html` from `logs.json`; open the page afterward to confirm the row count.

## Sourcing & attribution

These logs were written by their individual authors and posted publicly on the
Dharma Overground and Kenneth Folk Dharma forums. This project keeps its footprint
deliberately narrow: the **raw scraped logs** (`Data/`) are **excluded** from this
repository via `.gitignore`, and what ships is the labelled dataset (`logs.json`) —
short quotations plus machine-generated summaries and tags — and the page that
renders it, rather than the full text of the original posts.

**Opt-outs are honoured.** A log is excluded from the dataset if its author expressed
that they don't want it processed by AI, republished, or read outside its original
forum — including requests to delete or privatise the thread, even where the forum never
acted on the request. Borderline cases are withheld and queued for a human decision in
`Tools/review_queue.txt` rather than included by default. The screen runs at labelling
time and is specified in `Tools/subagent_prompt.md`; `RUNBOOK.md` §12 documents the
workflow.

If you are an author and would like your log removed or amended, please open an issue
or email johnduality0@gmail.com.

## Labelling schema

The full field-by-field schema, the diagnostic criteria used for attainment
labelling, and a worked example live in `Tools/subagent_prompt.md`. In brief, each
record carries the log's title/URL/source plus labels for author, themes, keywords,
a one-line summary, an interesting and a helpful quote, claimed vs. estimated
attainment, techniques, teachers discussed, the author's own personal teachers,
map-territory focus, and 1–10 quality scores (usefulness, advice quality, practice
volume) alongside experience, retreat, and "spice" (degree of disagreement) fields.

Two of those are easy to confuse. **`teachers_mentioned`** ("Teachers discussed" in the
table) is everyone a log talks about; **`personal_teachers`** is the narrower subset the
author actually studied under, as distinct from influences they've only read or met once.
`personal_teachers` was added in July 2026 and so is absent from records labelled before
then — it is not yet shown as a column; see `RUNBOOK.md` §6a.
