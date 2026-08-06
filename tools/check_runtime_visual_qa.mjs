import { spawn } from "node:child_process";
import { mkdirSync, readFileSync, rmSync } from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUT_DIR = path.join(ROOT, "art", "act01-production", "qa", "runtime-playthrough");
const HOST = "127.0.0.1";
const PORT = 5191;
const BASE_URL = `http://${HOST}:${PORT}/`;
const geometry = JSON.parse(readFileSync(path.join(ROOT, "ags", "room1", "geometry.json"), "utf-8"));

const viewports = [
  { name: "desktop", width: 1280, height: 900, isMobile: false },
  { name: "mobile-portrait", width: 390, height: 844, isMobile: true },
];

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const fail = (message) => {
  throw new Error(`Runtime visual QA failed: ${message}`);
};

const startServer = async () => {
  const child = spawn(
    "cmd.exe",
    ["/c", "npm.cmd", "run", "preview", "--", "--host", HOST, "--port", String(PORT), "--strictPort"],
    {
      cwd: ROOT,
      shell: false,
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
    },
  );

  let output = "";
  child.stdout.on("data", (chunk) => {
    output += chunk.toString();
  });
  child.stderr.on("data", (chunk) => {
    output += chunk.toString();
  });

  for (let attempt = 0; attempt < 80; attempt += 1) {
    if (child.exitCode !== null) fail(`Vite server exited early:\n${output}`);
    try {
      const response = await fetch(BASE_URL);
      if (response.ok) return child;
    } catch {
      // Keep waiting.
    }
    await sleep(250);
  }

  child.kill();
  fail(`Vite server did not answer at ${BASE_URL}:\n${output}`);
};

const clearDialogue = async (page, maxClicks = 40) => {
  for (let count = 0; count < maxClicks; count += 1) {
    const card = page.locator(".dialogue-card").first();
    if ((await card.count()) === 0 || !(await card.isVisible())) return;
    await card.click();
    await page.waitForTimeout(90);
  }
  fail("dialogue did not clear within expected click budget");
};

const screenshot = async (page, viewportName, label) => {
  await page.screenshot({
    path: path.join(OUT_DIR, `${viewportName}-${label}.png`),
    fullPage: true,
  });
};

const expectNoOverlap = async (page, firstSelector, secondSelector, description) => {
  const result = await page.evaluate(
    ([first, second]) => {
      const a = document.querySelector(first)?.getBoundingClientRect();
      const b = document.querySelector(second)?.getBoundingClientRect();
      if (!a || !b) return { ok: false, reason: "missing element" };
      const separated = a.bottom <= b.top || b.bottom <= a.top || a.right <= b.left || b.right <= a.left;
      return { ok: separated, a: { top: a.top, bottom: a.bottom, left: a.left, right: a.right }, b: { top: b.top, bottom: b.bottom, left: b.left, right: b.right } };
    },
    [firstSelector, secondSelector],
  );
  if (!result.ok) fail(`${description} overlaps: ${JSON.stringify(result)}`);
};

const expectVisibleBox = async (page, selector, description, min = { width: 8, height: 8 }) => {
  const box = await page.locator(selector).first().boundingBox();
  if (!box) fail(`${description} is missing or not visible`);
  if (box.width < min.width || box.height < min.height) {
    fail(`${description} is too small/cropped: ${JSON.stringify(box)}`);
  }
  return box;
};

const expectRenderedBox = async (page, selector, description, min = { width: 8, height: 8 }) => {
  const box = await page.evaluate((target) => {
    const element = document.querySelector(target);
    if (!element) return null;
    const rect = element.getBoundingClientRect();
    return { width: rect.width, height: rect.height, top: rect.top, left: rect.left };
  }, selector);
  if (!box) fail(`${description} is missing`);
  if (box.width < min.width || box.height < min.height) {
    fail(`${description} is too small/cropped: ${JSON.stringify(box)}`);
  }
  return box;
};

