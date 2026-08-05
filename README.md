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
  recorded voice for all 49 of Act 1's lines (ElevenLabs, `eleven_multilingual_v2`,
  paid Creator tier — commercial use permitted). See "Voice audio" below for the
  attribution requirement that still applies, and for Pip's voice specifically —
  it's a pitch-shifted premade voice, not a stock pick, worth reading before
  regenerating any of Pip's lines.
- **`public/audio/AUDIO_MANIFEST.json`** + **`public/audio/music/`** / **`sfx/`** —
  real music and SFX for Act 1: one ambience bed, one success stinger, and 15 SFX
  covering every hotspot interaction, UI feedback, and footsteps. Built from curated
  Freesound.org recordings (CC0/CC-BY), gain-matched by functional category (ui /
  footstep / interaction / reward / ambient_character / music) from the start — see
  `AUDIO_CREDITS.md` for full per-file attribution.

## Voice audio

Act 1's voice (`public/audio/voice/act-01/`, manifest in `script/ACT_01_DIALOGUE.json`)
is ElevenLabs TTS on a **paid Creator-tier account** — commercial use permitted, but
ElevenLabs still requires attribution on any public use per their Terms of Service;
that's a permanent requirement of using their TTS at all, not a free-tier-only
caveat. All 49 lines are voiced.

| Character | ElevenLabs voice | Voice ID | Post-processing |
|---|---|---|---|
| Pip | Harry — Fierce Warrior | `SOYHLrjzK2X1ezoPC6cr` | **Pitch-shifted +3 semitones** (`sox in.wav out.wav pitch 300`) — required every time, not a saved custom voice |
| Bramble | Alice — Clear, Engaging Educator | `Xb7hH8MSUJpSbSDYk0k2` | none |
| Old Bottlecap | Bill — Wise, Mature, Balanced | `pqHfZKP75CvOlQylNhV4` | none |
| Scuttle | Liam — Energetic, Social Media Creator | `TX3LPaxmHKxFdv7VOQHJ` | none |

**Pip's voice needed real A/B testing to land** — worth knowing before touching it:
ElevenLabs Voice Design refuses prompts describing a child voice outright (a
deliberate safety policy, confirmed directly against the API, not a bug to route
around). The shared Voice Library does have real voice actors who cloned themselves
performing kid/boy characters (searchable — "kid", "boy" turn up options like Vardan,
Valf, Tuna, Teddy Twinkle) and those are legitimate, usable options, but none beat a
plain premade adult voice (Harry) pitch-shifted up in this project's A/B testing.
Formant-shifting beyond the pitch shift (simulating a smaller vocal tract, distinct
from just raising pitch) was also tried via `rubberband` and made the voice sound
*older*, not younger, to the ear — abandoned. Plain pitch-shift, +3 semitones, won
on three separate rounds of testing against real alternatives. If Pip's voice is
ever regenerated, redo this exact pitch-shift step — it is not baked into a saved
ElevenLabs voice, just a processing step on top of the stock Harry voice.

## Music & SFX audio

`public/audio/music/` (ambience loop + a success stinger) and `public/audio/sfx/`
(15 cues — UI feedback, footsteps, and every Act 1 hotspot interaction) are real
Freesound.org recordings, CC0 or CC-BY only, no NC/ND/SA/Sampling+. Unlike the voice
audio above, **this material is commercially usable now** — CC0/CC-BY carries no
non-commercial restriction — but the CC-BY sources (7 of 17 files) require
attribution if the game ships publicly; the full credit list is in
`AUDIO_CREDITS.md` and must ship with the game. Levels are gain-matched by
functional category (not left at each recording's inconsistent source loudness) and
capped so nothing clips — see `public/audio/AUDIO_MANIFEST.json` for the full cue
list with triggers, volumes, and durations.

## Status

Pre-production, with Act 1 fully scripted, fully voiced (49/49 lines), and fully
scored (all music/SFX for Act 1's hotspots and UI). No engine code, no character art
yet. Acts 2 ("The Button Sovereignty") and 3 ("The Roar") still only exist as the
loose outline in `docs/GAME_CONCEPT.md` — do those as a follow-up pass once Act 1
has been built and played. Next step is handing `docs/CODEX_BUILD_PROMPT.md` to
Codex to start the project scaffold, prove the registration tooling against a real
test sheet, and build Act 1 against
`script/ACT_01_SCRIPT.json` + `docs/ACT_01_DESIGN.md` + the recorded voice and audio.
