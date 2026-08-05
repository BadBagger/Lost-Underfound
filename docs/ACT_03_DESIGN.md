# Act 3 Design — "The Roar"

Companion to `script/ACT_03_SCRIPT.json`, same relationship the other two design
docs have to their scripts. Read `docs/STORY_ARC.md` first. Not yet built or
produced — script/design pass only.

**Inventory carries across act boundaries.** `intake-parcel` and `founders-ledger`,
both picked up in Act 2, are used again here (`014`/`015` re-examines the parcel for
fine print; `018` shows the ledger to Chairman Toggle). This is the first act where
that matters mechanically — flag it for whoever builds the save/inventory system,
since Act 1 and Act 2 each resolved with a clean inventory (button consumed on the
gate, threaded-needle consumed on Grommet) and never needed to test carry-over.

## Location description

Three connected spaces, same composite-scene approach as Acts 1 and 2:

- **The Annex** — dark, cramped, floor-to-ceiling piles of confiscated shine. Not
  sinister, just sad in a way the game hasn't been yet — years of somebody else's
  lucky charms. Grommet's threshold is the doorway back out to the Concourse.
  Chairman Toggle's desk from Act 2 is empty; he shows up here instead once alerted.
- **The Concourse** — same room as Act 2, now background to the escape rather than
  a hub to explore. No new hotspots here; Act 2's exchange window/notice
  board/filing booth are set dressing Pip runs past, not re-examined.
  `act03-027`'s "fastest way out is through the filing booth" is a route callout,
  not a puzzle.
- **The Grate** — Act 1's toll-gate location, revisited. Old Bottlecap is here,
  not at the Annex or Concourse — this is deliberate, it's his post and always has
  been, and this act's whole point is that he chooses to use it differently.

## Cast present

| Character | Role this act | Idle/behavior |
|---|---|---|
| **Pip** | Player-controlled | N/A |
| **Grommet** | Opens the Annex, then holds the chokepoint during the Roar | Furniture-anchored through the block sequence — **then walks**, for the first and only time in the game, in the goodbye beat (`041`–`044`), once the danger's passed and he no longer has a post to keep. This needs a new walk-plane cycle built just for this one moment; treat it as a small, deliberate animation event, not a reused-Bramble-cycle shortcut — the whole emotional point is that this is the first time he's moved. |
| **Chairman Toggle** | Confronts Pip in the Annex, then flees with everyone else | Furniture-anchored idle carries from Act 2 for the confrontation; needs a new panicked-scramble exit beat once the Roar hits (`023`) — his first non-desk animation, comedic not dignified |
| **Bramble** | Present throughout, walk-plane (established Act 2) | Continues Act 2's walk-plane rig |
| **Scuttle** | Reappears to guide the escape route | Fast walk-plane, same rig as Act 1/2 |
| **Old Bottlecap** | Reappears at the Grate | Furniture-anchored, reuses Act 1's rig — this is his one other appearance in the whole game, keep his stillness-as-comedy read intact even in this warmer scene, don't over-animate the vulnerability in `032` |

## Hotspots

