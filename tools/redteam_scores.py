#!/usr/bin/env python3
"""redteam_scores.py — offline cosine diagnostics (no chat calls, no sessions).

Loads corpus/{index,vectors}.json, embeds probe queries with the pinned model
(bge-m3, same code path as build_index), and reports per-kind score structure
for red-team findings F2 (trika recall), F3 (tension hijack), F5 (lived logs).

  python3 tools/redteam_scores.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ai import embed_batch

ROOT = Path(__file__).resolve().parent.parent

PROBES = [
    ("rt05", "during the vowel install I feel heat and pressure in my chest, is that normal in the matrika body"),
    ("rt10", "does the guru have to find you first or can you start the practice alone"),
    ("rt04", "what is vimarśa and why does Abhinavagupta say the light of consciousness is felt"),
    ("rt03", "how do other people deal with debt while building something that does not pay yet"),
    ("rt09", "i woke up with a lot of energy singing about the money and the coffee again"),
]


def norm(v):
    n = sum(x * x for x in v) ** 0.5 or 1e-9
    return [x / n for x in v]


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b))


def main():
    idx = json.loads((ROOT / "corpus/index.json").read_text())
    vecs = json.loads((ROOT / "corpus/vectors.json").read_text())
    by_id = {i["id"]: i for i in idx}
    for pid, q in PROBES:
        qv = norm(embed_batch([q])[0])
        scored = []
        for i in idx:
            v = vecs.get(i["id"])
            if not v:
                continue
            scored.append((cosine(qv, norm(v)), i))
        scored.sort(key=lambda x: -x[0])
        print(f"\n===== {pid}: {q[:70]}")
        # top overall with kinds
        for s, i in scored[:6]:
            print(f"  ALL  {s:.3f}  [{i['kind']}] {(i['label'] or '')[:58]}")
        # per-kind bests for the finding-relevant kinds
        for kind in ("trika", "own-tension", "lived-log", "own-diary", "canon"):
            best = [x for x in scored if x[1]["kind"] == kind][:3]
            if not best:
                print(f"  {kind:12s} (none)")
                continue
            for s, i in best:
                print(f"  {kind:12s} {s:.3f}  {(i['label'] or '')[:56]}")
        # how many cleared the .28 global floor overall
        n28 = sum(1 for s, _ in scored if s >= 0.28)
        print(f"  >= .28 floor: {n28} / {len(scored)} items")


if __name__ == "__main__":
    main()
