# Roots — the dependency graph

How the AI figures out what is going on.

## Pipeline

```
observation (diary text, behaviour)
   → candidate root: lobha / dosa / moha (+ co-present moha — always check)
   → Abhidhamma mechanics: which citta-class, which cetasikas, javana count
   → antidote: alobha / adosa / amoha, replacement, or non-feeding
```

## Layers

1. **Observable** — concrete behaviours in plain words (phone-grabbing, extra
   cake, goodbye-coffee, shame-armouring). From `entries/` + `tensions/`.
2. **Roots (entities)** — `greed-lobha.md`, `hatred-dosa.md`, `delusion-moha.md`.
   The user's language: entities that demand to be fed and punish unfed-ness.
3. **Mechanics (advanced)** — 12 unwholesome cittas (8 lobha-rooted, 2
   dosa-rooted, 2 moha-rooted), 14 unwholesome cetasikas, 7 javana moments per
   process with āsevana (repetition) condition — each javana feeds the next.
   This is the canonical machinery behind "feeding strengthens, leaving alone
   weakens". See Upton's impulsion tables in `sources.md`.
4. **Antidotes** — `antidotes.md`. The three wholesome roots + replacement
   strategy + non-feeding.

## Machine-readable graph

`graph.yaml` — nodes and edges. Candidate links are flagged `status: candidate`
(the AI's job is to confirm or re-route them against new diary evidence, not
to treat them as doctrine).
