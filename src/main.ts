import roomGeometry from "../ags/room1/geometry.json";
import ambientMotion from "../ags/ambient_motion_layers.json";
import characterModels from "../content/act1_character_models.json";
import pipIdleRegistration from "../art/act01-production/characters/pip/meshy-current/idle/registration.json";
import brambleVisemes from "../art/rigs/bramble/visemes/index.json";
import audioManifest from "../public/audio/AUDIO_MANIFEST.json";
import dialogueAudio from "../script/ACT_01_DIALOGUE.json";
import script from "../script/ACT_01_SCRIPT.json";
import "./styles.css";

type LineId = string;
type ScreenId = "discovery" | "clerk" | "gate";
type HotspotId =
  | "couch-ceiling"
  | "dust-clump"
  | "cubby-wall"
  | "wall-note"
  | "sign-in-log"
  | "service-bell"
  | "popcorn-boulder"
  | "cobweb-curtain"
  | "bramble-desk"
  | "toll-gate";
type ExitId = "to-discovery" | "to-clerk" | "to-gate" | "through-grate";
type ItemId = "button";
type Mode = "inspect" | "use";
type Facing = "left" | "right";

type DialogueLine = {
  line_id: LineId;
  speaker: string;
  text: string;
};
type GeometryPoint = { x: number; y: number; facing?: Facing };
type GeometryRect = { x: number; y: number; width: number; height: number };
type GeometryHotspot = { id: HotspotId; rect: GeometryRect };
type GeometryWalkBehind = {
  id: HotspotId;
  rect: GeometryRect;
  baseline: number;
  counterTopY?: number;
  frontOccluderPolygon?: Array<[number, number]>;
};
type GeometryExit = {
  id: ExitId;
  exitHotspot: GeometryRect;
  destinationScreenId: ScreenId | "act-02";
  entryPoint: string;
  requiresFlag?: keyof State["flags"];
  transitionLineId?: string;
};
type GeometryScreen = {
  id: ScreenId;
  title: string;
  entryPoints: Record<string, GeometryPoint>;
  standingPositions?: Record<string, GeometryPoint>;
  walkBehinds?: GeometryWalkBehind[];
  hotspots: GeometryHotspot[];
  exits: GeometryExit[];
};
type Geometry = {
  nativeSize: { width: number; height: number };
  start: { screenId: ScreenId; entryPoint: string };
  actorReference: {
    pipHeight: number;
    brambleTalkingHeadHeight: number;
    oldBottlecapHeight: number;
    scuttleHeight: number;
  };
  screens: GeometryScreen[];
};
type MouthCueValue = "X" | "A" | "B" | "C" | "D" | "E" | "F";
type MouthCue = { start: number; end: number; value: MouthCueValue };
type VisemeTrack = { line_id: string; source: string; duration_s: number; mouthCues: MouthCue[] };
type DialogueAudioLine = { line_id: LineId; audio_filename: string | null };
type AudioCue = { filename: string; trigger: string; type: "music" | "sfx"; volume: number; loop: boolean };
type RegistrationSheet = {
  canvas: { width: number; height: number };
  frames: Array<{
    anchor: [number, number];
    canonical?: boolean;
    scale_reference?: [number, number];
  }>;
};
type CharacterFrameState = {
  frames: number;
  folder: string;
  prefix: string;
  pad?: number;
  fps: number;
  loop: boolean;
  ext?: string;
};
type CharacterModel = {
  admission: "finalized" | "provisional-runtime";
  note?: string;
  engine_manifest: string;
  runtime_scale_ref: string;
  states: Record<string, CharacterFrameState>;
  mouths?: {
    folder: string;
    prefix: string;
    cues: MouthCueValue[];
  };
};
type CharacterModelRegistry = {
  schema_version: number;
  scope: string;
  source_of_truth: string;
  characters: Record<string, CharacterModel>;
  not_finalized?: Record<string, string>;
};
type AmbientClip = {
  id: string;
  screen: ScreenId;
  kind: string;
  data_layer: "ambient-motion";
  folder: string;
  prefix: string;
  frames: number;
  fps: number;
  loop: boolean;
  non_interactive: boolean;
  position: GeometryRect;
  path: { dx: number; dy: number; duration_s: number };
  opacity: number;
  blend?: "screen";
};
type AmbientMotionManifest = {
  schema_version: number;
  clips: AmbientClip[];
};

const geometry = roomGeometry as unknown as Geometry;
const ambientManifest = ambientMotion as AmbientMotionManifest;
const characterRegistry = characterModels as unknown as CharacterModelRegistry;
const pipRegistration = pipIdleRegistration as unknown as RegistrationSheet;
const screens = new Map(geometry.screens.map((screen) => [screen.id, screen]));
const lines = new Map((script.lines as DialogueLine[]).map((line) => [line.line_id, line]));
const voiceLines = new Map((dialogueAudio.lines as DialogueAudioLine[]).map((line) => [line.line_id, line.audio_filename]));
const audioCues = audioManifest.cues as AudioCue[];
const brambleVisemeTracks = brambleVisemes as Record<string, VisemeTrack>;
const characterImageModules = {
  ...import.meta.glob("../art/act01-production/characters/pip/meshy-current/idle/pip_meshy_idle_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/act01-production/characters/pip/meshy-current/walk/pip_meshy_walk_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/act01-production/characters/pip/meshy-current/talk/pip_meshy_talk_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/act01-production/characters/pip/meshy-current/inspect/pip_meshy_inspect_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/act01-production/characters/pip/meshy-current/dust-reach/pip_meshy_dust_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/act01-production/characters/pip/meshy-current/toll-paid/pip_meshy_toll_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/act01-production/characters/bramble/idle/bramble_idle_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/act01-production/characters/bramble/talk/bramble_talk_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/act01-production/characters/bramble/greeting/bramble_greeting_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/act01-production/characters/bramble/handoff/bramble_handoff_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/act01-production/characters/bramble/wrong-action/bramble_wrong_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/act01-production/characters/bramble/mouths/bramble_mouth_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/rigs/bramble/idle_firefly_v1/frame_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/rigs/bramble/gesture_firefly_v1/frame_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/rigs/bramble/reaction_concerned_firefly_v1/frame_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/rigs/bramble/reaction_listening_firefly_v1/frame_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/rigs/bramble/reaction_surprised_firefly_v1/frame_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/act01-production/characters/old-bottlecap/meshy-current/idle/old_bottlecap_meshy_idle_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/act01-production/characters/old-bottlecap/meshy-current/toll-refused/old_bottlecap_meshy_refuse_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/act01-production/characters/old-bottlecap/meshy-current/toll-paid/old_bottlecap_meshy_paid_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/rigs/old-bottlecap/idle_firefly_v1/frame_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/rigs/old-bottlecap/gesture_firefly_v1/frame_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/rigs/old-bottlecap/reaction_surprised_firefly_v1/frame_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/rigs/old-bottlecap/tollpaid_firefly_v1/frame_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/rigs/old-bottlecap/tollrefused_firefly_v1/frame_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/rigs/chairman-toggle/greeting_firefly_v1/frame_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/rigs/chairman-toggle/deflecting_firefly_v1/frame_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/rigs/chairman-toggle/reaction_shocked_firefly_v1/frame_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/rigs/chairman-toggle/reaction_deflating_firefly_v1/frame_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/rigs/chairman-toggle/reaction_conceding_firefly_v1/frame_*.png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/act01-production/characters/scuttle/meshy-current/dash/scuttle_meshy_dash_*.png", { eager: true, query: "?url", import: "default" }),
} as Record<string, string>;
const ambientImageModules = {
  ...import.meta.glob("../art/act01-production/scene/ambient/spider/spider_[0-9][0-9].png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/act01-production/scene/ambient/hanging_tag/hanging_tag_[0-9][0-9].png", { eager: true, query: "?url", import: "default" }),
  ...import.meta.glob("../art/act01-production/scene/ambient/lamp_glow/lamp_glow_[0-9][0-9].png", { eager: true, query: "?url", import: "default" }),
} as Record<string, string>;
const pipCanonicalFrame = pipRegistration.frames.find((frame) => frame.canonical) ?? pipRegistration.frames[0];
if (!pipCanonicalFrame?.scale_reference) throw new Error("Pip registration needs a canonical scale_reference");
const pipRegisteredBodyHeight = pipCanonicalFrame.anchor[1] - pipCanonicalFrame.scale_reference[1];
const pipCanvasHeight = (geometry.actorReference.pipHeight / pipRegisteredBodyHeight) * pipRegistration.canvas.height;
const pipAnchorYPercent = (pipCanonicalFrame.anchor[1] / pipRegistration.canvas.height) * 100;
const layoutMode = new URLSearchParams(window.location.search).get("layout") === "1";
const PIP_WALK_PX_PER_SECOND = 85;
const PIP_MIN_WALK_DURATION_MS = 950;
const PIP_IDLE_FRAME_MS = 340;
const PIP_WALK_FRAME_MS = 96;
const PIP_TALK_FRAME_MS = 115;
const BRAMBLE_IDLE_FRAME_MS = 260;
const BRAMBLE_TALK_FRAME_MS = 120;

