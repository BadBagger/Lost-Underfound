# Act 2 Design — "The Button Sovereignty"

Companion to `script/ACT_02_SCRIPT.json`, same relationship `docs/ACT_01_DESIGN.md`
has to Act 1's script. Read `docs/STORY_ARC.md` first — this document is the
mechanical layer under the plot beats that doc lays out. Not yet built or produced;
this is a script/design pass only, the same stage Act 1 was in before Codex built
its engine data and before the audio pass.

**Difficulty pass note:** this is a full rewrite of the first-draft version of this
document. The Grommet trust puzzle went from "examine Grommet, he has an obviously
loose seam, combine two items lying on the floor, use on him" (one-step, hint
handed to the player) to a genuine multi-clue chain: an oblique environmental clue,
an NPC line that describes a symptom without naming a cause, a dialogue-gated
resource instead of a free floor pickup, and a fair decoy target. See
`docs/STORY_ARC.md`'s difficulty-target note for why. Nothing here was voiced yet,
so a wholesale rewrite carried no production cost — unlike Act 1, where the
equivalent pass had to be additive only.

## Location description

The Exchange Concourse — the Button Court's public face, one large room reached
through the Grate Pip opened at the end of Act 1. Where Underneath's Act 1 chamber
read as cozy and improvised (a shoebox-lid desk, bottle-cap cubbies), the Concourse
reads as institutional: teller windows, a notice board thick with bulletins, a
citizen filing booth with a real queue, everything a little too formal for how
small the stakes actually are. Three areas share this one room, same "composite
scene with hotspot clusters" approach Act 1 used rather than a hard scene
transition:

