# advice/

Your own words, played back to you.

One JSON per capture: `advice/YYYY-MM-DD-<tension-id>.json`

```json
{
  "date": "2026-10-28",
  "tension": "coffee-addiction",
  "situation": "one-line summary at capture time",
  "to_friend": "what you'd say to a dear friend in it",
  "from_future_self": "what month-past-you would say"
}
```

Created by `python3 tools/echo.py capture`, read back by
`python3 tools/echo.py playback`. Verbatim — never edited after capture.
