# Lost & Underfound

A point-and-click adventure game, built to a classic Humongous Entertainment-era
quality bar (Pajama Sam / Putt-Putt / Freddi Fish) — bouncy, expressive,
personality-first character animation and goofy exploration-driven puzzle design.
Original property, original cast.

Nothing has been built yet. This repo currently holds the planning/pre-production
package: the creative brief, the animation production rules, the build prompt for
Codex, and the animation-registration QA tooling the whole pipeline is built around
from day one.

## What's here

- **`docs/GAME_CONCEPT.md`** — the pitch: premise, tone, full cast with personalities,
  and the target ~1 hour, 3-act structure.
- **`docs/ANIMATION_BIBLE.md`** — binding animation production rules. This is a synced
  copy of [`BadBagger/Animation-Bible`](https://github.com/BadBagger/Animation-Bible),
  the shared source of truth across projects — edit rules upstream there, not here.
  Twelve principles, walk-cycle contract, turnaround contract, scene-character
  contract, smear-frame rule, registration/normalization gate, required approval
  evidence, plus a project-specific "Current status" section that isn't synced.
- **`docs/CODEX_BUILD_PROMPT.md`** — the actual prompt to hand Codex to start building.
  Explains the specific animation-quality bugs this pipeline is designed to prevent
  (frame-to-frame scale drift, furniture-anchored characters clipping/misregistering)
  and the build order.
- **`tools/check_registration.py`** — the QA gate, also sourced from
  `BadBagger/Animation-Bible` (`tools/`). Two checks: `frames` (does every frame in
  one character's sheet share the same canvas size and contact anchor) and
  `cast-scale` (does every character's source art match the cast's intended relative
  proportions, so nobody renders accidentally huge or tiny next to the rest of the
  cast). Tested against synthetic fixtures before being added here — see the script's
  own docstring for usage and the `registration.json` / `cast_scale.json` schemas.
- **`art/cast_scale.json`** — the actual roster's declared relative scale (Pip = 1.0
  baseline, Grommet = 2.4 deliberately huge, Scuttle = 0.35 deliberately tiny, etc).
  Registration paths inside it are placeholders until real character sheets exist.
- **`script/ACT_01_SCRIPT.json`** — the actual Act 1 script ("The Crack Under the
  Couch"), 49 lines: location intro, every hotspot's examine/use text (including
  failure/success variants), Bramble's full dialogue tree, the Old Bottlecap toll-gate
  puzzle exchange, idle/fallback lines, and the transition out.
- **`docs/ACT_01_DESIGN.md`** — the structured puzzle logic the script plugs into:
  location description, cast/idle-behavior table, the `HotspotId`/`ItemId`/`TopicId`/
  `EventId` data (what Codex should build `scene-data.ts`-equivalent types from), and
  an animation-cue table mapping every beat to which `ANIMATION_BIBLE.md` rule governs
  it. Acts 2 and 3 don't have this treatment yet.
- **`script/ACT_01_DIALOGUE.json`** + **`public/audio/voice/act-01/*.ogg`** — real
  recorded voice for 45 of Act 1's 49 lines (ElevenLabs, `eleven_multilingual_v2`).
  ⚠️ **Free-tier, non-commercial, not cleared to ship** — see "Voice audio" below
  before wiring this up anywhere public. The 4 unvoiced lines are the least-critical
  generic fallbacks (`act01-046` through `act01-049`); the entire core playable path
  — location, every hotspot, Bramble's full tree, the toll-gate puzzle — is voiced.

## Voice audio

Act 1's voice (`public/audio/voice/act-01/`, manifest in `script/ACT_01_DIALOGUE.json`)
is ElevenLabs TTS on the **free tier** — non-commercial per ElevenLabs' Terms of
Service, requires attributing ElevenLabs on any public use, **not cleared to ship in
a commercial release as-is**. Treat it as a real audition/pacing pass, not final audio.
Voice-to-character mapping (same premade ElevenLabs voices, reuse if regenerating):

| Character | ElevenLabs voice | Voice ID |
|---|---|---|
| Pip | Jessica — Playful, Bright, Warm | `cgSgspJ2msm6clMCkdW9` |
| Bramble | Alice — Clear, Engaging Educator | `Xb7hH8MSUJpSbSDYk0k2` |
| Old Bottlecap | Bill — Wise, Mature, Balanced | `pqHfZKP75CvOlQylNhV4` |
| Scuttle | Liam — Energetic, Social Media Creator | `TX3LPaxmHKxFdv7VOQHJ` |

Generation stopped mid-Act-1 because the account's free-tier monthly quota (10,000
characters) ran out — Act 1 needs 3,471 characters total, only ~3,218 remained when
this pass started. Regenerating the last 4 lines, or upgrading to a paid tier and
redoing the whole batch for commercial clearance, both work as drop-in replacements
by `line_id`/filename, no code changes needed.

## Status

Pre-production, with Act 1 fully scripted and mostly voiced (45/49 lines). No engine
code, no character art yet. Acts 2 ("The Button Sovereignty") and 3 ("The Roar")
still only exist as the loose outline in `docs/GAME_CONCEPT.md` — do those as a
follow-up pass once Act 1 has been built and played. Next step is handing
`docs/CODEX_BUILD_PROMPT.md` to Codex to start the project scaffold, prove the
registration tooling against a real test sheet, and build Act 1 against
`script/ACT_01_SCRIPT.json` + `docs/ACT_01_DESIGN.md` + the recorded voice.
