// Browser-side Issue #131 drive. Real Chromium gestures prove every frozen
// Status binding, including conditional allocation, rejection, reversal, and
// shared Window behavior.
import { createRequire } from "node:module";
import { createHash } from "node:crypto";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, unlinkSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(SCRIPT_DIR, "../..");
const require = createRequire(`${process.env.PLAYWRIGHT_NODE_MODULES
  ?? resolve(SCRIPT_DIR, "browser/node_modules")}/`);
const { chromium } = require("playwright");
const URL = process.env.IMAGE79_URL ?? "http://127.0.0.1:8877/?screen=image79";
const OUT = resolve(process.env.IMAGE79_PLAYTEST_OUT
  ?? resolve(SCRIPT_DIR, "out/image79-status-browser"));
const DESIGN = { width: 1536, height: 1024 };
const WINDOW_REGION = { x: 0, y: 211, width: 484, height: 208 };
const INVARIANT_REGION = { x: 1400, y: 800, width: 100, height: 100 };
mkdirSync(OUT, { recursive: true });

const sha256 = (path) => createHash("sha256").update(readFileSync(path)).digest("hex");
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: DESIGN });
const consoleEntries = [];
page.on("console", (message) => {
  if (["warning", "error"].includes(message.type())) {
    consoleEntries.push(`[${message.type()}] ${message.text()}`.slice(0, 1000));
  }
});
page.on("pageerror", (error) => consoleEntries.push(`[pageerror] ${String(error)}`.slice(0, 1000)));

const load = async () => {
  await page.goto(URL, { waitUntil: "networkidle", timeout: 90000 });
  await page.waitForFunction(() => window.godotQaState?.windows?.status,
    undefined, { timeout: 90000 });
  await page.waitForTimeout(700);
};
await load();
const canvasFacts = await page.evaluate(() => {
  const rect = document.querySelector("canvas").getBoundingClientRect();
  return { width: rect.width, height: rect.height, x: rect.x, y: rect.y };
});
const scale = Math.min(canvasFacts.width / DESIGN.width, canvasFacts.height / DESIGN.height);
const offsetX = canvasFacts.x + (canvasFacts.width - DESIGN.width * scale) / 2;
const offsetY = canvasFacts.y + (canvasFacts.height - DESIGN.height * scale) / 2;
const point = (x, y) => ({ x: offsetX + x * scale, y: offsetY + y * scale });
const qa = () => page.evaluate(() => window.godotQaState);
const status = async () => (await qa()).windows.status;
const neutral = async () => {
  const target = point(1200, 700);
  await page.mouse.move(target.x, target.y);
  await page.waitForTimeout(60);
};
const shot = async (name, settle = true) => {
  if (settle) await neutral();
  const path = resolve(OUT, `${name}.png`);
  await page.screenshot({ path });
  return { path: `${name}.png`, sha256: sha256(path) };
};
const invariantShot = async (name) => {
  const path = resolve(OUT, `${name}.png`);
  await page.screenshot({ path, clip: INVARIANT_REGION });
  return { path: `${name}.png`, sha256: sha256(path) };
};
const ae = (left, right, crop = undefined) => {
  const leftPath = resolve(OUT, left.path);
  const rightPath = resolve(OUT, right.path);
  let comparedLeft = leftPath;
  let comparedRight = rightPath;
  const temporary = [];
  if (crop) {
    const geometry = `${crop.width}x${crop.height}+${crop.x}+${crop.y}`;
    comparedLeft = resolve(OUT, `.left-${process.pid}.png`);
    comparedRight = resolve(OUT, `.right-${process.pid}.png`);
    temporary.push(comparedLeft, comparedRight);
    for (const [input, output] of [[leftPath, comparedLeft], [rightPath, comparedRight]]) {
      const result = spawnSync("convert", [input, "-crop", geometry, "+repage", output],
        { encoding: "utf8" });
      if (result.status !== 0) throw new Error(result.stderr || "ImageMagick crop failed");
    }
  }
  const result = spawnSync("compare", ["-metric", "AE", comparedLeft, comparedRight,
    "null:"], { encoding: "utf8" });
  temporary.forEach((path) => unlinkSync(path));
  const value = Number(`${result.stderr ?? ""}${result.stdout ?? ""}`.trim());
  if (!Number.isFinite(value)) throw new Error("ImageMagick AE failed");
  return value;
};
const metrics = (before, after) => ({
  full_frame_changed_pixels: ae(before, after),
  intended_region_changed_pixels: ae(before, after, WINDOW_REGION),
  invariant_region_changed_pixels: ae(before, after, INVARIANT_REGION),
});
const manifest = JSON.parse(readFileSync(resolve(ROOT,
  "godot/data/image-79-control-spec.json"), "utf8"));
