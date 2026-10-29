# sessions/

Untangling records. One JSON per session:

```json
{
  "date": "2026-10-28",
  "tension": "coffee-addiction",
  "tension_text": "verbatim tension at session start",
  "embedding": [0.01, ...],
  "matches": [{"id": "...", "label": "...", "url": "...", "score": 0.71}],
  "chat": [{"you": "...", "ai": "..."}]
}
```

Made by `python3 tools/tension.py new --tension <id>`, or by the chat
(`sessions/chat-*.json`, recorded live with relayed sources).
Everything verbatim — your words and the AI's, unedited. The embedding is
stored so future matches improve without re-asking; re-run
`tools/build_index.py` if tensions or corpora change.

## Stacking self-answers

When you answer your own question mid-chat, that is the most valuable
record in the repo. `tools/stack.py` scans new chat sessions and writes a
sidecar each (`chat-<id>.analysis.json`): tensions mentioned, your own
verbatim insights, roots tags, suggested tension updates. Nothing is
auto-filed into tensions/ — you confirm, then it lands as a dated
`## Progress` note. The AI's job is logging, tagging, analysing, and
playing your words (or others' lived words) back to you — never advising.
