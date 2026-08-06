# Content Authoring Rules

This folder is the Codex-editable content layer for the planned Godot/Popochiu
production version.

## Rules

- Keep content data declarative: room graph, hotspots, items, cutscenes, dialogue
  references, and randomization tables.
- Asset paths are repo-relative for now. Godot import can later translate them to
  `res://` paths.
- Every room exit must point to a valid room id and named entry point.
- Every essential interaction must be reachable through a smoke walkthrough or
  solvability test.
- Non-essential click gags should be marked `"essential": false`.
- Keep Act 1 content grounded in `script/ACT_01_SCRIPT.json` and
  `docs/ACT_01_DESIGN.md`.

## Checks

Run `npm.cmd run qa:godot-content` after editing this folder.
