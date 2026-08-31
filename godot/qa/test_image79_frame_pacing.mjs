// Issue #136 complete-Assembly idle and continuous-drag performance regression.
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { resolve } from "node:path";

const require = createRequire(`${process.env.PLAYWRIGHT_NODE_MODULES
  ?? resolve(import.meta.dirname, "browser/node_modules")}/`);
const { chromium } = require("playwright");
const URL = process.env.IMAGE79_URL ?? "http://127.0.0.1:8894/?screen=image79";
const MAX_P95_FRAME_MS = Number(process.env.IMAGE79_MAX_P95_FRAME_MS ?? 50);
const MAX_LONG_FRAME_MS = Number(process.env.IMAGE79_MAX_LONG_FRAME_MS ?? 150);
const MAX_DRAG_REGRESSION_MS = Number(
  process.env.IMAGE79_MAX_DRAG_REGRESSION_MS ?? 51);

const percentile = (values, fraction) => {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.min(sorted.length - 1, Math.floor(sorted.length * fraction))];
};

const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1536, height: 1024 } });
  const consoleErrors = [];
  page.on("pageerror", error => consoleErrors.push(String(error)));
  page.on("console", message => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  await page.goto(URL, { waitUntil: "load", timeout: 90000 });
  await page.waitForFunction(() => window.godotQaState?.windows?.chat_room,
    undefined, { timeout: 90000 });
  await page.waitForTimeout(300);

  const before = await page.evaluate(() => ({
    stateBytes: JSON.stringify(window.godotQaState).length,
    metrics: { ...window.godotQaMetrics },
    windows: structuredClone(window.godotQaState.windows),
  }));
  assert.equal(Object.keys(before.windows).length, 11);
  assert.ok(Object.values(before.windows).every(state => !state.window.process_active),
    "all eleven Windows must be idle before input");

  const idleIntervals = await page.evaluate(() => new Promise(resolveIdle => {
    const intervals = [];
    let prior = 0;
    let started = 0;
    const sample = now => {
      if (!started) started = now;
      if (prior) intervals.push(now - prior);
      prior = now;
      if (now - started >= 1000) resolveIdle(intervals);
      else requestAnimationFrame(sample);
    };
    requestAnimationFrame(sample);
  }));
  const idleP95 = percentile(idleIntervals, 0.95);
  const idleMaximum = Math.max(...idleIntervals);

  await page.evaluate(() => {
    window.__image79FrameIntervals = [];
    window.__image79FrameStop = false;
    let prior = 0;
    const sample = now => {
      if (prior) window.__image79FrameIntervals.push(now - prior);
      prior = now;
      if (!window.__image79FrameStop) requestAnimationFrame(sample);
    };
    requestAnimationFrame(sample);
  });

  const start = { x: 620, y: 14 };
  const end = { x: 800, y: 134 };
  await page.mouse.move(start.x, start.y);
  await page.mouse.down();
  for (let index = 1; index <= 60; index += 1) {
    const ratio = index / 60;
    await page.mouse.move(start.x + (end.x - start.x) * ratio,
      start.y + (end.y - start.y) * ratio);
    await page.waitForTimeout(8);
  }
  await page.mouse.up();
  await page.waitForTimeout(250);
  const after = await page.evaluate(() => {
    window.__image79FrameStop = true;
    return {
      intervals: [...window.__image79FrameIntervals],
      metrics: { ...window.godotQaMetrics },
      skillTree: structuredClone(window.godotQaState.windows.skill_tree),
      windows: structuredClone(window.godotQaState.windows),
    };
  });

  assert.ok(after.intervals.length >= 5, "drag must collect browser frame samples");
  const p95 = percentile(after.intervals, 0.95);
  const maximum = Math.max(...after.intervals);
  const p95Ceiling = Math.max(MAX_P95_FRAME_MS,
    idleP95 + MAX_DRAG_REGRESSION_MS);
  const longFrameCeiling = Math.max(MAX_LONG_FRAME_MS,
    idleMaximum + MAX_DRAG_REGRESSION_MS * 3);
  assert.ok(p95 <= p95Ceiling,
    `drag frame p95 ${p95.toFixed(1)}ms exceeds measured ceiling `
      + `${p95Ceiling.toFixed(1)}ms (idle ${idleP95.toFixed(1)}ms)`);
  assert.ok(maximum <= longFrameCeiling,
    `drag long frame ${maximum.toFixed(1)}ms exceeds measured ceiling `
      + `${longFrameCeiling.toFixed(1)}ms`);
  assert.deepEqual(after.skillTree.window.position, [672, 120]);
  assert.equal(after.skillTree.window.last_gesture, "Drag");
  assert.ok(after.skillTree.window.drag.motion_samples >= 30,
    "Godot must retain at least 30 real continuous motion samples");
  const positions = after.skillTree.window.drag.position_samples;
  assert.ok(positions.every((position, index) => index === 0
    || (position[0] >= positions[index - 1][0]
      && position[1] >= positions[index - 1][1])),
  "Godot drag samples must remain monotonic");
  assert.ok(after.metrics.patchPublishes > before.metrics.patchPublishes);
  assert.ok(after.metrics.maxPatchBytes < before.stateBytes,
    "changed-Window patches must remain smaller than the complete desktop state");
  assert.ok(Object.values(after.windows).every(state => !state.window.process_active),
    "drag must not wake idle Window frame processing");
  assert.deepEqual(consoleErrors, []);
  console.log(JSON.stringify({ pass: true, idle_p95_frame_ms: idleP95,
    idle_max_frame_ms: idleMaximum, drag_p95_frame_ms: p95,
    max_frame_ms: maximum, frame_samples: after.intervals.length,
    patch_publishes: after.metrics.patchPublishes - before.metrics.patchPublishes,
    geometry_publishes: after.metrics.geometryPublishes,
    geometry_skips: after.metrics.geometrySkips,
    max_patch_bytes: after.metrics.maxPatchBytes,
    full_state_bytes: before.stateBytes }));
} finally {
  await browser.close();
}
