# Act 1 Design — "The Crack Under the Couch"

Companion to `script/ACT_01_SCRIPT.json`. This document is the structured puzzle
logic and animation-cue mapping that script plugs into — read both together. Once
Codex builds the actual engine, this doc is the spec for `HotspotId`/`ItemId`/
`TopicId`/`EventId` and the scene/hotspot data table, the same relationship
`department-impossible-complaints`' `scene-data.ts` has to its own script.

**Difficulty pass note:** the dead-battery decoy below (`act01-050` through
`act01-052`) was added after the original 49 lines were already recorded and
produced, to raise Act 1's puzzle past a single obvious hand-off. Those three lines
are the *only* new/unvoiced content in this act — everything else in this document
describes the original recorded script unchanged. See `docs/STORY_ARC.md`'s
difficulty-target note for why.

## Location description

The entry chamber of Underneath, directly beneath the living-room couch. Low
ceiling (the couch's underside — visible staples, a manufacturer's tag, ancient
snack debris), dim light filtering in dust-mote shafts from the crack Pip fell
through. The room reads as a functioning little office grafted onto found household
junk: Bramble's Lost & Found desk is a shoebox lid on two thread spools, the cubby
wall is a stack of bottle caps glued into cells, the toll gate is a literal
window-screen grate with Old Bottlecap parked in front of it like a tollbooth
attendant. Warm and cluttered, not spooky — this is Bramble's tidy little kingdom,
not a threat.

## Cast present

| Character | Role this act | Idle behavior |
|---|---|---|
| **Pip** | Player-controlled | N/A |
| **Bramble** | Main NPC, quest-giver, desk-fixed | Passive loop: shuffling bottle-cap folders, occasionally stamping something, per the furniture-anchored rig in `docs/ANIMATION_BIBLE.md`'s scene-character contract |
| **Old Bottlecap** | Gate-puzzle NPC, fixed at the toll gate | Passive loop: slow rock side to side, occasional disapproving head-tilt — minimal motion, this character's comedy is stillness/deadpan, not business |
| **Scuttle** | Cameo only, non-interactive | Scripted one-shot dash-through on `cobweb-curtain` examine, does not appear again this act |

## Hotspots

| `HotspotId` | Label | Rules |
|---|---|---|
| `couch-ceiling` | Couch-Bottom Ceiling | inspect → `003` (flavor only, no state) |
| `dust-clump` | Dust Clump | inspect (before searched) → `004`; use/search (before searched) → `005`, `addItem: button`, `setFlag: dustSearched`, `event: found-button`; inspect or use (after searched) → `006` |
| `cubby-wall` | Lost & Found Cubby Wall | inspect, rotating pool `007` (1st) then `008`/`009`/`010` (loop). **NEW:** once `009` (cubby seven, the dead watch battery) has been seen, a `take` action unlocks on that one cubby only — `050`, `addItem: dead-battery`, `setFlag: batteryTaken`. The other cubbies stay flavor-only; this is a single deliberate decoy, not a general "take anything" rule. |
| `sign-in-log` | Sign-In Log | inspect → `011` (flavor/foreshadowing only — no clue flag yet; Act 2/3 pays this off) |
| `popcorn-boulder` | Popcorn Kernel Boulder | inspect → `012`; use → `013` (permanent flavor fail, not a real gate) |
| `cobweb-curtain` | Cobweb Curtain | inspect → `014`, then once only: `015` (Scuttle bark) + `016` (Pip reaction) |
| `bramble-desk` | Bramble's Desk | `conversation: bramble` (see Topics below) |
| `toll-gate` | The Grate / Old Bottlecap | inspect → `037`; use (no item, or any item other than `button`/`dead-battery`) → `038`, `event: toll-refused`; **NEW:** use `item: dead-battery` → `051`+`052` (2-beat), `event: toll-refused-claimed`, item is NOT consumed and NOT removed from inventory — this is the decoy path, it must be retryable; use `item: button` → `039`+`040` (2-beat), `setFlag: gateOpen`, `removeItem: button`, `event: toll-paid`, `sceneChanged: true` (transition to Act 2 space); inspect (after `gateOpen`) → `043` |

## Items

| `ItemId` | Source | Used on |
|---|---|---|
| `button` | `dust-clump` search | `toll-gate` (consumed on success) |
| `dead-battery` | `cubby-wall`, cubby seven, take (after `009` seen) | `toll-gate` (rejected, not consumed — the decoy) |

## Topics (Bramble conversation)

