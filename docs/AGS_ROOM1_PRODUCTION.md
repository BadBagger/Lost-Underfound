# AGS Room 1 Production Contract

Room 1 is a scrolling `3840x720` room viewed through a fixed `1280x720` AGS
viewport. The greybox is the authoritative layout; the final background must fit it,
never revise it implicitly. The room spans three viewport widths. Pip enters at the
right edge, travels left through the discovery and clerk stations, then returns right
to Bottlecap and the exit.

## Step 1 - Geometry

See `ags/room1/geometry.json` and `ags/room1/room1-greybox.png`.

| Zone | Type | Coordinates / baseline | Purpose |
|---|---|---:|---|
| Under-couch floor | walkable area | room X `38-3802`; screens `0-2` | Pip movement plane. |
| Discovery station | hotspot cluster | cubbies `146-476`, dust `610-738`; screen `0` | Early inspection/pickup beat. |
| Clerk station | walk-behind | desk `1440,488,460x154`; baseline `614`; screen `1` | Painted into background. Pip at clerk spot draws behind it; foreground Pip draws in front. |
| Wall note / bell | hotspots | note `1160-1302`, bell `1768-1822`; screens `0-1` | Connects discovery to clerk station. |
| Toll gate | walk-behind | `2760,302,300x300`; baseline `568`; screen `2` | Painted into background. Bottlecap baseline `576` keeps the guard in front of the bars. |
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
cubbies, bookshelf, and gate are painted into that single background with a finished
wall and floor behind all furniture. Keep the same warm upper-left key and one
continuous eye level across all three screens: no repeated bays, seams, tonal jumps,
or lighting reversal. Match the prior room's quality tier only: Deponia-style
painterly rendering, rich cohesive dressing, and a muted earth palette. The old
composition is not a layout source.

Act 1 uses no parallax. A single painted background is the deliberate choice; do not
split it per object. Future parallax, if introduced, may use only far/near full-width
horizontal paintings.

## Step 4 - AGS integration

Room occlusion uses AGS walk-behind areas and baselines, never transparent furniture
layers or custom depth sorting. Import only character cels that have passed the
Animation Bible's registration, cast-scale, and full-construction gates.
