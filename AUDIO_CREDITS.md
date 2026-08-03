# Audio Credits — Third-Party Sourced Material

All music and SFX in this pack are built from Freesound.org recordings (CC0 or CC-BY
only — no NC, ND, SA, or Sampling+), trimmed/normalized/gain-matched by functional
category rather than used verbatim. Voice lines are sourced separately — see the
ElevenLabs section below.

## Music & SFX: Freesound.org

CC0 sources need no attribution but are listed for traceability. CC-BY sources
**must** be credited if this game is ever distributed — keep this list intact and
ship it (or an equivalent in-game credits screen) alongside any public release.

### CC-BY (attribution required)

| Cue | Freesound title | Author | Source | License |
|---|---|---|---|---|
| `music/underneath-ambience-loop.ogg` | "basement room-tone 1635 220811_0491" | klankbeeld | [freesound.org/s/683491](https://freesound.org/s/683491/) | CC BY 4.0 |
| `music/toll-paid-stinger.ogg` | "Level Up 02" | mokasza | [freesound.org/s/810754](https://freesound.org/s/810754/) | CC BY 4.0 |
| `sfx/footstep-01.ogg` | "Carpet Footstep 1.wav" | morganpurkis | [freesound.org/s/384638](https://freesound.org/s/384638/) | CC BY 4.0 |
| `sfx/footstep-02.ogg` | "Carpet Footstep 2.wav" | morganpurkis | [freesound.org/s/384637](https://freesound.org/s/384637/) | CC BY 4.0 |
| `sfx/button-pickup.ogg` | "Single Coin Drop" | mokasza | [freesound.org/s/810185](https://freesound.org/s/810185/) | CC BY 4.0 |
| `sfx/signinlog-open.ogg` | "Page_Turn_26.wav" | Koops | [freesound.org/s/20260](https://freesound.org/s/20260/) | CC BY 4.0 |
| `sfx/scuttle-dash.ogg` | "Rat Scurry" | alexyquest42 | [freesound.org/s/630473](https://freesound.org/s/630473/) | CC BY 4.0 |

### CC0 (public domain, no attribution required)

| Cue | Freesound title | Author | Source |
|---|---|---|---|
| `sfx/ui-hover.ogg` | "Blip_C_01" | cabled_mess | [freesound.org/s/350865](https://freesound.org/s/350865/) |
| `sfx/ui-select.ogg` | "Blip_C_02" | cabled_mess | [freesound.org/s/350864](https://freesound.org/s/350864/) |
| `sfx/ui-cancel.ogg` | "Menu FX 03 (descending).wav" | Nightflame | [freesound.org/s/422515](https://freesound.org/s/422515/) |
| `sfx/dust-clump-reveal.ogg` | "Chime Notification" | Jofae | [freesound.org/s/380482](https://freesound.org/s/380482/) |
| `sfx/cubby-open.ogg` | "open-cardboard-box-compartment.wav" | newagesoup | [freesound.org/s/364740](https://freesound.org/s/364740/) |
| `sfx/popcorn-thud.ogg` | "LowThump_01.wav" | Faulkin | [freesound.org/s/336494](https://freesound.org/s/336494/) |
| `sfx/cobweb-rustle.ogg` | "Jacket/Cloth Rustle 6" | brandondelehoy | [freesound.org/s/494794](https://freesound.org/s/494794/) |
| `sfx/toll-refused.ogg` | "Wood Knock" | Mrguff | [freesound.org/s/369710](https://freesound.org/s/369710/) |
| `sfx/toll-gate-open.ogg` | "open screen door step in close" (trimmed to the opening slide only) | PostProdDog | [freesound.org/s/537830](https://freesound.org/s/537830/) |
| `sfx/bramble-paper-shuffle.ogg` | "Paper shuffling.mp3" | meeser9 | [freesound.org/s/642770](https://freesound.org/s/642770/) |

## Voice: ElevenLabs (⚠️ non-commercial free tier, read before shipping)

Act 1's 45 recorded voice lines (`public/audio/voice/act-01/*.ogg`) are generated via
the [ElevenLabs](https://elevenlabs.io) text-to-speech API, model
`eleven_multilingual_v2`:

| Character | ElevenLabs voice | Voice ID |
|---|---|---|
| Pip | Jessica — Playful, Bright, Warm | `cgSgspJ2msm6clMCkdW9` |
| Bramble | Alice — Clear, Engaging Educator | `Xb7hH8MSUJpSbSDYk0k2` |
| Old Bottlecap | Bill — Wise, Mature, Balanced | `pqHfZKP75CvOlQylNhV4` |
| Scuttle | Liam — Energetic, Social Media Creator | `TX3LPaxmHKxFdv7VOQHJ` |

**⚠️ Generated on ElevenLabs' free tier, which is explicitly non-commercial per their
Terms of Service and requires crediting ElevenLabs on any public use.** Not cleared
to ship in a commercial release as-is. Regenerate on a paid tier (same voice IDs) or
replace with real voice-actor performance before release — both are drop-in
replacements by `line_id`/filename, no code changes needed. See README.md's "Voice
audio" section for what's voiced vs. still missing (4 of 49 lines).
