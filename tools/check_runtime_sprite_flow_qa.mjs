import { spawn } from "node:child_process";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUT_DIR = path.join(ROOT, "art", "act01-production", "qa", "runtime-sprite-flow");
const HOST = "127.0.0.1";
const PORT = 5192;
const BASE_URL = `http://${HOST}:${PORT}/`;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const fail = (message) => {
  throw new Error(`Runtime sprite-flow QA failed: ${message}`);
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

const clearDialogue = async (page, maxClicks = 50) => {
  for (let count = 0; count < maxClicks; count += 1) {
    const card = page.locator(".dialogue-card").first();
    if ((await card.count()) === 0 || !(await card.isVisible())) return;
    await card.click();
    await page.waitForTimeout(80);
  }
  fail("dialogue did not clear within expected click budget");
};

const waitForInteractionReady = async (page) => {
  await page.waitForFunction(() => {
    const stage = document.querySelector(".stage");
    return stage && !stage.classList.contains("interaction-blocked");
  });
};

const waitForDialogue = async (page, description, timeoutMs = 12000) => {
  try {
    await page.locator(".dialogue-card").first().waitFor({ state: "visible", timeout: timeoutMs });
  } catch {
    fail(`${description} dialogue did not appear`);
  }
};

const waitForScreen = async (page, id) => {
  await page.locator(`.stage.screen-${id}`).waitFor({ state: "visible" });
  await page.waitForTimeout(240);
};

const clickMode = async (page, mode) => {
  await page.locator(`[data-mode="${mode}"]`).click();
};

const clickHotspot = async (page, id) => {
  await page.locator(`[data-hotspot="${id}"]`).click();
};

const clickExit = async (page, id) => {
  await page.locator(`[data-exit="${id}"]`).click();
};

const sampleSprite = async (page, selector, durationMs, sampleEveryMs) => {
  const samples = [];
  const startedAt = Date.now();
  while (Date.now() - startedAt <= durationMs) {
    const sample = await page.locator(selector).first().evaluate((element) => {
      const rect = element.getBoundingClientRect();
      const style = getComputedStyle(element);
      const image = element instanceof HTMLImageElement ? element : element.querySelector("img");
      const imageRect = image?.getBoundingClientRect() ?? rect;
      const src = image instanceof HTMLImageElement ? image.currentSrc || image.src : "";
      const stageRect = document.querySelector(".stage")?.getBoundingClientRect();
      let color = {
        opaquePixels: 0,
        sampledPixels: 0,
        avgR: 0,
        avgG: 0,
        avgB: 0,
        avgSaturation: 0,
        blueCoverage: 0,
      };
      if (image instanceof HTMLImageElement && image.complete && image.naturalWidth > 0 && image.naturalHeight > 0) {
        try {
          const canvas = document.createElement("canvas");
          canvas.width = image.naturalWidth;
          canvas.height = image.naturalHeight;
          const context = canvas.getContext("2d", { willReadFrequently: true });
          context?.drawImage(image, 0, 0);
          const data = context?.getImageData(0, 0, canvas.width, canvas.height).data;
          if (data) {
            const stride = Math.max(1, Math.floor(data.length / 4 / 12000));
            let opaquePixels = 0;
            let sampledPixels = 0;
            let bluePixels = 0;
            let rTotal = 0;
            let gTotal = 0;
            let bTotal = 0;
            let saturationTotal = 0;
            for (let pixel = 0; pixel < data.length / 4; pixel += stride) {
              const offset = pixel * 4;
              const alpha = data[offset + 3];
              sampledPixels += 1;
              if (alpha <= 35) continue;
              const r = data[offset];
              const g = data[offset + 1];
              const b = data[offset + 2];
              const max = Math.max(r, g, b);
              const min = Math.min(r, g, b);
              const saturation = max === 0 ? 0 : (max - min) / max;
              opaquePixels += 1;
              rTotal += r;
              gTotal += g;
              bTotal += b;
              saturationTotal += saturation;
              if (b >= 90 && b > r + 12 && b >= g - 14) bluePixels += 1;
            }
            if (opaquePixels > 0) {
              color = {
                opaquePixels,
                sampledPixels,
                avgR: rTotal / opaquePixels,
                avgG: gTotal / opaquePixels,
                avgB: bTotal / opaquePixels,
                avgSaturation: saturationTotal / opaquePixels,
                blueCoverage: bluePixels / opaquePixels,
              };
            }
          }
        } catch {
          // Pixel sampling is best-effort; blank/asset-source checks still run below.
        }
      }
      return {
        src,
        complete: image instanceof HTMLImageElement ? image.complete : false,
        naturalWidth: image instanceof HTMLImageElement ? image.naturalWidth : 0,
        naturalHeight: image instanceof HTMLImageElement ? image.naturalHeight : 0,
        opacity: Number(style.opacity),
        display: style.display,
        visibility: style.visibility,
        left: rect.left,
        top: rect.top,
        width: rect.width,
        height: rect.height,
        centerX: rect.left + rect.width / 2,
        centerY: rect.top + rect.height / 2,
        imageWidth: imageRect.width,
        imageHeight: imageRect.height,
        stageWidth: stageRect?.width ?? 0,
        stageHeight: stageRect?.height ?? 0,
        color,
      };
    });
    samples.push({ t: Date.now(), ...sample });
    await page.waitForTimeout(sampleEveryMs);
  }
  return samples;
};

const frameName = (src) => {
  const clean = decodeURIComponent(src.split("?")[0] ?? src);
  return clean.slice(clean.lastIndexOf("/") + 1);
};

const changeStats = (samples) => {
  const sources = samples.map((sample) => frameName(sample.src));
  const changes = sources.slice(1).filter((source, index) => source !== sources[index]).length;
  const durationSeconds = Math.max(0.001, (samples.at(-1).t - samples[0].t) / 1000);
  return {
    uniqueFrames: new Set(sources).size,
    changes,
    changesPerSecond: changes / durationSeconds,
    sources,
  };
};

const assertNoBlankSamples = (samples, description) => {
  const blanks = samples
    .map((sample, index) => ({ index, ...sample }))
    .filter(
      (sample) =>
        !sample.complete ||
        sample.naturalWidth <= 0 ||
        sample.naturalHeight <= 0 ||
        sample.width <= 0 ||
        sample.height <= 0 ||
        sample.opacity <= 0 ||
        sample.display === "none" ||
        sample.visibility === "hidden",
    );
  if (blanks.length) fail(`${description} popped blank/incomplete frames: ${JSON.stringify(blanks)}`);
};

const average = (values) => values.reduce((sum, value) => sum + value, 0) / Math.max(1, values.length);

const assertPipLooksBlue = (samples, description) => {
  const valid = samples.filter((sample) => sample.color?.opaquePixels > 40);
  if (!valid.length) fail(`${description} could not sample sprite color; canvas was empty or unreadable`);
  const blueCoverage = average(valid.map((sample) => sample.color.blueCoverage));
  const saturation = average(valid.map((sample) => sample.color.avgSaturation));
  const avgB = average(valid.map((sample) => sample.color.avgB));
  const avgR = average(valid.map((sample) => sample.color.avgR));
  if (blueCoverage < 0.1 || saturation < 0.14 || avgB <= avgR + 8) {
    fail(
      `${description} no longer reads as the blue Pip model: blueCoverage=${blueCoverage.toFixed(3)}, ` +
        `saturation=${saturation.toFixed(3)}, avgRGB=${average(valid.map((sample) => sample.color.avgR)).toFixed(1)}/` +
        `${average(valid.map((sample) => sample.color.avgG)).toFixed(1)}/${avgB.toFixed(1)}`,
    );
  }
  return {
    blueCoverage,
    saturation,
    avgB,
  };
};

const assertSpriteScale = (samples, description, { minStageHeightRatio, maxStageHeightRatio, minPixelHeight }) => {
  const ratios = samples.filter((sample) => sample.stageHeight > 0).map((sample) => sample.height / sample.stageHeight);
  const heights = samples.map((sample) => sample.height);
  const avgRatio = average(ratios);
  const avgHeight = average(heights);
  if (avgRatio < minStageHeightRatio || avgRatio > maxStageHeightRatio || avgHeight < minPixelHeight) {
    fail(
      `${description} is out of scale: height=${avgHeight.toFixed(1)}px, stageRatio=${avgRatio.toFixed(3)}, ` +
        `required ${minPixelHeight}px and ${minStageHeightRatio}-${maxStageHeightRatio} of stage height`,
    );
  }
  return { avgHeight, avgStageHeightRatio: avgRatio };
};

const assertFrameFlow = (
  samples,
  description,
  { prefix, minUniqueFrames, minChangesPerSecond = 0, maxChangesPerSecond, minPrefixRatio = 0.72 },
) => {
  assertNoBlankSamples(samples, description);
  const stats = changeStats(samples);
  const prefixMatches = samples.filter((sample) => frameName(sample.src).includes(prefix)).length;
  const prefixRatio = prefixMatches / samples.length;
  if (prefixRatio < minPrefixRatio) {
    fail(
      `${description} used wrong animation frames: expected prefix ${prefix}, ratio=${prefixRatio.toFixed(2)}, frames=${JSON.stringify(stats.sources)}`,
    );
  }
  if (stats.uniqueFrames < minUniqueFrames) {
    fail(`${description} froze or under-cycled: ${stats.uniqueFrames} unique frame(s), frames=${JSON.stringify(stats.sources)}`);
  }
  if (stats.changesPerSecond < minChangesPerSecond) {
    fail(`${description} changed too slowly: ${stats.changesPerSecond.toFixed(2)} changes/sec`);
  }
  if (stats.changesPerSecond > maxChangesPerSecond) {
    fail(`${description} changed too fast: ${stats.changesPerSecond.toFixed(2)} changes/sec`);
  }
  return stats;
};

const assertWalkMotion = (samples, description) => {
  const deltas = samples.slice(1).map((sample, index) => ({
    dx: sample.centerX - samples[index].centerX,
    dy: sample.centerY - samples[index].centerY,
    dt: (sample.t - samples[index].t) / 1000,
  }));
  const totalDx = samples.at(-1).centerX - samples[0].centerX;
  const totalDy = samples.at(-1).centerY - samples[0].centerY;
  const totalDistance = Math.hypot(totalDx, totalDy);
  const durationSeconds = (samples.at(-1).t - samples[0].t) / 1000;
  const speed = totalDistance / Math.max(0.001, durationSeconds);
  const biggestJump = Math.max(...deltas.map((delta) => Math.hypot(delta.dx, delta.dy)));
  const maxStepSpeed = Math.max(...deltas.map((delta) => Math.hypot(delta.dx, delta.dy) / Math.max(0.001, delta.dt)));

  if (totalDistance < 70) fail(`${description} did not visibly travel during walk: ${totalDistance.toFixed(1)}px`);
  if (speed > 185) fail(`${description} zips too fast through the scene: ${speed.toFixed(1)}px/sec`);
  const maxAllowedStepSpeed = 300;
  if (maxStepSpeed > maxAllowedStepSpeed) {
    fail(`${description} teleported between samples: biggest jump ${biggestJump.toFixed(1)}px, max step speed ${maxStepSpeed.toFixed(1)}px/sec, limit ${maxAllowedStepSpeed}px/sec`);
  }
  if (Math.abs(totalDx) < Math.abs(totalDy)) {
    fail(`${description} did not follow the expected mostly-horizontal room movement: dx=${totalDx.toFixed(1)}, dy=${totalDy.toFixed(1)}`);
  }
  return { totalDistance, speed, biggestJump, maxStepSpeed };
};

const run = async () => {
  rmSync(OUT_DIR, { recursive: true, force: true });
  mkdirSync(OUT_DIR, { recursive: true });

  const server = await startServer();
  const browser = await chromium.launch();
  const report = { checks: [] };

  try {
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
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
    await clearDialogue(page);
    await waitForInteractionReady(page);

    const pipIdle = await sampleSprite(page, ".pip", 1500, 100);
    report.checks.push({
      name: "pip idle",
      ...assertFrameFlow(pipIdle, "Pip idle", {
        prefix: "pip_meshy_idle_",
        minUniqueFrames: 3,
        minChangesPerSecond: 1.6,
        maxChangesPerSecond: 4.2,
      }),
      scale: assertSpriteScale(pipIdle, "Desktop Pip idle", {
        minStageHeightRatio: 0.6,
        maxStageHeightRatio: 0.78,
        minPixelHeight: 380,
      }),
      color: assertPipLooksBlue(pipIdle, "Desktop Pip idle"),
    });

    await clickMode(page, "use");
    await clickHotspot(page, "dust-clump");
    const pipWalk = await sampleSprite(page, ".pip", 1250, 100);
    report.checks.push({
      name: "pip walk to dust",
      ...assertFrameFlow(pipWalk, "Pip walk to dust", {
        prefix: "pip_meshy_walk_",
        minUniqueFrames: 5,
        minChangesPerSecond: 5,
        maxChangesPerSecond: 12,
      }),
      motion: assertWalkMotion(pipWalk, "Pip walk to dust"),
      color: assertPipLooksBlue(pipWalk, "Pip walk to dust"),
    });

    await waitForDialogue(page, "Pip dust search");
    const pipTalk = await sampleSprite(page, ".pip", 900, 90);
    report.checks.push({
      name: "pip talk",
      ...assertFrameFlow(pipTalk, "Pip talk", {
        prefix: "pip_meshy_talk_",
        minUniqueFrames: 4,
        minChangesPerSecond: 5,
        maxChangesPerSecond: 12,
      }),
      color: assertPipLooksBlue(pipTalk, "Pip talk"),
    });

    await clearDialogue(page);
    await waitForInteractionReady(page);
    await clickExit(page, "to-clerk");
    await waitForScreen(page, "clerk");
    await waitForInteractionReady(page);

    const brambleIdle = await sampleSprite(page, ".bramble-rig .body", 1600, 130);
    report.checks.push({
      name: "bramble idle",
      ...assertFrameFlow(brambleIdle, "Bramble idle", {
        prefix: "bramble_idle_",
        minUniqueFrames: 2,
        minChangesPerSecond: 1,
        maxChangesPerSecond: 5,
      }),
    });

    await clickMode(page, "inspect");
    await clickHotspot(page, "bramble-desk");
    await waitForDialogue(page, "Bramble greeting");
    const brambleTalk = await sampleSprite(page, ".bramble-rig .body", 1000, 100);
    report.checks.push({
      name: "bramble greeting/talk flow",
      ...assertFrameFlow(brambleTalk, "Bramble greeting/talk flow", {
        prefix: "bramble_",
        minUniqueFrames: 3,
        minChangesPerSecond: 2,
        maxChangesPerSecond: 12,
      }),
    });

    await clearDialogue(page);
    await waitForInteractionReady(page);
    await clickExit(page, "to-gate");
    await waitForScreen(page, "gate");
    await waitForInteractionReady(page);

    const bottlecapIdle = await sampleSprite(page, ".bottlecap-rig .body", 1700, 170);
    report.checks.push({
      name: "old bottlecap idle",
      ...assertFrameFlow(bottlecapIdle, "Old Bottlecap idle", {
        prefix: "old_bottlecap_meshy_idle_",
        minUniqueFrames: 2,
        minChangesPerSecond: 0.6,
        maxChangesPerSecond: 7,
      }),
    });

    await page.screenshot({ path: path.join(OUT_DIR, "sprite-flow-final.png"), fullPage: true });
    await context.close();

    const mobileContext = await browser.newContext({ viewport: { width: 390, height: 850 }, isMobile: true });
    const mobilePage = await mobileContext.newPage();
    await mobilePage.addInitScript(() => {
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
    await mobilePage.goto(BASE_URL, { waitUntil: "networkidle" });
    await clearDialogue(mobilePage);
    await waitForInteractionReady(mobilePage);
    const mobilePipIdle = await sampleSprite(mobilePage, ".pip", 1500, 100);
    report.checks.push({
      name: "mobile portrait pip idle",
      ...assertFrameFlow(mobilePipIdle, "Mobile portrait Pip idle", {
        prefix: "pip_meshy_idle_",
        minUniqueFrames: 3,
        minChangesPerSecond: 1.6,
        maxChangesPerSecond: 4.2,
      }),
      scale: assertSpriteScale(mobilePipIdle, "Mobile portrait Pip idle", {
        minStageHeightRatio: 0.6,
        maxStageHeightRatio: 0.78,
        minPixelHeight: 118,
      }),
      color: assertPipLooksBlue(mobilePipIdle, "Mobile portrait Pip idle"),
    });
    await mobilePage.screenshot({ path: path.join(OUT_DIR, "sprite-flow-mobile.png"), fullPage: true });
    await mobileContext.close();
  } finally {
    await browser.close();
    server.kill();
  }

  writeFileSync(path.join(OUT_DIR, "sprite-flow-report.json"), `${JSON.stringify(report, null, 2)}\n`);
  console.log(`Runtime sprite-flow QA passed. Report written to ${path.relative(ROOT, OUT_DIR)}`);
};

run().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
});
