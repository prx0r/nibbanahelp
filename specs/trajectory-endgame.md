# Spec: Typed Liberation Trajectories (the endgame) — NOT BUILT

Status: specced 2026-10-29 at owner request. **Do not build until owner says
go.** Prerequisite: the Jev register gate (`specs/jev-register-gate.md`) is
built first — same infrastructure (typed questions, calibrated thresholds,
fail-open policy).

## Thesis

Every session and tension in this repo is evidence. Jev (or any decision
model on the Decisions API) turns that evidence into types — cheap enough
to run over everything, calibrated enough to trust at thresholds we choose.
The types join into **trajectories**: state × relayed-passage × next-state
over time. The miner then answers, with evidence, the only question that
matters: *for people whose tensions later loosened, what co-occurred before
the loosening?* — and answers it with typed counts + verbatim quotes, never
generated advice. The zero-generation law survives the endgame because
patterns are types and words are always someone's own.

## Data model

```json
// trajectories/<tension-id>.json  (one per tension, append-only)
{
  "tension": "coffee-addiction",
  "scored": [
    {
      "at": "2026-10-31",
      "state": "loosening",              // choice: open|loosening|resolved
      "roots": {"lobha": 0.87, "moha": 0.62, "dosa": 0.11},  // noul
      "circumstance": 0.4, "affliction": 0.8,                 // noul
      "evidence": "tensions/coffee-addiction.md#progress-2026-10-29",
      "model": "jev-latest", "thresholds": "v1", "conf": 0.81
    }
  ]
}

// sessions/<chat>.json gains a "types" field — NEVER merged into messages
{
  "types": {
    "turns": [
      {"i": 0, "user_state": "looped", "intensity": 0.6,       // choice+score
       "self_answer": 0.12}                                    // noul
    ],
    "model": "jev-latest", "thresholds": "v1"
  }
}

// trajectory aggregates — refreshed after each batch, read by chat
// corpus/trajectories_agg.json
{
  "patterns": [
    {
      "match": {"roots_any": ["dosa", "moha"]},
      "n_transitions": 7, "n_loosened": 5,                    // typed counts
      "pre_move_passages": [                                   // verbatim, sourced
        {"id": "hx:...", "label": "...", "url": "...", "text": "..."},
        {"id": "tension:...", "text": "..."}
      ]
    }
  ]
}
```

Types are **annotations**, never presented as speech. The VOICE RULE holds:
typed fields are machine-derived metadata, labeled as such in any context
block (`[typed stat, not words]`).

## Jev question sets (concrete)

A. **Turn-pair classifier** (per chat exchange, evidence = user turn i and i+1):
   - choice `user_state`: {clarified, looped, deepened, deflected}
     - clarified: user narrows or specifies; looped: same ground re-trod;
       deepened: new layer or honest uncertainty; deflected: topic/body shift
   - score `intensity` 0–1 (register INTENSITY dimension context in question)
   - noul `self_answer`: "does the user state their own resolution or insight
     in this turn?" (calibrated against stacker output)
B. **Tension-state classifier** (per tension file, evidence = full body):
   - choice `state`: {open, loosening, resolved}
   - noul ×3: lobha/dosa/moha presence (question text = graph.yaml root defs)
   - noul `circumstance`, noul `affliction` (the locked split — flag conflation)
C. **Passage-outcome linker** (batch, evidence = session timeline of a tension):
   - noul per (relayed-passage, next-state-change) pair: "did this passage
     appear in the exchange immediately preceding the user's state change?"
     (this one is nearly mechanical — Jev verifies the join, code does the
     timeline; keep it because off-by-one joins are where data goes wrong)

## Pipeline stages (each shippable alone)

- **A. Typing sessions** — batch over `sessions/chat-*.json` without `types`.
  Cron (weekly) or `tools/type_sessions.py` manual. Fail-open: Jev error →
  skip batch, session stays untyped, never blocks anything.
- **B. Scoring tensions** — batch over `tensions/*.md` → append a `scored`
  row per tension when the file's mtime changed since last score. Weekly.
- **C. Trajectory assembly** — join sessions (turns with `self_answer` high)
  ↔ tensions via relayed ids in session JSON + state deltas from B.
  Output `trajectories/*.json` + `trajectories_agg.json`.
- **D. The miner** — pattern query over C. Anti-overfit rule hard-coded:
  **a pattern needs ≥3 supporting transitions or it stays silent.** Output
  = counts + top-3 pre-move passages, each verbatim + sourced.
- **E. Chat tier** — composer gains `trajectory` slot (max 1, only if
  `n_transitions ≥ 3`). System prompt: typed stats are counts, present as
  "in this repo's records, N of M matching tensions later moved to
  loosening" — never prediction, never advice, never "you will".

## Calibration (half the build)

- Positives: ~50 annotated hxrmxs turns (function_id/phase = ground truth
  for A's user_state mapping — e.g. RM-phase turns ↔ clarified).
- Positives: hand-labeled ~20 of our own tension files for B (status is
  already hand-set — the labels exist).
- Negatives: the 715 hxrmxs *teaching* turns must NOT be typed as user
  turns (speaker-field check + Jev "is this a teacher move?" noul).
- Thresholds per question, stored like the register gate: one
  `roots/trajectory-thresholds-v1.json`, version-stamped, re-tuned when a
  decision-model swap changes calibration.

## Failure modes & laws

- **Fail-open everywhere.** Jev timeout/error/low-confidence → skip that
  item. Chat never blocks on typing. The miner never sees untyped items
  (they simply don't count).
- **Anti-prediction law.** The system may report what happened to others;
  it may never forecast ("you will resolve in…"). Typed counts are past
  tense, always.
- **Anti-generalization floor.** <3 transitions → pattern invisible. <5
  → surfaced with "small sample" flag in the context block.
- **Model/threshold stamping.** Every typed row carries model id + threshold
  version. On model swap, old rows are quarantined (not deleted), miner
  refuses to mix versions in one pattern.
- **Privacy.** All typing happens locally or on the free tier; sessions
  contain no secrets (owner's own words, public by practice) — but the
  `types` fields never leave the repo either (no third-party API beyond
  the decision-model call itself).

## Cost

Jev: ~$0.00x per 1000 items. Our volume: ~50 sessions × ~10 turns = ~500
calls/week (A) + ~5 tensions (B) + linker per transition (C). Inline
chat-time truth-checks: one call per chat (the register gate does this
already). Total: well under a dollar a year on paid; $0 on Ollama-local.

## Non-goals

- No real-time per-keystroke classification. No fine-tuning. No new UI
  beyond: (optional, later) vis gains a per-tension trajectory ribbon.
- No automatic status flips — B's `state` is a suggestion; owner confirms
  into the tension file, as with stack.py.
- No cross-user anything. Single diarist until the repo decides otherwise.

## Build order (when owner says go)

1. Register gate (`jev-register-gate.md`) — infra + calibration harness.
2. Stage A + B (typing) — value immediately: tensions keep themselves honest.
3. Stage C (assembly) — joins, the fiddly part.
4. Stage D (miner) — the payoff.
5. Stage E (chat tier) — one slot, one prompt block.
