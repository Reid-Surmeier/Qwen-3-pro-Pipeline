// Issue #136 exact-candidate browser proof for reset, raise, and continuous drag.
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { createRequire } from "node:module";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const require = createRequire(`${process.env.PLAYWRIGHT_NODE_MODULES
  ?? resolve(import.meta.dirname, "browser/node_modules")}/`);
const { chromium } = require("playwright");
const URL = process.env.IMAGE79_URL ?? "http://127.0.0.1:8894/?screen=image79";
const OUT = resolve(process.env.IMAGE79_PLAYTEST_OUT
  ?? resolve(import.meta.dirname, "out/image79-assembly-browser"));
const CANDIDATE = process.env.CANDIDATE_SHA ?? "";
const DESIGN = { width: 1536, height: 1024 };
const manifest = JSON.parse(readFileSync(resolve(import.meta.dirname,
  "../data/image-79-control-spec.json"), "utf8"));
const skillGeometry = manifest.windows.find(window => window.id === "skill_tree").geometry;
const SKILL_HOME = [skillGeometry.x, skillGeometry.y];

assert.match(CANDIDATE, /^[0-9a-f]{40}$/,
  "CANDIDATE_SHA must name the exact forty-character candidate commit");
mkdirSync(OUT, { recursive: true });
const sha256 = path => createHash("sha256").update(readFileSync(path)).digest("hex");

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: DESIGN });
const consoleErrors = [];
page.on("pageerror", error => consoleErrors.push(`[pageerror] ${String(error)}`));
page.on("console", message => {
  const value = message.text();
  if (message.type() === "error"
    && !(value.includes("GL Driver Message") && value.includes("ReadPixels"))) {
    consoleErrors.push(`[error] ${value}`.slice(0, 1000));
  }
});

const waitForAssembly = async () => {
  await page.waitForFunction(() => Object.keys(window.godotQaState?.windows ?? {})
    .length === 11, undefined, { timeout: 90000 });
  await page.waitForTimeout(350);
};
const qa = () => page.evaluate(() => structuredClone(window.godotQaState));
const shot = async name => {
  const path = resolve(OUT, `${name}.png`);
  await page.screenshot({ path });
  return { path: `${name}.png`, sha256: sha256(path) };
};
const stacks = state => Object.fromEntries(Object.entries(state.windows)
  .map(([id, value]) => [id, value.window.stack_index]));

await page.goto(URL, { waitUntil: "domcontentloaded", timeout: 90000 });
await waitForAssembly();
const reset = await qa();
const resetFrame = await shot("assembled-desktop-reset");
const resetStack = stacks(reset);
assert.deepEqual(reset.viewport, [DESIGN.width, DESIGN.height]);
assert.equal(Object.keys(reset.windows).length, 11);
assert.ok(Object.values(reset.windows).every(value => value.window.visible
  && !value.window.minimized && !value.window.process_active));
assert.equal(new Set(Object.values(resetStack)).size, 11);

const start = { x: 620, y: 14 };
const end = { x: 800, y: 134 };
await page.mouse.move(start.x, start.y);
await page.mouse.down();
for (let index = 1; index <= 60; index += 1) {
  const ratio = index / 60;
  await page.mouse.move(start.x + (end.x - start.x) * ratio,
    start.y + (end.y - start.y) * ratio);
  if (index === 30) await shot("skill-tree-drag-mid");
  await page.waitForTimeout(8);
}
await page.mouse.up();
await page.waitForTimeout(300);
const moved = await qa();
const movedFrame = await shot("skill-tree-raised-moved");
assert.notDeepEqual(moved.windows.skill_tree.window.position, SKILL_HOME);
assert.equal(moved.windows.skill_tree.window.stack_index,
  Math.max(...Object.values(stacks(moved))));
assert.ok(moved.windows.skill_tree.window.drag.motion_samples >= 30);
assert.ok(moved.windows.skill_tree.window.drag.position_samples.every(
  (position, index, values) => index === 0
    || (position[0] >= values[index - 1][0]
      && position[1] >= values[index - 1][1])));

await page.reload({ waitUntil: "domcontentloaded", timeout: 90000 });
await waitForAssembly();
const restored = await qa();
const restoredFrame = await shot("assembled-desktop-restored");
assert.deepEqual(restored.windows.skill_tree.window.position, SKILL_HOME);
assert.deepEqual(stacks(restored), resetStack);
assert.deepEqual(consoleErrors, []);

const report = {
  schema_version: 1,
  issue: 136,
  candidate_commit: CANDIDATE,
  source_reference_sha256: reset.reference_sha256,
  pass: true,
  console_errors: consoleErrors,
  frames: { reset: resetFrame, moved: movedFrame, restored: restoredFrame },
  reset: { window_count: 11, stack: resetStack },
  moved: {
    position: moved.windows.skill_tree.window.position,
    stack_index: moved.windows.skill_tree.window.stack_index,
    motion_samples: moved.windows.skill_tree.window.drag.motion_samples,
  },
  restored: { position: restored.windows.skill_tree.window.position,
    stack: stacks(restored) },
};
writeFileSync(resolve(OUT, "assembly-browser-report.json"),
  `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify({ pass: true, output: OUT,
  motion_samples: report.moved.motion_samples }));
await browser.close();
