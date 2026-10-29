# Process notes — how this got built, what broke, what's locked in

Written 2026-10-29 after the page finally stopped moving. Read before
touching the frontend.

## Mistakes made (each one cost a round)

1. **Shipped interactions I couldn't click.** No browser on the box, so the
   first five versions of tap/scroll/edit behavior were guesses. Fix: stood
   up headless Chromium as a phone (`ms-playwright`, `click_test*.py` in
   /tmp). Tap everything, measure everything, screenshot everything.
   Never ship a UI change without a headless tap test again.
2. **Invisible tap zones.** Made kid links big for thumbs but left them
   looking like plain text — taps on "blank space" fired links and the page
   "randomly" switched essays. Rule: if it's tappable it looks tappable.
   Blank space must be dead — verified by tapping it.
3. **Editor measured before it existed.** `fit()` ran before the textarea
   was in the DOM, measured ~0 height, page collapsed 1700px and the finger
   landed on whatever slid underneath. Rule: measure after insertion, and
   keep a floor (`Math.max(original, scroll)`).
4. **Swapping elements to edit.** Replacing rendered HTML with a fresh
   textarea moved the page on open. Fix: overlay in place — hide the original
   with `visibility` (space preserved by definition), absolutely-positioned
   transparent editor on top. Nothing may ever reflow on tap.
5. **Committed a stale generated bundle.** Edited source, forgot to rebuild
   `site/index.html` + worker bundle, deployed old content while saying it
   was fixed. Rule: rebuild both before every commit; `grep` the output,
   don't trust the pipeline. (`site/index.html`, `worker/src/page.js`,
   `files.js`, `anchors.js` are all generated.)
6. **Deleted possibly-user data while debugging.** Cleared R2 pending keys
   of unknown provenance during a test. Rule: back up before deleting
   anything that isn't provably yours.
7. **Tested on live.** Typed test strings into the production worker; the
   autosave + sync loop faithfully published graffiti to the public site.
   Rule: all tap/typing tests run against local serve ports only.
8. **Raced myself with cron + manual deploys.** The 3-min sync loop can
   interleave with manual work and resurrect things just cleaned. Rule:
   after any manual cleanup, check `git log` + live output, not assumptions.
9. **Three copies of the CSS.** site.py, serve.py, worker index.js each carry
   the stylesheet; they drifted twice. Partial fix: single `GAP` constant in
   site.py, worker `theme.js` generated at build. The rest is still manual —
   check all three on any visual change.
10. **Lost work with `git reset --hard`.** Uncommitted changes wiped.
    Rule: commit before any test that mutates the tree; test commits get
    reverted with `--hard + force-push` only when the tree is otherwise clean.

## Locked in (do not reopen without asking)

- White page, black text, monospace. Nothing on screen the owner didn't write.
- Only four render rules: `**bold**`, `__underline__`, `*italic*`, `#` → bold.
- One square per day in the left rail. Tap toggles that day's kids, nothing else.
- Kids are plain text, kinds only (`diary`, `essay`/`poem`, `audio`, `video`, `note`).
- Tapping body text opens an in-place transparent editor. Zero layout shift,
  autosaves, syncs to the repo every 3 minutes via cron + R2.
- Motto: max 5 lines, newest darkest (`#333` → `#bbb`), quoted, centred.
- Prosecco rule for spacing: left screen edge to nav == nav to body (`GAP`).
- Content rules: everything public is the practice; no names needed; upload
  time IS the timestamp; old material flagged `backfill`, never re-dated.
- AI rules: the relay matches + relays with provenance, never generates
  advice. Abhayagiri is link-first only. Tensions are persistent entities
  with dated progress notes; `resolved` ends them, nothing is rewritten.
