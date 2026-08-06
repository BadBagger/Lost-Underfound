# Interactable Change Layer Contract

This contract exists to prevent the desk/gate failure class: an interactable looked
painted into the world, but the runtime could not name and verify the layer that
changed or occluded an actor.

## Rule

If an object changes, opens, reveals, receives a prop, disturbs, or occludes an actor,
it must be declared as a change layer before production art is accepted. Background
plates may contain fixed dressing only.

Change layers must be:

- named in `ags/interactive_change_layers.json`
- bound to a hotspot, walk-behind, or separate prop in the AGS geometry
- non-interactive; hotspot masks own clicks
- ordered with an explicit z value
- marked `production-ready` only when the source asset or runtime layer exists
- included in the local QA chain and GitHub nightly audit

## Production Interpretation

Desk and counter fronts are not optional decoration when a character sits behind
them. They are foreground occluders with a named layer. Gates, grates, doors,
cobwebs, dust reveals, tossed buttons, stamps, needles, and marble candidates are
also not allowed to hide inside the background if they ever change state.

If a layer is still planned for Act 2 or Act 3, it stays in the manifest with
`status: "planned"` so the scene blocking remains honest without falsely admitting
unfinished production art.

## QA

Run:

```powershell
npm.cmd run qa:change-layers
```

The full local and nightly audit runs this check through `npm test`.
