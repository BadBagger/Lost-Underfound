# Act 2/3 Animation Backlog

Source of truth: `docs/STORY_ARC.md`, `docs/ACT_02_DESIGN.md`,
`docs/ACT_03_DESIGN.md`, `script/ACT_02_SCRIPT.json`, and
`script/ACT_03_SCRIPT.json`.

This is a production backlog, not an admission record. A clip listed here is not
final until it passes the normal Animation Bible gates: registration, cast-scale,
animation admission, contact-sheet/onion review, and in-scene visual QA.

## Current Production Baseline

| Character | Existing usable baseline | Notes |
|---|---|---|
| Pip | Act 1 idle, 9-key walk-plane cycle, Act 1 action sheets, Meshy 3D sprite-render spike proofs; Act 2/3 proof clips now exist from the correct export 4 Pip model | Act 2/3 proofs are useful animation-intake evidence only. Do not replace the Act 1 admitted walk without QA, and do not use the misfiled patchwork-rag-doll proof set as Pip. |
| Bramble | Act 1 desk/furniture-anchored idle and talk; manual expression/idle proof exists from six user-corrected plates | Act 2 requires her first walk-plane rig. Furniture-anchored desk work is not enough. Manual expression proof is source-derived only and still needs in-scene scale review before admission. |
| Old Bottlecap | Act 1 gate/furniture-anchored idle, toll-refused, toll-paid beat; Meshy rig proof exists for Act 3 admission stillness-break | Preserve stillness-as-comedy. The Act 3 proof is useful intake evidence only and still needs gate staging/cast-scale review before admission. |
| Scuttle | Act 1 smear dash cameo; Act 2 rig-driven proof clips now exist for braking stop, fidget idle, and parcel fumble/drop | Proofs are useful animation-intake evidence only. The parcel is a temporary timing cube, and all clips still need cast-scale review, animation admission, and in-scene visual QA before production use. |
| Grommet | Meshy candidate with proof clips for anchored idle variants, mended reaction, Annex decision, guardian brace/strain-hold, post-danger relief, and first-walk side cycle | Proof work exists under `spikes/sprite_render/input/meshy_cast/grommet/`; none of it is final until registration, cast-scale, animation admission, contact-sheet/onion review, and in-scene visual QA pass. |
| Chairman Toggle | Meshy intake proof exists for `Ropebound_Log_biped`; skeleton-driven proof clips now exist for idle, stamp-down, confrontation entrance, parcel deflect, ledger deflect, deflate/concede, and panic exit | Proofs are useful animation-intake evidence only. They still need furniture/counter staging, cast-scale review, animation admission, and in-scene visual QA before production use. |

## Pip

