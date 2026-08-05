# Act 3 Design — "The Roar"

Companion to `script/ACT_03_SCRIPT.json`, same relationship the other two design
docs have to their scripts. Read `docs/STORY_ARC.md` first. Not yet built or
produced — script/design pass only.

**Difficulty pass note:** full rewrite of the first-draft version. The marble
search went from a fixed 2-decoys-then-guaranteed-success sequence (no actual
choice, just three clicks) to a real 5-candidate search where the player has to
apply a clue planted back in Act 2 (`act02-021`) rather than one restated fresh at
the puzzle moment. The Chairman Toggle confrontation went from "use two items
you're already carrying, either order, both individually sufficient" to a genuine
combine puzzle — `intake-parcel` and `founders-ledger` are each explicitly
insufficient alone and rejected on their own merits; only combining them into
`annotated-evidence` works. See `docs/STORY_ARC.md`'s difficulty-target note.
Nothing here was voiced yet, so this carried no production cost, unlike Act 1's
equivalent (additive-only) pass.

**Inventory still carries across act boundaries.** `intake-parcel` and
`founders-ledger`, both picked up in Act 2, are combined here into a new item —
first time the project has needed a combine puzzle whose ingredients were gathered
in different acts. Flag this for the save/inventory system.

## Location description

Three connected spaces, same composite-scene approach as Acts 1 and 2:

- **The Annex** — dark, cramped, floor-to-ceiling piles of confiscated shine. Not
  sinister, just sad in a way the game hasn't been yet — years of somebody else's
  lucky charms. The Marble Pile is its own hotspot cluster near the entrance, five
  distinct candidate props rather than one generic "pile" sprite (see Items below —
  each needs its own small art asset, this is new scope beyond what the first-draft
  design needed). Grommet's threshold is the doorway back out to the Concourse.
  Chairman Toggle's desk from Act 2 is empty; he shows up here instead once alerted.
- **The Concourse** — same room as Act 2, now background to the escape rather than
  a hub to explore. No new hotspots here; Act 2's exchange window/notice
  board/filing booth are set dressing Pip runs past, not re-examined.
  `act03-039`'s "fastest way out is through the filing booth" is a route callout,
  not a puzzle.
- **The Grate** — Act 1's toll-gate location, revisited. Old Bottlecap is here,
  not at the Annex or Concourse — this is deliberate, it's his post and always has
  been, and this act's whole point is that he chooses to use it differently.

## Cast present

| Character | Role this act | Idle/behavior |
|---|---|---|
| **Pip** | Player-controlled | N/A |
| **Grommet** | Opens the Annex, then holds the chokepoint during the Roar | Furniture-anchored through the block sequence — **then walks**, for the first and only time in the game, in the goodbye beat (`053`–`056`), once the danger's passed and he no longer has a post to keep. This needs a new walk-plane cycle built just for this one moment; treat it as a small, deliberate animation event, not a reused-Bramble-cycle shortcut — the whole emotional point is that this is the first time he's moved. |
| **Chairman Toggle** | Confronts Pip in the Annex, then flees with everyone else | Furniture-anchored idle carries from Act 2 for the confrontation; needs a new panicked-scramble exit beat once the Roar hits (`035`), and a distinct stalling/deflating/conceding arc across `030`→`032` — see animation table | 
| **Bramble** | Present throughout, walk-plane (established Act 2) | Continues Act 2's walk-plane rig. Her `027` nudge line during the Toggle confrontation needs a "thinking it through out loud" beat, not a throwaway line — it's the game's one moment of a supporting character steering the player toward a combine puzzle without solving it outright |
| **Scuttle** | Reappears to guide the escape route | Fast walk-plane, same rig as Act 1/2 |
| **Old Bottlecap** | Reappears at the Grate | Furniture-anchored, reuses Act 1's rig — this is his one other appearance in the whole game, keep his stillness-as-comedy read intact even in this warmer scene, don't over-animate the vulnerability in `044` |

## Hotspots

