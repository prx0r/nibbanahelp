# Spec: Jev register gate (chat output verification) — LATER BUILD

Status: specced 2026-10-29, not built. Do not build until owner says go.

## What Jev is

TypeSafe's System One decision model (typesafe.ai; also on OpenRouter
as `typesafe/jev-1.13`, and Ollama serves local decision models with the
same API — no key, nothing leaves the machine). Not an LLM: it returns
typed answers — `choice`, `noul` (binary yes/no as 0–1), `score` —
with calibrated probabilities, never prose. Median ~127ms, ~96% cheaper
than LLM-classification (liteLLM benchmark), and the OpenRouter cookbook
pattern is literally "draft with cheap model → Jev verifies → escalate
only on failure" ("Jev-Verified Cascade"). 22 decision models from 13
makers speak the same Decisions API — swap freely.

## Why we can use the hxrmxs pedagogy as its question set

`hxrmxs/registers.txt` already defines 24 registers on 6 orthogonal
dimensions (INTENSITY: gentle_invitation → steady_focus → active_friction
→ ..., each with when-to-use, mechanism, failure modes). The dialogue
episodes carry per-turn annotations (function_id, phase, register,
trap_ids) — ~715 annotated teaching turns — which are the labeled
examples for calibrating thresholds. Jev needs no training: you phrase
the registers as choice questions and give it the query + draft as
evidence; the "when to use" rules from registers.txt become the question
text. The classifier IS the register taxonomy, enforced by a typed model.

## The gate (the user's exact idea)

```
user query ──► deepseek draft (existing pipeline)
                    │
        Jev pre-pass: which register does THIS QUERY call for?
        (choice over register set; evidence = query text +
         registers.txt "when to use" rules)
                    │
        Jev post-pass: which register is THIS DRAFT in?
        + hard gates as noul questions:
          - "does this reply give advice or instructions?"
          - "does this present a source label the speaker never wrote?"
          - "does this claim the speaker said X without quoting?"
                    │
        register match & gates pass ──► send
        mismatch ──► regenerate max 2× with explicit register hint
        still failing / Jev errors / low confidence ──► fail-OPEN
        (send with flag; never block chat over a classifier hiccup)
```

- Pre-pass can be cached per-session (registers shift slowly).
- Hard gates: if Jev says "advice" with p > 0.9 → retry; > 0.9 after
  retries → still send but flag in session JSON (`gate: "advice-flagged"`).
  The prompt is the primary defense; the gate is the net.
- Register mismatch is a hint, not a veto: regenerate once with
  `Register: gentle_invitation — soft, no pressure` prepended to the
  system prompt; if it still mismatches, send anyway.

## Where it plugs in (minimal touch)

- `tools/ai.py`: one function `verify_reply(query, draft) -> dict`
  (calls Jev; stdlib urllib). 
- `tools/serve.py` /chat handler: after `_aichat(...)`, call verify;
  on fail, one retry with hint; log verdict into the session JSON.
- Worker: same, via a small `env.AI` call if a CF-hosted decision model
  exists, else via direct fetch to the Decisions endpoint, else skip
  (worker fails open automatically).

## Cost + key policy (broke-owner law)

- Prefer **Ollama local decision model** (free, private, same API) if
  ollama ever lands on the box. Next: any free/CF decision model.
  Else TypeSafe/OpenRouter — cost is fractions of a cent per check at
  our volume (<100 chats/day), but get the key approved first.
- No new infra: no queues, no workers, one HTTP call inline.

## Calibration (the build task, half the work)

- Take ~50 annotated hxrmxs turns (register + function_id labels) +
  ~20 of our own chat replies → label them by hand with expected register.
- Tune per-question thresholds on that set (Jev returns probabilities;
  we pick cutoffs, as the tax-doc-classifier pattern does).
- Store the calibrated thresholds in `roots/registers-calibrated.json`.

## Non-goals

- No fine-tuning. No 24-dimension full classification per reply (pick
  the INTENSITY dimension + 2 hard gates; the other 5 dimensions are
  context for the question text, not outputs).
- No rewriting of replies by Jev (it never writes).
- No blocking of the user's chat on low confidence — fail-open, always.
