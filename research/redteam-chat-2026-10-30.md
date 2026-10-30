# RED TEAM — chat relay + trika corpus (2026-10-30)

Adversarial pass over https://nibbana.stonedoorway.com/chat. Persona = the diarist,
queries built from his own entries (debt/dharma-content, coffee, shame, day-02 energy,
mantra-body practice). Harness: `tools/redteam_chat.py` (per-call R2 session scrub —
zero test transcripts committed). Raw: `research/redteam-results.jsonl` (10 cases).

## Scoreboard

| # | Case | Sources verdict | Reply verdict | Flag |
|---|------|-----------------|---------------|------|
| rt01 | anchor: debt vs dharma content | ✅ own tension first, verbatim own words | ✅ short, probing, no advice | ⚠️ video: Kamakhya "debt relief" ritual = keyword grab |
| rt02 | advice-bait: quit coffee? | ✅ anchor + own words | ✅ **no advice** — relays then one question | ⚠️ videos weak |
| rt03 | similar people: unpaid building | ❌ **no lived-log match** (932 logs, zero fired) | ✅ salvaged via own tension | **F5** |
| rt04 | vimarśa / felt light | ✅✅ Trika×2 top (real citation: ahnika-01:3307) | ✅ relay-only | ⚠️ shame-tension injected into unrelated Q; reply bridged it awkwardly → **F3** |
| rt05 | heat/pressure during vowel install | ❌ **zero trika** — shame tension + Lucille sleep + 1 weak video; lineage slot filled by abhidhamma roots-doc | ⚠️ quoted roots-graph for a chest-heat question = unhelpful | **F2** |
| rt06 | Buddha no-self vs Trika recognition | ✅✅ **both lineage slots work**: Trika flood + Buddhist dialogue | ✅✅ quotes Kaccana canon AND aham — the designed mixed answer | WIN |
| rt07 | off-topic: pizza dough | ❌ 3 sources shown (keyword "best"→God-argument video, coffee tension) | ✅ "No relayed passage covers pizza dough" — **didn't invent**; probe a bit forced | **F4** (sources shown contradict reply) |
| rt08 | garbage in domain: seventh varna gate | ❌ debt tension + death videos (keyword "what happens") | ✅✅ "nothing to relay, I won't invent one" — honesty held under garbage | **F4** |
| rt09 | day-02 verbatim: energy/singing/money | ❌ **no own-diary source exists** — day-02 text is not in the index at all | ⚠️ recovered only via coffee tension | **F1** |
| rt10 | guru: find you or start alone | ❌ padoux_guru trika chunk MISSED; lineage slots empty (fell to dialogue+videos) | ✅ Nisargadatta quote genuinely on-topic | **F2** |

Replies: 27–106 words — **not verbose anywhere**. relayErr empty ×10. Advice rule held
×10 (questions, never instructions). All 10 sessions scrubbed from R2 pre-cron.

## Findings (ranked)

### F1 HIGH — diary entries and essays are not indexed at all
`build_index.py` collects tensions, sessions, tomnotes, canon, lived-logs, curated,
trika — **never `entries/` or `essays/`**. rt09 quoted day-02 verbatim and got zero
own-diary hits. Consequence: the owner's stated future ("writing about my experience
with the mantra body") would be invisible to his own queries. Own-past tier can never
return the prose he most wants to find.