const byId = (id: string): DialogueLine => {
  const found = lines.get(id);
  if (!found) throw new Error(`Missing script line ${id}`);
  return found;
};

const characterState = (characterId: string, stateName: string) => {
  const character = characterRegistry.characters[characterId];
  const state = character?.states[stateName];
  if (!state) throw new Error(`Missing runtime character state ${characterId}:${stateName}`);
  return state;
};

const characterFrames = (characterId: string, stateName: string) => {
  const state = characterState(characterId, stateName);
  const extension = state.ext ?? ".png";
  return Array.from({ length: state.frames }, (_, index) => {
    const name = `${state.prefix}_${String(index + 1).padStart(state.pad ?? 2, "0")}${extension}`;
    const key = `../${state.folder}/${name}`;
    const bundled = characterImageModules[key];
    if (!bundled) throw new Error(`Missing bundled runtime character frame: ${key}`);
    return bundled;
  });
};

const brambleMouthFrames = () => {
  const mouths = characterRegistry.characters.bramble?.mouths;
  if (!mouths) throw new Error("Missing Bramble mouth registry");
  return Object.fromEntries(
    mouths.cues.map((cue) => [
      cue,
      characterImageModules[`../${mouths.folder}/${mouths.prefix}_${cue}.png`],
    ]),
  ) as Record<MouthCueValue, string>;
};

const ambientFrames = (clip: AmbientClip) =>
  Array.from({ length: clip.frames }, (_, index) => {
    const key = `../${clip.folder}/${clip.prefix}_${String(index).padStart(2, "0")}.png`;
    const bundled = ambientImageModules[key];
    if (!bundled) throw new Error(`Missing bundled ambient frame: ${key}`);
    return bundled;
  });

const assets = {
  scene: {
    backgrounds: {
      discovery: new URL("../ags/room1/background/discovery.png", import.meta.url).href,
      clerk: new URL("../ags/room1/background/clerk.png", import.meta.url).href,
      gate: new URL("../ags/room1/background/gate.png", import.meta.url).href,
    } satisfies Record<ScreenId, string>,
    shadow: new URL("../art/act01-production/scene/layered-v2/fx/soft_oval_shadow.png", import.meta.url).href,
  },
  button: {
    icon: new URL("../art/act01-production/scene/layered-v2/button/icon.png", import.meta.url).href,
    held: new URL("../art/act01-production/scene/layered-v2/button/held.png", import.meta.url).href,
    tossed: new URL("../art/act01-production/scene/layered-v2/button/tossed.png", import.meta.url).href,
  },
  pipWalk: characterFrames("pip", "walk"),
  pipIdle: characterFrames("pip", "idle"),
  pipTalk: characterFrames("pip", "talk"),
  pipInspect: characterFrames("pip", "inspect"),
  pipDust: characterFrames("pip", "dustReach"),
  pipToll: characterFrames("pip", "tollPaid"),
  brambleIdle: characterFrames("bramble", "idle"),
  brambleTalk: characterFrames("bramble", "talk"),
  brambleGreeting: characterFrames("bramble", "greeting"),
  brambleHandoff: characterFrames("bramble", "handoff"),
  brambleWrong: characterFrames("bramble", "wrongAction"),
  brambleMouths: brambleMouthFrames(),
  brambleIdleFirefly: characterFrames("bramble", "idle_firefly"),
  brambleGestureFirefly: characterFrames("bramble", "gesture_firefly"),
  brambleReactionConcerned: characterFrames("bramble", "reaction_concerned"),
  brambleReactionListening: characterFrames("bramble", "reaction_listening"),
  brambleReactionSurprised: characterFrames("bramble", "reaction_surprised"),
  bottlecapIdle: characterFrames("old-bottlecap", "idle"),
  bottlecapRefused: characterFrames("old-bottlecap", "tollRefused"),
  bottlecapPaid: characterFrames("old-bottlecap", "tollPaid"),
  bottlecapIdleFirefly: characterFrames("old-bottlecap", "idle_firefly"),
  bottlecapGestureFirefly: characterFrames("old-bottlecap", "gesture_firefly"),
  bottlecapReactionSurprised: characterFrames("old-bottlecap", "reaction_surprised_firefly"),
  bottlecapTollPaidFirefly: characterFrames("old-bottlecap", "tollpaid_firefly"),
  bottlecapTollRefusedFirefly: characterFrames("old-bottlecap", "tollrefused_firefly"),
  toggleGreetingFirefly: characterFrames("chairman-toggle", "greeting_firefly"),
  toggleDeflectingFirefly: characterFrames("chairman-toggle", "deflecting_firefly"),
  toggleReactionShockedFirefly: characterFrames("chairman-toggle", "reaction_shocked_firefly"),
  toggleReactionDeflatingFirefly: characterFrames("chairman-toggle", "reaction_deflating_firefly"),
  toggleReactionConcedingFirefly: characterFrames("chairman-toggle", "reaction_conceding_firefly"),
  scuttleDash: characterFrames("scuttle", "dash"),
  dustReveal: Array.from({ length: 6 }, (_, index) => `reveal_${String(index + 1).padStart(2, "0")}.png`).map(
    (name) => new URL(`../art/act01-production/scene/layered-v2/dust/${name}`, import.meta.url).href,
  ),
  grateOpen: [
    "closed.png",
    "open_01.png",
    "open_02.png",
    "open_03.png",
    "open_04.png",
    "open_05.png",
    "open_06.png",
  ].map((name) => new URL(`../art/act01-production/scene/layered-v2/grate/${name}`, import.meta.url).href),
  ambient: Object.fromEntries(ambientManifest.clips.map((clip) => [clip.id, ambientFrames(clip)])) as Record<string, string[]>,
};

