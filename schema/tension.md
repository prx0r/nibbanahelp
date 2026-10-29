# Tension record

One file per tension. Plain language. Example: `tensions/coffee-addiction.md`.

```yaml
id: coffee-addiction          # slug
diarist: ...                  # handle
opened: 2026-10-28            # first logged
status: open | loosening | resolved
domain: money | addiction | identity | relationship | health | doubt | other
roots: [lobha, moha]          # which of the three roots feed it
summary: one-line plain statement
```

Then free text below: history, how it grips, what loosening would look like.
Update `status` over time — the arc of a tension from open to resolved is
the most valuable data in this repo.

## Progress

Tensions are persistent entities. Don't rewrite history — append dated notes:

```
## Progress

### YYYY-MM-DD

What changed, in your own words. Verbatim, unedited.
```

Flip `status` to `loosening` when it shifts, `resolved` when it's done.
The original entry stays untouched; the progress log is the story.
