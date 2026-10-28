# Essays

Diary is raw. Essays are worked: a diary entry (or several) distilled into
something speakable — then spoken, and pinned to a day.

## Flow

```
entries/ (raw, any visibility)
   → essays/ (worked, has day + visibility + voice)
   → spoken audio (own voice or TTS, local audio/ + R2)
   → assigned to its day (tools/day.py bundles it)
```

## Fields (header block, same style as entries)

```
day: 1
visibility: private | public
voice: own | tts:<engine>
audio: audio/day-01-what-nibbana-is-like.mp3   # relative to repo root
```

- `visibility: private` = never leaves the repo. Default. The day-01
  material stays private until the diarist flips it.
- `visibility: public` = cleared for publishing (site, readings, sharing).
  Only the diarist flips their own.
- Spoken audio lives in `audio/` locally; mirrored to R2 under
  `nibbanahelp/audio/`. Text is canonical — audio is the same essay aloud.

## Rule

An essay is only public if every person named in it consents. Diarist's own
material, diarist's call — nobody else's.
