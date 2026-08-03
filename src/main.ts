import script from "../script/ACT_01_SCRIPT.json";
import "./styles.css";

type LineId = string;
type HotspotId =
  | "couch-ceiling"
  | "dust-clump"
  | "cubby-wall"
  | "sign-in-log"
  | "popcorn-boulder"
  | "cobweb-curtain"
  | "bramble-desk"
  | "toll-gate";
type ItemId = "button";
type Mode = "inspect" | "use";

type DialogueLine = {
  line_id: LineId;
  speaker: string;
  text: string;
};

const lines = new Map((script.lines as DialogueLine[]).map((line) => [line.line_id, line]));

const line = (shortId: string): DialogueLine => {
  const found = [...lines.values()].find((entry) => entry.line_id.includes(`-${shortId}-`));
  if (!found) throw new Error(`Missing script line ${shortId}`);
  return found;
};

const byId = (id: string): DialogueLine => {
  const found = lines.get(id);
  if (!found) throw new Error(`Missing script line ${id}`);
  return found;
};

const assets = {
  scene: {
    bg: new URL("../art/act01-production/scene/entry-chamber-bg.png", import.meta.url).href,
    foregroundMask: new URL("../art/act01-production/scene/entry-chamber-foreground-mask.png", import.meta.url).href,
  },
  pipWalk: [
    "pip_walk_01.png",
    "pip_walk_02.png",
    "pip_walk_03.png",
    "pip_walk_04.png",
    "pip_walk_05.png",
    "pip_walk_06.png",
    "pip_walk_07.png",
    "pip_walk_08.png",
    "pip_walk_09.png",
  ].map((name) => new URL(`../art/act01-production/characters/pip/walk/${name}`, import.meta.url).href),
  pipIdle: ["pip_idle_01.png", "pip_idle_02.png"].map((name) => new URL(`../art/act01-production/characters/pip/idle/${name}`, import.meta.url).href),
  pipDust: ["pip_dust_01.png", "pip_dust_02.png", "pip_dust_03.png", "pip_dust_04.png"].map(
    (name) => new URL(`../art/act01-production/characters/pip/dust-reach/${name}`, import.meta.url).href,
  ),
  pipToll: ["pip_toll_01.png", "pip_toll_02.png"].map(
    (name) => new URL(`../art/act01-production/characters/pip/toll-paid/${name}`, import.meta.url).href,
  ),
  brambleIdle: ["bramble_idle_01.png", "bramble_idle_02.png", "bramble_idle_03.png", "bramble_idle_04.png"].map(
    (name) => new URL(`../art/act01-production/characters/bramble/idle/${name}`, import.meta.url).href,
  ),
  brambleTalk: ["bramble_talk_01.png", "bramble_talk_02.png", "bramble_talk_03.png"].map(
    (name) => new URL(`../art/act01-production/characters/bramble/talk/${name}`, import.meta.url).href,
  ),
  bottlecapIdle: [
    "old_bottlecap_idle_01.png",
    "old_bottlecap_idle_02.png",
    "old_bottlecap_idle_03.png",
    "old_bottlecap_idle_04.png",
  ].map((name) => new URL(`../art/act01-production/characters/old-bottlecap/idle/${name}`, import.meta.url).href),
  bottlecapRefused: ["old_bottlecap_refuse_01.png", "old_bottlecap_refuse_02.png", "old_bottlecap_refuse_03.png"].map(
    (name) => new URL(`../art/act01-production/characters/old-bottlecap/toll-refused/${name}`, import.meta.url).href,
  ),
  bottlecapPaid: ["old_bottlecap_paid_01.png", "old_bottlecap_paid_02.png", "old_bottlecap_paid_03.png"].map(
    (name) => new URL(`../art/act01-production/characters/old-bottlecap/toll-paid/${name}`, import.meta.url).href,
  ),
  scuttleDash: ["scuttle_dash_01.png", "scuttle_dash_02.png", "scuttle_dash_03.png"].map(
    (name) => new URL(`../art/act01-production/characters/scuttle/dash/${name}`, import.meta.url).href,
  ),
  dustReveal: ["dust_reveal_01.png", "dust_reveal_02.png", "dust_reveal_03.png", "dust_reveal_04.png"].map(
    (name) => new URL(`../art/act01-production/props/dust-clump-reveal/${name}`, import.meta.url).href,
  ),
  grateOpen: ["grate_open_01.png", "grate_open_02.png", "grate_open_03.png", "grate_open_04.png"].map(
    (name) => new URL(`../art/act01-production/props/grate-open/${name}`, import.meta.url).href,
  ),
};

