# AGS Room 1 Production Contract

Room 1 is three discrete native `1280x720` AGS screens, never a scrolling
`3840x720` panorama. The screens are joined by player-driven edge transitions:
Discovery <-> Clerk <-> Gate. `ags/room1/geometry.json` is authoritative for every
screen-local placement, baseline, standing position, and link.

## Screen Route

Pip begins the cold open in **Discovery**, moves right to **Clerk** for Bramble's
greeting/tutorial, then right to **Gate**. Edge links are bidirectional so the
optional post-gate Bramble exchange remains possible. The open toll gate is an Act 2
transition, not a Room 1 edge link; it must play script line
`act01-049-pip-transition-out`.

| Screen | Required scene content | Links |
|---|---|---|
| Discovery | Couch ceiling, cap-folder cubbies, dust nest, popcorn boulder | Right edge -> Clerk; Clerk return -> right-side entry. |
| Clerk | Solid Bramble desk, bookshelf, sign-in log, wall note, bell | Left edge -> Discovery; right edge -> Gate. |
| Gate | Toll grate/Old Bottlecap station and distinct cobweb tunnel | Left edge -> Clerk; opened grate -> Act 2. |

## Geometry And Scale

Pip is the reference actor at `194 px` tall. Each screen has a local walkable-floor
polygon and uses AGS native character walking only. There is no scrolling and no
custom depth sorting. Pip needs separate left/right walk sprites; standard edge exits
walk offscreen and the destination plays the reciprocal walk-on animation. The toll
gate instead uses the bespoke `duck-through-gate` exit animation after `gateOpen`.

The Clerk desk is a **solid painted background piece** at `160,488,460x154`, with
baseline `614`. Bramble is a counter-height talking-head actor registered at
`280,510`: only head and hands clear the counter. The chair is background dressing
only and may be repainted or omitted; no player or clerk walk space exists behind the
desk. Pip's clerk-talk spot is `440,584`, placing the counter at mid-torso.

The Gate is painted at `760,302,300x300`, baseline `568`. Old Bottlecap's `y=576`
anchor deliberately renders in front of the bars. The cobweb tunnel is a distinct
hotspot, not part of the grate.

## Background Production

Produce one opaque painted background per screen:

- `ags/room1/background/discovery.png`
- `ags/room1/background/clerk.png`
- `ags/room1/background/gate.png`

Each is a cohesive, dense, warm painterly Lost & Found composition with consistent
upper-left light **within that screen**. The approved studies are look references
only. They do not override the local coordinates in `geometry.json`. Do not generate
transparent furniture layers or recreate the old continuous-room seam workflow.

The Discovery screen needs lost household history around the cubbies and floor props.
The Clerk screen needs a dense little bureaucracy made of salvaged objects, but the
desk remains a legible solid counter for Bramble's talking head. The Gate screen needs
the grumpy toll station, a clear Bottlecap staging spot in front of the bars, and a
separate cobweb tunnel for Scuttle.

## Background Acceptance Gate

Do not import a screen into AGS until `npm run qa:ags:background` passes. For each
screen that command requires:

- opaque, exactly `1280x720` art;
- a sibling review manifest, such as `background/discovery.review.json`, confirming
  `geometryAuthority: true` and `studiesReferenceOnly: true`;
- all of `objectPlacement`, `internalLighting`, `perspectiveEyeLevel`,
  `finishedSurfaces`, and `dimensions` marked `pass`;
- measured placement evidence for every local hotspot and walk-behind: `2 px`
  tolerance for the desk and gate, `6 px` for the other props;
- painted wall/floor behind every AGS walk-behind region, with no alpha holes or
  placeholders.

There are no seam crops and no full-room light-continuity gate because screens are
discrete. A strong-looking background that misses local geometry still fails.

## AGS Integration

After all three background gates pass, import them as three AGS rooms. Define each
local walkable area, the Clerk desk and Gate walk-behind masks/baselines, local
hotspots, entry points, and edge-transition handlers from `geometry.json`. Do not
begin character wiring before the matching screen background has passed QA.

Import only character cels that have passed the Animation Bible's registration,
cast-scale, and full-construction gates.
