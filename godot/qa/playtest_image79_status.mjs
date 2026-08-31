// Browser-side Issue #131 drive. Real Chromium gestures prove conditional
// Status allocation, rejection, reversal, and Window behavior.
import { createRequire } from "node:module";
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, unlinkSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(SCRIPT_DIR, "../..");
const require = createRequire(`${process.env.PLAYWRIGHT_NODE_MODULES
  ?? resolve(SCRIPT_DIR, "browser/node_modules")}/`);
const { chromium } = require("playwright");
const URL = process.env.IMAGE79_URL ?? "http://127.0.0.1:8877/?screen=image79";
const OUT = resolve(process.env.IMAGE79_PLAYTEST_OUT
  ?? resolve(SCRIPT_DIR, "out/image79-status-browser"));
const DESIGN = { width: 1536, height: 1024 };
const WINDOW = { x: 0, y: 211, width: 484, height: 208 };
const INVARIANT = { x: 1400, y: 800, width: 100, height: 100 };
mkdirSync(OUT, { recursive: true });

const sha256 = (path) => createHash("sha256").update(readFileSync(path)).digest("hex");
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: DESIGN });
const consoleEntries = [];
page.on("console", (message) => {
	if (message.type() === "error")
    consoleEntries.push(`[${message.type()}] ${message.text()}`.slice(0, 1000));
});
page.on("pageerror", (error) => consoleEntries.push(`[pageerror] ${String(error)}`.slice(0, 1000)));

const load = async () => {
  await page.goto(URL, { waitUntil: "networkidle", timeout: 90000 });
  await page.waitForFunction(() => window.godotQaState?.windows?.status,
    undefined, { timeout: 90000 });
  await page.waitForTimeout(900);
};
await load();
const canvas = await page.evaluate(() => {
  const rect = document.querySelector("canvas").getBoundingClientRect();
  return { width: rect.width, height: rect.height, x: rect.x, y: rect.y };
});
const scale = Math.min(canvas.width / DESIGN.width, canvas.height / DESIGN.height);
const offsetX = canvas.x + (canvas.width - DESIGN.width * scale) / 2;
const offsetY = canvas.y + (canvas.height - DESIGN.height * scale) / 2;
const point = (x, y) => ({ x: offsetX + x * scale, y: offsetY + y * scale });
const qa = () => page.evaluate(() => window.godotQaState);
const status = async () => (await qa()).windows.status;
const neutral = async () => {
  const target = point(1200, 700);
  await page.mouse.move(target.x, target.y);
  await page.waitForTimeout(60);
};
const shot = async (name) => {
  await neutral();
  const path = resolve(OUT, `${name}.png`);
  await page.screenshot({ path });
  return { path: `${name}.png`, sha256: sha256(path) };
};
const ae = (left, right, crop) => {
  const geometry = `${crop.width}x${crop.height}+${crop.x}+${crop.y}`;
  const temporary = [resolve(OUT, `.left-${process.pid}.png`),
    resolve(OUT, `.right-${process.pid}.png`)];
  for (const [input, output] of [[left, temporary[0]], [right, temporary[1]]]) {
    const result = spawnSync("convert", [resolve(OUT, input.path), "-crop", geometry,
      "+repage", output], { encoding: "utf8" });
    if (result.status !== 0) throw new Error(result.stderr || "ImageMagick crop failed");
  }
  const result = spawnSync("compare", ["-metric", "AE", temporary[0], temporary[1],
    "null:"], { encoding: "utf8" });
  temporary.forEach((path) => unlinkSync(path));
  return Number(`${result.stderr ?? ""}${result.stdout ?? ""}`.trim());
};
const metrics = (before, after) => ({
  intended_region_changed_pixels: ae(before, after, WINDOW),
  invariant_region_changed_pixels: ae(before, after, INVARIANT),
});
const manifest = JSON.parse(readFileSync(resolve(ROOT,
  "godot/data/image-79-control-spec.json"), "utf8"));
const approved = new Set(manifest.windows.flatMap((window) =>
  window.actions.concat(window.controls.flatMap((control) => control.actions))
    .map((binding) => `${binding.gesture}:${binding.action}`)));
const actions = [];
const checks = [];
const record = (controlId, gesture, action, assertions, frames, observed) => {
  const pixelMetrics = metrics(frames.before, frames.after);
  const passed = Object.values(assertions).every(Boolean)
    && pixelMetrics.invariant_region_changed_pixels === 0
    && approved.has(`${gesture}:${action}`);
  actions.push({ control_id: controlId, gesture, window_action: action,
    expected: "Status Behaviour Card and manifest", observed: JSON.stringify(observed),
    responsive: passed, matches_expected: passed, assertions, frames,
    intended_region: WINDOW, invariant_region: INVARIANT, pixel_metrics: pixelMetrics,
    contract_facts: { real_gesture_path: Object.values(assertions).every(Boolean),
      invariants_stable: pixelMetrics.invariant_region_changed_pixels === 0,
      source_approved: approved.has(`${gesture}:${action}`) } });
  checks.push({ name: `${controlId}:${gesture}:${action}`, passed,
    detail: { assertions, pixelMetrics } });
};