- **The Concourse floor** — exchange window, notice board, filing booth, the
  needle prop, where Scuttle is first caught, and where Bramble can be found this
  act (she's left her desk — see cast notes).
- **The Annex threshold** — a heavy, dark doorway at the back, Grommet parked in
  front of it exactly the way Old Bottlecap was parked in front of the Grate.
- **The Audience Chamber** — a side alcove, Chairman Toggle's desk, reachable once
  Pip has a reason to petition (no hard gate on entry, but nothing productive
  happens there until the parcel is in hand).

## Cast present

| Character | Role this act | Idle behavior |
|---|---|---|
| **Pip** | Player-controlled | N/A |
| **Bramble** | Travels with Pip this act — **new rig requirement**: Act 1 built her furniture-anchored (desk-fixed); Act 2 needs a walk-plane version, since her arc requires her to leave the desk and see the Annex threshold herself. Flag this early for the animation pass, it's new work, not a reuse. | Walk-plane idle/follow; no longer the shuffling-folders loop from Act 1 |
| **Scuttle** | Interactive this act (cameo-only in Act 1) | Fast walk-plane loop until caught, then a still fidgety-impatient idle during dialogue, per his "twitchy" trait |
| **Grommet** | Main new NPC, Annex-threshold, fixed | Furniture-anchored idle, same contract class as Old Bottlecap's Act 1 rig — but the performance target is shy/gentle, not stern, per `docs/STORY_ARC.md`'s character notes. Do not reuse Old Bottlecap's timing wholesale. His idle needs a subtle periodic shift/shiver cue once `act02-049` has played (see animation table) — small enough to miss on a first pass, that's intentional. |
| **Chairman Toggle** | New NPC, Audience Chamber, desk-fixed | Furniture-anchored idle, brisk and self-satisfied — stamping things rapidly, unlike Bramble's careful shuffle |
| **Old Bottlecap** | Not physically present | Referenced only, via the notice board rumor and the Founder's Ledger |

## Hotspots

| `HotspotId` | Label | Rules |
|---|---|---|
| `exchange-window` | Currency Exchange Window | inspect → `003`; use → `004` (permanent flavor fail) |
| `notice-board` | Public Notice Board | inspect, rotating pool `005` (1st) then `006`/`007`/`008`/`009` (loop, 4 entries). `007` is the Old-Bottlecap red-herring seed. `009` is the puzzle clue — a "maintenance advisory" that never names Grommet, only "the Annex access corridor." This has to be read and mentally cross-referenced against Grommet's own `049` line; neither alone gives the answer. |
| `filing-booth` | Citizen Filing Booth | inspect → `010`; flavor rotate pool `011`/`012` (2 entries). `012` seeds the decoy target for the threaded-needle puzzle — a second citizen with a drafty, popped-seam coat. |
| `needle` | Dropped Needle | inspect → `013`; take → `014`, `addItem: needle` |
| `bramble` (early beat) | Bramble, walk-plane, found on the Concourse floor | Auto-fires once on first approach this act: `015`→`022` (the reunion scene). This is where `thread` is obtained — **no `thread-spool` floor hotspot this act**, replaced entirely by this dialogue gate. This scene also plants the marble's identifying detail (`021`) that Act 3's search puzzle depends on — don't let a player skip this beat and still expect the Act 3 clue to feel planted; it's the only place that detail is stated before Act 3 restates it. |
| `annex-threshold` (examine only, pre-trust) | The Annex doorway | inspect → covered by Grommet's greeting sequence, no separate examine text needed while Grommet is present |
| `grommet` | Grommet | see NPC conversation below |
| `chairman-toggle` | Chairman Toggle | see NPC conversation below |
| `founders-ledger` | Founder's Ledger (prop, tucked near the notice board, discoverable any time after entering the Concourse) | inspect (1st) → `059`, `addItem: founders-ledger`; inspect (2nd) → `060` (realization beat) |

## Items

| `ItemId` | Source | Used on |
|---|---|---|
| `thread` | `bramble` reunion dialogue (`022`), NOT a floor pickup this act — dialogue-gated on purpose, see difficulty note above | combine with `needle` |
| `needle` | `needle` take | combine with `thread` |
| `threaded-needle` | combine `thread` + `needle` → `023`, consumes both | correct use: `grommet`. Decoy use: `filing-booth` citizen (the drafty-coat one from `012`) → `051`, rejected, not consumed, retryable — a fair near-miss, not a trap |
| `intake-parcel` | `scuttle` conversation, event `parcel-dropped` | shown to `bramble` (auto-topic trigger), shown to `chairman-toggle` (petition) |
| `founders-ledger` | `founders-ledger` prop, 1st inspect | shown to `bramble` (auto-topic trigger) |

## NPC conversations

### Bramble — reunion (new this pass)

Auto-fires once, first approach to Bramble this act: `015`→`022`. This replaces
what would otherwise be a silent walk past a hotspot with no content — it's also
carrying two structural jobs at once (item-gating `thread`, and planting the Act 3
clue), so don't cut it for pacing; it's short (8 lines) but load-bearing.

### Scuttle

- Auto-fires on approach: fixed sequence `024`→`028` (5 lines, catching him)
- **`about-himself`** — player-selectable, `029`→`031`
- **`about-deliveries`** — player-selectable, `032`→`034`
- After both topics have been seen at least once, the parcel-drop beat auto-fires
  once: `035`→`038`, `event: parcel-dropped`, `addItem: intake-parcel`. Scuttle then
  exits the scene (`setFlag: scuttleExited`) — non-interactive for the rest of the
  act, matching his Act 1 cameo-only footprint everywhere except this one stop.

### Bramble — main topics

- **`parcel-checkin`** — auto-fires once, first time Pip approaches Bramble after
  `intake-parcel` is obtained: `039`→`043`. This is the act's first real crack in
  her deflection from Act 1 (`act01-021`) — direct callback, worth the VO director
  noting when this act is eventually recorded.
- **`ledger-reveal`** — auto-fires once, first time Pip approaches Bramble after
  `founders-ledger` is obtained: `061`→`062`.
- **`toggle-pushback`** — not a separate topic, fires inline during the Chairman
  Toggle conversation (`066`), see below.

### Grommet

- Auto-fires on first approach: `044`→`048` (5 lines) — personality-establishing
  only, no puzzle content yet.
- `049` auto-fires on second approach (or a short delay after first approach) —
  the vague-unease line. This is the puzzle's NPC-side clue, deliberately not a
  diagnosis ("there's a draft... probably nothing," not "my seam's coming loose").
- `examine: grommet` (repeatable, available once `049` has played) → `050`. Pip
  notices something's off but explicitly doesn't solve it for the player — this
  line's whole job is to confirm "yes, something here is worth investigating,"
  not to hand over the answer. The answer requires connecting `049` to the notice
  board's `009`.
- `use: threaded-needle` on `grommet` → `052`→`055`, `event: grommet-trust-earned`,
  `setFlag: grommetTrust`, `removeItem: threaded-needle`. This works regardless of
  whether the player read `009` and `050` first — deduction makes it satisfying,
  it doesn't gate it; per the project's no-dead-ends rule, a player who just tries
  the obvious "use my new item on the big friendly NPC" still succeeds, they just
  get less of the "aha."
- **`about-annex`** — unlocked only after `grommetTrust`, player-selectable, `056`
- Direct ask, player-selectable once `grommetTrust` is set → `057`→`058`. Grommet
  holds (`058`) — this does not open the Annex. That happens in Act 3 only, once the
  tremor forces the issue. Don't build an Annex-access flag off this exchange.

### Chairman Toggle

- Auto-fires on approach: `063`
- `use: intake-parcel` on `chairman-toggle` (the petition) → `064`→`067`,
  `event: petition-denied`, `setFlag: toggleRefused`. `066` is Bramble's inline
  pushback line — Toggle's conversation is the one place in this act where a second
  NPC interjects mid-exchange; stage it as a three-way beat, not back-to-back
  two-way lines.
- No other topics this act — Toggle is a wall, not a quest-giver, by design. Act 3
  is where he actually has to engage.

## Events → what plays

| `EventId` | Triggers | Notes |
|---|---|---|
| `parcel-dropped` | Scuttle conversation, after both topics seen | SFX: a soft paper-thud; Scuttle fumbles it mid-stride per the smear-frame rule (fast character, sudden stop) rather than a clean pratfall — he's still trying to keep moving even while dropping it |
| `grommet-trust-earned` | `threaded-needle` used on Grommet | The act's warmest beat — see animation table. No SFX sting needed, this one should land on performance alone |
| `petition-denied` | Chairman Toggle petition | Toggle's stamp comes down hard on cue with "Good AFTERNOON" (`067`) — a single decisive stamp-thud, comedic timing, door-slam energy without an actual door |
| `first-tremor` | Auto-fires once, after `toggleRefused` is set and Pip returns to the Concourse floor | First physical foreshadowing of the Roar — light flicker + a low rumble, per `docs/GAME_CONCEPT.md`'s Act 3 tension ramp starting early, not waiting for Act 3 to open |

## Generic fallbacks

- Use item on scenery (no rule matches) → `068`
- Examine self → `069`

## Transition

`first-tremor` plays (`070`/`071`), then `072` is the transition line into Act 3 —
same pattern as Act 1's `sceneChanged: true` cut, but this time the transition is
interrupted urgency, not a clean puzzle-solved beat: Pip doesn't get the tidy
victory lap Act 1 ended on, the floor makes the decision instead.

## Animation cue table

| Beat | Actor | Type | Bible section that governs it |
|---|---|---|---|
| Bramble walk-plane (new) | Bramble | Walk-plane cycle | Full 9-key-pose walk-cycle contract — this is new work, she was furniture-anchored in Act 1, don't reuse those cels |
| Scuttle caught mid-dash | Scuttle | Reaction/stop beat | Smear-frame rule applies to the stop itself, not just the run — a fast character braking hard needs the same treatment as the run cycle, not a plain instant-stop |
| Scuttle fumble/drop | Scuttle, intake-parcel prop | Item + reaction beat | #2 anticipation on the fumble, #1 squash/stretch on the parcel's landing bounce |
| Grommet idle (pre-`049`) | Grommet | Furniture-anchored idle loop | Scene-character contract, but performance target is shy/still, closer to Old Bottlecap's sparse timing than Bramble's busy shuffle — small held gestures (looking down, small foot-shift), not business |
| Grommet idle (post-`049`) | Grommet | Furniture-anchored idle loop, modified | Add a small, easy-to-miss periodic shoulder-shift/shiver — the "draft" line needs a physical tell for observant players, but it must read as subtle, not a flashing hotspot marker. This is the closest thing this act's puzzle has to a visual hint, and it should stay subtle by design. |
| **Grommet mended (the act's climax beat)** | Grommet + Pip + threaded-needle prop | Multi-actor performance beat | Same weight class as Act 1's toll-paid beat — full contact-sheet-plus-approval-evidence treatment. Grommet's reaction (`053`) needs a held beat before any dialogue anim starts, per the golden review test's "timing purpose" rule — let the moment land silently for a few frames first |
| Chairman Toggle idle | Chairman Toggle | Furniture-anchored idle loop | Brisk, busy — the opposite direction from Grommet, rapid small stamping motions, self-satisfied posture; this character's comedy is motion and self-importance, not stillness (contrast with Old Bottlecap on purpose) |
| Toggle's stamp-down | Chairman Toggle | Reaction beat | #10 exaggeration — this one beat can be big, it's the closest thing this act has to a slapstick punctuation mark |
| First tremor | Environment (whole scene) | Environmental cue, no character rig | Light-flicker + subtle screen-shake per `docs/GAME_CONCEPT.md` Act 3 notes — establish the visual language here at low intensity so Act 3 can escalate it, don't invent a new tremor treatment in Act 3 |

## What Act 2 deliberately does not do yet

No Annex interior (that's Act 3's real payoff space — don't build it here, Grommet's
`058` explicitly holds the line), no direct Old Bottlecap appearance (his reveal is
evidence-based, through the ledger and Bramble's reaction, not a scene with him),
and Chairman Toggle does not lose this round — his defeat is Act 3's, earned through
the petition's own paperwork, not repeated stonewalling worn down by attrition.

**On the puzzle being harder, not unfair:** every clue needed to solve the Grommet
puzzle without guessing is available before the puzzle is offered (`009` and `049`
can both be seen well before Pip ever picks up the needle), and guessing still
works — using the threaded-needle on Grommet directly succeeds without having read
either clue, it's just a less satisfying solve. The one true decoy (`051`, the
citizen's coat) costs nothing to attempt wrong. No flag, timer, or resource makes
this puzzle failable; it only makes it require attention.
