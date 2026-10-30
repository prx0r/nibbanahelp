#!/usr/bin/env python3
"""fetch_trika.py — copy curated Trika passages from the deitybody repo.

Repos stay separate (deitybody AGENTS: plug via contracts, never merge).
This writes trika/passages/*.md with a stamped provenance header, then
build_index.py chunks them as kind=trika (lineage tier).

  python3 tools/fetch_trika.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "trika" / "passages"
DEITY = Path("/root/deitybody")

# (source path relative to /root/deitybody, output stem)
FILES = [
    ("corpus/extracts/TA15_NYASA.md", "ta15_nyasa"),
    ("corpus/extracts/TA_KEY_LOCI.md", "ta_key_loci"),
    ("corpus/extracts/TA_EXTRA_HITS.md", "ta_extra_hits"),
    ("corpus/extracts/MV_CH3_MALINI.md", "mv_ch3_malini"),
    ("corpus/extracts/MALINI_VARIATIONS.md", "malini_variations"),
    ("corpus/extracts/FLOOD_TANTRIC_BODY.md", "flood_tantric_body"),
    ("corpus/extracts/FLOOD_PURIFICATION_BODY.md", "flood_purification"),
    ("corpus/extracts/BODY_GEOGRAPHY.md", "body_geography"),
    ("corpus/extracts/MUSICAL-SOUND.md", "musical_sound"),
    ("corpus/extracts/PADOUX_GURU.md", "padoux_guru"),
    ("corpus/extracts/PADOUX_HTW_BODY_WORD.md", "padoux_htw_body_word"),
    ("docs/PATHWAY.md", "pathway"),
    ("docs/ARCHITECTURE.md", "architecture"),
    ("practice/CURRICULUM_CARDS.md", "curriculum_cards"),
]


def render_ptv() -> str:
    doc = json.loads((DEITY / "site/data/ptv_nights.json").read_text())
    lines = ["# PTv vowel powers per locus (Parātrīśikāvivaraṇa)",
             "",
             "Source: deitybody site/data/ptv_nights.json — restatement of Jaideva "
             "Singh's recension vowel table; loci per TĀ 15 (verse-literal). "
             "Ṛ/ḷ/ḹ carry no gloss in the table — held in silence.", ""]
    for n in doc["nights"]:
        lines.append(f"## Night {n['n']} — {n['title']}")
        for ph in n["phonemes"]:
            lines.append(f"- **{ph['id']}** ({ph['dev']}) at {ph['locus']}: {ph['power']}")
        lines.append("")
    return "\n".join(lines)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    copied = 0
    missing = []
    for rel, stem in FILES:
        src = DEITY / rel
        if not src.is_file():
            missing.append(rel)
            continue
        body = src.read_text(encoding="utf-8", errors="ignore")
        header = (f"# Trika passage: {stem}\n\n"
                  f"Source: deitybody/{rel} — project notes citing primary texts "
                  f"(quotes short, attributed inline). Copied by tools/fetch_trika.py.\n\n")
        (OUT / f"{stem}.md").write_text(header + body, encoding="utf-8")
        copied += 1
    (OUT / "ptv_nights.md").write_text(
        "# Trika passage: ptv_nights\n\n"
        + render_ptv(), encoding="utf-8")
    copied += 1
    print(f"fetched {copied} passages -> trika/passages/")
    if missing:
        print("MISSING:", *missing, sep="\n  ")


if __name__ == "__main__":
    main()
