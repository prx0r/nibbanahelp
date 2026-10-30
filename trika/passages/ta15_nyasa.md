# Trika passage: ta15_nyasa

Source: deitybody/corpus/extracts/TA15_NYASA.md — project notes citing primary texts (quotes short, attributed inline). Copied by tools/fetch_trika.py.

# Tantrāloka 15 — Nyāsa extracts (Dyczkowski apparatus on volume)

> Source file: `/mnt/HC_Volume_106959365/root/projects/source-library/tantra/abhinavagupta/ahnika-15.txt`
> Companion notes: `corpus/index/RESOURCES.md`
> Practice encoding: `data/matrika_body_map.json` · `data/malini_order.json`

---

## Frame (Appendix A intro)

Abhinavagupta stresses that basic Trika rites are heralded by **three depositions (nyāsa)** onto the body:

| Nyāsa | Character | Order |
|-------|-----------|-------|
| **Mātṛkā** | feminine | normal alphabetical order |
| **Mālinī** | feminine | seeds (vowels/bīja) mixed with matrices (consonants/yoni) |
| **śabdarāśi** | male | Assembly of Sounds — fifty Bhairavas |

References: **TĀ 15/115cd–145**. Mātṛkānyāsa normally begins. Base drawn from **MV 8/27–32**.

> “By performing the deposition of the hands (karanyāsa) … the hands become full of the energy of mātṛkā.”
> “By placing the consecrated hands on the different parts of the body with the appropriate sounds, the whole body is consecrated and **transformed into mātṛkā**.”

---

## Aṅganyāsa (limb deposition) — compressed formula

| Locus | Formula |
|-------|---------|
| Heart | `aṅ kaṁ khaṁ ghaṁ ṅaṁ āṁ hr̥dayāya namaḥ` |
| Head | `iṁ caṁ chaṁ jaṁ jhaṁ ñaṁ īṁ śirase svāhā` |
| Shoulders (kavaca) | `eṁ taṁ thaṁ daṁ dhaṁ naṁ aiṁ kavacāya hūṃ` |
| Three eyes | `oṁ paṁ phaṁ baṁ bhaṁ maṁ auṁ netratrayāya vauṣaṭ` |
| Hands (astra) | `arṁ yaṁ raṁ laṁ vaṁ śaṁ ṣaṁ haṁ laṁ kṣaṁ aḥ karatalapṛṣṭhābhyām astrāya phaṭ` |

Useful as a **rapid install sequence** after slow locus-by-locus work.

---

## Tattvamudrā body loci (Mātṛkā apparatus, abridged)

Vowel field on head/face (as encoded in `matrika_body_map.json`):

- forehead / topknot / mouth
- right eye · left eye
- right ear · left ear
- right nostril (piṅgalā) · left nostril (iḍā)
- right cheek · left cheek
- lower teeth · upper teeth
- lower lip · upper lip
- tongue

Consonant limbs:

- right upper limb: ka → kha → ga → gha → ṅa
- left upper limb: ca → cha → ja → jha → ña
- right lower limb: ṭa-varga
- left lower limb: ta-varga
- torso: pa/pha sides · ba back · bha belly · ma heart
- deeper: ya skin · ra blood · la flesh · va sūtra (sinews) · śa bone · ṣa marrow · sa essence · ha prāṇa · kṣa generative

---

## Mālinī order (Appendix B)

Source: **MV 3/37–41ab**, reproduced in **TĀ 15/121–125ab**.

Canonical sequence (nādiphāntā — begins **na**, ends **pha**):

```text
na ṛ ṝ ḷ ḹ tha ca dha ī ṇa u ū ba
ka kha ga gha ṅa i a va bha ya ḍa ḍha ṭha jha ña ja ra ṭa
pa cha la ā sa aḥ ha ṣa kṣa ma śa aṃ ta e ai o au da pha
```

Mālinīnyāsa opening (yoginī names optional for secular phonemic training):

```text
oṁ sauḥ naṁ nandinī ai namaḥ
oṁ sauḥ ṛṁ nivṛtty ai namaḥ
… continue mutatis mutandis through the order …
```

Body-of-Mālinī principle (MV 4/116cd–118ab, summarized in apparatus): Earth in **pha**; other tattvas distributed through the Mālinī phonemes; Śakti-body rather than grammar chart.

**Practice encoding:** `data/malini_order.json` (order + body_map + Month-2 zones).

---

## Śabdarāśinyāsa (Appendix C)

Third deposition — Assembly of Sounds. Opening formula variants:

```text
oṁ raḥ harakṣa malavayūm śrīkaṇṭhāya namaḥ
# Kubjikā variant:
aiṁ hrīṁ śrīṁ hsaḥ khpḥremaḥ hsaḥ auḥ aṁ śrīkaṇṭhāya namaḥ
```

Body loci largely mirror the Mātṛkā tattvamudrā list (forehead → mouth → eyes → ears → nostrils → cheeks → teeth → lips → limbs → deep constituents).

**Role in this OS:** third coordinate — male śabdarāśi (50 Bhairavas). Encode later as optional layer after Mātṛkā + Mālinī are stable.

---

## Other loci worth extracting next

| Loci | Content |
|------|---------|
| TĀ 3.198–199 | śabdarāśi / Mātṛkā / Mālinī metaphysics |
| TĀ 4.91 | prāṇāyāma without tormenting the body |
| Tantrasāra (Āhnika 5 / varṇa-uccāra notes) | Rite of the Phonemes |
| PTv pp. 148–156 | Mālinī at madhyamā-vāc |
| TĀ Āhnika 11 | varṇa as pramā; ṣaḍadhvan |

Extract script: `scripts/deepdive_tantraloka.py`.

---

## Verse vs apparatus (resolved 2026-10-05, volume-checked)

Two Abhinavagupta-tradition readings of the arm series. Both source-attested — never collapse them.

**Project decision (peer review 2026-10-05): verse-literal is canonical**
(`matrika-body-map-v2`, regression-tested). The apparatus survives only as a
recorded per-entry variant, never used for install.

| Phonemes | Verse (TĀ 15.118 GRETIL) | Apparatus (Dyczkowski vol 8, App. A + C, number-paired) |
|----------|--------------------------|----------------------------------------------------------|
| ka / ca | skandha — shoulder | Right/Left shoulder (agree) |
| kha / cha | bāhu — arm | Right/Left arm (agree) |
| ga / ja | **kara — hand** | Right/Left **elbow** |
| gha / jha | **aṅguli — fingers** | Right/Left **wrist** |
| ṅa / ña | **nakha — nails** | **Fingers** of the hand |

Verse text: `dakṣānyayoḥ skandha-bāhu-kara-aṅguli-nakhe kacau vargau` (TĀ 15.118).
Apparatus tables (Mātṛkānyāsa App. A + Śabdarāśinyāsa App. C) agree with each other — deliberate, not a slip.
Same split: ṭa/ta verse `kaṭi` (**hip**, TĀ 15.119) vs apparatus **buttock**; `a` verse `lalāṭa` (**forehead**, TĀ 15.117) vs App. A locus 1 = **Topknot**.

**Encoding rule:** `matrika_body_map.json` AND `matrka-data.json` both follow the verse literally
(canonical v1, regression-tested). Apparatus survives only as `apparatus_variant` per entry + readout on the integrated wheel, never used for install.
Unresolved from disk: whether apparatus follows MV 8/27–32 wording against the verse, or a kara-as-joints gloss (needs MV Sanskrit or Jayaratha — neither on volume).