| Need | Source anchor | Production notes |
|---|---|---|
| Crouch/reach/mend action | `act02-052` through `act02-055`, Grommet mended beat | Can reuse the shape language of Act 1 pickup/reach, but timing must feel gentler and more careful than item pickup. Correct-model proof exists at `spikes/sprite_render/input/meshy_cast/pip/story_action_proofs_act23_export4/mend_reach/out/`: 16 frames, 12 fps, fixed 512px canvas, no manifest warnings. Current proof reads as careful upper-body reach more than true crouch; final needs deeper lower-body acting or a stronger rig pose source. |
| Worried reaction | `act03-037-pip-worried-for-grommet` | Clear fear for Grommet, not generic surprise. Stronger correct-model proof exists at `spikes/sprite_render/input/meshy_cast/pip/story_action_proofs_act23_export4_stronger/worried_grommet/out/`: 12 frames, 12 fps, fixed 512px canvas, no manifest warnings, max jitter 0.472px. Current proof is materially better body acting than the first pass, but still needs face/scene QA before admission. |
| Relief reaction | `act03-050-pip-relief-grommet-held` | Small exhale/softening beat after danger passes. Correct-model proof exists at `spikes/sprite_render/input/meshy_cast/pip/story_action_proofs_act23_export4_stronger/relief_grommet/out/`: 16 frames, 12 fps, fixed 512px canvas, no manifest warnings, max jitter 0.936px. Current proof reads as a modest body softening/held look; final still needs face/scene QA before admission. |
| Urgency-paced walk/run | Act 3 escape dash, `act03-033` through `act03-046` | Retimed faster from a valid walk/run source; no frame skipping that creates pops. Better correct-model retime proof exists at `spikes/sprite_render/input/meshy_cast/pip/story_action_proofs_act23_export4_stronger/urgent_walk_retime/out/`: 12 frames, 16 fps, fixed 512px canvas, no manifest warnings, max jitter 0.853px. This uses the real Pip walk source and is preferred over the hand-posed `urgent_stumble_step`, which remains too mild for escape urgency. |
| Marble search interact loop | `act03-008` through `act03-018` | Repeatable inspect/take motion that can play against five distinct candidate props. Correct-model proof exists at `spikes/sprite_render/input/meshy_cast/pip/story_action_proofs_act23_export4/marble_search/out/`: 18 frames, 12 fps, fixed 512px canvas, no manifest warnings. Current proof reads as lean/search, but needs deeper ground contact and prop staging for final. |
| Shrink-down opening image | Implied by `docs/GAME_CONCEPT.md`; Act 1 starts with Pip already shrunk | Provisional scale-transition proof exists at `spikes/sprite_render/input/meshy_cast/pip/shrink_transition_proofs/shrink_down/out/`: 24 frames, 12 fps, fixed 640px canvas, no manifest warnings, max jitter 1.074px. This is blocking language only; final opening still needs authored normal-size scene framing. |
| Shrink-back-up ending image | `act03-057` to `act03-058`, ending transition | Provisional scale-transition proof exists at `spikes/sprite_render/input/meshy_cast/pip/shrink_transition_proofs/shrink_back_up/out/`: 24 frames, 12 fps, fixed 640px canvas, no manifest warnings, max jitter 1.074px. This proves an in-place size-change treatment, but final must be staged in the ending room with marble-in-hand continuity. |

## Bramble

| Need | Source anchor | Production notes |
|---|---|---|
| Full walk-plane cycle | `docs/ACT_02_DESIGN.md`, Cast present and Animation cue table | New 9-key walk-plane cycle. She leaves the desk for the first time; do not reuse desk cels. Source-derived proof exists at `spikes/sprite_render/bramble_mobile_proof/out/walk_9key_shuffle/`: 9 frames, all nine proof roles labeled, 12 fps, fixed 512px canvas, locked anchor, no manifest warnings. This is a front-facing shuffle proof, not final admitted side-view art. |
| Walk-plane idle/follow | Act 2 Concourse presence | Should feel officious but less desk-busy than Act 1; she is mobile now. Source-derived mobile idle proof exists at `spikes/sprite_render/bramble_mobile_proof/out/mobile_idle/`: 6 frames, 12 fps, fixed 512px canvas, no full-body wobble emphasis. |
| Manual face/emotion idle proof | `C:/Users/KyleB/OneDrive/Pictures/Lost Animation PNGS/Bramble1.png` through `Bramble6.png` | Proof exists at `spikes/sprite_render/bramble_manual_expression_intake/manual_patch_out/`. Fixed body uses Bramble1; the other plates contribute only feathered face patches. Current proof: 37 frames, 12 fps, 512px canvas, 73px top margin, no head-crop warnings, zero generated facial features. Timing now holds readable expression beats with one quick in-between per expression change; RGBA resizing uses premultiplied alpha to suppress magenta source-background fringe. |
| Reunion / thread handoff | `act02-015` through `act02-022` | Thread is dialogue-gated; handoff should read as a real supplied item, not a floor pickup. Source-derived proof exists at `spikes/sprite_render/bramble_manual_expression_intake/story_beats/thread_handoff/`: 14 frames, 12 fps, fixed 512px canvas, 73px top margin, no manifest warnings. Fixed body uses Bramble1; other plates contribute only feathered face patches. |
| Parcel check-in defensive beat | `act02-039` through `act02-043` | First visible crack in Bramble's Act 1 deflection. Source-derived proof exists at `spikes/sprite_render/bramble_manual_expression_intake/story_beats/parcel_defensive/`: 14 frames, 12 fps, fixed 512px canvas, 73px top margin, no manifest warnings. |
| Ledger reveal reaction | `act02-061` through `act02-062` | Recognition/realization beat, quieter than greeting. Source-derived proof exists at `spikes/sprite_render/bramble_manual_expression_intake/story_beats/ledger_recognition/`: 16 frames, 12 fps, fixed 512px canvas, 73px top margin, no manifest warnings. |
| Toggle pushback | `act02-066` inline during Toggle petition | Stage as three-way dialogue, not isolated talk flap. Source-derived proof exists at `spikes/sprite_render/bramble_manual_expression_intake/story_beats/toggle_pushback/`: 16 frames, 12 fps, fixed 512px canvas, 73px top margin, no manifest warnings. |
| Thinking/nudge beat | `act03-027-bramble-nudge` | Pause, look between documents, then speak. This is her one "I am working it out" moment. Source-derived proof exists at `spikes/sprite_render/bramble_manual_expression_intake/story_beats/thinking_nudge/`: 15 frames, 12 fps, fixed 512px canvas, 73px top margin, no manifest warnings. |
| Urgency-paced escape movement | Act 3 escape dash | Reuse walk-plane rig with faster timing after it passes. |

