#!/usr/bin/env python3
"""export_dharma_graph.py — nibbanahelp graph in dharma-tech's JSONL schema.

Reads tensions/ (roots, status), roots/*.md, roots/graph.yaml seed
observations. Writes corpus/dharma_graph/{passages,concepts,passage_edges,edges}.jsonl
so dharma-tech's GraphRAG runs unmodified against our lived corpus
(see tools/dharma_engine.py).
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "corpus" / "dharma_graph"
OUT.mkdir(exist_ok=True)


def header(p):
    text = p.read_text()
    head = text.split("---")[0] if "---" in text else ""
    out = {}
    for k in ("day", "visibility", "id", "status", "domain", "summary",
              "kind"):
        m = re.search(rf"^{k}:\s*(.+)$", head, re.M)
        if m:
            out[k] = m.group(1).strip()
    m = re.search(r"^roots:\s*\[(.+?)\]\s*$", head, re.M)
    if m:
        out["roots"] = [x.strip() for x in m.group(1).split(",")]
    body = text.split("---", 1)[1] if "---" in text else text
    return out, body.strip()


CONCEPTS = [
    {"id": "lobha", "label": "Greed", "label_alt": ["greed", "lust", "craving-pull"],
     "pali": "lobha", "tradition": ["theravada"],
     "definition": "Unwholesome root: pulling toward, delight that strengthens wanting. 8 lobha-mula cittas.",
     "category": "akusala-mula"},
    {"id": "dosa", "label": "Hate", "label_alt": ["hatred", "aversion", "pushing-away"],
     "pali": "dosa", "tradition": ["theravada"],
     "definition": "Unwholesome root: pushing away, aversion, from irritation to hatred. 2 dosa-mula cittas.",
     "category": "akusala-mula"},
    {"id": "moha", "label": "Delusion", "label_alt": ["delusion", "fog", "not-seeing"],
     "pali": "moha", "tradition": ["theravada"],
     "definition": "Unwholesome root: not-seeing; present in every unwholesome citta. 2 moha-mula cittas (doubt, restlessness).",
     "category": "akusala-mula"},
    {"id": "alobha", "label": "Non-greed", "label_alt": ["generosity", "contentment"],
     "pali": "alobha", "tradition": ["theravada"],
     "definition": "Wholesome root: generosity, renunciation, contentment with less.",
     "category": "kusala-mula"},
    {"id": "adosa", "label": "Non-hatred", "label_alt": ["loving-kindness", "acceptance"],
     "pali": "adosa", "tradition": ["theravada"],
     "definition": "Wholesome root: letting the feeling sit unfed; metta.",
     "category": "kusala-mula"},
    {"id": "amoha", "label": "Non-delusion", "label_alt": ["wisdom", "clear-seeing"],
     "pali": "amoha", "tradition": ["theravada"],
     "definition": "Wholesome root: seeing the temporary as temporary; discernment.",
     "category": "kusala-mula"},
    {"id": "javana", "label": "Impulsion", "label_alt": ["impulsion", "javana moments"],
     "pali": "javana", "tradition": ["theravada"],
     "definition": "7 (or 6) impulsion moments per sense-door process where kusala/akusala happens.",
     "category": "process"},
    {"id": "asevana", "label": "Repetition condition",
     "label_alt": ["repetition", "feeding", "asevana-paccaya"],
     "pali": "asevana-paccaya", "tradition": ["theravada"],
     "definition": "Each javana conditions the next by repetition: delight now builds pull later; unfed rounds weaken it.",
     "category": "process"},
]

EDGES = [
    {"id": "n01", "source": "moha", "target": "lobha", "relation": "accompanies",
     "tradition": "theravada", "weight": 1.0,
     "notes": "Moha is present in every akusala citta, including all 8 lobha-rooted ones."},
    {"id": "n02", "source": "moha", "target": "dosa", "relation": "accompanies",
     "tradition": "theravada", "weight": 1.0,
     "notes": "Moha is present in both dosa-rooted cittas."},
    {"id": "n03", "source": "asevana", "target": "javana", "relation": "conditions",
     "tradition": "theravada", "weight": 1.0,
     "notes": "Repetition condition: each javana feeds the next."},
    {"id": "n04", "source": "alobha", "target": "lobha", "relation": "opposes",
     "tradition": "theravada", "weight": 1.0, "notes": "Wholesome counterpart."},
    {"id": "n05", "source": "adosa", "target": "dosa", "relation": "opposes",
     "tradition": "theravada", "weight": 1.0, "notes": "Wholesome counterpart."},
    {"id": "n06", "source": "amoha", "target": "moha", "relation": "opposes",
     "tradition": "theravada", "weight": 1.0, "notes": "Wholesome counterpart."},
]


def main():
    passages, pedges = [], []
    # 1. tensions as passages, linked to their roots
    for p in sorted((ROOT / "tensions").glob("*.md")):
        h, body = header(p)
        if h.get("status") not in ("open", "loosening"):
            continue
        pid = f"tension-{p.stem}"
        roots = h.get("roots", [])
        passages.append({"id": pid, "text_id": f"tensions/{p.name}",
                         "passage_index": 0, "text": body[:1500],
                         "summary": h.get("summary", ""),
                         "status": h.get("status", "open"),
                         "concepts_mentioned": roots})
        for r in roots:
            pedges.append({"source": pid, "target": r,
                           "relation": "diagnosed_as", "text_id": p.stem})
    # 2. roots docs as passages, self-linked
    for name, root in [("greed-lobha.md", "lobha"),
                       ("hatred-dosa.md", "dosa"),
                       ("delusion-moha.md", "moha"),
                       ("antidotes.md", None),
                       ("abhidhamma.md", None)]:
        p = ROOT / "roots" / name
        if not p.is_file():
            continue
        _, body = header(p)
        pid = f"roots-{p.stem}"
        roots = [root] if root else []
        if root is None:
            roots = ["alobha", "adosa", "amoha"] if "antidotes" in name else ["lobha", "dosa", "moha"]
        passages.append({"id": pid, "text_id": f"roots/{name}",
                         "passage_index": 0, "text": body[:1500],
                         "concepts_mentioned": roots})
        for r in roots:
            pedges.append({"source": pid, "target": r,
                           "relation": "explains", "text_id": name})
    for name, rows in [("passages.jsonl", passages),
                       ("concepts.jsonl", CONCEPTS),
                       ("passage_edges.jsonl", pedges),
                       ("edges.jsonl", EDGES)]:
        with open(OUT / name, "w") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(passages)} passages, {len(CONCEPTS)} concepts, "
          f"{len(pedges)} passage edges, {len(EDGES)} edges -> {OUT}")


if __name__ == "__main__":
    main()