const hotspots: Record<HotspotId, { label: string; x: number; y: number; w: number; h: number }> = {
  "couch-ceiling": { label: "Couch-Bottom Ceiling", x: 12, y: 4, w: 76, h: 20 },
  "dust-clump": { label: "Dust Clump", x: 7, y: 69, w: 18, h: 14 },
  "cubby-wall": { label: "Lost & Found Cubby Wall", x: 7, y: 25, w: 25, h: 29 },
  "sign-in-log": { label: "Sign-In Log", x: 34, y: 54, w: 15, h: 10 },
  "popcorn-boulder": { label: "Popcorn Kernel Boulder", x: 67, y: 69, w: 18, h: 14 },
  "cobweb-curtain": { label: "Cobweb Curtain", x: 82, y: 28, w: 13, h: 30 },
  "bramble-desk": { label: "Bramble's Desk", x: 36, y: 34, w: 24, h: 23 },
  "toll-gate": { label: "The Grate / Old Bottlecap", x: 72, y: 39, w: 24, h: 25 },
};

const state = {
  mode: "inspect" as Mode,
  selectedItem: null as ItemId | null,
  inventory: [] as ItemId[],
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
  queue: [] as DialogueLine[],
  current: null as DialogueLine | null,
  scuttleDash: false,
  action: null as null | { type: "found-button" | "toll-refused" | "toll-paid"; startedAt: number; durationMs: number },
};

const cubbyLoop = [
  "act01-008-pip-cubbywall-rotate-1",
  "act01-009-pip-cubbywall-rotate-2",
  "act01-010-pip-cubbywall-rotate-3",
];

const enqueue = (ids: string[]) => {
  state.queue.push(...ids.map(byId));
  if (!state.current) advanceDialogue();
};

const advanceDialogue = () => {
  state.current = state.queue.shift() ?? null;
  render();
};

const speak = (...ids: string[]) => enqueue(ids);

const playAction = (type: NonNullable<typeof state.action>["type"], durationMs: number) => {
  state.action = { type, startedAt: Date.now(), durationMs };
  window.setTimeout(() => {
    if (state.action?.type === type) {
      state.action = null;
      render();
    }
  }, durationMs);
};

const actionProgress = (type: NonNullable<typeof state.action>["type"]) => {
  if (state.action?.type !== type) return null;
  return Math.min(1, Math.max(0, (Date.now() - state.action.startedAt) / state.action.durationMs));
};

const frameAt = (frames: string[], speedMs: number) => frames[Math.floor(Date.now() / speedMs) % frames.length];

const frameProgress = (frames: string[], progress: number) => frames[Math.min(frames.length - 1, Math.floor(progress * frames.length))];

const hasItem = (item: ItemId) => state.inventory.includes(item);

const addItem = (item: ItemId) => {
  if (!hasItem(item)) state.inventory.push(item);
  state.selectedItem = item;
  state.mode = "use";
};

const removeItem = (item: ItemId) => {
  state.inventory = state.inventory.filter((candidate) => candidate !== item);
  if (state.selectedItem === item) state.selectedItem = null;
};

const inspectHotspot = (id: HotspotId) => {
  switch (id) {
    case "couch-ceiling":
      speak("act01-003-pip-ceiling-examine");
      break;
    case "dust-clump":
      speak(state.flags.dustSearched ? "act01-006-pip-dustclump-search-again" : "act01-004-pip-dustclump-examine");
      break;
    case "cubby-wall":
      if (!state.flags.cubbyFirst) {
        state.flags.cubbyFirst = true;
        speak("act01-007-pip-cubbywall-examine-1st");
      } else {
        speak(cubbyLoop[state.cubbyIndex]);
        state.cubbyIndex = (state.cubbyIndex + 1) % cubbyLoop.length;
      }
      break;
    case "sign-in-log":
      speak("act01-011-pip-signinlog-examine");
      break;
    case "popcorn-boulder":
      speak("act01-012-pip-popcorn-examine");
      break;
    case "cobweb-curtain":
      if (!state.flags.cobwebCameo) {
        state.flags.cobwebCameo = true;
        state.scuttleDash = true;
        window.setTimeout(() => {
          state.scuttleDash = false;
          render();
        }, 1300);
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
    playAction("found-button", 1100);
    speak("act01-005-pip-dustclump-search-success");
    return;
  }

  if (id === "popcorn-boulder") {
    speak("act01-013-pip-popcorn-use-fail");
    return;
  }

  if (id === "bramble-desk") {
    speak("act01-036-bramble-wrong-action");
    return;
  }

  if (id === "toll-gate") {
    if (state.selectedItem === "button" && hasItem("button")) {
      state.flags.gateOpen = true;
      removeItem("button");
      playAction("toll-paid", 1700);
      speak(
        "act01-039-bottlecap-toll-accepted",
        "act01-040-bottlecap-toll-close",
        "act01-041-pip-lost-and-underfound-joke",
        "act01-042-bottlecap-go",
        "act01-049-pip-transition-out",
      );
      state.flags.actComplete = true;
      return;
    }
    playAction("toll-refused", 900);
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
  renderTopics();
};

const onHotspot = (id: HotspotId) => {
  if (state.current) return;
  if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
  if (state.mode === "inspect") inspectHotspot(id);
  else useHotspot(id);
};

const tryExit = () => {
  if (state.flags.gateOpen) {
    speak("act01-049-pip-transition-out");
    state.flags.actComplete = true;
  } else {
    speak("act01-048-pip-fallback-try-exit");
  }
};

const speakerClass = (speaker: string) => speaker.toLowerCase().replaceAll("_", "-");

const app = document.querySelector<HTMLDivElement>("#app");
if (!app) throw new Error("Missing #app");

const renderTopics = () => {
  const topicPanel = document.querySelector<HTMLDivElement>(".topics");
  if (!topicPanel) return;
  topicPanel.innerHTML = `
    <button data-topic="about-bramble">Bramble</button>
    <button data-topic="about-bottlecap">Old Bottlecap</button>
  `;
  topicPanel.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      const topic = button.getAttribute("data-topic");
      topicPanel.innerHTML = "";
      if (topic === "about-bramble") speak("act01-032-bramble-about-herself", "act01-033-pip-nobody-made-you", "act01-034-bramble-the-tragedy");
      if (topic === "about-bottlecap") speak("act01-035-bramble-about-bottlecap");
    });
  });
};