| `HotspotId` | Label | Rules |
|---|---|---|
| `grommet` (continued from Act 2) | Grommet | `event: annex-opened` auto-fires this act's cold open (`001`–`004`) — no player action needed, this is not a repeat of Act 2's trust puzzle |
| `annex-interior` | The Annex (general) | inspect, rotating pool `005` (1st) then `006`/`007` (loop) |
| `marble-pile` | Marble Pile | inspect (1st) → `008` (states the identifying detail — a lopsided-star nick — this is the search puzzle's win condition, phrased as flavor, not a UI prompt); search attempt 1 → `009` (decoy); search attempt 2 → `010` (decoy); search attempt 3 → `011`, success, `addItem: pips-marble`, `event: marble-found`, no further searches needed or offered |
| `chairman-toggle` (relocated) | Chairman Toggle | auto-fires on `marble-found`: `012`–`013`. `use: intake-parcel` on Toggle → `014`–`015` (fine-print discovery), `setFlag: finePrintFound`. `use: founders-ledger` on Toggle → `018`, requires `finePrintFound` and the intervening exchange (`016`–`017`) to have played; if the player shows the ledger before the parcel fine-print, queue the fine-print beat first — the ledger is the closing argument, not the opener, don't let sequence-skipping undercut the beat |
| `escape-route` | (implicit, triggered by scene transition once `toggle-defeated` + `roar` fire) | No player-directed hotspot interaction during the escape sequence — Sec 3–5 is a mostly-linear urgency beat, per `docs/GAME_CONCEPT.md`'s Act 3 tension ramp. Don't build player-choice branching into a sequence whose whole point is that there isn't time to deliberate. |
| `old-bottlecap` (Grate, revisited) | Old Bottlecap | auto-fires once Pip reaches the Grate: `030`–`033` |

## Items

| `ItemId` | Source | Used on |
|---|---|---|
| `pips-marble` | `marble-pile` search success | Carried to the end as the resolved goal item — not consumed, not used on anything, just held; the point is Pip finally has it back |
| `intake-parcel` (carried from Act 2) | — | `chairman-toggle`, re-examined for fine print |
| `founders-ledger` (carried from Act 2) | — | `chairman-toggle`, shown as closing evidence |

## Events → what plays

| `EventId` | Triggers | Notes |
|---|---|---|
| `annex-opened` | Cold open, auto | Grommet's decision beat (`002`–`003`) — held on Grommet's face/pose for a beat before the door itself animates open, same "let the moment land before the mechanism moves" principle as Act 1's toll-paid beat |
| `marble-found` | `marble-pile` search success | Quiet beat, no fanfare SFX needed — `011`'s "This is a weird thing to say to a marble" line is doing the emotional work, don't undercut it with a triumphant sting |
| `toggle-defeated` | Founder's Ledger shown, Toggle concedes (`020`) | Comedic deflation, not a victory fanfare — Toggle should read embarrassed, not crushed, per `docs/STORY_ARC.md`'s note that Humongous villains lose face, not everything |
| `roar-arrives` | Auto-fires immediately after `toggle-defeated` | This is the tension-ramp payoff `docs/ACT_02_DESIGN.md`'s `first-tremor` event set up — reuse that same visual language (light-flicker, rumble) at full intensity, don't invent a new treatment here |
| `grommet-guardian-payoff` | Grommet's block offer (`024`) | The scale payoff for `world_height_units: 2.4` — see animation table, this is the single most important beat in the act to get right |
| `roar-passed` | Pip checks on Grommet post-escape (`036`) | Danger-over cue — light/rumble fade out, mirrored inverse of `roar-arrives` |

## Generic fallbacks

None new this act — Sec 3–5's linear urgency sequence intentionally has no
scenery/self-examine fallback branch; Acts 1 and 2 already established that idiom,
re-triggering it mid-chase would undercut the pacing.

## Transition / ending

`045`–`046` close the game. No `sceneChanged` cut to a new location — Pip shrinks
back up in place, per `docs/GAME_CONCEPT.md`'s "closes on a small goodbye beat with
Bramble and Grommet." `046` is a deliberate callback to `act01-002` ("never mention
any of this to anyone, ever") and to the talent-show stakes from the game's logline
in `docs/GAME_CONCEPT.md` — this is the only place in three acts the talent show is
named outside that one pitch document, so it needs to land as the payoff it is, not
a throwaway last line. Worth a beat of held silence before it, per the golden
review test.

## Animation cue table

| Beat | Actor | Type | Bible section that governs it |
|---|---|---|---|
| Grommet's decision | Grommet | Held reaction beat | #2 anticipation — hold before the door animates, per the events table above |
| Marble-pile search | Pip + prop pile | Repeatable interact beat | Three passes need visually distinct decoy props (don't reuse one marble sprite recolored) — the "galaxy marble" (`010`) in particular deserves a distinct look, it gets a callback laugh in `020` |
| Toggle's confrontation entrance | Chairman Toggle | Reaction/entrance beat | #10 exaggeration on the entrance (`012`), reusing his Act 2 "brisk, self-satisfied" idle language but interrupted/alarmed instead of composed |
| Toggle's deflation | Chairman Toggle | Multi-beat reaction arc across `017`→`020` | This needs to read as a *process*, not a single pose swap — stalling, cracking, conceding are three distinct held beats, matching the "timing purpose" rule the same way the toll-paid and Grommet-mended beats did in Acts 1–2 |
| **Grommet holds the chokepoint (the game's climax beat)** | Grommet | Sustained strain-hold performance, not a one-shot | This is the payoff for a `world_height_units: 2.4` scale gag that's been sitting unused since `art/cast_scale.json` was first authored — give it the full contact-sheet-plus-approval-evidence treatment Acts 1 and 2 reserved for their own single best beat. Needs: a bracing/anchoring pose, visible strain (not just held-still), and a "still holding" loop that can sustain for however long the escape sequence's timing needs without reading as static |
| Escape dash (Pip, Bramble, Scuttle) | All three | Walk/run-plane, urgency-paced | Same walk-cycle contracts already built for each, just re-timed faster; Scuttle's smear-frame dash rule applies directly, reused from Act 1/2 |
| Old Bottlecap, revisited | Old Bottlecap | Reaction beat, `032`'s admission | Keep this small — a slight stillness-break at most (a longer pause before speaking, maybe one held downward glance), per the note above about not over-animating his one vulnerable line |
| **Grommet's first walk** | Grommet | New walk-plane cycle, one-time use | Full 9-key-pose contract, built once, used once — this is the visual proof of his arc's resolution, don't skip it as "just have him stay put and wave" |
| Toggle's panicked exit | Chairman Toggle | One-shot reaction/exit beat | First time this character isn't composed — deliberately messier posing than anything else he does, comedic not distressing |

## What Act 3 deliberately does not do yet

No combat, no fail-state on the marble search (three attempts is a fixed
comedic beat, not a timer or a game-over condition), and Chairman Toggle's fate
past `020`/`023` is left open — he flees with everyone else and isn't seen again
this act. Whether he recurs in a hypothetical future chapter is out of scope; this
act only needs to resolve Pip, Bramble, Grommet, and Old Bottlecap's arcs, per
`docs/STORY_ARC.md`.
