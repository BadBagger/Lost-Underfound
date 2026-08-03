# Act 1 Layering Contract

Act 1 is not a single background with sprites pasted on top. The entry chamber is
rendered as an ordered scene stack so actors can sit behind, in front of, or inside
furniture without breaking staging.

The generated layer manifest lives at:

- `art/act01-production/scene/layers.json`

Required layer order:

1. `background-plate` - the room plate.
2. `cubby-wall`, `cobweb-curtain`, `popcorn-boulder` - separated room props.
3. `dust-prop` - floor prop animation.
4. `desk-back`, `gate-back` - furniture backing layers behind fixed actors.
5. `bramble-body` - Bramble's furniture-anchored actor slot, behind the desk front.
6. `desk-foreground` - the desk-front occlusion layer.
7. `gate-foreground` - the gate/bar foreground layer.
8. `old-bottlecap-body` - Old Bottlecap's fixed gate-front actor slot.
9. `gate-animation` - visible only when the toll gate opens.
10. `pip-body` - Pip's walk-plane actor layer.
11. `hotspot-masks` - invisible interaction layer.

`npm run qa:layers` verifies that the layer manifest exists, required layer IDs are
declared, referenced layer assets exist, and the runtime renders the expected layer
slots. This supplements registration/cast-scale QA; it does not replace it.

This Act 1 pass uses authored fixed slots because Pip does not yet need to walk
behind multiple independent foreground masks. When a room adds true walk-behind
movement, implement the shared baseline algorithm in
`specs/DYNAMIC_BASELINE_DEPTH_SORTING.md`: each walk-behind mask gets a scene-space
baseline and each actor's draw order follows its contact Y.

Character model source for the current Act 1 production pass is:

- `art/act01-production/source/character-reference-sheet.png`

Generated model-sheet cutouts are normalized into the existing registered canvases.
Do not hand-scale individual frames to make them fit the room. If scene placement is
wrong, adjust the actor slot or layer plane. If the model drawing itself is wrong,
replace the model-sheet source/crop and regenerate.