const publicAssetUrl = (filename: string) => `/${filename.replace(/^public[\\/]/, "").replaceAll("\\", "/")}`;
const audioCuesByTrigger = audioCues.reduce((byTrigger, cue) => {
  byTrigger.set(cue.trigger, [...(byTrigger.get(cue.trigger) ?? []), cue]);
  return byTrigger;
}, new Map<string, AudioCue[]>());
const audioCueUrl = (cue: AudioCue) => publicAssetUrl(`public/audio/${cue.filename}`);
const ambienceCue = audioCuesByTrigger.get("scene_underneath_ambience")?.[0];

const audio = {
  unlocked: false,
  music: ambienceCue ? new Audio(audioCueUrl(ambienceCue)) : null,
  voice: new Audio(),
};

if (audio.music) {
  audio.music.loop = true;
  audio.music.volume = ambienceCue?.volume ?? 0.45;
}
audio.voice.volume = 0.92;
let audioVariantCursor = 0;

const attemptPlay = (media: HTMLMediaElement) => {
  media.play().catch(() => {
    // Autoplay policy can still reject in unusual embedded contexts.
  });
};

const stopVoice = () => {
  audio.voice.pause();
  audio.voice.removeAttribute("src");
  audio.voice.load();
};

const playSfx = (trigger: string) => {
  if (!audio.unlocked) return;
  const cues = audioCuesByTrigger.get(trigger) ?? [];
  const cuesToPlay = trigger === "footstep" && cues.length > 1 ? [cues[audioVariantCursor++ % cues.length]] : cues;
  cuesToPlay.forEach((cue) => {
    const effect = new Audio(audioCueUrl(cue));
    effect.volume = cue.volume;
    effect.loop = cue.loop;
    attemptPlay(effect);
  });
};

const eagerImageAttrs = `loading="eager" decoding="sync"`;
const readyImageSources = new Set<string>();
const loadingImageSources = new Map<string, HTMLImageElement>();
const imageCache = new Map<string, HTMLImageElement>();

const preloadImages = (value: unknown) => {
  if (typeof value === "string" && /\.(png|webp|jpg|jpeg|gif)(\?|$)/i.test(value)) {
    if (readyImageSources.has(value) || loadingImageSources.has(value)) return;
    const image = new Image();
    image.decoding = "sync";
    image.loading = "eager";
    image.onload = () => {
      readyImageSources.add(value);
      loadingImageSources.delete(value);
    };
    image.onerror = () => {
      loadingImageSources.delete(value);
    };
    loadingImageSources.set(value, image);
    imageCache.set(value, image);
    image.src = value;
    return;
  }
  if (Array.isArray(value)) {
    value.forEach(preloadImages);
    return;
  }
  if (value && typeof value === "object") Object.values(value).forEach(preloadImages);
};

preloadImages(assets);

const hotspotLabels: Record<HotspotId, string> = {
  "couch-ceiling": "Couch-Bottom Ceiling",
  "dust-clump": "Dust Clump",
  "cubby-wall": "Lost & Found Cubby Wall",
  "wall-note": "Wall Note",
  "sign-in-log": "Sign-In Log",
  "service-bell": "Service Bell",
  "popcorn-boulder": "Popcorn Kernel Boulder",
  "cobweb-curtain": "Cobweb Curtain",
  "bramble-desk": "Bramble's Desk",
  "toll-gate": "The Grate / Old Bottlecap",
};

const stageProps: Partial<Record<ScreenId, string>> = {};
const ambientClipsByScreen = ambientManifest.clips.reduce((byScreen, clip) => {
  byScreen.set(clip.screen, [...(byScreen.get(clip.screen) ?? []), clip]);
  return byScreen;
}, new Map<ScreenId, AmbientClip[]>());

const cubbyLoop = [
  "act01-008-pip-cubbywall-rotate-1",
  "act01-009-pip-cubbywall-rotate-2",
  "act01-010-pip-cubbywall-rotate-3",
];

type State = {
  mode: Mode;
  selectedItem: ItemId | null;
  inventory: ItemId[];
  screenId: ScreenId;
  pip: GeometryPoint & { facing: Facing };
  layout: null | {
    target: "bramble-talking-head";
    point: GeometryPoint;
    copied: boolean;
  };
  flags: {
    introPlayed: boolean;
    dustSearched: boolean;
    cubbyFirst: boolean;
    cobwebCameo: boolean;
    brambleIntro: boolean;
    bramblePostGate: boolean;
    gateOpen: boolean;
    actComplete: boolean;
  };
  cubbyIndex: number;
  queue: DialogueLine[];
  current: DialogueLine | null;
  currentStartedAt: number;
  topicPanelOpen: boolean;
  scuttleDash: null | { startedAt: number; durationMs: number };
  pipWalk: null | {
    startedAt: number;
    durationMs: number;
    from: GeometryPoint & { facing: Facing };
    to: GeometryPoint & { facing: Facing };
    after: () => void;
  };
  action: null | {
    type:
      | "found-button"
      | "toll-refused"
      | "toll-paid"
      | "walking"
      | "pip-inspect"
      | "bramble-greeting"
      | "bramble-handoff"
      | "bramble-wrong";
    startedAt: number;
    durationMs: number;
  };
};

const startScreenId = layoutMode ? "clerk" : geometry.start.screenId;
const startEntryPoint = layoutMode ? "from-discovery" : geometry.start.entryPoint;
const startScreen = screens.get(startScreenId);
if (!startScreen) throw new Error(`Missing start screen ${startScreenId}`);
const startPoint = startScreen.entryPoints[startEntryPoint];
if (!startPoint) throw new Error(`Missing start point ${startEntryPoint}`);
const initialBramblePoint = screens.get("clerk")?.standingPositions?.["bramble-talking-head"] ?? { x: 280, y: 510 };

const state: State = {
  mode: "inspect",
  selectedItem: null,
  inventory: [],
  screenId: startScreenId,
  pip: { x: startPoint.x, y: startPoint.y, facing: startPoint.facing ?? "left" },
  layout: layoutMode
    ? {
        target: "bramble-talking-head",
        point: { x: initialBramblePoint.x, y: initialBramblePoint.y },
        copied: false,
      }
    : null,
  flags: {
    introPlayed: false,
    dustSearched: false,
    cubbyFirst: false,
    cobwebCameo: false,
    brambleIntro: false,
    bramblePostGate: false,
    gateOpen: false,
    actComplete: false,
  },
  cubbyIndex: 0,
  queue: [],
  current: null,
  currentStartedAt: 0,
  topicPanelOpen: false,
  scuttleDash: null,
  pipWalk: null,
  action: null,
};

const playVoiceForCurrentLine = () => {
  stopVoice();
  if (!audio.unlocked || !state.current) return;
  const filename = voiceLines.get(state.current.line_id);
  if (!filename) return;
  audio.voice.src = publicAssetUrl(filename);
  audio.voice.currentTime = 0;
  attemptPlay(audio.voice);
};

const unlockAudio = () => {
  if (audio.unlocked) return;
  audio.unlocked = true;
  if (audio.music) attemptPlay(audio.music);
  playVoiceForCurrentLine();
};

window.addEventListener("pointerdown", unlockAudio, { passive: true });
window.addEventListener("keydown", unlockAudio);

const app = document.querySelector<HTMLDivElement>("#app");
if (!app) throw new Error("Missing #app");

const pctX = (x: number) => (x / geometry.nativeSize.width) * 100;
const pctY = (y: number) => (y / geometry.nativeSize.height) * 100;
const rectStyle = (rect: GeometryRect) =>
  `left:${pctX(rect.x)}%;top:${pctY(rect.y)}%;width:${pctX(rect.width)}%;height:${pctY(rect.height)}%;`;
