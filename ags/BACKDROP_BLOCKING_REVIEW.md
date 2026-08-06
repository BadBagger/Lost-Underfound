# Lost & Underfound AGS Backdrop Blocking Review

These plates are admitted as **intake backgrounds**, not final imported game art.
The current QA proves each screen is opaque, 1280x720, registered to its local
`geometry.json`, and has a documented visual review state. It does not replace
the actor-scale proof pass.

## Current Rule

- Keep each screen as a discrete 1280x720 AGS room plate.
- Do not flatten actors into backgrounds.
- Do not add isolated Forge-style per-object layers unless a later engine import
  specifically needs a sprite/prop.
- Before final import, every screen needs an actor-scale composite proof with the
  intended characters at their standing points.

## Screen Notes

| Screen | Intake Read | Required Before Final |
| --- | --- | --- |
| `room1/discovery` | Strong dusty discovery stage. Cubbies, dust clump, and popcorn boulder are readable. | Tighten dust/popcorn hotspot boxes after final prop choices; avoid adding more button-wall detail. |
| `room1/clerk` | Best current Act 1 office plate: desk, ledger, bell, chair, and shelf read as one place. | Prove Bramble head/hands sit cleanly behind the desk and Pip reads at the counter height. |
| `room1/gate` | Gate and cobweb are staged clearly with room for Bottlecap and Pip. | Prove Bottlecap is not buried by bars and cobweb does not cover the clickable gate path. |
| `room2/concourse` | Functional exchange hallway with clear paperwork/bureaucracy personality. | Reduce sign/button clutter if it competes with real puzzle objects; prove Scuttle and Pip pathing. |
| `room2/annex-threshold` | Clean threshold plate with strong door focus and enough empty floor for blocking. | Prove Grommet scale at the door and make sure the threshold does not imply a closed-off dead end. |
| `room2/audience-chamber` | Toggle's station has the right petty-official energy. | Prove Chairman Toggle behind the counter and keep the seal/button motif singular, not wallpaper. |
| `room3/annex-interior` | Good treasure-hoard/marble-search room. | Split candidate marble hotspots after final prop art; avoid broad "whole shelf" interaction boxes. |
| `room3/escape-concourse` | Now reads as a stable room plate, not an explosion/action frame. | Prove Grommet guardian-block pose and Pip's escape route without covering the playable floor. |
| `room3/grate-revisit` | Strong quiet goodbye/revisit plate with gate focus. | Prove Bottlecap revisit placement and final gate/open-passage click target. |

## Next Gate

The next production pass should create one composite proof per screen with:

- background plate
- walkable floor overlay
- actor standing points
- current actor renders at intended scale
- hotspot labels

Only after that pass should any background move from `visualReview.status:
intake` to `approved`.
