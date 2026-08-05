# Lost & Underfound

A point-and-click adventure game built to a classic Humongous Entertainment-era
quality bar: bouncy, expressive, personality-first character animation and goofy
exploration-driven puzzle design. Original property, original cast.

This repo holds the creative/design package, animation production rules, registration
QA tooling, Act 1 script/design data, an Act 1 audio pass, and the first playable web
scaffold.

## What's Here

- **`docs/GAME_CONCEPT.md`** — the pitch: premise, tone, full cast with personalities,
  and the target ~1 hour, 3-act structure.
- **`docs/ANIMATION_BIBLE.md`** — binding animation production rules synced from
  [`BadBagger/Animation-Bible`](https://github.com/BadBagger/Animation-Bible), the
  shared source of truth across projects — edit rules upstream there, not here.
- **`docs/CODEX_BUILD_PROMPT.md`** — the build brief and required build order.
- **`tools/check_registration.py`** — the hard QA gate for per-sheet frame
  registration and cast-scale parity, also sourced from `BadBagger/Animation-Bible`.
- **`art/cast_scale.json`** — the cast's declared relative scale (Pip = 1.0 baseline,
  Grommet = 2.4 deliberately huge, Scuttle = 0.35 deliberately tiny, etc).
- **`script/ACT_01_SCRIPT.json`** — the full 49-line Act 1 script ("The Crack Under
  the Couch"): location intro, every hotspot's examine/use text (including
  failure/success variants), Bramble's full dialogue tree, the Old Bottlecap toll-gate
  puzzle exchange, idle/fallback lines, and the transition out.
- **`docs/ACT_01_DESIGN.md`** — Act 1 hotspot, item, topic, event, puzzle, and
  animation-cue structure the script plugs into.
- **`script/ACT_01_DIALOGUE.json`** + **`public/audio/voice/act-01/*.ogg`** — real
  recorded voice for all 49 of Act 1's lines (ElevenLabs, `eleven_multilingual_v2`,
  paid Creator tier — commercial use permitted). See "Voice Audio" below for the
  attribution requirement that still applies, and for Pip's voice specifically — it's
  a pitch-shifted premade voice, not a stock pick, worth reading before regenerating
  any of Pip's lines.
- **`public/audio/AUDIO_MANIFEST.json`** + **`public/audio/music/`** / **`sfx/`** —
  Act 1 music and SFX, sourced from Freesound (CC0/CC-BY), gain-matched by
  functional category from the start; see `AUDIO_CREDITS.md` for full attribution.
- **`art/act01-production/`** — Act 1 production visual source art, scene plates,
  registered character/prop sheets, onion skins, contact sheets, and loop captures;
  see `VISUAL_ASSET_CREDITS.md`.
- **`src/`** — the current Vite/TypeScript playable Act 1 scaffold.
- **`art/qa-placeholder`** and **`art/qa-broken`** — fixtures proving the registration
  gate passes clean art and rejects bad art.

## Voice Audio

Act 1's voice (`public/audio/voice/act-01/`, manifest in `script/ACT_01_DIALOGUE.json`)
is ElevenLabs TTS on a **paid Creator-tier account** — commercial use permitted, but
ElevenLabs still requires attribution on any public use per their Terms of Service;
that's a permanent requirement of using their TTS at all, not a free-tier-only
caveat. All 49 lines are voiced.

| Character | ElevenLabs voice | Voice ID | Post-processing / notes |
|---|---|---|---|
| Pip | Harry — Fierce Warrior | `SOYHLrjzK2X1ezoPC6cr` | **Pitch-shifted +3 semitones** (`sox in.wav out.wav pitch 300`) — required every time, not a saved custom voice |
| Bramble | Grimblewood Thornwhisker — Snarky Gnome & Magical Maintainer | `ouL9IsyrSnUkCmfnD02u` | **3x credit rate** (`rate: 3.0` on this shared-library voice, vs. 1x for everything else in this project) — factor that in if regenerating a lot of Bramble dialogue |
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

**Bramble's voice changed from the original pick (Alice, a standard-rate female
educator-toned voice) to Grimblewood Thornwhisker** after a direct A/B test on the
same line — the "snarky gnome, magical maintainer, grumpy-but-warm" character voice
matched Bramble's "fussy, procedure-proud, means well, understands nothing" brief
better than Alice did. Worth being deliberate about if touching this again: neither
Bramble's script nor design docs use gendered pronouns for the character (always
just "Bramble"), so this was a clean swap, not a rewrite — but it is a real
character-voice decision, and it's the one voice in this project billed at a
premium rate.

## Music & SFX Audio

`public/audio/music/` and `public/audio/sfx/` are real Freesound.org recordings, CC0
or CC-BY only, no NC/ND/SA/Sampling+. Unlike the voice audio above, this material is
commercially usable now, but the CC-BY sources require attribution if the game ships
publicly. The full credit list is in `AUDIO_CREDITS.md` and must ship with the game.

Act 1 is now a playable local web slice built from `script/ACT_01_SCRIPT.json` and
`docs/ACT_01_DESIGN.md`, fully voiced (49/49 lines) and fully scored (all music/SFX
for Act 1's hotspots and UI), with the recorded audio pass available in
`public/audio/` and a provisional production visual pass in `art/act01-production/`.
The project scaffold wires the registration gate into `npm test`, GitHub Actions, and
per-sheet QA scripts. The production visual pass is still provisional pending human
review of the required Animation Bible evidence, but it is registered from the start:

- `art/qa-placeholder` proves the frame gate passes a clean placeholder sheet.
- `art/qa-broken` is an intentionally bad fixture that fails on canvas size and
  anchor drift.
- `art/pip-walk` is the first walk-plane actor sheet and passes registration.
- `art/old-bottlecap-idle` is the first furniture-anchored rig sheet and passes
  registration with a foreground mask in the playable scene.
- `art/act01-production/` contains the AI-source-derived background plate, layered
  Bramble and Old Bottlecap rigs, Pip action sheets, Scuttle smear-rule dash, dust
  reveal, grate opening, and QA evidence.
- `art/cast_scale.json` now resolves Act 1 production registration paths and passes
  cast-scale. Grommet remains placeholder scale art only; Acts 2 and 3 are not built.

Acts 2 ("The Button Sovereignty") and 3 ("The Roar") still only exist as the loose
outline in `docs/GAME_CONCEPT.md`. They need the same script/design pass Act 1 has
before implementation continues.