## Old Bottlecap

| Need | Source anchor | Production notes |
|---|---|---|
| Admission stillness-break | `act03-044-oldbottlecap-admission` | One small reaction beat only: longer pause, downward glance, or tiny posture break. Do not over-animate vulnerability. Rig-driven proof exists at `spikes/sprite_render/input/meshy_cast/old_bottlecap/admission_stillness_break_proof/out/`: 18 frames, 12 fps, fixed 512px canvas, no manifest warnings, max jitter 0.76px. |
| Gate-open revisit staging | `act03-042` through `act03-045` | Act 1 gate rig can be reused; line delivery should preserve dry, grounded stillness. |

## Scuttle

| Need | Source anchor | Production notes |
|---|---|---|
| Caught mid-dash / braking stop | `act02-024` through `act02-028` | Smear-frame rule applies to the stop/brake, not just forward dash. Rig-driven proof exists at `spikes/sprite_render/input/meshy_cast/scuttle/act2_brake_stop/out/`: 8 frames, 16 fps, fixed 512px canvas, no manifest warnings. Frames 0-1 are marked smear frames; remaining frames are readable solid brake/settle poses. |
| Fidgety dialogue idle | Act 2 Scuttle topics `act02-029` through `act02-034` | He has stopped, but barely. Small impatient foot/antenna/body ticks. Rig-driven proof exists at `spikes/sprite_render/input/meshy_cast/scuttle/act2_fidget_idle/out/`: 12 frames, 12 fps, fixed 512px canvas, no manifest warnings. Current motion is subtle; review in-scene before admission. |
| Parcel fumble/drop | `act02-035` through `act02-038`, `event: parcel-dropped` | Needs anticipation, off-balance fumble, parcel prop drop/bounce. Rig-driven timing proof exists at `spikes/sprite_render/input/meshy_cast/scuttle/act2_parcel_fumble_drop/out/`: 9 frames, 12 fps, fixed 512px canvas, no manifest warnings. The gray parcel is temporary timing geometry only; final parcel prop art is still required. |
| Escape guide dash | `act03-039` through `act03-041` | Reuse Scuttle speed language; smear frames remain valid. Existing Act 1/rig dash proof can provide the speed language, but Act 3 still needs in-scene staging and exit direction. |

## Grommet

