# Contributing to nibbanahelp

## Start a diary

Writing happens in your notebook. The repo is the shared shelf:

1. Upload files via the frontend (`python3 tools/serve.py`) — or drop them
   in `uploads/` directly. Anything: photos of pages, audio, markdown.
2. Upload time IS the timestamp. There is no backfilling the timeline.
3. Old material is welcome but must be flagged `backfill` (tick the box,
   optionally note when it's from). Backfill keeps its upload day but reads
   as older — honest history, honest order.
4. Log your tensions in `tensions/` (one file each, see `schema/tension.md`).

## Rules

- Honest or nothing. No enlightenment performance.
- Real details beat vague dharma-speak. "£1500 debt" beats "financial difficulty".
- One day per file. Date everything. Every entry/essay carries `day:` + `visibility:`.
- Anonymity is fine — use a handle, not your name, if you need to.

## Public or private

Everything public is the practice itself. No names needed — a handle or
nothing. `visibility: public` is the norm: entries, essays, tensions.
`visibility: private` exists for material not yet ready; flip it when it is.
An essay is only public if every person named in it consents.

## Essays → speech → days

1. Distil diary raw material into `essays/` (write to be spoken; mark pauses).
2. Speak it — own voice or TTS (`voice:` field). Audio in `audio/`, mirrored
   to R2 under `nibbanahelp/audio/`. Text stays canonical.
3. Assign it: `day:` pins it. `python3 tools/day.py N` bundles the day —
   its entries, essays, open tensions, echoed advice.

## Tensions

A tension is anything pulling you away from the present path. Debt, addiction,
shame, grief, doubt — if it has gravity, it belongs here. Tensions are not
problems to solve before practice. They *are* the practice material.