const polygonStyle = (points: Array<[number, number]>) =>
  `clip-path:polygon(${points.map(([x, y]) => `${pctX(x)}% ${pctY(y)}%`).join(",")});`;
const interpolateLineY = (a: [number, number], b: [number, number], x: number) => {
  const width = b[0] - a[0];
  if (Math.abs(width) < 0.001) return a[1];
  const t = (x - a[0]) / width;
  return a[1] + (b[1] - a[1]) * t;
};

const enqueue = (ids: string[]) => {
  state.topicPanelOpen = false;
  state.queue.push(...ids.map(byId));
  if (!state.current) advanceDialogue();
};

const advanceDialogue = () => {
  state.current = state.queue.shift() ?? null;
  state.currentStartedAt = state.current ? Date.now() : 0;
  render();
  playVoiceForCurrentLine();
};

const speak = (...ids: string[]) => enqueue(ids);

const playAction = (type: NonNullable<State["action"]>["type"], durationMs: number) => {
  state.action = { type, startedAt: Date.now(), durationMs };
  window.setTimeout(() => {
    if (state.action?.type === type) {
      state.action = null;
      render();
    }
  }, durationMs);
};

const actionProgress = (type: NonNullable<State["action"]>["type"]) => {
  if (state.action?.type !== type) return null;
  return Math.min(1, Math.max(0, (Date.now() - state.action.startedAt) / state.action.durationMs));
};

const scuttleProgress = () => {
  if (!state.scuttleDash) return null;
  return Math.min(1, Math.max(0, (Date.now() - state.scuttleDash.startedAt) / state.scuttleDash.durationMs));
};

const pipWalkProgress = () => {
  if (!state.pipWalk) return null;
  return Math.min(1, Math.max(0, (Date.now() - state.pipWalk.startedAt) / state.pipWalk.durationMs));
};

const isImageReady = (source: string) => {
  const cached = imageCache.get(source);
  return readyImageSources.has(source) && !!cached?.complete && cached.naturalWidth > 0;
};

const readyFrameFallback = (frames: string[]) => frames.find((frame) => isImageReady(frame)) ?? frames[0];

const frameAt = (frames: string[], speedMs: number) => {
  const frame = frames[Math.floor(Date.now() / speedMs) % frames.length];
  return isImageReady(frame) ? frame : readyFrameFallback(frames);
};
const frameForFps = (frames: string[], fps: number) => frameAt(frames, 1000 / fps);
const frameProgress = (frames: string[], progress: number) => {
  const frame = frames[Math.min(frames.length - 1, Math.floor(progress * frames.length))];
  return isImageReady(frame) ? frame : readyFrameFallback(frames);
};

const speakerClass = (speaker: string) => speaker.toLowerCase().replaceAll("_", "-");
const currentScreen = () => {
  const screen = screens.get(state.screenId);
  if (!screen) throw new Error(`Missing screen ${state.screenId}`);
  return screen;
};

const setPip = (point: GeometryPoint, fallbackFacing: Facing) => {
  state.pip = { x: point.x, y: point.y, facing: point.facing ?? fallbackFacing };
};

const standingPoint = (name: string, fallback: GeometryPoint) => currentScreen().standingPositions?.[name] ?? fallback;
const hasItem = (item: ItemId) => state.inventory.includes(item);
const brambleDeskOccluder = () => currentScreen().walkBehinds?.find((item) => item.id === "bramble-desk");
const brambleLayoutPoint = () => state.layout?.point ?? standingPoint("bramble-talking-head", { x: 280, y: 510 });

const brambleActorStyle = (point: GeometryPoint, occluder?: GeometryWalkBehind) => {
  const actorHeight = geometry.actorReference.brambleTalkingHeadHeight;
  const actorWidth = actorHeight * (320 / 260);
  const top = point.y - actorHeight * 0.7885;
  const left = point.x - actorWidth / 2;
  const base = `left:${pctX(point.x)}%;top:${pctY(point.y)}%;height:${pctY(actorHeight)}%;`;
  const topEdge = occluder?.frontOccluderPolygon?.slice(0, 2) as [[number, number], [number, number]] | undefined;
  if (!topEdge) return base;

  const leftCut = Math.max(0, Math.min(100, ((interpolateLineY(topEdge[0], topEdge[1], left) - top) / actorHeight) * 100));
  const rightCut = Math.max(0, Math.min(100, ((interpolateLineY(topEdge[0], topEdge[1], left + actorWidth) - top) / actorHeight) * 100));
  return `${base}--bramble-cut-left:${leftCut.toFixed(2)}%;--bramble-cut-right:${rightCut.toFixed(2)}%;`;
};

const currentPipPoint = () => {
  const progress = pipWalkProgress();
  if (progress === null || !state.pipWalk) return state.pip;
  const eased = easeOutCubic(progress);
  return {
    x: state.pipWalk.from.x + (state.pipWalk.to.x - state.pipWalk.from.x) * eased,
    y: state.pipWalk.from.y + (state.pipWalk.to.y - state.pipWalk.from.y) * eased,
    facing: state.pipWalk.to.facing,
  };
};

const pipInteractionPoint = (id: HotspotId): GeometryPoint & { facing: Facing } => {
  if (id === "bramble-desk" || id === "service-bell") return standingPoint("pip-talk-bramble", state.pip) as GeometryPoint & { facing: Facing };
  if (id === "toll-gate") return standingPoint("pip-gate", state.pip) as GeometryPoint & { facing: Facing };
  if (id === "dust-clump") return { x: 674, y: 666, facing: "left" };
  if (id === "cubby-wall") return { x: 508, y: 666, facing: "left" };
  if (id === "popcorn-boulder") return { x: 780, y: 666, facing: "right" };
  if (id === "cobweb-curtain") return { x: 410, y: 640, facing: "left" };
  if (id === "sign-in-log") return { x: 150, y: 666, facing: "left" };
  if (id === "wall-note") return { x: 720, y: 666, facing: "right" };
  return { ...state.pip, facing: state.pip.facing };
};

const walkPipTo = (point: GeometryPoint & { facing: Facing }, after: () => void) => {
  const from = currentPipPoint();
  const dx = point.x - from.x;
  const dy = point.y - from.y;
  const distance = Math.hypot(dx, dy);
  if (distance < 12) {
    setPip(point, point.facing);
    render();
    after();
    return;
  }
  const durationMs = Math.max(PIP_MIN_WALK_DURATION_MS, (distance / PIP_WALK_PX_PER_SECOND) * 1000);
  state.pipWalk = {
    startedAt: Date.now(),
    durationMs,
    from,
    to: point,
    after,
  };
  state.action = { type: "walking", startedAt: state.pipWalk.startedAt, durationMs };
  playSfx("footstep");
  render();
  window.setTimeout(() => {
    if (!state.pipWalk) return;
    const afterWalk = state.pipWalk.after;
    setPip(state.pipWalk.to, state.pipWalk.to.facing);
    state.pipWalk = null;
    if (state.action?.type === "walking") state.action = null;
    render();
    afterWalk();
  }, durationMs);
};

const addItem = (item: ItemId) => {
  if (!hasItem(item)) state.inventory.push(item);
  state.selectedItem = item;
  state.mode = "use";
};

const removeItem = (item: ItemId) => {
  state.inventory = state.inventory.filter((candidate) => candidate !== item);
  if (state.selectedItem === item) state.selectedItem = null;
};

const playInspectBeat = (after: () => void) => {
  playAction("pip-inspect", 480);
  window.setTimeout(after, 360);
};