| Need | Source anchor | Production notes |
|---|---|---|
| Furniture-anchored idle, pre-clue | Act 2 Grommet first approach `act02-044` through `act02-048` | Shy/still, huge but gentle. Sparse timing; not Old Bottlecap grumpy timing. Meshy proof exists at `spikes/sprite_render/input/meshy_cast/grommet/patchwork_rag_doll_export_1/proof_pre_idle_v2/out/`: 36 frames, 12 fps, fixed 512px canvas, no manifest warnings, max jitter 0.891px. |
| Furniture-anchored idle, post-clue | `act02-049-grommet-draft-line` onward | Add subtle shoulder-shift/shiver. It is a clue, but should not flash like a hotspot marker. Meshy proof exists at `spikes/sprite_render/input/meshy_cast/grommet/patchwork_rag_doll_export_1/proof_post_shiver_v2/out/`: 36 frames, 12 fps, fixed 512px canvas, no manifest warnings, max jitter 0.991px. |
| Mended climax beat | `act02-052` through `act02-055`, `event: grommet-trust-earned` | Act 2's biggest performance beat. Meshy proof exists at `spikes/sprite_render/input/meshy_cast/grommet/patchwork_rag_doll_export_1/proof_mended_reaction/out/`: 48 frames, 12 fps, fixed 512px canvas, no manifest warnings, max jitter 0.94px. Current proof is stable but visually quiet in contact sheet; strengthen the emotional read before final admission. |
| Annex decision/open beat | `act03-002` through `act03-003`, `event: annex-opened` | Hold Grommet's decision before the door moves. This is anticipation, not instant mechanism. Character proof exists at `spikes/sprite_render/input/meshy_cast/grommet/patchwork_rag_doll_export_1/proof_annex_decision/out/`: 36 frames, 12 fps, fixed 512px canvas, no manifest warnings, max jitter 0.897px. The Annex door/mechanism animation remains separate environment work and still needs in-scene staging. |
| Guardian block / sustained strain loop | `act03-036` through `act03-038`, `event: grommet-guardian-payoff` | Game climax. Needs bracing pose, visible strain, and loopable "still holding" cycle. Brace proof exists at `spikes/sprite_render/input/meshy_cast/grommet/patchwork_rag_doll_export_1/proof_guardian_brace/out/`: 48 frames, 12 fps, fixed 512px canvas, no manifest warnings, max jitter 0.854px. Strain-hold proof exists at `spikes/sprite_render/input/meshy_cast/grommet/patchwork_rag_doll_export_1/proof_strain_hold/out/`: 36 frames, 12 fps, fixed 512px canvas, no manifest warnings, max jitter 0.618px. |
| Post-danger relief | `act03-048` through `act03-050` | Danger-over cue and Pip relief need Grommet to read alive after the strain. Meshy proof exists at `spikes/sprite_render/input/meshy_cast/grommet/patchwork_rag_doll_export_1/proof_post_danger_relief/out/`: 48 frames, 12 fps, fixed 512px canvas, no manifest warnings, max jitter 0.862px. |
| First walk cycle | `act03-053` through `act03-056` | Meshy side-view walk proof exists at `spikes/sprite_render/input/meshy_cast/grommet/patchwork_rag_doll_export_1/proof_first_walk_side/out/`: 27 frames, 12 fps, fixed 512px canvas, no manifest warnings, max jitter 0.917px. It is a useful first-walk intake proof, but still needs in-scene goodbye staging, direction, cast-scale approval, and explicit 9-key admission mapping before final. |

## Chairman Toggle