const expectHiddenReleaseHitboxes = async (page) => {
  const bad = await page.evaluate(() =>
    [...document.querySelectorAll(".hotspot, .exit")]
      .map((element) => {
        const style = getComputedStyle(element);
        return {
          id: element.getAttribute("data-hotspot") ?? element.getAttribute("data-exit"),
          borderColor: style.borderTopColor,
          backgroundColor: style.backgroundColor,
          color: style.color,
        };
      })
      .filter((style) => {
        const transparent = "rgba(0, 0, 0, 0)";
        return style.borderColor !== transparent || style.backgroundColor !== transparent || style.color !== transparent;
      }),
  );
  if (bad.length) fail(`release hitboxes are visibly styled without hover/focus: ${JSON.stringify(bad)}`);
};

const expectNoWhiteActorShadows = async (page) => {
  const bad = await page.evaluate(() =>
    [...document.querySelectorAll(".shadow")]
      .map((element) => {
        const style = getComputedStyle(element);
        return {
          className: element.className,
          mixBlendMode: style.mixBlendMode,
          filter: style.filter,
          opacity: Number(style.opacity),
        };
      })
      .filter((style) => style.filter.includes("brightness") || style.mixBlendMode !== "multiply" || style.opacity > 0.8),
  );
  if (bad.length) fail(`actor shadows are not dark multiply shadows: ${JSON.stringify(bad)}`);
};

const expectImageCycles = async (page, selector, description, delayMs = 520) => {
  const sources = [];
  const sampleCount = 5;
  const sampleDelay = Math.max(120, Math.round(delayMs / sampleCount));
  for (let index = 0; index < sampleCount; index += 1) {
    const source = await page.locator(selector).first().getAttribute("src");
    if (!source) fail(`${description} does not have a frame source`);
    sources.push(source);
    await page.waitForTimeout(sampleDelay);
  }
  if (new Set(sources).size < 2) fail(`${description} did not cycle frames over ${delayMs}ms`);
};

const expectStableImagePresence = async (page, selector, description, delayMs = 720) => {
  const sampleCount = 8;
  const sampleDelay = Math.max(60, Math.round(delayMs / sampleCount));
  const failures = [];
  for (let index = 0; index < sampleCount; index += 1) {
    const result = await page.locator(selector).first().evaluate((element) => {
      if (!(element instanceof HTMLImageElement)) {
        return { ok: false, reason: "not-image", className: element.className };
      }
      const rect = element.getBoundingClientRect();
      const style = getComputedStyle(element);
      return {
        ok: element.complete && element.naturalWidth > 0 && element.naturalHeight > 0 && rect.width > 0 && rect.height > 0 && Number(style.opacity) > 0,
        complete: element.complete,
        naturalWidth: element.naturalWidth,
        naturalHeight: element.naturalHeight,
        width: rect.width,
        height: rect.height,
        opacity: style.opacity,
        src: element.currentSrc || element.src,
      };
    });
    if (!result.ok) failures.push({ sample: index, ...result });
    await page.waitForTimeout(sampleDelay);
  }
  if (failures.length) fail(`${description} has blank/incomplete sampled frame(s): ${JSON.stringify(failures)}`);
};