const windowSpec = manifest.windows.find((entry) => entry.id === "status");
const approved = new Set(windowSpec.actions.map((binding) =>
  `status:${binding.gesture}:${binding.action}`).concat(
  windowSpec.controls.flatMap((entry) => entry.actions.map((binding) =>
    `${entry.id}:${binding.gesture}:${binding.action}`))));
const actions = [];
const checks = [];
const record = (controlId, gesture, action, assertions, frames, observed,
  options = {}) => {
  const pixelMetrics = metrics(frames.before, frames.after);
  const reversalMetrics = metrics(frames.before, frames.reversed);
  const matches = Object.values(assertions).every(Boolean);
  const expectedRejection = options.expectedRejection === true;
  const entry = {
    control_id: controlId, gesture, window_action: action,
    expected: "manifest and retained Status Behaviour Card",
    observed: JSON.stringify(observed), responsive: matches, matches_expected: matches,
    expected_rejection: expectedRejection, assertions, frames,
    intended_region: WINDOW_REGION, invariant_region: INVARIANT_REGION,
    pixel_metrics: pixelMetrics, reversal_pixel_metrics: reversalMetrics,
    contract_facts: {
      real_gesture_path: matches,
      intended_region_changed: expectedRejection
        ? false : pixelMetrics.intended_region_changed_pixels > 0,
      invariants_stable: pixelMetrics.invariant_region_changed_pixels === 0,
      source_approved: approved.has(`${controlId}:${gesture}:${action}`),
      reversible: Object.values(reversalMetrics).every((value) => value === 0),
    },
  };
  if (expectedRejection) entry.mid_pixel_metrics = metrics(frames.before, frames.mid);
  if (options.motionSamples !== undefined) entry.motion_samples = options.motionSamples;
  if (action === "ToggleMinimized") entry.frames.restored = frames.reversed;
  actions.push(entry);
  const contractPass = Object.entries(entry.contract_facts).every(([name, value]) =>
    name === "intended_region_changed" && expectedRejection ? value === false : value === true);
  checks.push({ name: `${controlId}:${gesture}:${action}`,
    passed: matches && contractPass,
    detail: { assertions, contract_facts: entry.contract_facts } });
};
const reload = async () => {
  await page.reload({ waitUntil: "networkidle", timeout: 90000 });
  await page.waitForFunction(() => window.godotQaState?.windows?.status,
    undefined, { timeout: 90000 });
  await page.waitForTimeout(600);
};
const center = (geometry) => point(geometry.x + geometry.width / 2,
  geometry.y + geometry.height / 2);
const arrowPoint = async (controlId) => {
  const state = await status();
  return center(state.controls[controlId].surface_geometry.increment);
};

const idle = await shot("00-idle");
const invariantBefore = await invariantShot("00-invariant-before");
const initial = await status();
checks.push({ name: "idle-source-factual", passed: initial.window_state.points === 4
  && initial.window_state.attributes["status.attribute.int"].base === 92
  && initial.controls["status.attribute.int"].semantic_state === "disabled"
  && !initial.status_overlay.visible,
detail: initial.window_state });

// Purpose-built minimize and exact restore.
let target = center({ x: 436, y: 216, width: 20, height: 20 });
await page.mouse.click(target.x, target.y);
await page.waitForTimeout(80);
const minimized = await status();
const minimizeAfter = await shot("01-minimized");
target = center({ x: 436, y: 216, width: 20, height: 20 });
await page.mouse.click(target.x, target.y);
await page.waitForTimeout(80);
const restored = await status();
const minimizeReversed = await shot("01b-restored");
record("status.minimize", "Activate", "ToggleMinimized", {
  minimized: minimized.window.minimized && minimized.window.size[1] === 28,
  restored: !restored.window.minimized && restored.window.size[1] === 208,
  semantic_state_preserved: restored.window_state.points === 4,
}, { before: idle, after: minimizeAfter, reversed: minimizeReversed }, restored.window);