const idle = await shot("00-idle");
const arrowGeometry = (await status()).controls["status.attribute.str"].surface_geometry.increment;
const arrow = point(arrowGeometry.x + arrowGeometry.width / 2,
  arrowGeometry.y + arrowGeometry.height / 2);
const beforeStep = await status();
await page.mouse.move(arrow.x, arrow.y);
const hovered = await status();
await page.mouse.down();
const pressed = await status();
await page.mouse.up();
const oneStep = await status();
const oneStepFrame = await shot("01-str-one-step");
record("status.attribute.str", "Activate", "StepStatusAttribute", {
  hover_exposed: hovered.controls["status.attribute.str"].interaction_phase === "hover",
  pressed_exposed: pressed.controls["status.attribute.str"].interaction_phase === "pressed",
  one_version: oneStep.window_state.version === beforeStep.window_state.version + 1,
  points_spent: oneStep.window_state.points === 2,
  derived_same_frame: oneStep.window_state.derived.Atk === 64,
  overlay_same_frame: oneStep.status_overlay.visible,
}, { before: idle, after: oneStepFrame }, oneStep.window_state);

await page.mouse.click(arrow.x, arrow.y);
const exhausted = await status();
const exhaustedFrame = await shot("02-str-exhausted");
await page.mouse.click(arrow.x, arrow.y);
const rejected = await status();
const rejectedFrame = await shot("03-str-rejected");
record("status.attribute.str", "Activate", "StepStatusAttribute", {
  two_steps_exhaust: exhausted.window_state.points === 0 && exhausted.window_state.version === 2,
  disabled_visual_state: exhausted.controls["status.attribute.str"].semantic_state === "disabled",
  rejected_named: rejected.controls["status.attribute.str"].last_error?.code === "TransactionRejectedError",
  rejected_atomic: JSON.stringify(rejected.window_state) === JSON.stringify(exhausted.window_state),
}, { before: exhaustedFrame, after: rejectedFrame }, rejected.window_state);

await page.mouse.click(arrow.x, arrow.y, { button: "right" });
const reversedOne = await status();
const reversedOneFrame = await shot("04-str-reversed-one");
record("status.attribute.str", "ContextActivate", "StepStatusAttribute", {
  refunded: reversedOne.window_state.points === 2,
  reversed_value: reversedOne.window_state.attributes["status.attribute.str"].base === 2,
  derived_reversed: reversedOne.window_state.derived.Atk === 64,
  available_again: reversedOne.controls["status.attribute.str"].semantic_state === "available",
}, { before: exhaustedFrame, after: reversedOneFrame }, reversedOne.window_state);
await page.mouse.click(arrow.x, arrow.y, { button: "right" });
const sourceAgain = await status();
const sourceFrame = await shot("05-source-restored");
checks.push({ name: "source-state-semantic-reversal", passed:
	sourceAgain.window_state.points === 4
	&& sourceAgain.window_state.attributes["status.attribute.str"].base === 1
	&& !sourceAgain.status_overlay.visible && ae(idle, sourceFrame, WINDOW) === 0,
	detail: { changed_pixels: ae(idle, sourceFrame, WINDOW), state: sourceAgain.window_state } });

const minimize = point(446, 226);
const beforeMinimize = await shot("06-before-minimize");
await page.mouse.click(minimize.x, minimize.y);
const minimized = await status();
const minimizedFrame = await shot("07-minimized");
await page.mouse.click(minimize.x, minimize.y);
const restored = await status();
const restoredFrame = await shot("08-minimize-restored");
record("status.minimize", "Activate", "ToggleMinimized", {
  purpose_built_height: minimized.window.size[1] === 28,
  restored_height: restored.window.size[1] === 208,
  semantic_state_preserved: restored.window_state.points === 4,
}, { before: beforeMinimize, after: minimizedFrame, reversed: restoredFrame }, restored.window);

const dragStart = point(250, 220);
const dragEnd = point(310, 260);
const beforeDrag = await shot("09-before-drag");
await page.mouse.move(dragStart.x, dragStart.y);
await page.mouse.down();
await page.mouse.move(dragEnd.x, dragEnd.y, { steps: 24 });
await page.mouse.up();
const moved = await status();
const movedFrame = await shot("10-dragged");
record("status", "Drag", "MoveWindow", {
  moved_x: moved.window.position[0] === 60,
  moved_y: moved.window.position[1] === 251,
}, { before: beforeDrag, after: movedFrame }, moved.window);

await page.keyboard.press("Escape");
const closed = await status();
const closedFrame = await shot("11-closed-by-key");
record("status", "KeyCommand", "CloseWindow", {
  closed: closed.window.visible === false,
}, { before: movedFrame, after: closedFrame }, closed.window);

const log = { schema_version: 1, issue: 131, candidate: "WORKTREE",
  reference_sha256: manifest.reference.sha256, window_id: "status",
  actions, checks, console_entries: consoleEntries,
  summary: { actions: actions.length, checks: checks.length,
    passed: checks.filter((entry) => entry.passed).length,
    failed: checks.filter((entry) => !entry.passed).length,
    console_errors: consoleEntries.length, provider_requests: 0 } };
writeFileSync(resolve(OUT, "play-log.json"), `${JSON.stringify(log, null, 2)}\n`);
await browser.close();
console.log(JSON.stringify(log.summary));
if (log.summary.failed || log.summary.console_errors) process.exitCode = 1;
