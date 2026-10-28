# Contributing to nibbanahelp

## Start a diary

1. Copy `entries/_template.md` to `entries/day-01-<your-theme>.md`.
2. Write the truth. Numbers, substances, shames — the specifics are the point.
3. Log your tensions in `tensions/` (one file each, see `schema/tension.md`).

## Rules

- Honest or nothing. No enlightenment performance.
- Real details beat vague dharma-speak. "£1500 debt" beats "financial difficulty".
- One day per file. Date everything. Every entry/essay carries `day:` + `visibility:`.
- Anonymity is fine — use a handle, not your name, if you need to.

## Public or private

- Default `visibility: private` — stays in the repo, never published.
- `visibility: public` = the diarist clears it for publishing (site, readings).
  Only the diarist flips their own material. An essay is only public if every
  person named in it consents.

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
