# Visual Asset Credits - Lost & Underfound

Act 1 production visual source art was created with the built-in Codex image
generation tool, then converted into registered project-local raster assets under
`art/act01-production/`.

Generated source files:

- `art/act01-production/source/ai-room-source.png` - Act 1 room/background source.
- `art/act01-production/source/ai-cast-source.png` - Act 1 cast/source style board.
- `art/act01-production/source/character-reference-sheet.png` - Act 1 character
  model/reference sheet used for the current normalized sprite pass.

The current Act 1 room is rebuilt as project-local separated raster layers from
the deterministic asset generator so actors can render behind or in front of
furniture instead of depending on one baked background plate.

The shipped in-game sprite frames are normalized derivatives with fixed canvases,
explicit anchors, onion-skin QA output, and contact sheets. They are not accepted as
final solely because they were AI-generated or visually polished; each sheet must pass
the registration and cast-scale gates documented in `docs/ANIMATION_BIBLE.md`.

No third-party copyrighted characters, trademarks, or licensed source images were used
as prompts or references in this pass.