| Need | Source anchor | Production notes |
|---|---|---|
| Furniture-anchored idle | Act 2 Audience Chamber | Brisk, self-satisfied, rapid small stamping. Comedy comes from busy authority. Skeleton proof exists at `spikes/sprite_render/input/meshy_cast/chairman_toggle/proof_idle/out/`: 36 frames, 12 fps, fixed 512px canvas, no jitter warnings, 123px top margin. Still needs actual furniture/counter staging. |
| Petition denied / stamp-down | `act02-064` through `act02-067`, `event: petition-denied` | Big stamp punctuation on `act02-067`; one decisive comic thud. Skeleton proof exists at `spikes/sprite_render/input/meshy_cast/chairman_toggle/proof_stamp_down/out/`: 36 frames, 12 fps, fixed 512px canvas, no jitter warnings. Revised pass has a clearer anticipation/snap but still needs prop/counter context. |
| Confrontation entrance | `act03-019` through `act03-020` | Alarmed interruption of his composed Act 2 language. Skeleton proof exists at `spikes/sprite_render/input/meshy_cast/chairman_toggle/proof_confrontation_entrance/out/`: 36 frames, 12 fps, fixed 512px canvas, no jitter warnings, max jitter 0.86px. Still needs furniture/counter staging and cast-scale review. |
| Deflect parcel alone | `act03-021` through `act03-022` | Distinct dismissive gesture; do not reuse ledger deflect one-for-one. Skeleton proof exists at `spikes/sprite_render/input/meshy_cast/chairman_toggle/proof_deflect_parcel/out/`: 30 frames, 12 fps, fixed 512px canvas, no jitter warnings, max jitter 0.823px. Gesture reads as a one-hand outward dismissal; final still needs parcel prop/staging. |
| Deflect ledger alone | `act03-025` through `act03-026` | Second, different deflection gesture. Skeleton proof exists at `spikes/sprite_render/input/meshy_cast/chairman_toggle/proof_deflect_ledger/out/`: 30 frames, 12 fps, fixed 512px canvas, no jitter warnings, max jitter 0.74px. Gesture reads as a two-hand inward shield/fluster beat; final still needs ledger prop/staging. |
| Deflate/concede arc | `act03-030` through `act03-032`, `event: toggle-defeated` | Multi-beat process, not a single pose swap. Embarrassed/comedic, not crushed. Combined proof exists at `spikes/sprite_render/input/meshy_cast/chairman_toggle/proof_deflect_concede/out/`: 36 frames, 12 fps, fixed 512px canvas, no jitter warnings, revised to include denial beats plus a clearer settle/deflate. The item-specific deflections above are now split into separate proof clips. |
| Panicked exit | `act03-035-toggle-panics-about-hoard` | First non-composed animation. Messy, comic, still readable. Skeleton proof exists at `spikes/sprite_render/input/meshy_cast/chairman_toggle/proof_panic_exit/out/`: 36 frames, 12 fps, fixed 512px canvas, no jitter warnings. |

## Environment And Props

