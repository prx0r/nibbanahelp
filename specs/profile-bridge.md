# Profile bridge: nibbanahelp → satsang (spec for future)

The big version: your satsang profile reads your nibbanahelp material
(tensions, sessions, advice) and recommends videos, talks, teachers,
places/retreats, practices, virtual retreats. Specified 2026-10-28.
**Phase 0 (now) is unchanged: text embedding of similar situations +
real diary advice via `tools/tension.py`.**

## What's already built on each side

Satsang (receiving end, live):
- Device-first private profile, exportable/deletable whole
  (`satsang/specs/PROFILE.md`): taste vectors from resonance, saves,
  practice log, journeys.
- For You feed (`satsang/specs/FORYOU.md`): scores clips with why-lines —
  including **"On your mind: X"**, the exact slot tensions fill.
- MCP/REST, no auth: `search`, `clips`, `teachers`, `places`,
  `search_places`, `practices`, `profile`, `resonates`.

Nibbanahelp (sending end, this repo):
- `tensions/` (root-tagged), `sessions/` (embeddings + verbatim chats),
  `advice/` (own words), `roots/graph.yaml` (lobha/dosa/moha join keys),
  `corpus/vectors.json` (939-item match index).

## The bridge

### 1. Profile bundle (export from nibbanahelp)

```json
{
  "diarist": "handle (never legal name)",
  "exported": "2026-10-28",
  "tensions": [{"id": "coffee-addiction", "roots": ["lobha", "moha"],
                "summary": "...", "status": "open",
                "embedding": [0.01, ...]}],
  "roots_active": ["lobha", "moha"],
  "share": {"tensions": ["coffee-addiction"], "sessions": false}
}
```

- Built by `tools/export_profile.py` (to write, Phase 1).
- **Consent per tension.** Default: nothing leaves the repo. Flipping a
  tension to `share: true` is explicit, reversible, per-item. Sessions and
  advice never export unless separately flagged.
- Anonymized option: ids + roots + embeddings only, no summaries.

### 2. Matching (satsang side, Phase 2)

- Roots → satsang topics/teachers (graph.yaml tags already align: lobha =
  craving/consumption clusters, dosa = aversion/conflict, moha = doubt).
- Tension embedding → satsang passage embeddings (their S7 pipeline, same
  cosine game as our `match`).
- Surfaces, in order of intimacy: practices (do now) → talks/clips (watch)
  → teachers (follow) → places/retreats (go) → virtual retreats (join).
- Why-lines come from the tension, verbatim-ish: "On your mind: coffee",
  never generated advice copy.

### 3. Principles (inherited, binding)

- Relay, never advise: recommendations are pointers to real things made by
  real teachers. No generated guidance text.
- Abhayagiri constraint propagates: link-first, no excerpt hosting, no
  teacher simulacra — anywhere in the chain.
- Private-by-default at both ends; export whole, delete whole; device-first
  until the diarist says otherwise.
- Own diary outranks everything (our `sessions/` + `advice/` first, then
  lived others, teachers, canon).

## Phases

- **Phase 0 (now):** `tools/tension.py match/new` — similar situations +
  diary advice. No satsang dependency. KEEP FOCUS HERE.
- **Phase 1:** `tools/export_profile.py` — bundle builder + consent flags.
- **Phase 2:** satsang reads bundle (opt-in paste/upload first; account
  link later) → For You "On your mind" slots + MCP `profile` enrichment.
- **Phase 3:** retreats/places/practices/virtual retreats wired to the same
  signal; tension-resolved events feed back as resonance.

## Open questions (owner)

1. Paste-a-file import first, or straight to account-linked sync?
2. Does the bundle live in R2 (private prefix) or move device-to-device?
3. Which tension, if any, becomes the first public test share?
