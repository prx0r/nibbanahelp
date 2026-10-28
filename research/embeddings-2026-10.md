# Embeddings, Oct 2026: what matters for the relay

Searched + probed 2026-10-28. All verified live on our free Cloudflare
Workers AI account (no new infra, no spend).

## SOTA landscape (this month)

- **Qwen3-Embedding** dominates MTEB (8B overall top, 4B size-group leader).
  Open weights, Apache 2.0.
- **jina-embeddings-v5** (nano/small) are the Pareto leaders under 500M.
- **EmbeddingGemma 2** (Oct 6, 2026): 740M, Apache 2.0, text+code+image+
  video+audio in ONE 768-dim space, MRL truncation (128–768 dims), 100+
  languages, 8k context, task-steered prefixes. The cool one.
- Voyage-4, NV-Embed, harrier-oss: API/large, irrelevant while free tier
  covers us.

## What we probed (all live, all working)

| Model | Dim | Notes |
|---|---|---|
| `@cf/baai/bge-base-en-v1.5` | 768 | current index. English-only, 6058 neurons/M tokens |
| `@cf/baai/bge-m3` | 1024 | multilingual, 60k context, **1075 neurons/M (5.6× cheaper)** |
| `@cf/qwen/qwen3-embedding-0.6b` | 1024 | SOTA family, same cheap price as m3 |
| `@cf/google/embeddinggemma-300m` | 768 | compact Gemma embedder, multilingual |
| `@cf/baai/bge-reranker-base` | — | cross-encoder; input `{"query", "contexts":[{text}]}` → scored ids. Verified: smoking-passage 0.053 vs bonds 0.00003 |

## Recommendation for nibbanahelp

1. **Switch index to bge-m3.** Reasons, in order: multilingual (Thai/Chinese/
   German corpus is coming — Nanavira ×5 langs, Jayasaro ×4, Tejaniya ×13),
   60k context (embed FULL logs, not summaries), cheapest neurons, still BGE
   quality. One re-index (~15 min), zero code changes beyond model name.
2. **Add rerank stage.** Retrieve top-20 by cosine, rerank to top-5 with
   bge-reranker-base. Cross-encoders beat bi-encoders at "which lived
   experience is TRULY closest" — our exact bottleneck. Cost: ~0.01 neurons
   per query. Format: `contexts: [{text}]`.
3. **EmbeddingGemma later, for audio.** When spoken essays + talk audio enter
   the corpus, one unified space for text+audio beats chaining STT +
   text-embed. Not needed while the corpus is text.
4. **Task prefixes now (free).** Prefix queries ("search for lived
   experience: ...") and docs ("passage: ...") — instruction-steered
   retrieval, works on any of the above.

## What NOT to do

- Don't chase MTEB top (Qwen3-8B) via paid API: our corpus is ~1k items,
  the bottleneck is corpus coverage + rerank, not 2 points of retrieval.
- Don't store 1024-dim floats forever: MRL/truncation or fp16 when the
  index passes ~100k items. At current scale vectors.json is trivial.
