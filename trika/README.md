# trika/ — Trika relay corpus (kind `trika`)

## Why

The owner writes diary entries about mantra-body practice (mātṛkā, nyāsa, uccāra).
The relay's Buddhist/lived corpus cannot match that vocabulary — metaphysical queries
("what is happening when I install sounds on the body") returned only generic matches.
Buddhism = experience material; Trika = metaphysical answers; both belong in the relay.
Verdict (owner): worth it — this corpus is what his own entries will talk about.

## Design

- **kind `trika`** → **lineage tier** (same slot class as canon/Upton/teacher-answer:
  floor .28, rerank gate .12, BOOST 1.2). Order maps keyed by tier name — unchanged.
- **lineage slots 1 → 2** (worker `slots` + serve `_slots`): mixed queries can now
  carry one canonical Buddhist + one Trika passage together instead of competing
  for a single seat.
- Mapped in ALL places (HANDOVER gotcha #7): `worker/src/index.js` (BOOST + tierOf),
  `tools/serve.py` (_BOOST + _tier), lineage slot counts in both.
- **Passages live here** (`trika/passages/*.md`), copied from the deitybody repo by
  `tools/fetch_trika.py` — repos stay separate (deitybody AGENTS lock); this dir is
  the plug, not a merge.

## Sources (v1, provenance stamped in each file header)

| Passage | From | Nature |
|---------|------|--------|
| TA15_NYASA, TA_KEY_LOCI, TA_EXTRA_HITS | deitybody corpus/extracts | TĀ 15 nyāsa: formulas, loci, variants (primary-text cites inside) |
| MV_CH3_MALINI, MALINI_VARIATIONS | deitybody | MV 3 Mālinī order/body |
| FLOOD_TANTRIC_BODY, FLOOD_PURIFICATION_BODY | deitybody | Flood notes: entextualisation, bhūtaśuddhi→nyāsa sequence (short attributed quotes) |
| BODY_GEOGRAPHY, MUSICAL-SOUND | deitybody | mātṛkā geography + sound metaphysics notes |
| PADOUX_GURU, PADOUX_HTW_BODY_WORD | deitybody | Padoux extracts: guru/grace; body + Word/mantra (ch.5/7) |
| pathway, architecture | deitybody docs | 8-phase pathway, textual spine, epistemic locks |
| ptv_nights | deitybody data (rendered to md) | PTv vowel powers per locus (restatement, recension labeled) |
| curriculum_cards | deitybody practice | how-to-perform instructions (ASSEMBLY, sources per card) |

All are project notes citing primary texts — internal-relay use with labels intact.
Long copyrighted translations are NOT copied; only short attributed quotes.

## Refresh / build

```bash
python3 tools/fetch_trika.py        # re-copy from /root/deitybody
python3 tools/build_index.py        # incremental: only new ids embed (bge-m3 pinned)
# upload to R2 relay/:
#   corpus/vectors.json  -> relay/vectors.json
#   corpus/index.json    -> relay/index.json
cd worker && node build.mjs && CLOUDFLARE_API_TOKEN=$(cat /root/.cf-api-token) wrangler deploy
```

Keep passage count modest (hundreds, not thousands): the index rides R2 as JSON —
the hxrmxs-bulk→Vectorize migration note in HANDOVER applies here too.

## Next (not built): vis Trika mode

NOT a mapping of lobha/dosa/moha onto malas — those threes are not the same threes
(doing so would be invented doctrine). If built: a parallel vis *lens* sharing the
same circle machinery, decode key here (malas + kañcukas in the owner's language,
SOURCE-labeled), tensions optionally tagged `trika:` in frontmatter (additive field,
ask before schema changes).
