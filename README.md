# Lost & Underfound

A point-and-click adventure game built to a classic Humongous Entertainment-era
quality bar: bouncy, expressive, personality-first character animation and goofy
exploration-driven puzzle design. Original property, original cast.

This repo holds the creative/design package, animation production rules, registration
QA tooling, Act 1 script/design data, an Act 1 audio pass, and the first playable web
scaffold.

## What's Here

- **`docs/GAME_CONCEPT.md`** - the pitch: premise, tone, full cast with
  personalities, and the target 3-act structure.
- **`docs/ANIMATION_BIBLE.md`** - binding animation production rules synced from
  `BadBagger/Animation-Bible`. Edit rules upstream, not here.
- **`docs/CODEX_BUILD_PROMPT.md`** - the build brief and required build order.
- **`tools/check_registration.py`** - the hard QA gate for per-sheet frame
  registration and cast-scale parity.
- **`art/cast_scale.json`** - the cast's declared relative scale.
- **`script/ACT_01_SCRIPT.json`** - the full 49-line Act 1 script.
- **`docs/ACT_01_DESIGN.md`** - Act 1 hotspot, item, topic, event, puzzle, and
  animation-cue structure.
- **`script/ACT_01_DIALOGUE.json`** + **`public/audio/voice/act-01/*.ogg`** - real
  recorded voice for 45 of Act 1's 49 lines.
- **`public/audio/AUDIO_MANIFEST.json`** + **`public/audio/music/`** / **`sfx/`** -
  Act 1 music and SFX sourced from Freesound; see `AUDIO_CREDITS.md`.
- **`src/`** - the current Vite/TypeScript playable Act 1 scaffold.
- **`art/qa-placeholder`** and **`art/qa-broken`** - fixtures proving the registration
  gate passes clean art and rejects bad art.

## Voice Audio

Act 1's voice (`public/audio/voice/act-01/`, manifest in
`script/ACT_01_DIALOGUE.json`) is ElevenLabs TTS on the free tier: non-commercial per
ElevenLabs' Terms of Service, requires attributing ElevenLabs on any public use, and
is not cleared to ship in a commercial release as-is. Treat it as a real
audition/pacing pass, not final audio.

Voice-to-character mapping:

| Character | ElevenLabs voice | Voice ID |
|---|---|---|
| Pip | Jessica - Playful, Bright, Warm | `cgSgspJ2msm6clMCkdW9` |
| Bramble | Alice - Clear, Engaging Educator | `Xb7hH8MSUJpSbSDYk0k2` |
| Old Bottlecap | Bill - Wise, Mature, Balanced | `pqHfZKP75CvOlQylNhV4` |
| Scuttle | Liam - Energetic, Social Media Creator | `TX3LPaxmHKxFdv7VOQHJ` |

Generation stopped mid-Act-1 because the account's free-tier monthly quota ran out.
Regenerating the last 4 lines, or upgrading to a paid tier and redoing the whole
batch for commercial clearance, both work as drop-in replacements by
`line_id`/filename.

## Music & SFX Audio

`public/audio/music/` and `public/audio/sfx/` are real Freesound.org recordings, CC0
or CC-BY only, no NC/ND/SA/Sampling+. Unlike the voice audio above, this material is
commercially usable now, but the CC-BY sources require attribution if the game ships
publicly. The full credit list is in `AUDIO_CREDITS.md` and must ship with the game.

## Status

Act 1 is now a playable local web slice built from `script/ACT_01_SCRIPT.json` and
`docs/ACT_01_DESIGN.md`, with the recorded Act 1 voice/audio pass available in
`public/audio/`. The project scaffold wires the registration gate into `npm test`,
GitHub Actions, and per-sheet QA scripts. The checked-in art is provisional generated
cel art, not final production character art, but it is registered from the start:

- `art/qa-placeholder` proves the frame gate passes a clean placeholder sheet.
- `art/qa-broken` is an intentionally bad fixture that fails on canvas size and
  anchor drift.
- `art/pip-walk` is the first walk-plane actor sheet and passes registration.
- `art/old-bottlecap-idle` is the first furniture-anchored rig sheet and passes
  registration with a foreground mask in the playable scene.
- `art/cast_scale.json` now resolves every declared cast registration path and passes
  cast-scale. Grommet remains placeholder scale art only; Acts 2 and 3 are not built.

Acts 2 ("The Button Sovereignty") and 3 ("The Roar") still only exist as the loose
outline in `docs/GAME_CONCEPT.md`. They need the same script/design pass Act 1 has
before implementation continues.
