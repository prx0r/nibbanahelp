# Self-advice loop ("echo")

## The function

1. **Capture:** the AI asks you: *"What would YOU say to someone in this
   situation?"* — asked per open tension, in two framings:
   - to a dear friend in exactly this situation (unlocks compassion you
     won't grant yourself)
   - from future-you, one month past it (unlocks perspective)
2. **Store:** your words, verbatim, timestamped, linked to the tension id.
   (`advice/YYYY-MM-DD-<tension-id>.json`)
3. **Playback:** when the tension is alive again — a week later, a month
   later — the AI outputs **your words back to you first**, its own advice
   second. You get counsel from the one person you can't dismiss: yourself,
   on a clear day.

## Why own-words beat AI-words

- No authority problem: you can't reject your own voice as "not getting it".
- No dependency: the loop trains self-interview (Chah: "examine your own
  mind-states, interview yourself"), not guru-dependence.
- Growth record: playbacks stack. Week-4 you hears week-1 you and laughs —
  that laugh is measurable progress.
- Friend-framing bypasses the shame-armour (day-01 tension): you'd never
  speak to a friend the way you speak to yourself.

## Relation to the graph

- Capture prompts are generated from open tensions (`tensions/*.md`,
  `status: open`).
- Playback triggers when a tension is re-logged or still open at review.
- Over time, advice records become training pairs: situation → own-wisdom.
  The AI learns how *you* heal, not how textbooks say people heal.

## Tool

`tools/echo.py` — stdlib only, no deps.

```bash
python3 tools/echo.py capture            # asked the question per open tension
python3 tools/echo.py playback           # your words back, for open tensions
python3 tools/echo.py playback --tension coffee-addiction
```