| `HotspotId` | Label | Rules |
|---|---|---|
| `grommet` (continued from Act 2) | Grommet | `event: annex-opened` auto-fires this act's cold open (`001`–`004`) — no player action needed, this is not a repeat of Act 2's trust puzzle |
| `annex-interior` | The Annex (general) | inspect, rotating pool `005` (1st) then `006`/`007` (loop) |
| `marble-pile` | Marble Pile (5 distinct candidates) | inspect (1st, the pile as a whole) → `008` (states the search criteria as an explicit callback to Act 2's `021`, not fresh info — see difficulty note). Each of the 5 candidates below is independently inspectable/takeable, in any order, unlimited retries, nothing consumed on a wrong take: |
| `marble-candidate-galaxy` | — | inspect → `009`; take → `010` (fail, returned to pile) |
| `marble-candidate-radiator` | — | inspect → `011`; take → `012` (fail, returned to pile) |
| `marble-candidate-scratch` | — | inspect → `013`; take → `014` (fail, returned to pile — the trap decoy, "scratch not nick," rewards a player who read `008`/Act 2's `021` closely) |
| `marble-candidate-flawless` | — | inspect → `015`; take → `016` (fail, returned to pile) |
| `marble-candidate-correct` | — | inspect → `017`; take → `018`, success, `addItem: pips-marble`, `event: marble-found`. No further searching offered or needed once this fires. |
| `chairman-toggle` (relocated) | Chairman Toggle | auto-fires on `marble-found`: `019`–`020`. See the multi-step petition sequence below — this is not a single hotspot rule, it's a short state machine. |
| `escape-route` | (implicit, triggered by scene transition once `toggle-defeated` + `roar` fire) | No player-directed hotspot interaction during the escape sequence — Sec 3–5 is a mostly-linear urgency beat, per `docs/GAME_CONCEPT.md`'s Act 3 tension ramp. Don't build player-choice branching into a sequence whose whole point is that there isn't time to deliberate. |
| `old-bottlecap` (Grate, revisited) | Old Bottlecap | auto-fires once Pip reaches the Grate: `042`–`045` |

## The Toggle petition — a state machine, not a single rule

This is the game's hardest puzzle and deliberately so — it's the climax. Sequence:

1. `use: intake-parcel` on `chairman-toggle` (alone) → `021`–`022`, deflected —
   Toggle's own wording ("no legal standing on its own") is the clue that something
   else is needed, not a dead end.
2. Re-`examine: intake-parcel` (now that the player has a reason to look closer) →
   `023`–`024`, reveals the fine-print re-verification clause. `setFlag: finePrintFound`.
3. `use: founders-ledger` on `chairman-toggle` (alone) → `025`–`026`, also deflected
   — same shape as step 1, teaches by symmetry that neither document alone is
   enough.
4. `030` Bramble's nudge fires automatically once both `021` and `025` have been
   attempted at least once, in either order — she does not solve it, she reframes
   it ("read them together"), which is the push toward the combine action without
   removing the "aha."
5. `combine: founders-ledger + intake-parcel` → `028`, `addItem: annotated-evidence`,
   `removeItem: founders-ledger`, `removeItem: intake-parcel`.
6. `use: annotated-evidence` on `chairman-toggle` → `029`, success, `event: toggle-defeated`.

If the player tries the combine before attempting either item alone, let it work
anyway — per the project's no-dead-ends rule, a player who reasons their way there
faster than the game expects should never be penalized for it. The alone-attempts
exist to teach, not to gate.

## Items

| `ItemId` | Source | Used on |
|---|---|---|
| `pips-marble` | `marble-candidate-correct` take | Carried to the end as the resolved goal item — not consumed, not used on anything, just held; the point is Pip finally has it back |
| `intake-parcel` (carried from Act 2) | — | `chairman-toggle` alone (deflected, `021`), then combined into `annotated-evidence` |
| `founders-ledger` (carried from Act 2) | — | `chairman-toggle` alone (deflected, `025`), then combined into `annotated-evidence` |
| `annotated-evidence` | combine `founders-ledger` + `intake-parcel` → `028`, consumes both | `chairman-toggle`, wins the confrontation |

## Events → what plays

| `EventId` | Triggers | Notes |
|---|---|---|
| `annex-opened` | Cold open, auto | Grommet's decision beat (`002`–`003`) — held on Grommet's face/pose for a beat before the door itself animates open, same "let the moment land before the mechanism moves" principle as Act 1's toll-paid beat |
| `marble-found` | `marble-candidate-correct` take success | Quiet beat, no fanfare SFX needed — `018`'s "This is a weird thing to say to a marble" line is doing the emotional work, don't undercut it with a triumphant sting |
| `toggle-defeated` | `annotated-evidence` used successfully (`029`), Toggle concedes (`032`) | Comedic deflation, not a victory fanfare — Toggle should read embarrassed, not crushed, per `docs/STORY_ARC.md`'s note that Humongous villains lose face, not everything |
| `roar-arrives` | Auto-fires immediately after `toggle-defeated` | This is the tension-ramp payoff `docs/ACT_02_DESIGN.md`'s `first-tremor` event set up — reuse that same visual language (light-flicker, rumble) at full intensity, don't invent a new treatment here |
| `grommet-guardian-payoff` | Grommet's block offer (`036`) | The scale payoff for `world_height_units: 2.4` — see animation table, this is the single most important beat in the act to get right |
| `roar-passed` | Pip checks on Grommet post-escape (`048`) | Danger-over cue — light/rumble fade out, mirrored inverse of `roar-arrives` |

## Generic fallbacks

None new this act — Sec 3–5's linear urgency sequence intentionally has no
scenery/self-examine fallback branch; Acts 1 and 2 already established that idiom,
re-triggering it mid-chase would undercut the pacing.

## Transition / ending

`057`–`058` close the game. No `sceneChanged` cut to a new location — Pip shrinks
back up in place, per `docs/GAME_CONCEPT.md`'s "closes on a small goodbye beat with
Bramble and Grommet." `058` is a deliberate callback to `act01-002` ("never mention
any of this to anyone, ever") and to the talent-show stakes from the game's logline
in `docs/GAME_CONCEPT.md` — this is the only place in three acts the talent show is
named outside that one pitch document, so it needs to land as the payoff it is, not
a throwaway last line. Worth a beat of held silence before it, per the golden
review test.

## Animation cue table

| Beat | Actor | Type | Bible section that governs it |
|---|---|---|---|
| Grommet's decision | Grommet | Held reaction beat | #2 anticipation — hold before the door animates, per the events table above |
| Marble-pile search (5 candidates) | Pip + 5 distinct props | Repeatable interact beat | Each candidate needs a visually distinct sprite (don't reuse one marble recolored) — the "galaxy" and "scratch" candidates in particular need to read clearly at a glance once the player has examined them, since the whole puzzle depends on the player being able to tell them apart on a second pass |
| Toggle's confrontation entrance | Chairman Toggle | Reaction/entrance beat | #10 exaggeration on the entrance (`019`), reusing his Act 2 "brisk, self-satisfied" idle language but interrupted/alarmed instead of composed |
| Toggle's deflect-deflect-deflate arc | Chairman Toggle | Multi-beat reaction arc across `022`→`032`, three distinct deflections plus a deflation | Each deflection (`022`, `026`) needs its own small dismissive gesture, distinct from each other — reusing one animation for both undercuts the sense that he's running out of angles. The final concession (`030`→`032`) needs to read as a *process*, not a single pose swap, matching the "timing purpose" rule the toll-paid and Grommet-mended beats already established |
| Bramble's nudge (`027`) | Bramble | Reaction/thinking beat | A visible "working it out" beat — a pause, a look between the two documents — before she speaks; this is the one moment she out-thinks the room and it should be staged like it matters |
| **Grommet holds the chokepoint (the game's climax beat)** | Grommet | Sustained strain-hold performance, not a one-shot | This is the payoff for a `world_height_units: 2.4` scale gag that's been sitting unused since `art/cast_scale.json` was first authored — give it the full contact-sheet-plus-approval-evidence treatment Acts 1 and 2 reserved for their own single best beat. Needs: a bracing/anchoring pose, visible strain (not just held-still), and a "still holding" loop that can sustain for however long the escape sequence's timing needs without reading as static |
| Escape dash (Pip, Bramble, Scuttle) | All three | Walk/run-plane, urgency-paced | Same walk-cycle contracts already built for each, just re-timed faster; Scuttle's smear-frame dash rule applies directly, reused from Act 1/2 |
| Old Bottlecap, revisited | Old Bottlecap | Reaction beat, `044`'s admission | Keep this small — a slight stillness-break at most (a longer pause before speaking, maybe one held downward glance), per the note above about not over-animating his one vulnerable line |
| **Grommet's first walk** | Grommet | New walk-plane cycle, one-time use | Full 9-key-pose contract, built once, used once — this is the visual proof of his arc's resolution, don't skip it as "just have him stay put and wave" |
| Toggle's panicked exit | Chairman Toggle | One-shot reaction/exit beat | First time this character isn't composed — deliberately messier posing than anything else he does, comedic not distressing |

## What Act 3 deliberately does not do yet

No combat, no fail-state or timer on the marble search or the Toggle petition —
wrong attempts always cost nothing but time, per the project's no-dead-ends
commitment even as the puzzles themselves get harder. Chairman Toggle's fate past
`032`/`035` is left open — he flees with everyone else and isn't seen again this
act. Whether he recurs in a hypothetical future chapter is out of scope; this act
only needs to resolve Pip, Bramble, Grommet, and Old Bottlecap's arcs, per
`docs/STORY_ARC.md`.