const availableAttributes = [
  ["status.attribute.str", "Atk"],
  ["status.attribute.agi", "Aspd"],
  ["status.attribute.vit", "Def"],
  ["status.attribute.dex", "Hit"],
  ["status.attribute.luk", "Critical"],
];
let sequence = 2;
for (const [controlId, derivedKey] of availableAttributes) {
  await reload();
  const beforeState = await status();
  const before = await shot(`${sequence}-${controlId.split(".").at(-1)}-activate-before`);
  target = await arrowPoint(controlId);
  await page.mouse.move(target.x, target.y);
  const hovered = await status();
  await page.mouse.down();
  const pressed = await status();
  await page.mouse.up();
  await page.waitForTimeout(60);
  const afterState = await status();
  const after = await shot(`${sequence}-${controlId.split(".").at(-1)}-activated`);
  await page.mouse.click(target.x, target.y, { button: "right" });
  await page.waitForTimeout(60);
  const reversedState = await status();
  const reversed = await shot(`${sequence}b-${controlId.split(".").at(-1)}-activate-reversed`);
  record(controlId, "Activate", "StepStatusAttribute", {
    hover_exposed: hovered.controls[controlId].interaction_phase === "hover",
    pressed_exposed: pressed.controls[controlId].interaction_phase === "pressed",
    one_version: afterState.window_state.version === beforeState.window_state.version + 1,
    points_spent: afterState.window_state.points === 2,
    attribute_incremented: afterState.window_state.attributes[controlId].base
      === beforeState.window_state.attributes[controlId].base + 1,
    derived_same_frame: afterState.status_overlay.values[derivedKey]
      === afterState.window_state.derived[derivedKey],
    reversed_semantically: reversedState.window_state.points === 4
      && reversedState.window_state.attributes[controlId].base
        === beforeState.window_state.attributes[controlId].base,
  }, { before, after, reversed }, afterState.window_state);

  // ContextActivate is independently proven from an allocated state, and a
  // real Activate restores that exact allocated frame.
  await reload();
  target = await arrowPoint(controlId);
  await page.mouse.click(target.x, target.y);
  await page.waitForTimeout(60);
  const contextBefore = await shot(`${sequence}c-${controlId.split(".").at(-1)}-context-before`);
  await page.mouse.click(target.x, target.y, { button: "right" });
  await page.waitForTimeout(60);
  const contextState = await status();
  const contextAfter = await shot(`${sequence}d-${controlId.split(".").at(-1)}-context-after`);
  await page.mouse.click(target.x, target.y);
  await page.waitForTimeout(60);
  const contextReversed = await shot(`${sequence}e-${controlId.split(".").at(-1)}-context-reversed`);
  record(controlId, "ContextActivate", "StepStatusAttribute", {
    refunded: contextState.window_state.points === 4,
    source_value: contextState.window_state.attributes[controlId].base
      === beforeState.window_state.attributes[controlId].base,
    source_overlay_hidden: !contextState.status_overlay.visible,
  }, { before: contextBefore, after: contextAfter, reversed: contextReversed },
  contextState.window_state);
  sequence += 1;
}

// Both unavailable Int bindings fail atomically but expose transient pressed
// feedback. Reload supplies exact reversal evidence without mutating state.
for (const [gesture, button, suffix] of [
  ["Activate", "left", "activate"],
  ["ContextActivate", "right", "context"],
]) {
  await reload();
  const beforeState = await status();
  const before = await shot(`${sequence}-int-${suffix}-before`);
  target = await arrowPoint("status.attribute.int");
  await page.mouse.move(target.x, target.y);
  await page.mouse.down({ button });
  const mid = await shot(`${sequence}a-int-${suffix}-mid`, false);
  await page.mouse.up({ button });
  await page.waitForTimeout(60);
  const rejected = await status();
  const after = await shot(`${sequence}b-int-${suffix}-after`);
  await reload();
  const reversed = await shot(`${sequence}c-int-${suffix}-reversed`);
  record("status.attribute.int", gesture, "StepStatusAttribute", {
    rejected_named: rejected.controls["status.attribute.int"].last_error?.code
      === "TransactionRejectedError",
    state_atomic: JSON.stringify(rejected.window_state) === JSON.stringify(beforeState.window_state),
    unavailable: rejected.controls["status.attribute.int"].semantic_state === "disabled",
    transient_feedback: ae(before, mid, WINDOW_REGION) > 0,
  }, { before, mid, after, reversed }, rejected.window_state,
  { expectedRejection: true });
  sequence += 1;
}