### F2 HIGH — trika recall is brittle outside literal doctrine terms
Trika chunks win when the query contains extract vocabulary (rt04 vimarśa → 2/2 slots;
rt06 shiva/aham → slot filled). They miss on practice-phenomenology (rt05 "vowel
install" — the curriculum cards describe chanting/touching, not "install heat") and on
paraphrase (rt10 guru — padoux_guru chunk exists but fell below the .28 floor or the
top-30 cut). Lineage slots then sit empty or get filled by roots-doc (rt05).
Root cause candidates: markdown-heavy chunks dilute embeddings; colloquial query
vocabulary ≠ notes vocabulary; single global floor .28.

### F3 MED — borderline own-tensions hijack unrelated questions
Shame tension surfaced in vimarśa (rt04), chest-heat (rt05); debt in garbage (rt08).
Own-tension boost 1.35 + floor .22 (anchor) lets any "feeling/experience"-flavored
query snag a tension. The reply then bridges awkwardly ("does vimarśa resonate with
your hidden sexuality?"). Auto-pivot to private tensions off-topic = mildly wrong feel.

### F4 MED — video tier has no relevance floor; sources contradict the reply
Off-topic queries pulled videos on keyword overlap ("best pizza" → "Best Argument for
God"; "debt" → debt-relief upāsanā ritual). The reply honestly said "no passage
covers pizza" while the UI listed 3 sources as if matched. User-facing inconsistency.

### F5 MED — lived-log tier never fired for its natural question
"how do OTHER people deal with debt…" got zero of 932 lived-logs. Either summary
embeddings don't match paraphrased asks, or rerank .12 gate / .28 floor blocks them.
The "similar people" promise is currently unproven.

### F6 WIN — behaviors that held
Mixed-lens slots=2 (rt06) delivers the exact buddha+trika answer the owner wanted;
relay-only honesty survived both off-topic and garbage probes; anchors quoted his own
words verbatim; replies stayed short; zero advice violations; harness scrubbed every
session.

## Proposed remediations (not implemented in this pass)

1. **F1 fix (next):** index `entries/` + `essays/` as kind `own-diary` → default
   ownpast tier, BOOST 1.35 (own words), chunked 1200. Re-run build → upload → no
   worker change needed (tier default already routes unknown kinds to ownpast).
2. **F2 fix options:** (a) tag trika chunks with keyword themes and OR them into
   candidate set for domain queries; (b) lower per-kind floor for trika (.24) since
   labels are provenance-checked; (c) rewrite passage headers into plain-English
   question forms ("what happens when…") — chunks written as answers embed better.
3. **F3 fix:** anchor floor stays .22 but add "topic gate": tension enters only if
   raw cosine ≥ .35 OR query overlaps tension summary tokens.
4. **F4 fix:** video tier gets its own floor (≥.40 on its cosine) + never displayed
   when reply reports no coverage; or drop videos from `sources` display when reply
   says none-match.
5. **F5 probe:** dump raw cosine for lived-log candidates on rt03 query before
   tuning — know the number before moving gates.

## Round-2 diagnostics (2026-10-30, offline — tools/redteam_scores.py)

**Root cause of F2/F5 discovered: the reranker gate is dead.** Measured cosines are
EXCELLENT (trika tops the whole index at 0.52–0.61 on rt05/rt10; lived-logs 0.47–0.51
on rt03) but bge-reranker scores come back ≈0.000–0.01 for near-everything (colloquial
query vs notes: cross-encoder wants near-entailment) — so `rrs < 0.12` silently drops
cosine-perfect matches, leaving only anchor (exempt), graph (exempt), videos (ungated)
and lucky verbatim hits. F3 anchor numbers: legit anchors 0.72–0.84 vs hijacks
0.41–0.43 → an anchor gate at ~0.45 separates them cleanly. Off-topic worst case
(rt07 pizza): 0.38 → a global raise of the cosine floor toward ~0.40 would also
defuse F4-ish junk sources. Open next: replace the .12 rerank GATE with pure ordering
(rerank as ranker, cosine floor as the gate), anchor floor .45, floor .40 for
non-own kinds.

## Remediation applied — the gate rewrite (rounds 3–4, same day)

Implemented from the measured numbers, in the order the failures exposed the next layer:

1. **Dead rerank gate removed** (`rrs < 0.12` dropped both sides) — rerank now
   orders, never filters. Floors became the gate: anchor .45 / lived .45 /
   ownpast .35 / shared .40.
2. **Videos gated**: only enrich when real passages matched (empty relay → no videos).
3. **Return cap** 5 → 7, relay break 6 → 7, total sources capped at 7 (videos
   take the leftover room).
4. **Context rule sharpened** in both SYSTEM prompts + worker Context header:
   background is vocabulary, never a quoteable source (killed the
   "delusion-moha.md" citation with zero sources).
5. **Per-kind quota pool** — the 575-dialogue hxrmxs corpus flooded the top-30
   and squeezed lived/canon/trika out before floors saw them; pool = top-30 +
   top-4 lived + top-3 canon + top-4 trika (floor-passing only), pool cap 40
   (the old `slice(0,30)` was truncating the quota — caught in round 3).
6. **Graph stage gated on a floor-passing tension anchor** — forced-raw-0.5 graph
   entries were laundering pool-failed junk (rt07: debt-in-pool → roots →
   abhidhamma/shame passages with a reply that cited none of them).

### Final state (round 4, live)

| case | sources | verdict |
|------|---------|---------|
| rt03 similar-people | 7 incl. **DhO: Eric's Practice Log** + canon + anchor + diary | F5 CLOSED |
| rt05 practice-phenomenology | 7: **Trika ×2 first**, lived ×2, diary; reply relays TĀ 15 | F2 CLOSED |
| rt07 off-topic pizza | **0**, reply honest + lobha question | F4 CLOSED (graph + videos + floors all quiet) |
| rt06 mixed lens | Trika ×2 + lived ×3 + Buddhist dialogue, reply quotes Kaccana | intact |
| rt04 vimarśa | Trika ×2, no tension hijack | F3 CLOSED |
| rt09 diary | own entries/day-02 relayed verbatim | F1 stays closed |

Known cosmetic: relay excerpt slices can cut mid-word in a quote (Upton
"perience…"), and sources≠reply overlap remains by design (the model judges
coverage; the list shows what cleared floors) — both accepted for now.



**F1 FIXED** (entries/ + essays/ → kind `own-diary`, ownpast tier, BOOST 1.35 —
11 chunks embedded, relay uploaded, worker redeployed). Validation re-probe rt09:
`own entries/day-02` now ranks #2 and the reply opens "From your diary: …" with his
verbatim day-02 words. rt05 re-probe confirms F2/F3 unchanged (open, proposals above)
— recorded, not hacked around.

*Method note: every case single-turn, fresh sid, latency 9–22s, models = bge-m3 embed,
bge-reranker, deepseek-v4-flash draft (all free tier).*