const runHotspotInteraction = (id: HotspotId) => {
  if (state.mode === "inspect") inspectHotspot(id);
  else useHotspot(id);
};

const inspectHotspot = (id: HotspotId) => {
  switch (id) {
    case "couch-ceiling":
    case "wall-note":
      speak("act01-003-pip-ceiling-examine");
      break;
    case "dust-clump":
      speak(state.flags.dustSearched ? "act01-006-pip-dustclump-search-again" : "act01-004-pip-dustclump-examine");
      break;
    case "cubby-wall":
      playSfx("cubby_wall_inspect");
      if (!state.flags.cubbyFirst) {
        state.flags.cubbyFirst = true;
        speak("act01-007-pip-cubbywall-examine-1st");
      } else {
        speak(cubbyLoop[state.cubbyIndex]);
        state.cubbyIndex = (state.cubbyIndex + 1) % cubbyLoop.length;
      }
      break;
    case "sign-in-log":
      playSfx("sign_in_log_inspect");
      speak("act01-011-pip-signinlog-examine");
      break;
    case "service-bell":
      talkToBramble();
      break;
    case "popcorn-boulder":
      speak("act01-012-pip-popcorn-examine");
      break;
    case "cobweb-curtain":
      playSfx("cobweb_curtain_inspect");
      if (!state.flags.cobwebCameo) {
        state.flags.cobwebCameo = true;
        playSfx("scuttle_cameo");
        state.scuttleDash = { startedAt: Date.now(), durationMs: 1450 };
        window.setTimeout(() => {
          state.scuttleDash = null;
          render();
        }, 1450);
        speak("act01-014-pip-cobweb-examine", "act01-015-scuttle-cameo-bark", "act01-016-pip-cobweb-reaction");
      } else {
        speak("act01-014-pip-cobweb-examine");
      }
      break;
    case "bramble-desk":
      talkToBramble();
      break;
    case "toll-gate":
      speak(state.flags.gateOpen ? "act01-043-pip-gate-reexamine-open" : "act01-037-pip-gate-examine");
      break;
  }
};

const useHotspot = (id: HotspotId) => {
  if (id === "dust-clump") {
    if (state.flags.dustSearched) {
      speak("act01-006-pip-dustclump-search-again");
      return;
    }
    state.flags.dustSearched = true;
    addItem("button");
    playSfx("found-button");
    window.setTimeout(() => playSfx("button_pickup"), 420);
    playAction("found-button", 1600);
    render();
    window.setTimeout(() => speak("act01-005-pip-dustclump-search-success"), 1640);
    return;
  }

  if (id === "popcorn-boulder") {
    playSfx("popcorn_boulder_use");
    speak("act01-013-pip-popcorn-use-fail");
    return;
  }

  if (id === "bramble-desk" || id === "service-bell") {
    playSfx("bramble_idle_shuffle");
    playAction("bramble-wrong", 2500);
    speak("act01-036-bramble-wrong-action");
    return;
  }

  if (id === "toll-gate") {
    if (state.selectedItem === "button" && hasItem("button")) {
      state.flags.gateOpen = true;
      removeItem("button");
      playSfx("toll-paid");
      playAction("toll-paid", 2300);
      speak(
        "act01-039-bottlecap-toll-accepted",
        "act01-040-bottlecap-toll-close",
        "act01-041-pip-lost-and-underfound-joke",
        "act01-042-bottlecap-go",
      );
      return;
    }
    playSfx("toll-refused");
    playAction("toll-refused", 1200);
    speak("act01-038-bottlecap-no-toll");
    return;
  }

  speak("act01-046-pip-fallback-use-scenery");
};

const talkToBramble = () => {
  if (state.flags.gateOpen && !state.flags.bramblePostGate) {
    state.flags.bramblePostGate = true;
    speak("act01-044-pip-return-to-bramble", "act01-045-bramble-almost-disappointed");
    return;
  }
  if (!state.flags.brambleIntro) {
    state.flags.brambleIntro = true;
    playAction("bramble-greeting", 3000);
    speak(
      "act01-017-bramble-greeting",
      "act01-018-pip-greeting-response",
      "act01-019-bramble-marble-common",
      "act01-020-pip-popular-how",
      "act01-021-bramble-deflect",
      "act01-022-bramble-teach-verbs",
      "act01-023-pip-already-do-that",
      "act01-024-bramble-natural-claimant",
      "act01-025-bramble-quest-lead",
      "act01-026-pip-quest-lead-interrupt",
      "act01-027-bramble-quest-lead-gate",
      "act01-028-pip-what-does-he-want",
      "act01-029-bramble-toll",
      "act01-030-pip-any-tips",
      "act01-031-bramble-toll-hint",
    );
    return;
  }
  state.topicPanelOpen = true;
  render();
};

const onHotspot = (id: HotspotId) => {
  if (state.current || state.topicPanelOpen || state.action) return;
  if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
  playSfx("ui_select");
  const target = pipInteractionPoint(id);
  walkPipTo(target, () => {
    const needsInspectBeat =
      state.mode === "inspect" &&
      !["bramble-desk", "service-bell", "toll-gate", "couch-ceiling", "wall-note"].includes(id);
    if (needsInspectBeat) {
      playInspectBeat(() => runHotspotInteraction(id));
      return;
    }
    runHotspotInteraction(id);
  });
};

const transitionTo = (screenId: ScreenId, entryPointName: string) => {
  const destination = screens.get(screenId);
  const point = destination?.entryPoints[entryPointName];
  if (!destination || !point) throw new Error(`Invalid transition target ${screenId}:${entryPointName}`);
  playSfx("footstep");
  playAction("walking", 280);
  window.setTimeout(() => {
    state.screenId = screenId;
    state.topicPanelOpen = false;
    setPip(point, point.facing ?? "right");
    render();
  }, 160);
};

const onExit = (id: ExitId) => {
  if (state.current || state.topicPanelOpen || state.action) return;
  if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
  const exit = currentScreen().exits.find((candidate) => candidate.id === id);
  if (!exit) return;
  playSfx("ui_select");
  if (exit.destinationScreenId === "act-02") {
    if (exit.requiresFlag && !state.flags[exit.requiresFlag]) {
      speak("act01-048-pip-fallback-try-exit");
      return;
    }
    if (exit.transitionLineId) speak(exit.transitionLineId);
    state.flags.actComplete = true;
    return;
  }
  const edge = exit.exitHotspot.x < geometry.nativeSize.width / 2 ? "left" : "right";
  setPip({ x: exit.exitHotspot.x + exit.exitHotspot.width / 2, y: 666 }, edge);
  transitionTo(exit.destinationScreenId, exit.entryPoint);
};

const selectTopic = (topic: string) => {
  state.topicPanelOpen = false;
  playSfx("ui_select");
  if (topic === "about-bramble") {
    playAction("bramble-handoff", 3000);
    speak("act01-032-bramble-about-herself", "act01-033-pip-nobody-made-you", "act01-034-bramble-the-tragedy");
  }
  if (topic === "about-bottlecap") speak("act01-035-bramble-about-bottlecap");
};

const brambleTalkFrame = () => {
  const elapsed = Date.now() - state.currentStartedAt;
  return assets.brambleTalk[Math.floor(elapsed / BRAMBLE_TALK_FRAME_MS) % assets.brambleTalk.length];
};

