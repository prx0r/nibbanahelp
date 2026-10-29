# Dhamma AI landscape (searched 2026-10-29)

Who built what, and where nibbanahelp's relay sits among them.

## The closest cousin: dharma-tech (joyboseroy/dharma-tech, MIT, 2026)

Open-source Buddhist AI: local LLM + knowledge graph + agents. Passage
index (1,126 segments, 10 canonical sources), quote verification ("is this
actually canonical?"), cross-tradition comparison via typed graph edges,
Anki from concepts, ngondro/practice tracking, lojong slogans.
Their thesis, verbatim in spirit: *"Most 'Buddhist AI' projects are
chatbots with a system prompt saying 'answer like a monk.' This repo is
different."* — ours says the same thing from the other side: no
generation at all, only relay with provenance.
**Steal:** quote-verification as a relay step (we have fojin verify;
wire it into chat answers that cite canon); typed-graph edges as the
join key (our graph.yaml roots play the same role — compare designs).
**Differ:** they have no lived-diary corpus, no tensions, no practice loop.

## The original retrieval bot: BuddhaBot (Kyoto Univ, Kumagai lab)

The 2021 BuddhaBot was **non-generative**: Suttanipāta + Dhammapada +
Udānavarga embedded with Sentence-BERT, nearest-passage returned. That is
our architecture, five years early, and it got deployed to 200+ Bhutan
monks (2025-26), now a full robot monk (Buddharoid, Kodai-ji, Feb 2026).
The 2023 BuddhaBot-Plus bolted on ChatGPT generation ("natural answers") —
exactly the step we refuse. VasubandhuBot (Abhidharmakośa) and ShinranBot
show the lineage-specific-bot pattern our roots mapping could follow.
**Lesson:** retrieval-only was credible enough for a monastic body; the
generative turn was product pressure, not dharma pressure.

## The advising kind (our anti-pattern, stated plainly)

- **NORBU** (norbu-ai.org): Tipitaka + commentaries + academia, and it
  *offers practical daily-life advice*. Competent, honest, and precisely
  what the relay refuses: advice from no-lived-experience.
- **dharma-ai.app** ($10–100/mo): RAG "AI teachers", voice cloning,
  API access. Commercial simulacra with pricing tiers.
- **jenova.ai Buddhist Monk AI + Eightfold Path platform** (2026):
  tradition-adaptive guidance, study guides, contemplation exercises.
- **AskBuddha**: "chat with AI Buddha", answers anything.
- **Roshibot** (character.ai Suzuki): persona simulation WITH honest
  disclaimers — "can replicate the greed, hate and delusion of the
  internet." The Abhayagiri archive says please don't build simulacra;
  Roshibot is why.
- **Emi Jido** (Hong Kong, ordained chatbot, Tricycle Fall 2025 cover):
  the endpoint of the simulacrum road — ordained, precept-held, still
  generating.

## The discourse around it

- Buddhistdoor 6-part series (Oct 2026): current AI use is mostly
  translation + passable simulacra; "naïve at best, spiritual bypassing
  at worst."
- Buddhism & AI Initiative survey (100+ Buddhists, Oct 2025): teachers
  split — some embracing, some afraid; real fear of AI slop flooding
  ("thousands of videos answering questions... shallow or misleading").
- Dharma Setu paper (2025): 10B-token BDRC corpus, vector ops as
  pramāṇa — academic cousin of our embedding index.
- Tricycle "Chatbot Dharma" (Fall 2025), Buddhistdoor symposium: the
  establishment is watching, nobody has set norms.

## Where the relay sits (the gap)

| Need | Who does it | Relay status |
|---|---|---|
| Scripture-grounded answers | BuddhaBot, NORBU, dharma-tech | ✅ canon JSON in corpus/ |
| Lived-practice corpus | DhO logs, johnduality (not AI) | ✅ 932 logs indexed |
| Zero-generation relay | **nobody** | ✅ this repo's law |
| Diary as training context | nobody | ✅ entries/tensions/sessions |
| Roots-mapped Q&A | nobody | ✅ graph.yaml + vis |
| Cetasika-level probing | nobody (Upton teaches humans) | 🚧 abhidhamma.md + chat prompts |

Nobody combines a public practice diary with a non-generating relay.
The commercial bots advise; the academic ones retrieve scriptures; the
forums log practice without AI. The open slot is exactly this: **your
tensions, matched to real others' tensions, answered only in the words
of teachers who lived it.**