| Need | Source anchor | Production notes |
|---|---|---|
| Needle, thread, threaded-needle | Act 2 item chain, `act02-013`, `act02-014`, `act02-023` | Inventory/held/handoff prop states required. User art candidates are curated at `spikes/sprite_render/user_prop_art_curated/accepted_review_crops/` (`thread_spool`, `needle`, `threaded_needle`); these are preferred visual source. Earlier isolated proof remains at `spikes/sprite_render/story_prop_proofs/item_state_sheet/` for readability/timing only. Final alpha cleanup and registration still required. |
| Intake parcel | Scuttle drop and Toggle petition | Needs held, dropped, inventory, and document-presentation states. User art candidate `intake_parcel` exists in `spikes/sprite_render/user_prop_art_curated/accepted_review_crops/`; parcel drop/bounce timing proof exists at `spikes/sprite_render/story_prop_proofs/parcel_drop_bounce/`: 8 frames, 12 fps, fixed 256px canvas, no warnings. |
| Founder's ledger | `act02-059` through `act02-062`; Act 3 combine puzzle | Needs readable prop state and combine presentation with parcel. User art candidates `founders_ledger_closed` and `annotated_evidence_candidate` exist in `spikes/sprite_render/user_prop_art_curated/accepted_review_crops/`; earlier proof remains readability-only. Final art must preserve the `FOUNDER` / `O.B.` readability language. |
| Annotated evidence | `act03-028` through `act03-029` | Combined item; must visually imply parcel + ledger read together. User art candidate exists at `spikes/sprite_render/user_prop_art_curated/accepted_review_crops/annotated_evidence_candidate.png`. Still needs final presentation state and in-scene handoff scale. |
| Marble candidates, five distinct props | `act03-009` through `act03-018` | Galaxy, radiator-tagged, scratch decoy, flawless, correct nick/star. Do not recolor one generic marble five times. Generated replacement candidates now exist at `spikes/sprite_render/generated_missing_prop_art/sliced/` (`marble_galaxy_final_candidate`, `marble_radiator_tag_final_candidate`, `marble_scratch_decoy_final_candidate`, `marble_flawless_final_candidate`, `marble_correct_star_nick_final_candidate`). `marble_broken_decoy_final_candidate` is an extra wrong-object decoy, not the correct marble. Contact proof: `spikes/sprite_render/generated_missing_prop_art/generated_missing_props_contact.png`. User marble source sheet is still stored in `spikes/sprite_render/user_prop_art_intake/source_sheets/marble_candidates_sheet.png`, but its first crop pass was rejected and auto-crop grouped all five together. Final admission still needs alpha/scale review. |
| Dust clump/button reveal candidates | Act 1/prop continuity, reused source language for later hidden-object staging | Generated source candidates exist at `spikes/sprite_render/generated_missing_prop_art/sliced/dust_button_hidden_final_candidate.png` and `spikes/sprite_render/generated_missing_prop_art/sliced/dust_clump_open_final_candidate.png`. These are better visual candidates than the earlier code-only proof, but fuzzy lint edges still have magenta-edge risk from the source sheet and require edge QA or true-alpha regeneration before admission. |
| Cobweb curtain candidate | Scuttle dash staging and foreground set dressing | Clean regenerated cobweb candidate exists at `spikes/sprite_render/generated_missing_prop_art/sliced/cobweb_curtain_final_candidate.png`, sourced from `spikes/sprite_render/generated_missing_prop_art/source_sheets/cobweb_curtain_generated_black.png` to avoid the rejected magenta-strand sheet. Its partial alpha was extracted from black, so it must be composited over both light and dark room plates before admission. |
| Annex door open | `act03-002` through `act03-003`, `event: annex-opened` | Door motion begins after Grommet's held decision beat. Timing proof exists at `spikes/sprite_render/environment_prop_proofs/annex_door_open/`: 12 frames, 12 fps, fixed 512x288 canvas, no warnings. This is timing-only art: final Annex door painting must replace the temporary drawing, but the hold/clunk/heavy swing/overshoot/settle timing is now concrete. |
| First tremor | `act02-070` through `act02-072`, `event: first-tremor` | Low-intensity light flicker + subtle shake. Establish Roar language. Transparent overlay timing proof exists at `spikes/sprite_render/environment_prop_proofs/first_tremor_overlay/`: 18 frames, 12 fps, fixed 512x288 canvas, intensity 0.45, no warnings. Draw over the finished room; do not bake into background art. |
| Roar arrives | `act03-033`, `event: roar-arrives` | Same language as first tremor, escalated. No Roar sprite. Transparent overlay timing proof exists at `spikes/sprite_render/environment_prop_proofs/roar_arrives_overlay/`: 18 frames, 12 fps, fixed 512x288 canvas, intensity 1.0, no warnings. |
| Roar passed | `act03-048`, `event: roar-passed` | Inverse fade of rumble/light cue. Transparent overlay timing proof exists at `spikes/sprite_render/environment_prop_proofs/roar_passed_overlay/`: 18 frames, 12 fps, fixed 512x288 canvas, intensity 0.35, no warnings. |

## Priority Order

1. Grommet anchored idle variants and mended beat.
2. Bramble walk-plane rig and mobile idle.
3. Chairman Toggle furniture-anchored idle and stamp/deflect arc.
4. Scuttle stop/fumble/drop with parcel final prop art and in-scene staging.
5. Pip Act 2/3 story reactions and marble-search interact loop.
6. Grommet guardian hold and first walk.
7. Act 3 environment escalation and ending shrink-back-up.

## Production Notes

- Keep the current Act 1 web prototype intact while adding these as source/proof
  assets.
- Meshy/3D proofs are allowed as intake evidence, but 2D sprite admission still
  requires the repo gates.
- Do not final-integrate Act 2 or Act 3 content until their local script/design
  files are present in the working tree and the relevant content data is built
  from those exact files.
- The shrink-down and shrink-back-up transforms are now tracked as backlog gaps.
  They need deliberate art direction because they are the opening and closing
  images of the full game.