const brambleStateFrame = () => {
  const greeting = actionProgress("bramble-greeting");
  if (greeting !== null) return frameProgress(assets.brambleGreeting, greeting);
  const handoff = actionProgress("bramble-handoff");
  if (handoff !== null) return frameProgress(assets.brambleHandoff, handoff);
  const wrong = actionProgress("bramble-wrong");
  if (wrong !== null) return frameProgress(assets.brambleWrong, wrong);
  const reactionConcerned = actionProgress("bramble-reaction-concerned");
  if (reactionConcerned !== null) return frameProgress(assets.brambleReactionConcerned, reactionConcerned);
  const reactionListening = actionProgress("bramble-reaction-listening");
  if (reactionListening !== null) return frameProgress(assets.brambleReactionListening, reactionListening);
  const reactionSurprised = actionProgress("bramble-reaction-surprised");
  if (reactionSurprised !== null) return frameProgress(assets.brambleReactionSurprised, reactionSurprised);
  const gesture = actionProgress("bramble-gesture");
  if (gesture !== null) return frameProgress(assets.brambleGestureFirefly, gesture);
  return state.current?.speaker === "BRAMBLE" ? brambleTalkFrame() : frameAt(assets.brambleIdle, BRAMBLE_IDLE_FRAME_MS);
};

const brambleMouthFrame = () => {
  if (!state.current || state.current.speaker !== "BRAMBLE") return null;
  const elapsed = Date.now() - state.currentStartedAt;
  if (elapsed < 80) return assets.brambleMouths.X;
  const track = brambleVisemeTracks[state.current.line_id];
  const trackedCue = track?.mouthCues.find((mouthCue) => elapsed / 1000 >= mouthCue.start && elapsed / 1000 < mouthCue.end)?.value;
  if (trackedCue) return assets.brambleMouths[trackedCue] ?? assets.brambleMouths.X;
  const text = state.current.text.replace(/[^a-zA-Z]/g, "");
  if (!text) return assets.brambleMouths.X;
  const index = Math.floor(elapsed / 92) % text.length;
  const char = text[index]?.toLowerCase() ?? "";
  const fallbackCue: MouthCueValue =
    char === "o" || char === "u" ? "E" : "aei".includes(char) ? "D" : "fvl".includes(char) ? "F" : "bmp".includes(char) ? "B" : "C";
  return assets.brambleMouths[fallbackCue] ?? assets.brambleMouths.X;
};

const easeOutCubic = (value: number) => 1 - Math.pow(1 - value, 3);

const dustTransform = (progress: number | null) => {
  if (progress === null) return "";
  const shake = Math.sin(progress * Math.PI * 8) * (1 - progress);
  const squash = progress < 0.35 ? 1 + progress * 0.48 : 1.22 - (progress - 0.35) * 0.35;
  return `style="transform: translate(${shake * 5}%, ${Math.sin(progress * Math.PI * 4) * -5}%) scale(${squash}, ${1 / squash});"`;
};

const buttonFlightStyle = (progress: number) => {
  const local = Math.min(1, progress / 0.58);
  const arc = Math.sin(local * Math.PI);
  const x = pctX(690) + easeOutCubic(local) * (pctX(900) - pctX(690));
  const y = pctY(592) - arc * 12 - local * 3;
  const opacity = local < 0.08 ? local / 0.08 : local > 0.88 ? (1 - local) / 0.12 : 1;
  return `style="left:${x}%;top:${y}%;opacity:${Math.max(0, opacity)};transform: translate(-50%, -50%) rotate(${local * 460 - 30}deg) scale(${0.7 + arc * 0.36});"`;
};

const scuttleStyle = (progress: number) => {
  const squash = progress < 0.16 ? 1 - progress * 1.6 : progress < 0.62 ? 1.85 - progress * 0.5 : 1 + (1 - progress) * 0.28;
  const yScale = progress < 0.16 ? 1.2 : progress < 0.62 ? 0.86 : 1;
  return `style="left:${pctX(180 + easeOutCubic(progress) * 360)}%;top:${pctY(568)}%;height:${pctY(
    geometry.actorReference.scuttleHeight,
  )}%;transform: translate(-50%, -100%) scaleX(${squash}) scaleY(${yScale});"`;
};

const cobwebDisturbanceStyle = (progress: number) => {
  const opacity = progress < 0.18 ? progress / 0.18 : progress > 0.78 ? (1 - progress) / 0.22 : 1;
  const spread = 1 + Math.sin(progress * Math.PI) * 0.08;
  return `style="opacity:${Math.max(0, opacity)};transform: translate(-50%, -50%) scale(${spread});"`;
};

const pipStyle = () => {
  const pip = currentPipPoint();
  return `left:${pctX(pip.x)}%;top:${pctY(pip.y)}%;height:${pctY(pipCanvasHeight)}%;transform:translate(-50%, -${pipAnchorYPercent}%) scaleX(${
    pip.facing === "left" ? -1 : 1
  });`;
};

const shadowStyle = (point: GeometryPoint, width: number, opacity = 0.42) =>
  `left:${pctX(point.x)}%;top:${pctY(point.y)}%;width:${pctX(width)}%;opacity:${opacity};`;

const pipFrameForState = () => {
  const dustProgress = actionProgress("found-button");
  const tollPaidProgress = actionProgress("toll-paid");
  const inspectProgress = actionProgress("pip-inspect");
  const walkingProgress = actionProgress("walking");
  if (dustProgress !== null) return frameProgress(assets.pipDust, dustProgress);
  if (tollPaidProgress !== null) return frameProgress(assets.pipToll, tollPaidProgress);
  if (inspectProgress !== null) return frameProgress(assets.pipInspect, inspectProgress);
  if (walkingProgress !== null) return frameAt(assets.pipWalk, PIP_WALK_FRAME_MS);
  if (state.current?.speaker === "PIP") return frameAt(assets.pipTalk, PIP_TALK_FRAME_MS);
  return frameAt(assets.pipIdle, PIP_IDLE_FRAME_MS);
};

const bottlecapFrameForState = () => {
  const reactionSurprised = actionProgress("bottlecap-reaction-surprised");
  if (reactionSurprised !== null) return frameProgress(assets.bottlecapReactionSurprised, reactionSurprised);
  const gesture = actionProgress("bottlecap-gesture");
  if (gesture !== null) return frameProgress(assets.bottlecapGestureFirefly, gesture);
  const tollPaidFirefly = actionProgress("bottlecap-tollpaid-firefly");
  if (tollPaidFirefly !== null) return frameProgress(assets.bottlecapTollPaidFirefly, tollPaidFirefly);
  const tollRefusedFirefly = actionProgress("bottlecap-tollrefused-firefly");
  if (tollRefusedFirefly !== null) return frameProgress(assets.bottlecapTollRefusedFirefly, tollRefusedFirefly);
  const tollRefusedProgress = actionProgress("toll-refused");
  const tollPaidProgress = actionProgress("toll-paid");
  const bottlecapFrames =
    tollPaidProgress !== null ? assets.bottlecapPaid : tollRefusedProgress !== null ? assets.bottlecapRefused : assets.bottlecapIdle;
  return tollPaidProgress !== null || tollRefusedProgress !== null
    ? frameProgress(bottlecapFrames, tollPaidProgress ?? tollRefusedProgress ?? 0)
    : frameAt(bottlecapFrames, 180);
};

const updateImageSource = (selector: string, source: string | null) => {
  if (!source) return;
  const image = document.querySelector<HTMLImageElement>(selector);
  if (!image || image.src === source) return;
  if (!isImageReady(source)) {
    preloadImages(source);
    return;
  }
  image.src = source;
};

