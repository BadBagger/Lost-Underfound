# Lost & Underfound — Game Concept

Genre/quality benchmark: classic Humongous Entertainment-style kids' point-and-click
adventure (the Pajama Sam / Putt-Putt / Freddi Fish era) — bouncy, expressive,
personality-first character animation, goofy warm tone, exploration-driven puzzle
design. This is an original property built to that quality bar, not a reproduction of
any existing licensed character, title, or story.

## Logline

The night before the school talent show, Pip's lucky charm rolls under the couch.
Armed with a shrinking button found wedged in the cushions, Pip shrinks down and
discovers *Underneath* — a whole civilization of small creatures living in the shadow
of the furniture, running their own chaotic little bureaucracy out of bottle caps,
lint, and lost buttons. Find the charm and get back to normal size before "The Roar"
— the vacuum cleaner, scheduled for its weekly sweep at dawn — comes through and takes
the whole neighborhood with it.

## Tone

Same comedic engine as Department of Impossible Complaints — mundane process taken
deadly seriously by people (creatures) who are deadly serious about the wrong things —
but warm and kid-pitched instead of noir. A bottle cap is currency. A dead calculator
is an oracle. Everyone has strong opinions about procedure and none of it actually
matters, which is the joke.

## Cast

| Character | Role | Personality | `world_height_units` |
|---|---|---|---|
| **Pip** | Protagonist | Resourceful, a little stubborn, talks to themselves when nervous | 1.0 (baseline — "shrunk-kid" scale) |
| **Bramble** | Dust Bunny, self-appointed Lost & Found Clerk | Fussy, procedure-proud, means well, understands nothing | 0.85 |
| **Grommet** | A sock-puppet husk that "woke up" under the couch; guards the deep Underneath | Slow, sweet, not very bright, deeply loyal once befriended | 2.4 — deliberately huge |
| **Scuttle** | Roly-poly courier bug, fastest thing in Underneath | Twitchy, self-important, always mid-delivery | 0.35 — deliberately tiny |
| **Old Bottlecap** | A stack of bottlecaps that gained sentience and appointed itself Treasurer | Ancient, grumpy, deadpan, guards a toll-gate puzzle. Secretly the founder of Underneath's original button standard — see `docs/STORY_ARC.md` | 0.6 |
| **Chairman Toggle** | Presiding officer of the Button Court, Act 2/3 antagonist | Pompous, sincere, fussy, self-appointed authority on a system he's convinced himself is for everyone's good — defeated by procedure and embarrassment, not force | n/a — desk-fixed, first appears Act 2 |
| *The Roar* | Environmental threat, no dialogue/sprite | The vacuum cleaner — heard rumbling, felt in light/dust tremors, the game's clock | n/a |

Grommet and Scuttle's scale gap is intentional — see `art/cast_scale.json` and
`tools/check_registration.py`. The whole point of that tool is to make sure *this*
kind of extreme size difference is an authored choice, verified consistent, not an
accident like the reference project's furniture-anchored-character bugs.

## Structure — target runtime ~1 hour

Three areas, same rough shape as Impossible Complaints' Lobby → Records Annex
progression, sized to land around an hour total. The full connective story — what
Pip's marble actually is, who's really behind it going missing, and how each act's
hooks pay off into the next — is `docs/STORY_ARC.md`. The summaries below are the
one-paragraph version; that document is the source of truth on plot.

### Act 1 — "The Crack Under the Couch" (~15 min)
Shrink down, meet Bramble, learn the core verbs (inspect / use / combine), first
small puzzle: pay Old Bottlecap's toll with a found object to get past the gate into
Underneath proper. Plants three hooks that don't pay off until later: the Sign-In
Log's mention of someone signing in "carrying something round and shiny," Bramble's
nervous deflection about marbles being "very popular around here," and Old
Bottlecap's claim that he "predates the filing system." Fully scripted, designed,
and voiced — see `script/ACT_01_SCRIPT.json` and `docs/ACT_01_DESIGN.md`.

### Act 2 — "The Button Sovereignty" (~25 min)
The main hub — the Button Court's public territory, a small bureaucracy built
entirely around buttons as currency. Meet Grommet at the Annex threshold, reconnect
with Scuttle mid-delivery, follow the sign-in log's clue trail, chase a red herring
that falsely points at Old Bottlecap and uncovers his real founder history instead,
and the biggest puzzle chain of the game (a needle+thread combine puzzle that earns
Grommet's trust). Ends turned away from the Annex by Chairman Toggle, on procedure.
Fully scripted, designed, voiced (72/72 lines), and scored — see
`script/ACT_02_SCRIPT.json`, `docs/ACT_02_DESIGN.md`, `script/ACT_02_DIALOGUE.json`,
and `public/audio/AUDIO_MANIFEST.json`. Not yet produced (no character art beyond
early concept passes for Grommet and Chairman Toggle).

### Act 3 — "The Roar" (~15–20 min)
The vacuum cleaner is coming early — dust starts shaking, ambient tension ramps
(lights flicker, tremors). Grommet lets Pip into the Annex, Pip finds the marble
among years of the Court's other confiscated finds, and Toggle is beaten with his
own paperwork, not force. The vacuum hits mid-escape: Grommet holds the chokepoint
(the payoff for his `world_height_units: 2.4` scale), Old Bottlecap reopens the
Grate on his own initiative, Scuttle guides the fastest way out. Closes on a small
goodbye beat with Bramble and Grommet. Fully scripted, designed, voiced (58/58
lines), and scored — see `script/ACT_03_SCRIPT.json`, `docs/ACT_03_DESIGN.md`,
`script/ACT_03_DIALOGUE.json`, and `public/audio/AUDIO_MANIFEST.json`. Not yet
produced.

## What doesn't exist yet

Act 1 has a full script, design doc, and voice/music/SFX pass, plus a provisional
production art pass — see the main `README.md`. Acts 2 and 3 now have a full script
and design doc each (this pass), but no voice audio, no music/SFX pass, and no
production art beyond Grommet's placeholder scale blob. No engine code exists yet
for either act. See `docs/CODEX_BUILD_PROMPT.md` for how to actually start
building, and `tools/check_registration.py` / `art/cast_scale.json` for the
animation QA gate the pipeline is built around from day one.
