Expression Plate Rebuild Attempt - Rejected
===========================================

Status: rejected, do not use for production.

Reason:
- The attempted `build_plates.py` path procedurally drew Otto's facial features.
- That violated the brief. Face plates must be derived from existing source expression art only.
- QA became circular because it measured generated features against the same generated rig assumptions.

Correct next path:
- Use source expression renders as the only source for facial pixels.
- Allowed operations are translate, rotate, uniform scale, and alpha masking.
- If only the flattened chroma patch sheet exists, re-export or regenerate clean full-frame expression renders before rebuilding the plate system.

