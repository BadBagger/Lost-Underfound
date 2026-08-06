# Lost & Underfound

A point-and-click adventure game built to a classic Humongous Entertainment-era
quality bar: bouncy, expressive, personality-first character animation and goofy
exploration-driven puzzle design. Original property, original cast.

This repo holds the creative/design package, animation production rules, registration
QA tooling, full script/design data and voice audio for all three acts, and the
first playable web scaffold (Act 1 only, so far).

## What's Here

- **`docs/GAME_CONCEPT.md`** — the pitch: premise, tone, full cast with personalities,
  and the target ~1 hour, 3-act structure.
- **`docs/STORY_ARC.md`** — the finalized overarching story: the central mystery
  behind Pip's missing marble, the Act 2/3 antagonist (Chairman Toggle and the
  Button Court), every character's arc across all three acts, and exactly how each
  of Act 1's planted hooks (the Sign-In Log, Bramble's deflection, Old Bottlecap's
  age) pays off later — written to require zero changes to Act 1's already-recorded
  script and audio.
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
- **`script/ACT_02_SCRIPT.json`** + **`docs/ACT_02_DESIGN.md`** — Act 2 ("The
  Button Sovereignty"), same format as Act 1: 72-line script and matching
  hotspot/item/topic/event/animation-cue design doc, now fully voiced too (see
  `script/ACT_02_DIALOGUE.json` and "Voice Audio" below) — not yet scored or built.
  Puzzle difficulty targets Monkey Island/King's Quest-style lateral thinking, not
  the easier Act 1 benchmark — see `docs/STORY_ARC.md`'s difficulty-target note.
- **`script/ACT_03_SCRIPT.json`** + **`docs/ACT_03_DESIGN.md`** — Act 3 ("The
  Roar"), 58-line script and design doc, closes out the story, also fully voiced
  (`script/ACT_03_DIALOGUE.json`). Same difficulty target as Act 2, same
  not-yet-scored/-built status.
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

All three acts are now voiced: Act 1 (`public/audio/voice/act-01/`, manifest
`script/ACT_01_DIALOGUE.json`), Act 2 (`act-02/`, `script/ACT_02_DIALOGUE.json`),
and Act 3 (`act-03/`, `script/ACT_03_DIALOGUE.json`), all ElevenLabs TTS on a
**paid Creator-tier account** — commercial use permitted, but ElevenLabs still
requires attribution on any public use per their Terms of Service; that's a
permanent requirement of using their TTS at all, not a free-tier-only caveat.

| Character | ElevenLabs voice | Voice ID | Post-processing / notes |
|---|---|---|---|
| Pip | Harry — Fierce Warrior | `SOYHLrjzK2X1ezoPC6cr` | **Pitch-shifted +3 semitones** (`sox in.wav out.wav pitch 300`) — required every time, not a saved custom voice |
| Bramble | Grimblewood Thornwhisker — Snarky Gnome & Magical Maintainer | `ouL9IsyrSnUkCmfnD02u` | **3x credit rate** (`rate: 3.0` on this shared-library voice, vs. 1x for everything else in this project) — factor that in if regenerating a lot of Bramble dialogue |
| Old Bottlecap | Marshal — Dry, Hoarse and Grumpy | `LysucvtFmzi1NVAE0rKp` | none |
| Scuttle | Ziggy — Cute little Aussie character | `J1lfByWs8gvoooryDWEi` | **Pitch-shifted +2 semitones AND tempo +12%** (`sox in.wav out.wav pitch 200 tempo 1.12`) — pitch alone tested as reading "higher," not "faster"; tempo was the piece that actually sold Scuttle's speed |
| Grommet | Jasper — Gentle and Cautious | `8RjxcQ6tY1F2YZiIvWqY` | none — new cast, first voiced in Act 2 |
| Chairman Toggle | Posh Josh | `NXaTw4ifg0LAguvKuIwZ` | none — new cast, first voiced in Act 2 |

Pip, Bramble, Old Bottlecap, and Scuttle carry the exact same voice ID and
post-processing across all three acts — no re-casting, just the established voice
reading new lines each act.

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

**Old Bottlecap changed from Bill (a neutral "wise elder" premade) to Marshal**
after A/B testing against Bill plus two other grumpy-old-man options (Mister Gruff,
Antonio). Bill read as calm and narratorial rather than actually grumpy; Marshal's
"dry, hoarse and grumpy... dreary demeanor" matched the character brief — "ancient,
grumpy, deadpan" — specifically the *deadpan* part, which is a stiller, less
actively-complaining kind of grumpy than the other candidates offered.

**Scuttle changed from Liam (generic energetic premade) to Ziggy** ("cute little
Aussie character... slightly quirky"), the strongest small-creature-coded option
tested against Moxy ("Hyped Mouse") and Jet ("short, modern, carries speed"). Pitch
and tempo are two different levers — pitching Ziggy up alone read as "higher," not
"faster" — so both were applied together to actually land Scuttle's "fastest thing
in Underneath" trait, not just make him sound smaller.

**Grommet (Jasper) and Chairman Toggle (Posh Josh) are new voices, cast in Act 2**
— the first act either character speaks in. Each was picked via a 3-candidate A/B
test on a representative line rather than a first guess. Grommet: Jasper ("gentle
and cautious") beat Kermy ("gentle and froggy," too cartoonish for a beat that
needs real emotional weight in Act 3) and a steady Southern-accented gentle option
(read as too confident/together for a character whose whole arc is not questioning
things until Pip prompts him to). Chairman Toggle: Posh Josh (classy, self-assured)
beat "Well Spoken English Man" and William Mayfair (both read as too calm/measured
for a character whose comedy is brisk self-importance, not composure — see
`docs/ACT_02_DESIGN.md`'s note that his idle is deliberately the opposite direction
from Old Bottlecap's stillness).

## Music & SFX Audio

`public/audio/music/` and `public/audio/sfx/` are real Freesound.org recordings, CC0
or CC-BY only, no NC/ND/SA/Sampling+. Unlike the voice audio above, this material is
commercially usable now, but the CC-BY sources require attribution if the game ships
publicly. The full credit list is in `AUDIO_CREDITS.md` and must ship with the game.
All three acts now share one 30-cue manifest (`public/audio/AUDIO_MANIFEST.json`),
gain-matched by the same functional categories throughout — Act 2/3's additions
didn't get their own looser pass.

Act 2 and 3 add: `music/concourse-ambience-loop.ogg` (the Exchange Concourse's
institutional room tone, replacing Act 1's cozier ambience for that scene),
`music/annex-ambience-loop.ogg` (the Annex's darker, hollow tone),
`music/roar-escape-tension-loop.ogg` (cuts in on `roar-arrives`, carries the whole
Act 3 escape sequence), and `music/epilogue-resolution-stinger.ogg` (the game's
actual ending, deliberately bigger than Act 1's toll-paid-stinger). SFX-wise:
`sfx/needle-thread-combine.ogg` is a **shared combine sound** — one asset reused by
trigger (`item_combine`) for both Act 2's threaded-needle and Act 3's
annotated-evidence, rather than two near-identical one-offs. `sfx/roar-rumble.ogg`
is a real vacuum-cleaner recording (the Roar is a vacuum cleaner, so it's not a
generic rumble bed) — the low-intensity version of that same visual/audio language
is `sfx/first-tremor-rumble.ogg`, planted a full act earlier in Act 2's
`first-tremor` event so Act 3 escalates something already established rather than
introducing a new sound cold. `sfx/toggle-deflate.ogg` is a small balloon-deflate
pun on Chairman Toggle's own name for his Act 3 concession — deliberately comedic,
not a victory fanfare, per `docs/STORY_ARC.md`'s note that his defeat should read
embarrassed, not crushed.

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

Acts 2 ("The Button Sovereignty") and 3 ("The Roar") now have the same script/design
pass Act 1 has — `script/ACT_02_SCRIPT.json` + `docs/ACT_02_DESIGN.md` and
`script/ACT_03_SCRIPT.json` + `docs/ACT_03_DESIGN.md` — plus `docs/STORY_ARC.md`
tying all three acts into one finalized story. Both acts are now fully voiced
(72/72 and 58/58 lines, `public/audio/voice/act-02/` and `act-03/`, manifests in
`script/ACT_02_DIALOGUE.json` / `ACT_03_DIALOGUE.json`) and fully scored (13 new
music/SFX cues covering both acts' scenes, events, and puzzle beats — see "Music &
SFX Audio" above). Neither act has production art yet (Grommet and Chairman Toggle
still have no finished character art beyond early concept passes); that's the next
step, same order Act 1 went through (script/design → voice → music/SFX →
production art → engine).