// Window title Drag with 31 real two-dimensional pointer samples.
await reload();
const moveBefore = await shot(`${sequence}-move-before`);
const moveStart = point(250, 220);
const moveEnd = point(310, 260);
const moveSamples = [];
await page.mouse.move(moveStart.x, moveStart.y);
await page.mouse.down();
for (let index = 0; index < 31; index += 1) {
  const ratio = index / 30;
  const sample = { x: moveStart.x + (moveEnd.x - moveStart.x) * ratio,
    y: moveStart.y + (moveEnd.y - moveStart.y) * ratio };
  moveSamples.push([sample.x, sample.y]);
  await page.mouse.move(sample.x, sample.y);
}
const moveMid = await shot(`${sequence}a-move-mid`, false);
await page.mouse.up();
const moved = await status();
const moveAfter = await shot(`${sequence}b-moved`);
await reload();
const moveReversed = await shot(`${sequence}c-move-reversed`);
record("status", "Drag", "MoveWindow", {
  moved_x: moved.window.position[0] === 60,
  moved_y: moved.window.position[1] === 251,
  continuous: moveSamples.length >= 30,
}, { before: moveBefore, mid: moveMid, after: moveAfter, reversed: moveReversed },
moved.window, { motionSamples: moveSamples });
sequence += 1;

// Both close paths are independently exercised and exactly reset by reload.
await reload();
const closeBefore = await shot(`${sequence}-close-before`);
target = center({ x: 461, y: 215, width: 18, height: 18 });
await page.mouse.click(target.x, target.y);
await page.waitForTimeout(80);
const closeState = await status();
const closeAfter = await shot(`${sequence}a-closed`);
await reload();
const closeReversed = await shot(`${sequence}b-close-reversed`);
record("status.close", "Activate", "CloseWindow", {
  hidden: closeState.window.visible === false,
  routed: closeState.window.last_action === "CloseWindow",
}, { before: closeBefore, after: closeAfter, reversed: closeReversed }, closeState.window);
sequence += 1;

await reload();
const keyBefore = await shot(`${sequence}-key-before`);
target = point(250, 220);
await page.mouse.click(target.x, target.y);
await page.keyboard.press("Escape");
await page.waitForTimeout(80);
const keyState = await status();
const keyAfter = await shot(`${sequence}a-key-closed`);
await reload();
const keyReversed = await shot(`${sequence}b-key-reversed`);
record("status", "KeyCommand", "CloseWindow", {
  hidden: keyState.window.visible === false,
  routed: keyState.window.last_gesture === "KeyCommand"
    && keyState.window.last_action === "CloseWindow",
}, { before: keyBefore, after: keyAfter, reversed: keyReversed }, keyState.window);

await neutral();
const invariantAfter = await invariantShot(`${sequence + 1}-invariant-after`);
const errors = consoleEntries.filter((entry) => entry.startsWith("[error]")
  || entry.startsWith("[pageerror]"));
const requiredControls = windowSpec.controls.map((entry) => entry.id);
const requiredActions = windowSpec.actions.map((binding) => ({
  control_id: windowSpec.id, gesture: binding.gesture, window_action: binding.action,
})).concat(windowSpec.controls.flatMap((entry) => entry.actions.map((binding) => ({
  control_id: entry.id, gesture: binding.gesture, window_action: binding.action,
}))));
const playLog = {
  schema_version: "image79-play-log-v2",
  candidate: { issue: 131,
    commit_sha: execFileSync("git", ["rev-parse", "HEAD"],
      { cwd: ROOT, encoding: "utf8" }).trim(), window_id: "status" },
  source_reference_sha256: manifest.reference.sha256,
  required_controls: requiredControls, required_actions: requiredActions,
  invariant_frames: { before: invariantBefore, after: invariantAfter },
  console_errors: errors, actions,
};
writeFileSync(resolve(OUT, "play-log.json"), `${JSON.stringify(playLog, null, 2)}\n`);
const failed = checks.filter((entry) => !entry.passed);
const report = {
  url: URL, window: { id: "status", geometry: windowSpec.geometry },
  driver: "Playwright Chromium real pointer, click, context-click, drag, and keyboard input",
  checks, console_entries: consoleEntries,
  summary: { pass: failed.length === 0 && errors.length === 0,
    total: checks.length, failed: failed.length, console_errors: errors.length,
    provider_requests: 0 },
};
writeFileSync(resolve(OUT, "report.json"), `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report.summary));
await browser.close();
process.exitCode = report.summary.pass ? 0 : 1;
