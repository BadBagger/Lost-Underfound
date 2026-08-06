# Godot + Popochiu Production Plan

This document captures the engine-direction handoff from the Pajama Sam-style
engineering plan. It does not delete or replace the current Vite prototype; it
defines the production stack we migrate toward after the Act 1 prototype proves
the content and animation rules.

## Decision

Target stack:

- Godot 4 for the production project.
- Popochiu-style adventure primitives: rooms, walkable areas, hotspots, exits,
  inventory, character actors, and dialogue.
- Data-driven content under `content/`, validated before engine import.
- Deterministic cutout rigs for characters. AI-generated images are source art,
  not final ungoverned animation frames.
- Voice and mouth timing stay manifest-driven so every line can be checked.

## Current Repo Split

- `src/` remains the working web prototype and Tailscale-previewable Act 1 slice.
- `content/` is the new production content layer. It mirrors Act 1 as room, hotspot,
  item, randomization, and walkthrough data.
- `tools/check_godot_content_manifest.py` is the first Godot-side content gate.
- `project.godot` is a minimal project placeholder until Godot, Popochiu, and GUT
  are pinned and vendored.

## Build Order

1. Content scaffold and validation gate.
2. Pin Godot version, vendor Popochiu and GUT, and add headless import/test commands.
3. Implement generic loaders for the JSON content layer.
4. Import Act 1 room plates and walkable polygons.
5. Import the approved registered character sheets or rebuild them as deterministic
   Godot cutout rigs.
6. Wire the Act 1 smoke walkthrough against the real interaction system.
7. Only then scale beyond Act 1.

## Non-Negotiables

- Geometry and content data are authority. Art must conform to locked interaction
  coordinates, not the other way around.
- Hotspots must have explicit `walk_to` points.
- Every exit must have a valid destination and destination entry point.
- Every referenced asset path must exist before import.
- Essential progression must be represented in a walkthrough or graph-solvability
  test.
- Acts 2 and 3 remain blocked until their script/design passes exist.

## Open Production Tasks

- Pin exact Godot version.
- Pin exact Popochiu release.
- Pin exact GUT release.
- Decide whether Ink/GodotInk is worth the .NET dependency for web export, or whether
  a pure-GDScript dialogue layer is safer.
