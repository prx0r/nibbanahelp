# Trika passage: architecture

Source: deitybody/docs/ARCHITECTURE.md — project notes citing primary texts (quotes short, attributed inline). Copied by tools/fetch_trika.py.

# DeityBody Architecture — Trika is the OS

> **Operating system:** Abhinavagupta / Trika.
> **Tool kit:** Goswami / Laya Yoga — only where it improves breath, concentration, elemental visualization, somatic sensitivity.
> **Repo:** `/root/deitybody` · Date: 2026-10-04

---

## Textual spine (strict order)

```text
Mālinīvijayottaratantra (MV)
    → Abhinavagupta: Tantrāloka · Tantrasāra · Parātrīśikāvivaraṇa
        → selected Vijñānabhairava dhāraṇās
```

| Tier | Text | Job here |
|------|------|----------|
| 1 | **Mālinīvijayottaratantra** | Mātṛkā/Mālinī order; body-of-Mālinī; nyāsa base |
| 2 | **Tantrāloka / Tantrasāra / PTv** | Sound metaphysics; three nyāsas; madhyamā-vāc; varṇa-uccāra |
| 3 | **Vijñānabhairava (selected)** | Self-executing techniques that serve the phonemic body |

Somadeva Vasudeva’s critical edition of MV is the serious modern scholarly reference for its yoga.

---

## What we train

**Visual + phonetic + respiratory + tactile + attentional embodiment of Sanskrit.**

Not: `क = ka = flashcard symbol`.

But:

```text
क → /ka/ → its articulation → its bodily location
   → its Devanāgarī glyph → its felt resonance
   → its place inside a larger Śakti-body
```

**Success signal:** hearing or thinking **ka** fires glyph + articulation + bodily location simultaneously.

That is excellent Sanskrit training even before metaphysical claims.

---

## Why this is Abhinavagupta, not bolted-on kundalini

Abhinavagupta himself:

- regards the *Mālinīvijayottara* as essential Trika scripture
- presents the alphabet as divine power (phonemes developed from anuttara, ānanda, icchā, unmeṣa — Tantrasāra)
- says *śabdarāśi* (mass of sound) is Bhairava; differentiated phonemic power is Mātṛkā; through intermingling she becomes Mālinī (**Tantrāloka 3.198–199**)
- explicitly installs Mātṛkā and Mālinī nyāsa on the body (TĀ 15)
- gives permission not to torment the body with prāṇāyāma (**TĀ 4.91**)

This is not kundalini bolted onto Sanskrit. It is his system.

---

## Two coordinate systems (advanced)

| System | Body | Role |
|--------|------|------|
| **Mātṛkā / Mālinī** | phonemic body | Primary OS — glyph = sound = locus |
| **bhūta / cakra** | elemental-axial body | Goswami tool layer — later overlay |

Do **not** replace Abhinavagupta’s phonemic anatomy with Goswami’s chakra chart. Investigate superimposition only after both are stable.

---

## Breath policy

| Context | Rule |
|---------|------|
| During Mātṛkā/Mālinī nyāsa | Let phonation lengthen the exhale. **Do not** force 1:4:2 while memorizing locations. |
| Separate prāṇāyāma | OK if completely comfortable. Not a prerequisite. |
| Authority | TĀ 4.91 — prāṇāyāma that torments the body is not to be practised |
| VBT carrier | saḥ (out) / haṃ (in), heart ↔ dvādaśānta — comfortable breath only |

The sophistication is in **sensitivity**, not violence.

---

## Product boundaries

| Do | Don’t |
|----|-------|
| Glyph as primary visual object | Lead with rainbow chakra colors |
| Voice as install | Invent Hz-per-phoneme doctrine |
| Provenance tags (SOURCE_ATTESTED vs PEDAGOGICAL) | Collapse body-map variants into one dogma |
| Stop always available | Competitive breath-holding |
| Keep Goswami as tool annex | Make Goswami the backbone |

---

## Relation to live stack

| Repo | Role |
|------|------|
| **deitybody (this)** | Trika phonemic-body OS: maps, protocols, corpus index |
| bruno | Memory engine / Notoria shell / Pāṇini runtime |
| stoned / stoneseed | Night audio imaginal OS + kernel protocols |
| sanskrithelp | Day frontend: zones, phoneme audio, tantra practice |
| volume tantraloka + source-library | Primary corpus deepdive source |

Do not merge repos. Plug them.