const assertClerkBlocking = async (page, viewportName) => {
  const clerkScreen = geometry.screens.find((screen) => screen.id === "clerk");
  const deskSpec = clerkScreen?.walkBehinds?.find((item) => item.id === "bramble-desk");
  if (!deskSpec?.frontOccluderPolygon) fail("clerk desk is missing frontOccluderPolygon in geometry.json");

  const result = await page.evaluate((desk) => {
    const rectFor = (selector) => {
      const element = document.querySelector(selector);
      if (!element) return null;
      const rect = element.getBoundingClientRect();
      return {
        left: rect.left,
        right: rect.right,
        top: rect.top,
        bottom: rect.bottom,
        width: rect.width,
        height: rect.height,
        centerX: rect.left + rect.width / 2,
      };
    };
    const stage = rectFor(".stage");
    const brambleElement = document.querySelector(".bramble-rig");
    const deskOccluderElement = document.querySelector(".desk-front-occluder");
    const bramble = rectFor(".bramble-rig");
    const pip = rectFor(".pip");
    if (!stage || !bramble || !pip || !deskOccluderElement) {
      return { ok: false, reason: "missing clerk composition element", stage, bramble, pip, hasDeskOccluder: Boolean(deskOccluderElement) };
    }
    const brambleStyle = getComputedStyle(brambleElement);
    const deskOccluderStyle = getComputedStyle(deskOccluderElement);
    const polygon = desk.frontOccluderPolygon.map(([x, y]) => ({
      x: stage.left + stage.width * (x / 1280),
      y: stage.top + stage.height * (y / 720),
    }));
    const xs = polygon.map((point) => point.x);
    const ys = polygon.map((point) => point.y);
    const deskBox = {
      left: Math.min(...xs),
      right: Math.max(...xs),
      top: Math.min(...ys),
      bottom: Math.max(...ys),
      width: Math.max(...xs) - Math.min(...xs),
      height: Math.max(...ys) - Math.min(...ys),
    };
    deskBox.centerX = deskBox.left + deskBox.width / 2;
    const [topLeft, topRight] = polygon;
    const topEdgeT = Math.max(0, Math.min(1, (bramble.centerX - topLeft.x) / (topRight.x - topLeft.x)));
    const frontEdgeAtBramble = topLeft.y + (topRight.y - topLeft.y) * topEdgeT;

    const brambleHeightRatio = bramble.height / stage.height;
    const brambleInsideDeskX = bramble.centerX > deskBox.left + deskBox.width * 0.12 && bramble.centerX < deskBox.right - deskBox.width * 0.12;
    const brambleStraddlesSlopedCounter = bramble.top < frontEdgeAtBramble && bramble.bottom > frontEdgeAtBramble;
    const deskOccluderActive = Number(deskOccluderStyle.zIndex) >= Number(brambleStyle.zIndex) && deskOccluderStyle.clipPath.startsWith("polygon(");
    const brambleCutLeft = Number.parseFloat(brambleStyle.getPropertyValue("--bramble-cut-left"));
    const brambleCutRight = Number.parseFloat(brambleStyle.getPropertyValue("--bramble-cut-right"));
    const brambleHasSlopedDeskCut =
      brambleStyle.clipPath.startsWith("polygon(") &&
      Number.isFinite(brambleCutLeft) &&
      Number.isFinite(brambleCutRight) &&
      Math.abs(brambleCutLeft - brambleCutRight) >= 1;
    const pipOffDeskFace = pip.centerX > deskBox.right + 8 || pip.centerX < deskBox.left - 8;

    return {
      ok:
        brambleHeightRatio >= 0.18 &&
        brambleInsideDeskX &&
        brambleStraddlesSlopedCounter &&
        deskOccluderActive &&
        brambleHasSlopedDeskCut &&
        pipOffDeskFace,
      brambleHeightRatio,
      brambleInsideDeskX,
      brambleStraddlesSlopedCounter,
      frontEdgeAtBramble,
      deskOccluderActive,
      brambleHasSlopedDeskCut,
      brambleCutLeft,
      brambleCutRight,
      brambleStyle: { zIndex: brambleStyle.zIndex, clipPath: brambleStyle.clipPath },
      deskOccluderStyle: { zIndex: deskOccluderStyle.zIndex, clipPath: deskOccluderStyle.clipPath },
      pipOffDeskFace,
      stage,
      polygon,
      deskBox,
      bramble,
      pip,
    };
  }, deskSpec);

  if (!result.ok) fail(`${viewportName} clerk blocking is wrong: ${JSON.stringify(result)}`);
};