- **`greeting`** — auto-fires once on first approach, fixed sequence `017`→`021` (5 lines)
- **`verbs`** — auto-fires immediately after greeting, fixed sequence `022`→`024` (3 lines, the tutorial beat)
- **`quest-lead`** — auto-fires immediately after `verbs`, fixed sequence `025`→`031` (7 lines, ends on the puzzle hint)
- **`about-bramble`** — player-selectable, `032`→`034`
- **`about-bottlecap`** — player-selectable, `035`
- Wrong-action fallback (using an item on Bramble that isn't relevant) → `036`

Post-gate-open idle: re-approaching `bramble-desk` after `gateOpen` plays `044`+`045`
once, then falls back to normal topic list.

## Events → what plays

| `EventId` | Triggers | Notes |
|---|---|---|
| `found-button` | `dust-clump` search success | SFX: a soft rustle/reveal chime; Pip reacts with a small "found it" beat, per Animation Bible principle 2 (anticipation) — a brief crouch/reach before the item appears, not an instant pop |
| `toll-refused` | `toll-gate` use, no/wrong item | Old Bottlecap's idle loop interrupts for a single dismissive head-shake beat, then resumes |
| `toll-refused-claimed` | `toll-gate` use, `dead-battery` | **NEW.** Distinct from generic `toll-refused` — this is the decoy's teaching beat, not a fail state. Same head-shake reaction beat as `toll-refused` is fine to reuse, no new animation needed, only the line differs |
| `toll-paid` | `toll-gate` use, `button` | The act's one real "performance" beat — see animation table below |

## Generic fallbacks

- Use item on scenery (no rule matches) → `046`
- Examine self → `047`
- Try to leave/transition before `gateOpen` → `048` (blocks the transition, doesn't fire it)

## Transition

On `toll-paid`, after the `039`/`040`/`041`/`042` exchange plays out, cut to Act 2
("The Button Sovereignty") — line `049` plays as the transition line, spoken over
the scene change per the same pattern `department-impossible-complaints` uses
(`sceneChanged: true` with a short delay before the cut, not an instant hard cut).

Runtime QA: `npm run qa:act1-playthrough` is the Act 1 progression gate. It
checks the discrete-screen link map, the dust-clump -> button -> Bottlecap toll
route, the gated Act 2 transition, the required script line IDs, dialogue
lockout, inventory selection, and hidden release hitboxes.

## Animation cue table

Per `docs/ANIMATION_BIBLE.md` — this is what needs an authored sequence, not just a
text line, and which category of that Bible's rules governs it.

| Beat | Actor | Type | Bible section that governs it |
|---|---|---|---|
| Pip idle in the room | Pip | Held idle loop | Twelve principles #12 (appeal) — must read as alive even unheld |
| Pip walk (room is small — likely a short walk-plane) | Pip | Walk-plane cycle | Walk-cycle contract, full 9-key-pose minimum |
| Pip crouch-and-reach into dust clump | Pip | Reaction/interact beat | #2 anticipation — the reach must precede the reveal, not be simultaneous |
| Dust clump reveal | Prop (dust-clump) | Item animation | #1 squash/stretch on the dust puff dispersing, not a static swap |
| Bramble idle work loop | Bramble | Furniture-anchored idle loop | Scene-character contract — layered rig, passive loop (shuffling folders/stamping), same treatment as the reference project's Quire but built correctly from the start |
| Bramble talk loop | Bramble | Furniture-anchored talk | Scene-character contract — interrupts/resumes the idle loop naturally, does not need per-topic unique cels for Act 1's short exchanges (unlike the reference project's confrontation arc, this act's dialogue doesn't carry that much emotional weight yet) |
| Old Bottlecap idle | Old Bottlecap | Fixed idle loop, minimal motion | #9 timing — a slow, heavy rock read as ancient/patient, deliberately sparse per this character's comedy being stillness |
| Old Bottlecap toll-refused reaction | Old Bottlecap | Reaction beat | #10 exaggeration on the head-shake, kept small — this is a deadpan character, don't over-animate it |
| **Toll-paid beat (the act's climax)** | Old Bottlecap + Pip + the button prop | Multi-actor performance beat | Old Bottlecap: takes the button (arc per #7), inspects it (a held beat per the golden review test's "timing purpose" rule), grudging approval. The Grate itself: a mechanical open animation (#1 squash/stretch as it slides/lifts). Pip: a small relief/excitement reaction. This is the one beat in the act worth the full contact-sheet-plus-approval-evidence treatment before calling it done. |
| Scuttle cameo dash | Scuttle | One-shot, non-looping | Smear-frame rule applies directly — a fast bug-dash is exactly the "fast, sudden motion" case a smear cel is for, with solid readable drawings immediately before/after |

## What Act 1 deliberately does not do yet

No branching confrontation arc (that's Act 2/3 territory), no combine-two-items
puzzle (this act's only puzzle is find-item → use-on-gate), and the Sign-In Log's
clue is flavor-only for now — it's a planted hook, not a mechanical gate, until
Act 2's design pass decides what it pays off into. Don't over-build mechanics this
act doesn't need yet.

**On the dead-battery decoy being fair, not a trap:** it's never consumed, never
sets a fail flag, and Old Bottlecap's rejection (`051`) states the actual rule
outright ("filed... I don't take other people's claimed") rather than being a pure
gotcha — the player learns the rule *by trying the wrong thing once*, not by being
punished for it. This is also the exact rule the endgame turns back on Chairman
Toggle in `docs/ACT_03_DESIGN.md` ("unclaimed property is unclaimed property"), so
Act 1 is now quietly teaching the mechanic the whole story's climax depends on, not
just planting narrative color.