const updateElementStyle = (selector: string, style: string) => {
  const element = document.querySelector<HTMLElement>(selector);
  if (!element || element.getAttribute("style") === style) return;
  element.setAttribute("style", style);
};

const ambientPathStyle = (clip: AmbientClip) => {
  const progress = ((Date.now() / 1000) % clip.path.duration_s) / clip.path.duration_s;
  const eased = (1 - Math.cos(progress * Math.PI * 2)) / 2;
  const x = clip.position.x + clip.path.dx * eased;
  const y = clip.position.y + clip.path.dy * eased;
  const blend = clip.blend ? `mix-blend-mode:${clip.blend};` : "";
  return `left:${pctX(x)}%;top:${pctY(y)}%;width:${pctX(clip.position.width)}%;height:${pctY(
    clip.position.height,
  )}%;opacity:${clip.opacity};${blend}`;
};

const renderAmbientMotion = () =>
  (ambientClipsByScreen.get(state.screenId) ?? [])
    .map((clip) => {
      const frames = assets.ambient[clip.id];
      return `<img class="ambient-clip ambient-${clip.kind}" data-ambient-id="${clip.id}" src="${frameForFps(
        frames,
        clip.fps,
      )}" alt="" ${eagerImageAttrs} style="${ambientPathStyle(clip)}" />`;
    })
    .join("");

const updateAmbientMotionFrames = () => {
  for (const clip of ambientClipsByScreen.get(state.screenId) ?? []) {
    updateImageSource(`[data-ambient-id="${clip.id}"]`, frameForFps(assets.ambient[clip.id], clip.fps));
    updateElementStyle(`[data-ambient-id="${clip.id}"]`, ambientPathStyle(clip));
  }
};

const updateAnimationFrames = () => {
  const pipPoint = currentPipPoint();
  updateImageSource(".pip", pipFrameForState());
  updateElementStyle(".pip", pipStyle());
  updateElementStyle(".pip-shadow", shadowStyle(pipPoint, 170));
  if (state.screenId === "clerk") {
    updateImageSource(".bramble-rig .body", brambleStateFrame());
  }
  if (state.screenId === "gate") {
    updateImageSource(".bottlecap-rig .body", bottlecapFrameForState());
  }
  updateAmbientMotionFrames();
};

const renderDialoguePanel = () => {
  if (state.layout) {
    return `<div class="status-line">Layout mode: nudge Bramble with arrow keys. Shift + arrow moves 10 pixels.</div>`;
  }
  if (state.current) {
    return `
      <button class="dialogue-card ${speakerClass(state.current.speaker)}" type="button">
        <strong>${state.current.speaker.replaceAll("_", " ")}</strong>
        <span>${state.current.text}</span>
      </button>
    `;
  }
  if (state.topicPanelOpen) {
    return `
      <div class="dialogue-card topics-card" role="group" aria-label="Conversation topics">
        <strong>BRAMBLE</strong>
        <div class="topics">
          <button data-topic="about-bramble" type="button">Bramble</button>
          <button data-topic="about-bottlecap" type="button">Old Bottlecap</button>
        </div>
      </div>
    `;
  }
  return `<div class="status-line">${state.action?.type === "walking" ? "Walking." : "Choose a verb, then click a hotspot."}</div>`;
};

const renderScreenActors = () => {
  const dustProgress = actionProgress("found-button");
  const tollPaidProgress = actionProgress("toll-paid");
  const currentScuttleProgress = scuttleProgress();
  const pipFrame = pipFrameForState();
  const pipPoint = currentPipPoint();
  const actorMarkup = [
    `<img class="shadow actor-shadow pip-shadow" data-layer="actor-shadow" src="${assets.scene.shadow}" alt="" ${eagerImageAttrs} style="${shadowStyle(
      pipPoint,
      170,
    )}" />`,
    `<img class="actor pip" data-layer="pip-body" src="${pipFrame}" alt="Pip" ${eagerImageAttrs} style="${pipStyle()}" />`,
  ];

  if (state.screenId === "clerk") {
    const bramblePoint = brambleLayoutPoint();
    const brambleFrame = brambleStateFrame();
    const deskOccluder = brambleDeskOccluder();
    actorMarkup.push(
      `<div class="bramble-rig" data-layer="bramble-body" style="${brambleActorStyle(bramblePoint, deskOccluder)}">
        <img class="actor bramble body" src="${brambleFrame}" alt="Bramble" ${eagerImageAttrs} />
      </div>`,
    );
    if (deskOccluder?.frontOccluderPolygon) {
      actorMarkup.push(
        `<img class="room-occluder desk-front-occluder" data-layer="desk-front-occluder" src="${
          assets.scene.backgrounds.clerk
        }" alt="" ${eagerImageAttrs} style="${polygonStyle(deskOccluder.frontOccluderPolygon)}" />`,
      );
    }
  }

  if (state.screenId === "discovery") {
    if (dustProgress !== null) {
      const dustFrame = frameProgress(assets.dustReveal, dustProgress);
      actorMarkup.push(
        `<img class="shadow prop-shadow" data-layer="actor-shadow" src="${assets.scene.shadow}" alt="" ${eagerImageAttrs} style="${shadowStyle(
          { x: 674, y: 666 },
          140,
          0.25,
        )}" />`,
        `<img class="prop dust-prop" data-layer="dust-prop" src="${dustFrame}" alt="" ${eagerImageAttrs} ${dustTransform(dustProgress)} />`,
      );
    }
  }

  if (state.screenId === "gate") {
    const bottlecapFrame = bottlecapFrameForState();
    const bottlecapPoint = standingPoint("old-bottlecap-guard", { x: 900, y: 576 });
    const grateFrame = state.flags.gateOpen ? frameProgress(assets.grateOpen, tollPaidProgress ?? 1) : null;
    actorMarkup.push(
      `<img class="shadow actor-shadow bottlecap-shadow" data-layer="actor-shadow" src="${assets.scene.shadow}" alt="" ${eagerImageAttrs} style="${shadowStyle(
        bottlecapPoint,
        136,
        0.36,
      )}" />`,
      grateFrame ? `<img class="scene-prop grate-prop" data-layer="gate-animation" src="${grateFrame}" alt="" ${eagerImageAttrs} />` : "",
      `<div class="bottlecap-rig" data-layer="old-bottlecap-body" style="left:${pctX(bottlecapPoint.x)}%;top:${pctY(bottlecapPoint.y)}%;height:${pctY(
        geometry.actorReference.oldBottlecapHeight,
      )}%;">
        <img class="actor bottlecap body" src="${bottlecapFrame}" alt="Old Bottlecap" ${eagerImageAttrs} />
      </div>`,
      tollPaidProgress !== null && tollPaidProgress < 0.58
        ? `<img class="button-flight" data-layer="button-flight" src="${assets.button.tossed}" ${buttonFlightStyle(tollPaidProgress)} alt="" ${eagerImageAttrs} />`
        : "",
      currentScuttleProgress !== null
        ? `<div class="cobweb-disturbance" data-layer="cobweb-disturbance" ${cobwebDisturbanceStyle(
            currentScuttleProgress,
          )}></div>`
        : "",
      currentScuttleProgress !== null
        ? `<img class="actor scuttle dash" src="${frameProgress(
            assets.scuttleDash,
            currentScuttleProgress,
          )}" data-layer="scuttle-dash" alt="Scuttle" ${eagerImageAttrs} ${scuttleStyle(
            currentScuttleProgress,
          )} />`
        : "",
    );
  }

  return actorMarkup.join("");
};