const expectStageRelativeBox = async (page, selector, description, min = { widthRatio: 0.06, heightRatio: 0.14 }) => {
  const result = await page.evaluate(
    ([target, ratios]) => {
      const stage = document.querySelector(".stage")?.getBoundingClientRect();
      const element = document.querySelector(target)?.getBoundingClientRect();
      if (!stage || !element) return { ok: false, reason: "missing element", stage, element };
      const widthRatio = element.width / stage.width;
      const heightRatio = element.height / stage.height;
      return {
        ok: widthRatio >= ratios.widthRatio && heightRatio >= ratios.heightRatio,
        widthRatio,
        heightRatio,
        stage: { width: stage.width, height: stage.height },
        element: { width: element.width, height: element.height, left: element.left, top: element.top },
      };
    },
    [selector, min],
  );

  if (!result.ok) fail(`${description} is too small/cropped relative to stage: ${JSON.stringify(result)}`);
};

const expectPipRegisteredScale = async (page, viewportName) => {
  const result = await page.evaluate(() => {
    const stage = document.querySelector(".stage")?.getBoundingClientRect();
    const pip = document.querySelector(".pip")?.getBoundingClientRect();
    if (!stage || !pip) return { ok: false, reason: "missing stage or Pip", stage, pip };
    const canvasHeightRatio = pip.height / stage.height;
    const registeredBodyHeightRatio = canvasHeightRatio * (360 / 512);
    const bodyRatioMin = 0.43;
    const bodyRatioMax = 0.49;
    return {
      ok: registeredBodyHeightRatio >= bodyRatioMin && registeredBodyHeightRatio <= bodyRatioMax,
      canvasHeightRatio,
      registeredBodyHeightRatio,
      expectedRegisteredBodyHeightRatio: [bodyRatioMin, bodyRatioMax],
      stage: { width: stage.width, height: stage.height },
      pip: { width: pip.width, height: pip.height, left: pip.left, top: pip.top },
    };
  });

  if (!result.ok) fail(`${viewportName} Pip registered body scale is wrong: ${JSON.stringify(result)}`);
};

const assertGateBlocking = async (page, viewportName) => {
  const result = await page.evaluate(() => {
    const bottlecap = document.querySelector(".bottlecap-rig");
    const gateHotspot = document.querySelector("[data-hotspot='toll-gate']");
    const cobwebHotspot = document.querySelector("[data-hotspot='cobweb-curtain']");
    if (!bottlecap || !gateHotspot || !cobwebHotspot) return { ok: false, reason: "missing gate composition element" };
    const bottlecapZ = Number(getComputedStyle(bottlecap).zIndex);
    const gateRect = gateHotspot.getBoundingClientRect();
    const cobwebRect = cobwebHotspot.getBoundingClientRect();
    const bottlecapRect = bottlecap.getBoundingClientRect();
    const stageRect = document.querySelector(".stage")?.getBoundingClientRect();
    if (!stageRect) return { ok: false, reason: "missing stage" };
    const gateWidthRatio = gateRect.width / stageRect.width;
    const cobwebWidthRatio = cobwebRect.width / stageRect.width;
    const bottlecapCenterX = bottlecapRect.left + bottlecapRect.width / 2;
    const bottlecapInGateZone = bottlecapCenterX > gateRect.left && bottlecapCenterX < gateRect.right;
    return {
      ok: bottlecapZ >= 15 && bottlecapInGateZone && gateWidthRatio >= 0.24 && gateWidthRatio <= 0.28 && cobwebWidthRatio >= 0.18 && cobwebWidthRatio <= 0.22,
      bottlecapZ,
      bottlecapInGateZone,
      gateWidthRatio,
      cobwebWidthRatio,
      bottlecapRect: { width: bottlecapRect.width, height: bottlecapRect.height, left: bottlecapRect.left, top: bottlecapRect.top },
      gateRect: { width: gateRect.width, height: gateRect.height, left: gateRect.left, top: gateRect.top },
      cobwebRect: { width: cobwebRect.width, height: cobwebRect.height, left: cobwebRect.left, top: cobwebRect.top },
    };
  });

  if (!result.ok) fail(`${viewportName} gate blocking is wrong: ${JSON.stringify(result)}`);
};

