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
| **Old Bottlecap** | A stack of bottlecaps that gained sentience and appointed itself Treasurer | Ancient, grumpy, deadpan, guards a toll-gate puzzle | 0.6 |
| *The Roar* | Environmental threat, no dialogue/sprite | The vacuum cleaner — heard rumbling, felt in light/dust tremors, the game's clock | n/a |

Grommet and Scuttle's scale gap is intentional — see `art/cast_scale.json` and
`tools/check_registration.py`. The whole point of that tool is to make sure *this*
kind of extreme size difference is an authored choice, verified consistent, not an
accident like the reference project's furniture-anchored-character bugs.

## Structure — target runtime ~1 hour

Three areas, same rough shape as Impossible Complaints' Lobby → Records Annex
progression, sized to land around an hour total.

### Act 1 — "The Crack Under the Couch" (~15 min)
Shrink down, meet Bramble, learn the core verbs (inspect / use / combine), first
small puzzle: pay Old Bottlecap's toll with a found object to get past the gate into
Underneath proper.

### Act 2 — "The Button Sovereignty" (~25 min)
The main hub. Meet Grommet, follow a clue trail through Underneath's chaotic little
institutions, at least one red herring, the biggest puzzle chain of the game.

### Act 3 — "The Roar" (~15–20 min)
The vacuum cleaner is coming — dust starts shaking, ambient tension ramps (lights
flicker, tremors), final puzzle to recover the charm and reach the shrinking button
before the sweep. Closes on a small goodbye beat with Bramble and Grommet.

## What doesn't exist yet

No script, no hotspot/puzzle data, no art, no engine code. This document is the
creative brief the rest of the project builds from — see `docs/CODEX_BUILD_PROMPT.md`
for how to actually start building, and `tools/check_registration.py` /
`art/cast_scale.json` for the animation QA gate the pipeline is built around from day
one.
