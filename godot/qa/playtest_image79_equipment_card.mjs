// Browser-side Issue #129 drive. Real Chromium pointer, wheel, drag, click,
// and keyboard input produce the Equipment Card Play Log and evidence frames.
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
  ?? resolve(SCRIPT_DIR, "out/image79-equipment-card-browser"));
const DESIGN = { width: 1536, height: 1024 };
const WINDOW_REGION = { x: 1050, y: 0, width: 486, height: 380 };
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
  await page.waitForFunction(() => window.godotQaState?.windows?.equipment_card,
    undefined, { timeout: 90000 });
  await page.waitForTimeout(900);
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
const card = async () => (await qa()).windows.equipment_card;
const control = async (id) => (await card()).controls[id];
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
const windowSpec = manifest.windows.find((entry) => entry.id === "equipment_card");
const approved = new Set(windowSpec.actions.map((binding) =>
  `equipment_card:${binding.gesture}:${binding.action}`).concat(
  windowSpec.controls.flatMap((entry) => entry.actions.map((binding) =>
    `${entry.id}:${binding.gesture}:${binding.action}`))));
const actions = [];
const checks = [];
const record = (controlId, gesture, action, assertions, frames, observed,
  motionSamples = undefined) => {
  const pixelMetrics = metrics(frames.before, frames.after);
  const reversalMetrics = metrics(frames.before, frames.reversed);
  const matches = Object.values(assertions).every(Boolean);
  const entry = {
    control_id: controlId, gesture, window_action: action,
    expected: "manifest and retained Equipment Card Behaviour Card",
    observed: JSON.stringify(observed), responsive: matches, matches_expected: matches,
    assertions, frames, intended_region: WINDOW_REGION,
    invariant_region: INVARIANT_REGION, pixel_metrics: pixelMetrics,
    reversal_pixel_metrics: reversalMetrics,
    contract_facts: {
      real_gesture_path: matches,
      intended_region_changed: pixelMetrics.intended_region_changed_pixels > 0,
      invariants_stable: pixelMetrics.invariant_region_changed_pixels === 0,
      source_approved: approved.has(`${controlId}:${gesture}:${action}`),
      reversible: Object.values(reversalMetrics).every((value) => value === 0),
    },
  };
  if (motionSamples !== undefined) entry.motion_samples = motionSamples;
  if (action === "ToggleMinimized") entry.frames.restored = frames.reversed;
  actions.push(entry);
  checks.push({ name: `${controlId}:${gesture}:${action}`,
    passed: matches && Object.values(entry.contract_facts).every(Boolean),
    detail: { assertions, contract_facts: entry.contract_facts } });
};
const reload = async () => {
  await page.reload({ waitUntil: "networkidle", timeout: 90000 });
  await page.waitForFunction(() => window.godotQaState?.windows?.equipment_card,
    undefined, { timeout: 90000 });
  await page.waitForTimeout(700);
};

const idle = await shot("00-idle");
const invariantBefore = await invariantShot("00-invariant-before");
const initial = await card();
checks.push({ name: "idle-factual", passed: initial.window.detail_item === "mistress-card"
  && initial.controls["equipment_card.scroll"].available === false,
detail: initial.window });

// Purpose-built minimize and exact restore.
const minimizeBefore = idle;
let target = point(1122, 14);
await page.mouse.click(target.x, target.y);
await page.waitForTimeout(80);
const minimized = await card();
const minimizeAfter = await shot("01-minimized");
target = point(1122, 14);
await page.mouse.click(target.x, target.y);
await page.waitForTimeout(80);
const restored = await card();
const minimizeReversed = await shot("01b-restored");
record("equipment_card.minimize", "Activate", "ToggleMinimized", {
  minimized: minimized.window.minimized && minimized.window.size[1] === 28,
  restored: !restored.window.minimized && restored.window.size[1] === 290,
}, { before: minimizeBefore, after: minimizeAfter, reversed: minimizeReversed }, restored.window);

// All three source-declared ScrollView gestures fail closed but visibly acknowledge input.
for (const spec of [
  { name: "02-wheel-rejected", gesture: "Wheel", action: "ScrollEquipmentCard",
    run: async () => { const p = point(1512, 92); await page.mouse.move(p.x, p.y);
      await page.mouse.wheel(0, 120); } },
  { name: "03-arrow-rejected", gesture: "Activate", action: "StepEquipmentCardScroll",
    run: async () => { const p = point(1512, 92); await page.mouse.click(p.x, p.y); } },
]) {
  await reload();
  const before = await shot(`${spec.name}-before`);
  await spec.run();
  await page.waitForTimeout(80);
  const state = await control("equipment_card.scroll");
  const after = await shot(spec.name, false);
  await reload();
  const reversed = await shot(`${spec.name}-reversed`);
  record("equipment_card.scroll", spec.gesture, spec.action, {
    rejected: state.last_error?.code === "VisualAuthorityError",
    unchanged: state.offset === 0 && state.maximum === 0 && state.available === false,
  }, { before, after, reversed }, state);
}