const render = () => {
  const dustProgress = actionProgress("found-button");
  const tollRefusedProgress = actionProgress("toll-refused");
  const tollPaidProgress = actionProgress("toll-paid");
  const pipFrames = dustProgress !== null ? assets.pipDust : tollPaidProgress !== null ? assets.pipToll : assets.pipIdle;
  const pipFrame =
    dustProgress !== null
      ? frameProgress(pipFrames, dustProgress)
      : tollPaidProgress !== null
        ? frameProgress(pipFrames, tollPaidProgress)
        : frameAt(pipFrames, 420);
  const brambleFrames = state.current?.speaker === "BRAMBLE" ? assets.brambleTalk : assets.brambleIdle;
  const bottlecapFrames =
    tollPaidProgress !== null ? assets.bottlecapPaid : tollRefusedProgress !== null ? assets.bottlecapRefused : assets.bottlecapIdle;
  const bottlecapFrame =
    tollPaidProgress !== null
      ? frameProgress(bottlecapFrames, tollPaidProgress)
      : tollRefusedProgress !== null
        ? frameProgress(bottlecapFrames, tollRefusedProgress)
        : frameAt(bottlecapFrames, 360);
  const dustFrame = dustProgress !== null ? frameProgress(assets.dustReveal, dustProgress) : assets.dustReveal[state.flags.dustSearched ? 3 : 0];
  const grateFrame = state.flags.gateOpen ? frameProgress(assets.grateOpen, tollPaidProgress ?? 1) : assets.grateOpen[0];
  const bubble = state.current
    ? `<button class="dialogue ${speakerClass(state.current.speaker)}" type="button">
        <strong>${state.current.speaker.replaceAll("_", " ")}</strong>
        <span>${state.current.text}</span>
      </button>`
    : "";

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
      <section class="stage ${state.current ? "dialogue-open" : ""}" aria-label="Underneath entry chamber">
        <img class="scene-bg" src="${assets.scene.bg}" alt="" />
        <img class="prop dust-prop" src="${dustFrame}" alt="" />
        <img class="prop grate-prop" src="${grateFrame}" alt="" />
        <img class="actor pip" src="${pipFrame}" alt="Pip" />
        <div class="bramble-rig">
          <img class="actor bramble body" src="${frameAt(brambleFrames, 220)}" alt="Bramble" />
          <div class="desk-mask"></div>
        </div>
        <div class="bottlecap-rig">
          <img class="actor bottlecap body" src="${bottlecapFrame}" alt="Old Bottlecap" />
          <div class="gate-mask"></div>
        </div>
        <img class="scene-fg-mask" src="${assets.scene.foregroundMask}" alt="" />
        ${
          state.scuttleDash
            ? `<img class="actor scuttle dash" src="${frameAt(assets.scuttleDash, 100)}" alt="Scuttle" />`
            : ""
        }
        ${Object.entries(hotspots)
          .map(
            ([id, h]) =>
              `<button class="hotspot" style="left:${h.x}%;top:${h.y}%;width:${h.w}%;height:${h.h}%;" data-hotspot="${id}" type="button"><span>${h.label}</span></button>`,
          )
          .join("")}
        <button class="exit" type="button">To Underneath</button>
        ${bubble}
        <div class="topics"></div>
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
      state.mode = button.dataset.mode as Mode;
      render();
    });
  });
  document.querySelectorAll<HTMLButtonElement>("[data-hotspot]").forEach((button) => {
    button.addEventListener("click", () => onHotspot(button.dataset.hotspot as HotspotId));
  });
  document.querySelectorAll<HTMLButtonElement>("[data-item]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedItem = button.dataset.item as ItemId;
      state.mode = "use";
      render();
    });
  });
  document.querySelector<HTMLButtonElement>(".dialogue")?.addEventListener("click", advanceDialogue);
  document.querySelector<HTMLButtonElement>(".exit")?.addEventListener("click", tryExit);
  document.querySelector<HTMLButtonElement>(".self")?.addEventListener("click", () => speak("act01-047-pip-fallback-examine-self"));
};

window.setInterval(() => {
  if (!document.hidden) render();
}, 160);

render();
speak("act01-001-pip-cold-open-landing", "act01-002-pip-cold-open-goal");
