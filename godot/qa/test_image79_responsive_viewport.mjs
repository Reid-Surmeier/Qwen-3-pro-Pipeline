// Regression for Issue #134's shared Web viewport seam. A browser viewport
// wider than the 1536x1024 Reference Screen must letterbox the complete
// desktop and map pointer input through the same transform.
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { createRequire } from "node:module";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const require = createRequire(`${process.env.PLAYWRIGHT_NODE_MODULES
  ?? resolve(import.meta.dirname, "browser/node_modules")}/`);
const { chromium } = require("playwright");
const URL = process.env.IMAGE79_URL ?? "http://127.0.0.1:8894/?screen=image79";
const DESIGN = { width: 1536, height: 1024 };
const VIEWPORT = {
  width: Number(process.env.IMAGE79_VIEWPORT_WIDTH ?? 1280),
  height: Number(process.env.IMAGE79_VIEWPORT_HEIGHT ?? 720),
};
const output = mkdtempSync(join(tmpdir(), "image79-responsive-"));
const screenshot = join(output, "viewport.png");

const pixelAt = (x, y) => {
  const result = spawnSync("convert", [screenshot, "-format",
    `%[pixel:p{${x},${y}}]`, "info:"], { encoding: "utf8" });
  assert.equal(result.status, 0, result.stderr);
  return result.stdout.trim();
};

const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: VIEWPORT });
  const consoleErrors = [];
  page.on("pageerror", (error) => consoleErrors.push(String(error)));
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });

  await page.goto(URL, { waitUntil: "load", timeout: 90000 });
  await page.waitForFunction(() => window.godotQaState?.windows?.basic_info,
    undefined, { timeout: 90000 });
  await page.waitForTimeout(300);

  const state = await page.evaluate(() => {
    const canvas = document.querySelector("canvas");
    const rect = canvas.getBoundingClientRect();
    return {
      canvas: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
      viewport: window.godotQaState.viewport,
      control: window.godotQaState.windows.basic_info.controls[
        "basic_info.destination.option"],
    };
  });
  assert.deepEqual(state.viewport, [DESIGN.width, DESIGN.height]);
  assert.deepEqual(state.canvas, { x: 0, y: 0, ...VIEWPORT });

  await page.screenshot({ path: screenshot });
  const scale = Math.min(VIEWPORT.width / DESIGN.width,
    VIEWPORT.height / DESIGN.height);
  const offsetX = (VIEWPORT.width - DESIGN.width * scale) / 2;
  const offsetY = (VIEWPORT.height - DESIGN.height * scale) / 2;
  if (offsetX > 0) {
    assert.equal(pixelAt(Math.floor(offsetX / 2), Math.floor(VIEWPORT.height / 2)),
      "srgb(0,0,0)", "the complete desktop must be horizontally letterboxed");
  } else if (offsetY > 0) {
    assert.equal(pixelAt(Math.floor(VIEWPORT.width / 2), Math.floor(offsetY / 2)),
      "srgb(0,0,0)", "the complete desktop must be vertically letterboxed");
  }

  const geometry = state.control.geometry;
  const x = offsetX + (geometry.x + geometry.width / 2) * scale;
  const y = offsetY + (geometry.y + geometry.height / 2) * scale;
  await page.mouse.click(x, y);
  await page.waitForTimeout(100);
  const result = await page.evaluate(() => ({
    control: window.godotQaState.windows.basic_info.controls[
      "basic_info.destination.option"],
    transaction: window.godotQaState.last_transaction,
  }));
  assert.equal(result.control.last_gesture, "Activate",
    "the pointer must activate the control rendered beneath it");
  assert.equal(result.control.last_action, "OpenWindow");
  assert.equal(result.transaction.target_window, "options");
  assert.deepEqual(consoleErrors, []);
  console.log(JSON.stringify({ pass: true, viewport: VIEWPORT, scale, offsetX,
    offsetY, control: result.control.id }));
} finally {
  await browser.close();
  rmSync(output, { recursive: true, force: true });
}
