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

Made by `python3 tools/tension.py new --tension <id>`.
Everything verbatim — your words and the AI's, unedited. The embedding is
stored so future matches improve without re-asking; re-run
`tools/build_index.py` if tensions or corpora change.
