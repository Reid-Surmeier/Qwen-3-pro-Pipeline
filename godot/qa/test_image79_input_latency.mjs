// Regression for Issue #134's browser input latency. The complete Image-79
// desktop must publish a real pointer action within the owner's perceptible
// response budget after the pointer has already settled over the control.
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { resolve } from "node:path";

const require = createRequire(`${process.env.PLAYWRIGHT_NODE_MODULES
  ?? resolve(import.meta.dirname, "browser/node_modules")}/`);
const { chromium } = require("playwright");
const URL = process.env.IMAGE79_URL ?? "http://127.0.0.1:8894/?screen=image79";
const MAX_INPUT_LATENCY_MS = Number(process.env.IMAGE79_MAX_INPUT_LATENCY_MS ?? 34);
const VIEWPORT = { width: 1280, height: 720 };

const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: VIEWPORT });
  const consoleErrors = [];
  page.on("pageerror", error => consoleErrors.push(String(error)));
  page.on("console", message => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });

  await page.goto(URL, { waitUntil: "load", timeout: 90000 });
  await page.waitForFunction(() => window.godotQaState?.windows?.system_menu,
    undefined, { timeout: 90000 });
  await page.waitForTimeout(300);

  const state = await page.evaluate(() => {
    const canvas = document.querySelector("canvas").getBoundingClientRect();
    return {
      canvas: { x: canvas.x, y: canvas.y, width: canvas.width, height: canvas.height },
      viewport: window.godotQaState.viewport,
      control: window.godotQaState.windows.system_menu.controls[
        "system_menu.return_to_game"],
    };
  });
  const [designWidth, designHeight] = state.viewport;
  const scale = Math.min(state.canvas.width / designWidth,
    state.canvas.height / designHeight);
  const offsetX = state.canvas.x + (state.canvas.width - designWidth * scale) / 2;
  const offsetY = state.canvas.y + (state.canvas.height - designHeight * scale) / 2;
  const geometry = state.control.geometry;
  const point = {
    x: offsetX + (geometry.x + geometry.width / 2) * scale,
    y: offsetY + (geometry.y + geometry.height / 2) * scale,
  };

  await page.mouse.move(point.x, point.y);
  await page.waitForTimeout(100);
  await page.evaluate(() => {
    window.__image79PointerUpAt = 0;
    window.__image79QaPublishedAt = 0;
    const before = window.godotQaState.windows.system_menu.window.visible;
    const observeQaState = () => {
      if (window.godotQaState.windows.system_menu.window.visible !== before) {
        window.__image79QaPublishedAt = performance.now();
      } else {
        requestAnimationFrame(observeQaState);
      }
    };
    requestAnimationFrame(observeQaState);
    document.querySelector("canvas").addEventListener("pointerup", () => {
      window.__image79PointerUpAt = performance.now();
    }, { capture: true, once: true });
  });
  await page.mouse.click(point.x, point.y);
  await page.waitForFunction(() =>
    !window.godotQaState.windows.system_menu.window.visible,
  undefined, { timeout: 5000, polling: "raf" });
  const timing = await page.evaluate(() => ({
    pointerUpAt: window.__image79PointerUpAt,
    qaPublishedAt: window.__image79QaPublishedAt,
  }));
  assert.ok(timing.pointerUpAt > 0 && timing.qaPublishedAt > 0,
    "browser timing markers must observe the real pointer and QA transition");
  const elapsedMs = timing.qaPublishedAt - timing.pointerUpAt;

  assert.ok(elapsedMs <= MAX_INPUT_LATENCY_MS,
    `return-to-game input latency ${elapsedMs.toFixed(1)}ms exceeds `
      + `${MAX_INPUT_LATENCY_MS}ms`);
  assert.deepEqual(consoleErrors, []);
  console.log(JSON.stringify({ pass: true, input_latency_ms: elapsedMs,
    ceiling_ms: MAX_INPUT_LATENCY_MS }));
} finally {
  await browser.close();
}
