# Codex build prompt — Lost & Underfound

Paste this to Codex to start the project. It assumes this repo's `docs/GAME_CONCEPT.md`,
`docs/ANIMATION_BIBLE.md`, `art/cast_scale.json`, and `tools/check_registration.py`
already exist — read them first.

---

Build **Lost & Underfound**, a point-and-click adventure game. Full concept, cast, and
target structure are in `docs/GAME_CONCEPT.md` — read it before writing any code.
Genre and animation-quality benchmark: classic Humongous Entertainment-style kids'
adventure games (Pajama Sam, Putt-Putt, Freddi Fish era) — bouncy, expressive,
personality-first character animation; goofy, warm tone; exploration-driven puzzle
design. This is an original property, not a reproduction of any existing licensed
character or title.

### Governing animation rule

`docs/ANIMATION_BIBLE.md` in this repo is the binding animation production rule from
day one — the twelve principles, the walk-cycle contract, the turnaround contract, the
scene-character contract, and the smear-frame rule all apply unchanged. Read it before
writing a line of animation code.

### The lesson this project must not repeat

A prior project (Department of Impossible Complaints) shipped with two classes of
animation-quality bugs that trace back to one root cause: **generated frames were
treated as finished sprites instead of registered animation cels.**

1. **Scale/registration drift on freely-walking characters** — even with engine-side
   perspective scaling disabled, individual walk frames were generated/cropped with
   inconsistent body size, canvas size, and foot position, so the character visibly
   grows/shrinks or slides frame to frame.
2. **Fixed/furniture-anchored characters rendered as a single loose full-body sprite
   slapped over the background** — with no separation between what should be occluded
   by furniture and what shouldn't, and no shared registration across frames. The
   result: torso/limbs clipping over the counter, and some generated frames
   containing outright bad registration (a detached arm) that had to be quarantined
   and locked out of the animation loop entirely — meaning the character effectively
   couldn't animate.

**This project's animation pipeline must prevent both failure classes structurally,
before any character art is finalized:**

1. **Separate actor placement from animation art.** Placement (anchor point, display
   size, world position) is engine-controlled and fixed per actor. Animation art (the
   frame sheet) must never be resized or repositioned per-frame to compensate for bad
   source art — if a frame doesn't fit the shared anchor/scale, the frame is wrong,
   not the code.
2. **Registration guides per actor sheet.** Every character sheet gets an explicit,
   documented baseline: a feet/contact line for freely-walking actors (Pip, Scuttle),
   a fixed-contact line for any furniture/prop-anchored actor (Old Bottlecap at the
   toll gate, potentially Grommet depending on how his guard-post scene is staged).
   Every frame in that sheet is authored or normalized against that same guide.
3. **A frame normalization step, not manual eyeballing.** Before any frame enters the
   game, run it through `tools/check_registration.py frames <sheet>/registration.json`
   — verifies identical canvas size, identical contact/anchor point (within
   tolerance), across every frame in a sheet. Reject or re-pad any frame that doesn't
   match; never ship a per-frame crop/resize hack to paper over a mismatch. See the
   script's own docstring for the `registration.json` schema.
4. **Cast-wide scale parity, checked, not eyeballed.** Grommet is *supposed* to be
   huge next to Scuttle — see `art/cast_scale.json` for the full cast's intended
   relative proportions. That's exactly why `tools/check_registration.py cast-scale
   art/cast_scale.json` exists: it verifies every character's source art was authored
   at the scale the roster actually calls for, catching the accidental version of size
   mismatch (art drawn at the wrong scale) without flagging the intentional one
   (Grommet being enormous on purpose). A character's source art must pass
   `cast-scale` against the full roster before it's considered authored — a sheet
   that's internally consistent (passes `frames`) but renders its owner oversized or
   undersized next to the rest of the cast relative to its declared
   `world_height_units` is still a registration failure, not a stylistic choice.
5. **Layered rig for any furniture-anchored/"windowed" character**, from the first
   frame authored, not retrofitted later:
   - fixed background plate with that character absent
   - character body layer, composited behind the counter/furniture line
   - a foreground occlusion mask (the counter/desk/gate edge) on top of the
     character's lower body
   - hands/tools/props allowed to render above the contact surface as a separate top
     layer
   - every frame in this rig shares one canvas, one origin, one contact guide — no
     exceptions, no one-off crops
6. **A visual QA page before anything is called playable.** `tools/check_registration.py
   frames <sheet>/registration.json --onion-skin out.png` overlays every frame of a
   sheet on top of each other, aligned by anchor. If feet, head, or the contact anchor
   visibly jumps between frames, that's caught here — not discovered later as "the
   model is hanging over the counter."
7. **Animate last, not first.** 24fps timing, in-betweens, and smear frames (per the
   Animation Bible's smear-frame rule) only get added once a sheet has passed the
   registration/normalization/cast-scale/QA gates above. More frames on top of
   ungoverned registration only produces more visible drift, not better animation.

### Hard gate

Codify this as an actual gate, not a guideline: **a frame that does not pass both
`check_registration.py frames` and `check_registration.py cast-scale` does not get
merged into the game.** Wire both into CI (or at minimum a documented pre-merge
checklist) so every future character sheet — not just the first one — goes through
them before shipping.

### Build order

1. Project scaffold + this repo's docs/tooling wired up and passing against a
   placeholder sheet, before any real character art is finalized.
2. Pip's walk-cycle sheet, authored against the tooling from step 1 — prove the
   pipeline catches a deliberately-broken test frame before trusting it on real art.
3. One furniture-anchored character (Old Bottlecap is the simplest test case) using
   the layered rig, same proof-before-trust approach, plus a `cast-scale` check
   against Pip.
4. First playable area (Act 1, "The Crack Under the Couch") once both actor types
   pass QA clean — build directly from `script/ACT_01_SCRIPT.json` (the actual
   line-by-line script) and `docs/ACT_01_DESIGN.md` (the hotspot/item/topic/event
   structure that script plugs into, plus the animation-cue table). Follow the same
   phased approach as before: UI → room functionality (hotspots, items, the Bramble
   conversation, the toll-gate puzzle) → ambiance (dust, light, the first hints of
   The Roar) → next area. Do not invent placeholder dialogue where the script already
   has the real line — use it verbatim.
5. Acts 2 ("The Button Sovereignty") and 3 ("The Roar") now have the same level of
   script/design detail Act 1 has: `script/ACT_02_SCRIPT.json` + `docs/ACT_02_DESIGN.md`,
   and `script/ACT_03_SCRIPT.json` + `docs/ACT_03_DESIGN.md`. Read `docs/STORY_ARC.md`
   first — it's the connective plot both design docs assume (Chairman Toggle, the
   Button Court, the Annex, Old Bottlecap's founder reveal) and explains exactly which
   Act 1 lines are being paid off. Build them the same way Act 1 was built (script and
   design doc first, verbatim dialogue, no invented placeholder lines) once Act 1 is
   playable — still don't build ahead of a script, there just isn't a script gap here
   anymore. Act 2 introduces Grommet (the real test of the layered rig at extreme
   scale) and a new walk-plane rig for Bramble (she's furniture-anchored in Act 1
   only). Act 3 introduces no new character rig but needs Grommet's one-time walk
   cycle (see `docs/ACT_03_DESIGN.md`) and a sustained strain-hold performance for his
   guardian payoff — the closest thing this game has to a climax beat.