const expectNoStaticSceneOverlays = async (page, viewportName) => {
  const result = await page.evaluate(() => {
    const staleSelectors = [".desk-front", ".desk-chair-back", ".gate-front", ".cobweb-curtain", ".painted-marker"];
    const found = staleSelectors.filter((selector) => document.querySelector(selector));
    return { ok: found.length === 0, found };
  });
  if (!result.ok) fail(`${viewportName} still renders stale static scene overlays: ${result.found.join(", ")}`);
};

const expectNoIdleDustOverlay = async (page, viewportName) => {
  const result = await page.evaluate(() => {
    const onDiscovery = Boolean(document.querySelector(".stage.screen-discovery"));
    const dust = document.querySelector(".dust-prop");
    return { ok: !onDiscovery || !dust, onDiscovery, hasDustProp: Boolean(dust) };
  });
  if (!result.ok) fail(`${viewportName} discovery should use the painted background dust until reveal animation starts`);
};

const clickMode = async (page, mode) => {
  await waitForInteractionReady(page);
  await page.locator(`[data-mode="${mode}"]`).evaluate((element) => {
    if (element instanceof HTMLElement) element.click();
  });
};

const clickHotspot = async (page, id) => {
  await waitForInteractionReady(page);
  await page.locator(`[data-hotspot="${id}"]`).evaluate((element) => {
    if (element instanceof HTMLElement) element.click();
  });
};

const clickExit = async (page, id) => {
  await waitForInteractionReady(page);
  await page.locator(`[data-exit="${id}"]`).evaluate((element) => {
    if (element instanceof HTMLElement) element.click();
  });
};

const assertStageClickAdvancesDialogue = async (page, viewportName) => {
  const before = await page.locator(".dialogue-card span").first().textContent();
  if (!before) fail(`${viewportName} expected opening dialogue before stage-click test`);
  await page.locator(".stage").click({ position: { x: 18, y: 18 } });
  await page.waitForTimeout(120);
  const after = await page.locator(".dialogue-card span").first().textContent();
  if (!after || after === before) fail(`${viewportName} stage click did not advance dialogue`);
};

const assertAudioStarted = async (page, viewportName) => {
  const calls = await page.evaluate(() => globalThis.__lostUnderfoundAudioPlayCalls ?? []);
  const played = (fragment) => calls.some((call) => String(call.src).includes(fragment));
  if (!played("underneath-ambience-loop.ogg")) {
    fail(`${viewportName} ambience audio did not attempt to play after first gesture: ${JSON.stringify(calls)}`);
  }
  if (!played("act01-001-pip-cold-open-landing.ogg") && !played("act01-002-pip-cold-open-goal.ogg")) {
    fail(`${viewportName} voice audio did not attempt to play after dialogue advance: ${JSON.stringify(calls)}`);
  }
};

const assertAudioCuePlayed = async (page, viewportName, fragment, description) => {
  const calls = await page.evaluate(() => globalThis.__lostUnderfoundAudioPlayCalls ?? []);
  if (!calls.some((call) => String(call.src).includes(fragment))) {
    fail(`${viewportName} ${description} audio cue did not play: expected ${fragment}; calls=${JSON.stringify(calls)}`);
  }
};

const waitForAudioCue = async (page, viewportName, fragment, description, timeoutMs = 7000) => {
  try {
    await page.waitForFunction(
      (target) => (globalThis.__lostUnderfoundAudioPlayCalls ?? []).some((call) => String(call.src).includes(target)),
      fragment,
      { timeout: timeoutMs },
    );
  } catch {
    await assertAudioCuePlayed(page, viewportName, fragment, description);
  }
};

