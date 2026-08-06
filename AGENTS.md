# Lost & Underfound Agent Brief

## Commands

- Install web prototype deps: `npm.cmd install`
- Run all current checks: `npm.cmd test`
- Run the Godot content scaffold gate only: `npm.cmd run qa:godot-content`
- Build the current playable web slice: `npm.cmd run build`
- Local dev server: `npm.cmd run dev`

## Architecture Direction

The current `src/` app is the playable Act 1 web prototype. Do not break it while
the Godot production stack is being prepared.

Long-term production is moving toward a Godot 4 + Popochiu-style adventure stack:
rooms, hotspots, exits, inventory, dialogue, randomization, and cutscenes are data.
Engine code should stay generic. Content belongs under `content/`.

## Boundaries

- Do not edit generated engine/vendor folders under `addons/` once Popochiu or GUT
  are vendored.
- Do not hardcode room-specific puzzle logic into engine code when the behavior can
  live in JSON/resources.
- Do not build Acts 2 or 3 until they have script/design detail comparable to
  `script/ACT_01_SCRIPT.json` and `docs/ACT_01_DESIGN.md`.
- Do not admit animation frames unless registration, cast-scale, animation-admission,
  and visual QA pass.

## Report Back

Every implementation report should include:

- Files changed or generated.
- Exact checks run and whether they passed.
- Any `[ASSUMPTION]` that affects production direction.
- Any blocker that prevents the next phase.