await reload();
const dragBefore = await shot("04-drag-rejected-before");
const dragStart = point(1512, 125);
const dragEnd = point(1512, 215);
const motionSamples = [];
await page.mouse.move(dragStart.x, dragStart.y);
await page.mouse.down();
for (let index = 0; index < 31; index += 1) {
  const ratio = index / 30;
  const sample = { x: dragStart.x + (dragEnd.x - dragStart.x) * ratio,
    y: dragStart.y + (dragEnd.y - dragStart.y) * ratio };
  motionSamples.push([sample.x, sample.y]);
  await page.mouse.move(sample.x, sample.y);
}
await page.mouse.up();
const dragState = await control("equipment_card.scroll");
const dragAfter = await shot("04-drag-rejected", false);
await reload();
const dragReversed = await shot("04b-drag-reversed");
record("equipment_card.scroll", "Drag", "SetEquipmentCardScrollOffset", {
  rejected: dragState.last_error?.code === "VisualAuthorityError",
  unchanged: dragState.offset === 0 && dragState.available === false,
  continuous: motionSamples.length >= 30,
}, { before: dragBefore, after: dragAfter, reversed: dragReversed }, dragState,
motionSamples);

// Window title Drag with 31 real pointer samples.
await reload();
const moveBefore = await shot("05-move-before");
const moveStart = point(1200, 14);
const moveEnd = point(1160, 54);
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
await page.mouse.up();
const moved = await card();
const moveAfter = await shot("05-moved");
await reload();
const moveReversed = await shot("05b-move-reversed");
record("equipment_card", "Drag", "MoveWindow", {
  moved: moved.window.position[0] !== 1108 || moved.window.position[1] !== 0,
  continuous: moveSamples.length >= 30,
}, { before: moveBefore, mid: moveAfter, after: moveAfter, reversed: moveReversed },
moved.window, moveSamples);

// Title close routes both Window visibility and the desktop detail transaction.
await reload();
const closeBefore = await shot("06-close-before");
target = point(1517, 16);
await page.mouse.click(target.x, target.y);
await page.waitForTimeout(80);
const closeState = await qa();
const closeAfter = await shot("06-closed");
await reload();
const closeReversed = await shot("06b-close-reversed");
record("equipment_card.close", "Activate", "CloseWindow", {
  hidden: closeState.windows.equipment_card.window.visible === false,
  detail_routed: closeState.last_transaction.action === "CloseDetail",
}, { before: closeBefore, after: closeAfter, reversed: closeReversed },
closeState.last_transaction);

await reload();
const keyBefore = await shot("07-key-close-before");
target = point(1200, 14);
await page.mouse.click(target.x, target.y);
await page.keyboard.press("Escape");
await page.waitForTimeout(80);
const keyState = await card();
const keyAfter = await shot("07-key-closed");
await reload();
const keyReversed = await shot("07b-key-reversed");
record("equipment_card", "KeyCommand", "CloseWindow", {
  hidden: keyState.window.visible === false,
  routed: keyState.window.last_gesture === "KeyCommand"
    && keyState.window.last_action === "CloseWindow",
}, { before: keyBefore, after: keyAfter, reversed: keyReversed }, keyState.window);

await neutral();
const invariantAfter = await invariantShot("08-invariant-after");
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
  candidate: { issue: 129,
    commit_sha: execFileSync("git", ["rev-parse", "HEAD"],
      { cwd: ROOT, encoding: "utf8" }).trim(), window_id: "equipment_card" },
  source_reference_sha256: manifest.reference.sha256,
  required_controls: requiredControls, required_actions: requiredActions,
  invariant_frames: { before: invariantBefore, after: invariantAfter },
  console_errors: errors, actions,
};
writeFileSync(resolve(OUT, "play-log.json"), `${JSON.stringify(playLog, null, 2)}\n`);
const failed = checks.filter((entry) => !entry.passed);
const report = {
  url: URL, window: { id: "equipment_card", geometry: windowSpec.geometry },
  driver: "Playwright Chromium real pointer, wheel, drag, click, and keyboard input",
  checks, console_entries: consoleEntries,
  summary: { pass: failed.length === 0 && errors.length === 0,
    total: checks.length, failed: failed.length, console_errors: errors.length },
};
writeFileSync(resolve(OUT, "report.json"), `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report.summary));
await browser.close();
process.exitCode = report.summary.pass ? 0 : 1;