const waitForDialogue = async (page, viewportName, description, timeoutMs = 12000) => {
  try {
    await page.locator(".dialogue-card").first().waitFor({ state: "visible", timeout: timeoutMs });
  } catch {
    fail(`${viewportName} ${description} dialogue did not appear after walking finished`);
  }
};

const waitForScreen = async (page, id) => {
  await page.locator(`.stage.screen-${id}`).waitFor({ state: "visible" });
  await page.waitForTimeout(250);
};

const waitForInteractionReady = async (page) => {
  await page.waitForFunction(() => {
    const stage = document.querySelector(".stage");
    return stage && !stage.classList.contains("interaction-blocked");
  });
};

const assertSharedLayout = async (page, viewportName) => {
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.mouse.move(1, 1);
  await page.evaluate(() => {
    if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
  });
  await expectRenderedBox(page, ".stage", `${viewportName} stage`, { width: 300, height: 160 });
  await expectNoOverlap(page, ".stage", ".dialogue-panel", `${viewportName} stage/dialogue-panel`);
  await expectHiddenReleaseHitboxes(page);
  await expectNoWhiteActorShadows(page);
  await expectNoStaticSceneOverlays(page, viewportName);
};

const assertDiscreteBackground = async (page, viewportName, screenId) => {
  const result = await page.evaluate(
    (targetScreenId) => {
      const stage = document.querySelector(`.stage.screen-${targetScreenId}`)?.getBoundingClientRect();
      const bgElement = document.querySelector(".scene-bg");
      const bg = bgElement?.getBoundingClientRect();
      if (!stage || !bg) return { ok: false, reason: "missing stage or background", stage, bg };
      const widthRatio = bg.width / stage.width;
      const heightRatio = bg.height / stage.height;
      const leftDelta = Math.abs(bg.left - stage.left);
      const topDelta = Math.abs(bg.top - stage.top);
      const backgroundId = bgElement instanceof HTMLElement ? bgElement.dataset.backgroundId : "";
      return {
        ok:
          widthRatio >= 0.98 &&
          widthRatio <= 1.02 &&
          heightRatio >= 0.98 &&
          heightRatio <= 1.02 &&
          leftDelta <= 2 &&
          topDelta <= 2 &&
          backgroundId === targetScreenId,
        widthRatio,
        heightRatio,
        leftDelta,
        topDelta,
        backgroundId,
      };
    },
    screenId,
  );

  if (!result.ok) fail(`${viewportName} ${screenId} background is not a native screen-local image: ${JSON.stringify(result)}`);
};

