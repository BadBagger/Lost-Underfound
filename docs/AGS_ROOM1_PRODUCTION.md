# AGS Room 1 Production Contract

Room 1 is a scrolling `3840x720` room viewed through a fixed `1280x720` AGS
viewport. The greybox is the authoritative layout; the final background must fit it,
never revise it implicitly. The room spans three viewport widths. Pip enters at the
right edge, travels left through the discovery and clerk stations, then returns right
to Bottlecap and the exit.

## Step 1 - Geometry

See `ags/room1/geometry.json` and `ags/room1/room1-greybox.png`.
`ags/room1/room1-paint-guide.png` and its three crops in
`ags/room1/paint-guides/` are the unlabeled art-placement references. They encode
the locked landmark footprints but are never runtime assets.

| Zone | Type | Coordinates / baseline | Purpose |
|---|---|---:|---|
| Under-couch floor | walkable area | room X `38-3802`; screens `0-2` | Pip movement plane. |
| Discovery station | hotspot cluster | cubbies `146-476`, dust `610-738`, popcorn `816-974`, note `1160-1302`; screen `0` | Early inspection/pickup and flavor beats. |
| Clerk station | walk-behind | desk `1440,488,460x154`; baseline `614`; screen `1` | Painted into background. Pip at clerk spot draws behind it; foreground Pip draws in front. |
| Wall note / bell | hotspots | note `1160-1302`, bell `1768-1822`; screens `0-1` | Connects discovery to clerk station. |
| Toll gate | walk-behind | `2760,302,300x300`; baseline `568`; screen `2` | Painted into background. Bottlecap baseline `576` keeps the guard in front of the bars. |
| Cobweb tunnel | hotspot | `3150-3392`; screen `2` | Foreground corner curtain; Scuttle's one-shot dash-through. |
| Pip entry | standing position | `3580,666`; screen `2` | Act opening position at right edge. |
| Pip clerk talk | standing position | `1720,584`; screen `1` | Counter interaction position. |
| Pip exit | standing position | `2690,592`; screen `2` | Grate exit position. |
| Bramble clerk | standing position | `1560,574`; screen `1` | Behind counter, low enough to read seated/short. |
| Old Bottlecap guard | standing position | `2900,576`; screen `2` | In front of gate bars. |

## Step 2 - Scale calibration

Pip is the reference actor: `194 px` tall at the clerk talk position, with feet at
`y=584`. The desk counter top at `y=488` crosses Pip `96 px` above his feet: just
below his chest / at mid-torso. The painted desk footprint is `420x154 px`.

AGS walkable-area scaling is `85%` at `y=510` rising linearly to `100%` at `y=682`.
The locked cast targets at their anchors are: Pip `194 px`, Bramble `160 px`, Old
Bottlecap `116 px`, and Scuttle `68 px`. These are room-pixel heights, not source
sprite crop sizes.

## Step 3 - Background brief

Paint one opaque, seamless `3840x720` room background around this geometry. The desk,
cubbies, bookshelf, gate, chair, cobweb curtain, and every non-actor prop are painted
into that single background with a finished wall and floor behind all furniture. This
is Bramble's tidy little kingdom: dense, specific, and full of small visual jokes,
not a generic empty basement. Keep the same warm upper-left key and one continuous
eye level across all three screens: no repeated bays, seams, tonal jumps, or lighting
reversal. Match the prior room's quality tier only: Deponia-style painterly rendering,
rich cohesive dressing, and a muted earth palette. The old composition is not a
layout source.

Author the following room-space beats into the painting. They are required scene
content, not optional decoration:

- Left: cap-folder cubbies, dust clump, popcorn-kernel boulder, wall note, and a
  believable accumulation of lost household junk around the floor edges.
- Centre: Bramble's shoebox-lid desk on thread spools, the chair behind it, service
  bell, sign-in log, filing clutter, and a narrow bookshelf of salvaged books,
  spools, labels, and oddments. Keep the floor clear at the clerk talk position.
- Right: the literal window-screen grate, its worn tollbooth hardware and exit
  tunnel, Old Bottlecap's clear staging area in front of the bars, and a cobweb
  curtain at the adjacent small tunnel where Scuttle can dash through.
- Across the ceiling: couch springs, staples, a manufacturer's tag, and ancient
  snack debris. Across walls and floor: small, readable Lost & Found history such as
  labels, thread, bent paper clips, toy parts, lint, and deliberately placed scraps.
  Dress the negative space without obscuring hotspots or the walk corridor.

Act 1 uses no parallax. A single painted background is the deliberate choice; do not
split it per object. Future parallax, if introduced, may use only far/near full-width
horizontal paintings.

### Background acceptance gate

Do not import a candidate painting into AGS until it passes every item below against
`ags/room1/room1-greybox.png`. A visually attractive image that drifts from this
contract is rejected and regenerated; geometry is never retrofitted to make it fit.

| Check | Required result |
|---|---|
| Canvas and registration | One opaque `3840x720` PNG. The couch ceiling, cubbies, dust, popcorn boulder, note, sign-in log, desk, bell, gate, cobweb curtain, and right-edge entry staging align to their room-space coordinates in `geometry.json`. |
| Desk clearance | A finished wall and floor exist behind the desk footprint. The desk is painted at `1440,488,460x154`; its counter top is at `y=488` and its walk-behind baseline is `y=614`. No hole, cutout, or separate desk layer. |
| Gate clearance | The gate is painted at `2760,302,300x300`, with the walk-behind baseline at `y=568`. Bottlecap's `y=576` staging must visibly place the guard in front of its bars. |
| Scrolling continuity | Light remains a warm upper-left key across room X `0-3840`. Horizon/eye level, floor perspective, line weight, palette, and value range remain continuous when panning through X `1280` and `2560`. No seam, repeated bay, tonal jump, or reversed light source. |
| Walk corridor | The floor clearly supports the uninterrupted walkable corridor from entry through gate, clerk, note, cubbies, and dust. Station dressing must not visually suggest an obstacle across that route. |
| Composition | The three screens are distinct play beats, not three copied panels: discovery/cubbies at left, clerk/note/bell at center, and gate/entry/exit at right. The return route retains readable environmental detail rather than becoming an empty transit void. |
| Environmental storytelling | Every scripted hotspot is visibly present and readable. The room has authored clutter, material history, small jokes, and useful-looking office detritus; empty wall or floor is used only to preserve silhouettes and movement readability. |
| Cohesion | Warm painterly rendering, upper-left light, and the muted earth palette match across the full width. Furniture is part of the painting, not pasted on or isolated. |

Review the candidate at full width and at three `1280x720` camera crops before
acceptance. Record a failure as layout, scrolling continuity, occlusion readability,
or scene cohesion; regenerate rather than loosening a locked coordinate.

## Step 4 - AGS integration

Room occlusion uses AGS walk-behind areas and baselines, never transparent furniture
layers or custom depth sorting. Import only character cels that have passed the
Animation Bible's registration, cast-scale, and full-construction gates.
