# Practice Logs — Update Runbook

*A hand-off guide for Claude Cowork. Everything needed to refresh the meditation
practice-log database and republish it. Replaces the old `Legacy/` scripts.*

> **Resuming? Read `PROGRESS.txt` first.** It's the on-disk checkpoint of what the
> last session did and what's left. Keep it updated as you work (see §11).

---

## 1. What this project is

A searchable database of meditation practice logs scraped from the **Dharma
Overground** (DhO) forum and the **Kenneth Folk Dharma** (KFD) archive. Each log
is labelled (attainment, techniques, themes, quality grades, etc.) and published
as a single filterable table at **johnduality.net/practice-logs/**, rendered by
`index.html`.

**Canonical data store:** `logs.json` — one JSON record per log, list-valued
fields (themes, techniques, teachers) kept as arrays.
**Publishing:** the records are embedded inline into `index.html` as a
`const DATA = [ ... ];` array. There is no spreadsheet in the loop anymore.

Pipeline at a glance:

```
DhO board ──(browser)──► per-thread .txt ──(label)──► logs.json ──(embed)──► index.html
```

---

## 2. Folder layout

```
Practice Logs/
├── index.html                         # the published page; holds const DATA = [...]
├── logs.json                          # canonical data store (build this; see §6)
├── RUNBOOK.md                         # this file
├── Data/
│   ├── DhO Practice Logs Board YY-MM-DD/   # one .txt per DhO thread; folder date = last cutoff
│   │   └── non-logs/                       # confirmed non-log threads (admin/meta/split-off
│   │                                        # debate/redacted-content), moved out of the top
│   │                                        # level so it holds only real, labelled logs.
│   │                                        # IMPORTANT: exclude this subfolder (or list
│   │                                        # non-recursively) when walking the board folder
│   │                                        # for candidates/rebuilds, or its files will
│   │                                        # wrongly resurface as unlabelled candidates.
│   ├── KFD Practice Logs/                  # KFD archive logs (.txt)
│   └── Additional Logs/                    # misc extra logs
└── Tools/
    ├── extract_snippet.js             # paste-run in Claude in Chrome to capture a thread
    ├── process_payload.py             # captured JSON  ->  formatted .txt
    └── build_index.py                 # logs.json      ->  embedded into index.html
```

The DhO board folder is **date-stamped** (e.g. `DhO Practice Logs Board 25-10-15`).
That date is the **cutoff**: everything up to it is already captured. **Always stamp
the folder with the day *before* the run** (i.e. "yesterday"), never the run day
itself — this guarantees full capture by forcing a re-scrape of any thread updated
on the boundary day (a same-day stamp could miss threads replied to later that day,
across time zones). Duplicates are harmless: a re-captured thread just overwrites
its own `.txt`.

---

## 3. Why the scraping method changed

The old `Legacy/1 - DhO Log Downloader.py` fetched pages with Python `requests`.
**DhO now sits behind Cloudflare, which blocks `requests`** (and any server-side
fetch, including this sandbox). A real signed-in browser passes Cloudflare
normally, so we drive **Claude in Chrome** to load each page, capture the message
HTML from the live DOM, and convert it locally. Everything downstream is unchanged.

### The browser→disk hand-off (this is the part that used to fail)

Getting captured text out of the browser onto disk has three traps. All are now
handled by the tools here; the reliable pattern is **stash every thread in
`localStorage`, then do ONE download per run from a fresh tab.**

- **Trap 1 — the tool-output channel blocks page data.** Returning captured
  HTML/JSON through the `javascript_tool` result trips a safety filter
  ("[BLOCKED: Cookie/query string data]" / base64), because forum posts are full of
  query-string URLs. It's also size-capped (~30k). **So the snippets never return
  page content — only a tiny status.** (`get_page_text` is unfiltered but hard-capped
  at 50,000 chars even in its persisted file, so it's not a general answer either.)
- **Trap 2 — Chrome's multi-download gate.** The FIRST automatic (blob) download in a
  browser tab succeeds; every later one in that same tab is silently blocked (no
  error, no file). So a per-thread download design dies after thread #1.
  **Fix: accumulate all threads in `localStorage` (it persists across same-origin
  navigations and is shared across tabs), then trigger exactly ONE combined download
  — and do it from a freshly-opened tab, which resets the gate.** Verified reliable.
- **Trap 3 — the thread-title selector changed.** The old `h1.header-title` is gone.
  Title now comes from `document.title` minus the
  ` - Discussion - www.dharmaoverground.org` suffix (HTML-unescaped). Handled in
  the snippet + `process_payload.py`.

---

## 4. Prerequisites

- **Claude in Chrome** extension connected and signed in with the same account.
- **Downloads folder access** — grant it with `request_cowork_directory`
  (host path e.g. `C:\Users\johnl\Downloads`). This is the drop point for
  captured payloads.
- Being logged into DhO in that Chrome isn't required for public logs, but doesn't hurt.

---

## 5. Update workflow (incremental — the usual case)

### Step 1 — Find the cutoff
Read the date in the `Data/DhO Practice Logs Board YY-MM-DD/` folder name. Any
thread whose **latest reply is on or after that date** needs (re)capturing — the
date is inclusive, and because the folder is stamped to the day before the previous
run (see §2), this re-scrapes the boundary day and guarantees nothing is missed.

### Step 2 — Collect new / updated threads from the board
- **Board URL:** `https://www.dharmaoverground.org/discussion/-/message_boards/category/2658626`
- The board is sorted by **most-recent reply first**, so new activity is at the
  top. (~768 threads, 40 per page, ~20 pages — but you'll only ever walk the
  first page or two before hitting threads older than the cutoff.)
- **Selectors** (verified current):
  - each thread row → `li.list-group-item`
  - title + link → `h2.h5 > a`  (`a.textContent` = title, `a.href` = thread URL)
  - recency shows as text like `"… replied 2 Hours ago."`
- Walk from page 1, collect `{title, url}` for every thread whose last reply is
  after the cutoff. Stop once you reach threads older than the cutoff. To page,
  either click the **Next Page** control in Chrome or append the board's page
  cursor. A thread already captured but with **new replies** should be re-captured
  (it will simply overwrite its `.txt` and its `logs.json` record).

### Step 3 — Capture + convert each thread
Capture ALL the run's threads first (into `localStorage`), then hand them off in a
single download. Do **not** download per thread (Trap 2 above).

1. For each `{title, url}`: navigate Claude in Chrome to `url` (this passes
   Cloudflare), then run `Tools/extract_snippet.js` via `javascript_tool`. It
   captures the title + every message's `{usernameRaw, contentHTML}`, stashes the
   payload in `localStorage` under `cap_dho_<threadId>`, and returns only a small
   status (message count, etc.). If it reports `ready:false`, the page hadn't
   finished rendering — wait a moment and re-run it.
2. When every thread for this run is captured, **open a NEW tab, navigate it to any
   dharmaoverground.org page, and run `Tools/combine_download.js` once.** It bundles
   all `cap_*` payloads into a single `dho_capture.json` and triggers ONE download to
   the Downloads folder. (Fresh tab + single download = always lands.)
3. Convert the whole bundle at once:
   ```
   python3 Tools/process_payload.py <Downloads>/dho_capture.json "Data/DhO Practice Logs Board <new-date>"
   ```
   → writes one `<Title>.txt` per thread in the exact legacy format.
   `process_payload.py` accepts either the bundle or a single-thread payload.

*Large runs:* `localStorage` holds ~5 MB per origin. For a big rebuild, download and
clear (`localStorage.clear()`) every ~30–40 threads rather than accumulating all at once.

*awakenetwork.org "special additions"* (client-rendered magazine articles, e.g. Chris
Marti's journals): use `Tools/extract_awakenetwork.js` instead — it parses the article
in-browser into finished log text and stashes it under `cap_txt_<slug>`. The same
`combine_download.js` + `process_payload.py` hand-off then writes the `.txt` files.

**What `process_payload.py` reproduces (format spec):**
```
Title: <thread title>
URL: <thread url>

User: <name>

<message text, whitespace-collapsed>
---

User: <name>
...
```
- Message blocks come from `div.card.panel` containing `div.message-content`.
- Username = `h5.message-user-display` text up to the first comma.
- Quotes render as `<quote> … </quote>` blocks (blank line before/after).
- **Nested (double) quotes are preserved** as nested `<quote><quote>…</quote>…</quote>`
  — processed deepest-first. Single quotes and quote-free text are **byte-identical**
  to the legacy scraper (verified by diffing a re-scrape against the old corpus:
  the only differences were the new posts and the one nested-quote message).
- Filenames keep only alphanumerics, space, hyphen, underscore, then rstrip — so
  apostrophes drop (`John's Log` → `Johns Log.txt`). Keep this rule for consistency
  with the existing corpus.

### Step 4 — Label each new log
**You (Cowork Claude) do the labelling directly — no API key, no external call.**
Read the `.txt` and produce the record following **`Tools/subagent_prompt.md`** (the
rubric + schema; see §7). For a handful of new logs, label them inline; for a large
batch, fan out to subagents as in §9. Output exactly the schema fields, nothing else.

**This step includes the opt-out screen (§12) — a log whose author asked not to be
processed by AI, or asked for privacy, never gets a record.** The rule lives in
`Tools/subagent_prompt.md` so it travels with every labelling subagent; §12 covers the
orchestrator's side (collecting the verdicts, maintaining `Tools/review_queue.txt`).

### Step 5 — Build each record and update `logs.json`
Turn the labels into one JSON record per log using the schema + derivations in
**§6**. Then, keyed by `URL`: replace the record if it already exists in
`logs.json`, otherwise append it.

**Withheld logs must also be removed, not just skipped.** A log can opt out *after* it was
already labelled in an earlier run — people ask for removal years into a thread — so for
every `EXCLUDE` verdict, delete any existing record with that URL from `logs.json` rather
than only declining to add a new one. This runs **both ways**: a re-scrape can also reveal
that an earlier opt-out was later withdrawn, in which case the log comes back (see the
worked example in §12). Either way the current state of the thread governs, not what an
earlier run concluded.

### Step 6 — Republish
```
python3 Tools/build_index.py logs.json index.html
```
This swaps the new records into `index.html`'s `const DATA = [...]` block
(bracket-depth scan; safe against brackets inside strings). Open `index.html` to
confirm the row count and spot-check a few rows. Then rename the Data board folder
to **the day before this run** (yesterday's date), per the cutoff convention in §2.

---

## 6. `logs.json` record schema

One object per log, **`snake_case` keys** — this is the shape `index.html` consumes.
The field-by-field definitions, types, and example live in **`Tools/subagent_prompt.md`**
(the single source of truth); they're not duplicated here. Four keys are *derived* rather
than labelled: `log` (title), `url` (line-2 URL), `source` (`"DhO"`/`"KFD"`), and
`exp_years` (a number from `practice_experience`). Numeric fields (`usefulness`,
`non_author_advice_quality`, `practice_volume`, `spice`, `exp_years`) are JSON numbers so
`index.html` sorts/filters them numerically; `practice_experience` is a display string;
list fields are arrays; everything else is a string.

**index.html:** already migrated to this snake_case, numeric schema — its `COLS`,
`ATT` list (`no attainment / A&P / Dark Night / Equanimity / 1st–4th path`, no `pre-1st`
stages), and the numeric 1–10 colour buckets all match. So routine publishing is just
`build_index.py` injecting `DATA`; no JS changes are needed unless the schema changes
again.

### 6a. `personal_teachers` — labelled now, not yet shown

The rubric collects a `personal_teachers` array alongside `teachers_mentioned`: the
subset of the teachers a log discusses with whom the author has a genuine student–teacher
relationship, as opposed to influences they've only read, met once, or admire from a
distance. See `Tools/subagent_prompt.md` for the full test; the short version is *leave
it blank rather than guess*, and `[]` is a common, correct answer.

**It is deliberately absent from `index.html`.** The 932 records labelled before July
2026 have no `personal_teachers` key, so adding the column now would show an almost
entirely empty field. **Add the column once a meaningful share of records carry the
field** — either after a full relabel (§8) or once enough incremental runs have
accumulated. Paste this into the `COLS` array in `index.html`, directly after the
`teachers_mentioned` entry:

```js
  {k:"personal_teachers", lab:"Personal teachers", w:140, get:r=>(r.personal_teachers||[]).join(", "),
   cell:r=>tags(r.personal_teachers), facet:"many"},
```

Two optional touches at the same time: add `fld("Personal teachers", tags(r.personal_teachers)) +`
next to the existing `fld("Teachers discussed", …)` line in `paintDrawer()` so the drawer
shows it too, and add `(r.personal_teachers||[]).join(" "),` to the array in `searchBlob()`
so it's searchable. Both `get` and `cell` already tolerate a missing key, so records
without the field render as an empty cell rather than breaking.

*(Naming note: the table column and drawer label for `teachers_mentioned` read
**"Teachers discussed"**, not "Teachers" — the point being that appearing there implies
nothing about studentship. Keep the two labels distinct if you rename either.)*

---

## 7. Labelling rubric

The full rubric — diagnostic criteria, every field, the JSON output schema, and a
worked example — lives in **`Tools/subagent_prompt.md`**, kept separate so the many
labelling subagents read only that small file and never this whole runbook. That
file is the single source of truth for labelling; edit it there, not here.

---

## 8. Full rebuild (re-process every `.txt` into a fresh `logs.json`)

To rebuild from scratch (e.g. first population, or after a labelling-rubric change):

1. Gather every `.txt` under `Data/` (DhO board + KFD + Additional).
2. For each, label it (§7) and build a record (§6). Set `source` to `"DhO"` or
   `"KFD"` based on which folder it came from; `url` is on line 2 of each `.txt`.
   Logs whose authors opted out get no record (§12).
3. Write all records to `logs.json`.
4. Reconcile the privacy verdicts and `Tools/review_queue.txt` (§12).
5. `python3 Tools/build_index.py logs.json index.html`.

This is a large batch (~950 logs). Do it in chunks, save `logs.json` incrementally,
and keep a note of the last file processed so it can resume. Skip any non-log index
files (e.g. a combined "AI-Sorted Database" text, if present).

A full rebuild is also the moment `personal_teachers` (§6a) becomes worth showing —
after it, add the column to `index.html`.

---

## 9. Parallel labelling (subagent fan-out)

Labelling the whole corpus (~950 logs) is slow in one thread — parallelize it.
Spawn several **subagents**, each handling a batch of `.txt` files, each returning
a JSON array of records. The orchestrator merges them into `logs.json`.

**Orchestrator (main agent) steps:**
1. List the target `.txt` files (all of `Data/**` for a full rebuild, or just the
   newly-exported ones for an incremental update).
2. Split into batches of **at most 5 files** per subagent.
3. Spawn one subagent per batch **in parallel**, passing that batch's file paths
   and a shared output folder (e.g. `Tools/label_parts/`).
4. When all return, concatenate every `part_*.json`, **replace-by-`URL`** against
   any existing `logs.json`, and write `logs.json`.
5. Collect every `part_*.privacy.txt` (§12): drop each `EXCLUDE` URL from `logs.json`
   and append the `REVIEW` lines to `Tools/review_queue.txt`.
6. `python3 Tools/build_index.py logs.json index.html`.

**Subagent prompt:** hand each subagent the contents of **`Tools/subagent_prompt.md`**
with its two placeholders filled in — `{{LOG_FILES}}` (that batch's ≤5 `.txt` paths)
and `{{OUTPUT_PATH}}` (e.g. `Tools/label_parts/part_03.json`). That file is fully
self-contained (context, rubric, schema, worked example, and write/validate
instructions), so subagents never open this runbook.

**Notes:**
- Cap batches at **5 logs per subagent**. Some logs exceed 300 KB, so keeping
  batches small ensures every log fits comfortably in the subagent's context; drop
  below 5 if a batch happens to contain several very large logs.
- **Avoid clustering same-author logs in one batch.** Many authors have multiple
  threads (numbered parts, "Reboot", "MIGRATE" duplicates, monthly journal
  installments — often detectable from filename patterns like "Name log 2",
  "Name log 3"). When forming batches, spread suspected same-author files across
  *different* subagent calls, or label them one-file-per-subagent, rather than
  handing several of one person's logs to a single subagent. Verified failure mode:
  a subagent given multiple logs by the same author has blended details (e.g. a
  technique or attainment from a later log bleeding into an earlier log's record)
  even though each record is supposed to reflect only its own file — see the
  contamination warning baked into `Tools/subagent_prompt.md`'s Rules section. That
  warning is a safety net, not a substitute for avoiding the clustering up front.
- Have the orchestrator verify the final `logs.json` count matches the number of
  input files (minus intended skips and minus privacy exclusions) before running
  `build_index.py`.
- Collect the `part_*.privacy.txt` files as well as the `part_*.json` ones — a subagent
  that withholds a log writes its reasoning only there, and an uncollected `REVIEW` line
  is a decision silently dropped.

---

## 10. Reference: selectors

| Purpose            | Selector |
|--------------------|----------|
| Board thread rows  | `li.list-group-item` |
| Board title + link | `h2.h5 > a` |
| Thread messages    | `div.card.panel` (that contain a `div.message-content`) |
| Message author     | `h5.message-user-display` (text before first comma) |
| Message body       | `div.message-content` (innerHTML) |
| Quote block        | `div.quote` → `div.quote-content` (nested = deepest-first) |
| Thread title       | `document.title` minus ` - Discussion - www.dharmaoverground.org` |

---

## 11. Resuming across sessions — `PROGRESS.txt`

Cowork sessions don't share memory, so state lives on disk in **`PROGRESS.txt`**
(project root). It's the single hand-off note between sessions.

**Every session:**
1. **Read `PROGRESS.txt` first.** It tells you the current run's goal, phase
   (capture / convert / label / build), the DhO cutoff date, a checklist of items
   with `[ ]`/`[x]` status, and a one-line **NEXT ACTION**.
2. **Update it as you go** — flip a checklist item to `[x]` the moment its artifact
   exists on disk (a `.txt` written, a record added to `logs.json`, etc.), not at the
   end. Refresh **NEXT ACTION**, **Phase**, and **Last updated** each time.
3. If you start a new run, list its intended threads/files as `[ ]` up front; the
   remaining `[ ]` items are exactly the resume point if the run is interrupted.

Because each `.txt` is idempotent (a re-captured thread just overwrites its own file),
the safe recovery rule is simply: **redo any item still marked `[ ]`.** Keep entries
terse; append a dated one-liner to the LOG section for anything non-obvious.

---

## 12. Opt-out / privacy screen

**The rule:** a log is excluded from the database if its **author** expressed that they
don't want it processed by AI, republished, or read outside its original forum. This is
stated publicly on the About page of `index.html`, so it needs to stay true.

The detection rule lives in **`Tools/subagent_prompt.md`**, at the top of its Rules
section — that way it travels with every labelling subagent and applies on the first read
of a log, before any record exists. It covers explicit AI opt-outs, privacy and deletion
requests, reuse restrictions, and any other expressed reservation about the log being used
outside DhO/KFD. Two guardrails matter and are spelled out there: it must be the
**author's** own wish about their own log (repliers objecting, and the very common on-topic
chatter *about* AI, don't count), and **borderline means withhold, not include.**

**Mechanics.** Each labelling subagent writes a `part_NN.privacy.txt` beside its
`part_NN.json` with one line per withheld file:

```
EXCLUDE | <filename>.txt | <URL> | <username> | "<verbatim quote>"
REVIEW  | <filename>.txt | <URL> | <username> | "<verbatim quote>" | <why it's borderline>
```

The orchestrator then, before `build_index.py`:
- **`EXCLUDE`** → ensure no record with that URL exists in `logs.json` (delete it if one
  does — see below), and leave the raw `.txt` in `Data/` alone.
- **`REVIEW`** → append the line to **`Tools/review_queue.txt`** and write no record. John
  decides; a resolved line moves to the RESOLVED section of that file with the outcome.

**Two things that are easy to get wrong:**

1. **An opt-out can arrive after the log was already labelled.** People ask for removal
   years into a thread, so a re-scrape can turn an existing record into an exclusion. Always
   *delete by URL*, don't just decline to add.
2. **The raw `.txt` stays on disk.** `Data/` is gitignored and never published, and keeping
   the file is what lets a later run recognise the same opt-out again instead of silently
   re-including the log. Excluding means "no record in `logs.json`", not "delete the
   scrape".

**Worked example — Bahiya Baby: an opt-out that was withdrawn (kept, 2026-07-30).** This
is the case to read before writing any screening logic, because the naive reading of it is
wrong.

In `Bahiya 4 or How I learned to stop worrying and love 4th path.txt` the author announces
*"Hey, I'm deleting my logs. The way things are going there's nothing really private anymore
and I don't want information I've shared in good faith to be used against me, here or
anywhere else"*, then — having lost account access — asks the admin *"Pretty please delete
my threads, I tried to do it myself but I can't"* and lists 13 thread URLs. Four of those
are in `logs.json`. Read that far and it is an open-and-shut exclusion, which is exactly
what the first sweep concluded, wrongly.

Keep reading. The thread argues with him — John L and shargrol both make the case for
leaving the logs up — and he relents: *"If y'all really think there's value in leaving the
posts up ... I'll fucken leave them up ... but, I really don't want to, but I also
understand why one might think that's important, and if it valuable for people,
hypothetically then I'll do it,"* and then *"Ok, well I'll do it for you Shargrol, but only
because I love ya."* That is a withdrawal of the request, so **all four logs stay in the
database.** He later returned under a new alias and started `skin in the game: log x`,
posting publicly again — consistent with the withdrawal.

The lesson, now baked into `Tools/subagent_prompt.md`: **these are conversations, and the
author's last word governs.** Never act on an opt-out found mid-file without reading to the
end of the file. Note also that consent here is *reluctant* ("I really don't want to") but
still consent — the screen honours what the author decided, not what we guess they'd
prefer.

One thing the case does **not** establish: DhO never deleted the threads (Chris M: *"Your
logs are still available. They were never deleted, and they never will be"*). Had the
withdrawal not happened, those logs would still be live on the forum and still excluded
here — **a log being publicly reachable on DhO is not evidence that its author consents.**

**Retro-sweeping the existing corpus.** The 932 records labelled before this rule existed
were swept on 2026-07-30 by keyword-scanning all 935 raw `.txt` files and reading every
hit in context. If you need to repeat it (e.g. after widening the rule), the useful
patterns were: AI/LLM/ChatGPT/GPT/Claude/"machine learning", `scrap(e|ing)`, `opt.?out`,
"do not (repost|distribute|share|copy|quote|publish)", copyright/"all rights reserved",
"(delete|remove) (this|my) (log|post|thread)", "take it down", "keep this private",
"outside (the|this) (forum|DhO|thread)", "without my permission", "I'd rather", "not
comfortable", plus mentions of the spreadsheet/johnduality itself. Expect a **very** high
false-positive rate — of 350 candidate passages, 334 were noise ("scraping the bottom" as
a practice metaphor, "private" meaning an offline notebook, people enthusiastically
discussing their own AI use, `A.I.` matching inside unrelated words). Budget for reading
the contexts, and check *whose* `User:` block each hit falls under.