const runViewport = async (browser, viewport) => {
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    isMobile: viewport.isMobile,
    deviceScaleFactor: viewport.isMobile ? 3 : 1,
  });
  const page = await context.newPage();
  await page.addInitScript(() => {
    globalThis.__lostUnderfoundAudioPlayCalls = [];
    HTMLMediaElement.prototype.play = function () {
      globalThis.__lostUnderfoundAudioPlayCalls.push({
        src: this.currentSrc || this.src,
        loop: this.loop,
        volume: this.volume,
      });
      return Promise.resolve();
    };
  });
  await page.goto(BASE_URL, { waitUntil: "networkidle" });

  await assertSharedLayout(page, viewport.name);
  await assertDiscreteBackground(page, viewport.name, "discovery");
  await expectNoIdleDustOverlay(page, viewport.name);
  await expectPipRegisteredScale(page, viewport.name);
  await expectImageCycles(page, ".pip", `${viewport.name} Pip idle`);
  await expectStableImagePresence(page, ".pip", `${viewport.name} Pip idle`);
  await assertStageClickAdvancesDialogue(page, viewport.name);
  await assertAudioStarted(page, viewport.name);
  await screenshot(page, viewport.name, "01-discovery-cold-open");

  await clearDialogue(page);
  await clickMode(page, "use");
  await clickHotspot(page, "dust-clump");
  await waitForAudioCue(page, viewport.name, "dust-clump-reveal.ogg", "dust reveal");
  await assertAudioCuePlayed(page, viewport.name, "dust-clump-reveal.ogg", "dust reveal");
  await screenshot(page, viewport.name, "02-discovery-dust-reveal");
  await waitForDialogue(page, viewport.name, "Pip dust search");
  await clearDialogue(page);
  await waitForInteractionReady(page);
  await expectRenderedBox(page, "[data-item='button']", `${viewport.name} button inventory`, { width: 20, height: 20 });

  await clickExit(page, "to-clerk");
  await waitForScreen(page, "clerk");
  await waitForInteractionReady(page);
  await assertSharedLayout(page, viewport.name);
  await assertDiscreteBackground(page, viewport.name, "clerk");
  await clickMode(page, "inspect");
  await clickHotspot(page, "bramble-desk");
  await waitForDialogue(page, viewport.name, "Bramble greeting");
  await screenshot(page, viewport.name, "03-clerk-bramble-greeting");
  await assertClerkBlocking(page, viewport.name);
  await expectImageCycles(page, ".bramble-rig .body", `${viewport.name} Bramble body`);
  await expectStableImagePresence(page, ".bramble-rig .body", `${viewport.name} Bramble body`);
  await clearDialogue(page);
  await waitForInteractionReady(page);

  await clickExit(page, "to-gate");
  await waitForScreen(page, "gate");
  await waitForInteractionReady(page);
  await assertSharedLayout(page, viewport.name);
  await assertDiscreteBackground(page, viewport.name, "gate");
  await screenshot(page, viewport.name, "04-gate-before-toll");
  await expectStageRelativeBox(page, ".bottlecap-rig", `${viewport.name} Old Bottlecap rig`, { widthRatio: 0.1, heightRatio: 0.15 });
  await expectImageCycles(page, ".bottlecap-rig .body", `${viewport.name} Old Bottlecap idle`, 760);
  await expectStableImagePresence(page, ".bottlecap-rig .body", `${viewport.name} Old Bottlecap idle`, 760);
  await assertGateBlocking(page, viewport.name);

  await clickMode(page, "use");
  await page.evaluate(() => {
    const item = document.querySelector("[data-item='button']");
    if (item instanceof HTMLElement) item.click();
  });
  await clickHotspot(page, "toll-gate");
  await waitForAudioCue(page, viewport.name, "toll-gate-open.ogg", "toll gate open");
  await assertAudioCuePlayed(page, viewport.name, "toll-gate-open.ogg", "toll gate open");
  await assertAudioCuePlayed(page, viewport.name, "toll-paid-stinger.ogg", "toll paid stinger");
  await screenshot(page, viewport.name, "05-gate-toll-paid");
  await clearDialogue(page);
  await waitForInteractionReady(page);

  await clickExit(page, "through-grate");
  await page.waitForTimeout(300);
  await screenshot(page, viewport.name, "06-act1-complete");
  await clearDialogue(page);
  await expectRenderedBox(page, ".boundary", `${viewport.name} Act 1 boundary notice`, { width: 120, height: 20 });

  await context.close();
};

const main = async () => {
  rmSync(OUT_DIR, { recursive: true, force: true });
  mkdirSync(OUT_DIR, { recursive: true });

  const server = await startServer();
  const browser = await chromium.launch();
  try {
    for (const viewport of viewports) {
      await runViewport(browser, viewport);
    }
  } finally {
    await browser.close();
    server.kill();
  }

  console.log(`Runtime visual QA passed. Screenshots written to ${path.relative(ROOT, OUT_DIR)}`);
};

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
});