const layoutJsonSnippet = () =>
  `"bramble-talking-head": { "x": ${Math.round(brambleLayoutPoint().x)}, "y": ${Math.round(brambleLayoutPoint().y)} }`;

const renderLayoutOverlay = () => {
  if (!state.layout || state.screenId !== "clerk") return "";
  const deskOccluder = brambleDeskOccluder();
  const point = brambleLayoutPoint();
  const polygon = deskOccluder?.frontOccluderPolygon;
  return `
    ${
      polygon
        ? `<svg class="layout-guide" viewBox="0 0 ${geometry.nativeSize.width} ${geometry.nativeSize.height}" aria-hidden="true">
            <polygon points="${polygon.map(([x, y]) => `${x},${y}`).join(" ")}"></polygon>
          </svg>`
        : ""
    }
    <div class="layout-anchor" style="left:${pctX(point.x)}%;top:${pctY(point.y)}%;" aria-hidden="true"></div>
    <aside class="layout-panel" aria-label="Bramble layout controls">
      <strong>Bramble placement</strong>
      <code>${layoutJsonSnippet()}</code>
      <p>Arrow keys move 1px. Shift + arrow moves 10px.</p>
      <button data-copy-layout type="button">${state.layout.copied ? "Copied" : "Copy JSON"}</button>
    </aside>
  `;
};

const copyLayoutSnippet = async () => {
  if (!state.layout) return;
  const text = layoutJsonSnippet();
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const fallback = document.createElement("textarea");
    fallback.value = text;
    fallback.style.position = "fixed";
    fallback.style.left = "-9999px";
    document.body.appendChild(fallback);
    fallback.focus();
    fallback.select();
    document.execCommand("copy");
    fallback.remove();
  }
  state.layout.copied = true;
  render();
};

const render = () => {
  const screen = currentScreen();
  const blocked = state.current || state.topicPanelOpen || state.action;
  const inventory = state.inventory.length
    ? state.inventory
        .map(
          (item) =>
            `<button class="item ${state.selectedItem === item ? "selected" : ""}" data-item="${item}" type="button">${item}</button>`,
        )
        .join("")
    : `<span class="empty">empty</span>`;

  app.innerHTML = `
    <main class="shell">
      <header class="topbar">
        <div>
          <h1>Lost & Underfound</h1>
          <p>Act 1: The Crack Under the Couch</p>
        </div>
        <div class="mode" role="group" aria-label="Verb mode">
          <button class="${state.mode === "inspect" ? "active" : ""}" data-mode="inspect" type="button">Inspect</button>
          <button class="${state.mode === "use" ? "active" : ""}" data-mode="use" type="button">Use</button>
        </div>
      </header>
      <section class="stage screen-${state.screenId} ${blocked ? "interaction-blocked" : ""} ${
        state.layout ? "layout-mode" : ""
      }" aria-label="${screen.title}">
        <img class="scene-bg" data-layer="background-plate" data-background-id="${state.screenId}" src="${assets.scene.backgrounds[state.screenId]}" alt="" />
        <div class="ambient-motion-layer" data-layer="ambient-motion" aria-hidden="true">${renderAmbientMotion()}</div>
        ${stageProps[state.screenId] ?? ""}
        ${renderScreenActors()}
        ${screen.hotspots
          .map(
            (hotspot) =>
              `<button class="hotspot" style="${rectStyle(hotspot.rect)}" data-hotspot="${hotspot.id}" type="button"><span>${hotspotLabels[hotspot.id]}</span></button>`,
          )
          .join("")}
        ${screen.exits
          .map(
            (exit) =>
              `<button class="exit ${exit.id} ${
                exit.requiresFlag && !state.flags[exit.requiresFlag] ? "locked-exit" : "open-exit"
              }" style="${rectStyle(exit.exitHotspot)}" data-exit="${exit.id}" type="button"><span>${
                exit.id === "through-grate" ? "To Underneath" : "Exit"
              }</span></button>`,
          )
          .join("")}
        <div class="post-pass" data-layer="post-pass" aria-hidden="true"></div>
        ${renderLayoutOverlay()}
      </section>
      <section class="dialogue-panel" aria-live="polite">
        ${renderDialoguePanel()}
      </section>
      <footer class="hud">
        <div class="inventory"><strong>Inventory</strong>${inventory}</div>
        <button class="self" type="button">Inspect Pip</button>
        ${
          state.flags.actComplete
            ? `<div class="boundary">Act 1 complete. Acts 2 and 3 need their own script/design pass before building continues.</div>`
            : ""
        }
      </footer>
    </main>
  `;

  document.querySelectorAll<HTMLButtonElement>("[data-mode]").forEach((button) => {
    button.addEventListener("click", () => {
      playSfx("ui_select");
      state.mode = button.dataset.mode as Mode;
      render();
    });
  });
  document.querySelectorAll<HTMLButtonElement>("[data-hotspot]").forEach((button) => {
    button.addEventListener("click", () => onHotspot(button.dataset.hotspot as HotspotId));
  });
  document.querySelectorAll<HTMLButtonElement>("[data-exit]").forEach((button) => {
    button.addEventListener("click", () => onExit(button.dataset.exit as ExitId));
  });
  document.querySelectorAll<HTMLButtonElement>("[data-topic]").forEach((button) => {
    button.addEventListener("click", () => selectTopic(button.dataset.topic ?? ""));
  });
  document.querySelectorAll<HTMLButtonElement>("[data-item]").forEach((button) => {
    button.addEventListener("click", () => {
      playSfx("ui_select");
      state.selectedItem = button.dataset.item as ItemId;
      state.mode = "use";
      render();
    });
  });
  document.querySelector<HTMLButtonElement>("[data-copy-layout]")?.addEventListener("click", () => {
    playSfx("ui_select");
    void copyLayoutSnippet();
  });
  document.querySelector<HTMLButtonElement>(".dialogue-card")?.addEventListener("click", () => {
    playSfx("ui_select");
    advanceDialogue();
  });
  document.querySelector<HTMLElement>(".stage")?.addEventListener("click", (event) => {
    if (event.target !== event.currentTarget || !state.current) return;
    playSfx("ui_select");
    advanceDialogue();
  });
  document.querySelector<HTMLButtonElement>(".self")?.addEventListener("click", () => {
    playSfx("ui_select");
    speak("act01-047-pip-fallback-examine-self");
  });
};

window.addEventListener("keydown", (event) => {
  if (!state.layout || state.screenId !== "clerk") return;
  const step = event.shiftKey ? 10 : 1;
  const delta = {
    ArrowLeft: { x: -step, y: 0 },
    ArrowRight: { x: step, y: 0 },
    ArrowUp: { x: 0, y: -step },
    ArrowDown: { x: 0, y: step },
  }[event.key];
  if (!delta) return;
  event.preventDefault();
  state.layout.point = {
    x: Math.max(0, Math.min(geometry.nativeSize.width, state.layout.point.x + delta.x)),
    y: Math.max(0, Math.min(geometry.nativeSize.height, state.layout.point.y + delta.y)),
  };
  state.layout.copied = false;
  render();
});

window.setInterval(() => {
  if (document.hidden) return;
  if (state.action && !["bramble-greeting", "bramble-handoff", "bramble-wrong", "walking", "pip-inspect"].includes(state.action.type)) {
    render();
    return;
  }
  if (state.scuttleDash) {
    render();
    return;
  }
  updateAnimationFrames();
}, 120);

render();
if (!state.layout) speak("act01-001-pip-cold-open-landing", "act01-002-pip-cold-open-goal");
