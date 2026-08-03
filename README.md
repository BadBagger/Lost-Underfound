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

## Status

Pre-production only. No engine code, no script, no character art. Next step is
handing `docs/CODEX_BUILD_PROMPT.md` to Codex to start the project scaffold and prove
the registration tooling against a real (not synthetic) test sheet.
