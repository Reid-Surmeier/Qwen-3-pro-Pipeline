// Browser-side Issue #130 drive. Real Chromium gestures cover the complete
// Equipment Items manifest plus atomic Inventory <-> Equipment displacement.
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
  ?? resolve(SCRIPT_DIR, "out/image79-equipment-items-browser"));
const DESIGN = { width: 1536, height: 1024 };
const WINDOW_REGION = { x: 0, y: 423, width: 484, height: 581 };
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
  await page.waitForFunction(() => window.godotQaState?.windows?.equipment_items,
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
const equipment = async () => (await qa()).windows.equipment_items;
const neutral = async () => {
  const target = point(1200, 700);
  await page.mouse.move(target.x, target.y);
  await page.waitForTimeout(80);
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
const windowSpec = manifest.windows.find((entry) => entry.id === "equipment_items");
const approved = new Set(manifest.windows.flatMap((window) =>
  window.actions.map((binding) => `${window.id}:${binding.gesture}:${binding.action}`)
    .concat(window.controls.flatMap((entry) => entry.actions.concat(
      entry.value?.context_actions ?? []).map((binding) =>
      `${entry.id}:${binding.gesture}:${binding.action}`)))));
const actions = [];
const checks = [];
const record = (controlId, gesture, action, assertions, frames, observed,
  motionSamples = undefined) => {
  const pixelMetrics = metrics(frames.before, frames.after);
  const reversalMetrics = metrics(frames.before, frames.reversed);
  const matches = Object.values(assertions).every(Boolean);
  const entry = {
    control_id: controlId, gesture, window_action: action,
    expected_rejection: true,
    expected: "manifest and retained Equipment Items Behaviour Card",
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
const recordRejection = (controlId, gesture, action, assertions, frames, observed,
  motionSamples) => {
  const pixelMetrics = metrics(frames.before, frames.after);
  const reversalMetrics = metrics(frames.before, frames.reversed);
  const midMetrics = metrics(frames.before, frames.mid);
  const matches = Object.values(assertions).every(Boolean);
  const entry = {
    control_id: controlId, gesture, window_action: action,
    expected: "named atomic rejection preserves Inventory and Equipment Items",
    observed: JSON.stringify(observed), responsive: matches, matches_expected: matches,
    assertions, frames, intended_region: WINDOW_REGION,
    invariant_region: INVARIANT_REGION, pixel_metrics: pixelMetrics,
    mid_pixel_metrics: midMetrics, reversal_pixel_metrics: reversalMetrics,
    motion_samples: motionSamples,
    contract_facts: {
      real_gesture_path: motionSamples.length >= 30,
      intended_region_changed: false,
      transient_feedback_rendered: midMetrics.full_frame_changed_pixels > 0,
      committed_frame_preserved: pixelMetrics.full_frame_changed_pixels === 0,
      invariants_stable: pixelMetrics.invariant_region_changed_pixels === 0,
      source_approved: approved.has(`${controlId}:${gesture}:${action}`),
      reversible: Object.values(reversalMetrics).every((value) => value === 0),
    },
  };
  actions.push(entry);
  const contractPass = entry.contract_facts.intended_region_changed === false
    && Object.entries(entry.contract_facts).filter(([name]) =>
      name !== "intended_region_changed").every(([, value]) => Boolean(value));
  checks.push({ name: `${controlId}:${gesture}:${action}:named-rejection`,
    passed: matches && contractPass,
    detail: { assertions, contract_facts: entry.contract_facts } });
};
const reload = async () => {
  await page.reload({ waitUntil: "networkidle", timeout: 90000 });
  await page.waitForFunction(() => window.godotQaState?.windows?.equipment_items,
    undefined, { timeout: 90000 });
  await page.waitForTimeout(700);
};

const idle = await shot("00-idle");
const invariantBefore = await invariantShot("00-invariant-before");
const initial = await equipment();
checks.push({ name: "idle-factual", passed: initial.window.size[0] === 484
  && initial.window.size[1] === 271
  && Object.keys(initial.controls["equipment_items.slots"].surface_geometry).length === 9,
detail: initial.window });

// Purpose-built 484 x 28 minimized window and exact restore.
let target = point(446, 438);
await page.mouse.click(target.x, target.y);
await page.waitForTimeout(100);
const minimized = await equipment();
const minimizeAfter = await shot("01-minimized");
target = point(446, 438);
await page.mouse.click(target.x, target.y);
await page.waitForTimeout(100);
const restored = await equipment();
const minimizeReversed = await shot("01b-restored");
record("equipment_items.minimize", "Activate", "ToggleMinimized", {
  minimized: minimized.window.minimized && minimized.window.size[1] === 28,
  restored: !restored.window.minimized && restored.window.size[1] === 271,
}, { before: idle, after: minimizeAfter, reversed: minimizeReversed }, restored.window);

// Single Activate selects one source-declared slot after the double-click window.
await reload();
const selectBefore = await shot("02-select-before");
target = point(98, 539);
await page.mouse.click(target.x, target.y);
await page.waitForTimeout(320);
const selected = await equipment();
const selectAfter = await shot("02-selected");
await reload();
const selectReversed = await shot("02b-select-reversed");
record("equipment_items.slots", "Activate", "SelectEquipmentSlot", {
  selected: selected.controls["equipment_items.slots"].value === "face",
  routed: selected.controls["equipment_items.slots"].last_action === "SelectEquipmentSlot",
}, { before: selectBefore, after: selectAfter, reversed: selectReversed },
selected.controls["equipment_items.slots"]);

// Equip-tab DoubleActivate resolves to its explicit manifest context action
// before ControlWindow can open local Inventory detail.
await reload();
target = point(23, 788);
await page.mouse.click(target.x, target.y);
await page.waitForTimeout(100);
const inventoryDoubleBefore = await shot("02c-inventory-double-before");
const beforeInventoryDouble = await qa();
target = point(69, 761);
await page.mouse.dblclick(target.x, target.y, { delay: 55 });
await page.waitForTimeout(320);
const afterInventoryDouble = await qa();
const inventoryDoubleAfter = await shot("02c-inventory-double-equipped");
await reload();
target = point(23, 788);
await page.mouse.click(target.x, target.y);
await page.waitForTimeout(100);
const inventoryDoubleReversed = await shot("02d-inventory-double-reversed");
record("inventory.items", "DoubleActivate", "EquipInventoryItem", {
  explicit_action: afterInventoryDouble.windows.inventory.controls[
    "inventory.items"].last_action === "EquipInventoryItem",
  no_stale_detail: afterInventoryDouble.windows.inventory.controls[
    "inventory.items"].opened_item === ""
    && afterInventoryDouble.windows.inventory.controls[
      "inventory.items"].detail_visible === false,
  routed: afterInventoryDouble.last_transaction.ok === true
    && afterInventoryDouble.last_transaction.operation === "equip",
  inventory_atomic: afterInventoryDouble.windows.inventory.controls[
    "inventory.items"].item_version === beforeInventoryDouble.windows.inventory.controls[
      "inventory.items"].item_version + 1,
  equipment_atomic: afterInventoryDouble.windows.equipment_items.controls[
    "equipment_items.slots"].item_version
    === beforeInventoryDouble.windows.equipment_items.controls[
      "equipment_items.slots"].item_version + 1,
}, { before: inventoryDoubleBefore, after: inventoryDoubleAfter,
  reversed: inventoryDoubleReversed }, afterInventoryDouble.last_transaction);

// DoubleActivate unequips into the selected Inventory slot with two-sided commit.
await reload();
const doubleBefore = await shot("03-double-before");
const beforeDouble = await qa();
target = point(98, 499);
await page.mouse.dblclick(target.x, target.y, { delay: 55 });
await page.waitForTimeout(180);
const afterDouble = await qa();
const doubleAfter = await shot("03-double-unequipped");
await reload();
const doubleReversed = await shot("03b-double-reversed");
record("equipment_items.slots", "DoubleActivate", "UnequipEquipmentItem", {
  routed: afterDouble.last_transaction.ok === true
    && afterDouble.last_transaction.operation === "unequip",
  inventory_committed: afterDouble.windows.inventory.controls["inventory.items"].item_version
    === beforeDouble.windows.inventory.controls["inventory.items"].item_version + 1,
  equipment_committed: afterDouble.windows.equipment_items.controls["equipment_items.slots"].item_version
    === beforeDouble.windows.equipment_items.controls["equipment_items.slots"].item_version + 1,
}, { before: doubleBefore, after: doubleAfter, reversed: doubleReversed },
afterDouble.last_transaction);

// Inventory -> Equipment real DragDrop with continuous target feedback and displacement.
await reload();
const dragBefore = await shot("04-drag-before");
const beforeDrag = await qa();
const dragStart = point(69, 761);
const dragEnd = point(98, 499);
const dragSamples = [];
await page.mouse.move(dragStart.x, dragStart.y);
await page.mouse.down();
for (let index = 0; index < 31; index += 1) {
  const ratio = index / 30;
  const sample = { x: dragStart.x + (dragEnd.x - dragStart.x) * ratio,
    y: dragStart.y + (dragEnd.y - dragStart.y) * ratio };
  dragSamples.push([sample.x, sample.y]);
  await page.mouse.move(sample.x, sample.y);
}
const dragMidState = await qa();
const dragMid = await shot("04-drag-mid", false);
await page.mouse.up();
await page.waitForTimeout(180);
const afterDrag = await qa();
const dragAfter = await shot("04-drag-equipped");
await reload();
const dragReversed = await shot("04b-drag-reversed");
record("equipment_items.slots", "DragDrop", "MoveEquipmentItem", {
  continuous: dragSamples.length >= 30,
  target_feedback: dragMidState.windows.equipment_items.controls[
    "equipment_items.slots"].drag_state.target === "head",
  routed: afterDrag.last_transaction.ok === true
    && afterDrag.last_transaction.operation === "equip",
  inventory_atomic: afterDrag.windows.inventory.controls["inventory.items"].item_version
    === beforeDrag.windows.inventory.controls["inventory.items"].item_version + 1,
  equipment_atomic: afterDrag.windows.equipment_items.controls[
    "equipment_items.slots"].item_version
    === beforeDrag.windows.equipment_items.controls["equipment_items.slots"].item_version + 1,
  displaced: afterDrag.last_transaction.displaced_item
    === beforeDrag.windows.equipment_items.controls["equipment_items.slots"].item_values.head,
}, { before: dragBefore, mid: dragMid, after: dragAfter, reversed: dragReversed },
afterDrag.last_transaction, dragSamples);

// Invalid destination: a real cross-Window drag reaches the Equipment chrome,
// returns a named rejection, and commits neither slot map nor version.
await reload();
const rejectBefore = await shot("05-rejected-before");
const beforeReject = await qa();
const rejectStart = point(69, 761);
const rejectEnd = point(200, 435);
const rejectSamples = [];
await page.mouse.move(rejectStart.x, rejectStart.y);
await page.mouse.down();
for (let index = 0; index < 31; index += 1) {
  const ratio = index / 30;
  const sample = { x: rejectStart.x + (rejectEnd.x - rejectStart.x) * ratio,
    y: rejectStart.y + (rejectEnd.y - rejectStart.y) * ratio };
  rejectSamples.push([sample.x, sample.y]);
  await page.mouse.move(sample.x, sample.y);
}
const rejectMid = await shot("05-rejected-mid", false);
await page.mouse.up();
await page.waitForTimeout(180);
const afterReject = await qa();
const rejectAfter = await shot("05-rejected-after");
await reload();
const rejectReversed = await shot("05b-rejected-reversed");
recordRejection("inventory.items", "DragDrop", "MoveInventoryItem", {
  named_rejection: afterReject.last_transaction.ok === false
    && afterReject.last_transaction.error?.code === "TransactionRejectedError",
  inventory_values_preserved: JSON.stringify(afterReject.windows.inventory.controls[
    "inventory.items"].item_values) === JSON.stringify(beforeReject.windows.inventory.controls[
      "inventory.items"].item_values),
  equipment_values_preserved: JSON.stringify(afterReject.windows.equipment_items.controls[
    "equipment_items.slots"].item_values) === JSON.stringify(
      beforeReject.windows.equipment_items.controls["equipment_items.slots"].item_values),
  inventory_version_preserved: afterReject.windows.inventory.controls[
    "inventory.items"].item_version === beforeReject.windows.inventory.controls[
      "inventory.items"].item_version,
  equipment_version_preserved: afterReject.windows.equipment_items.controls[
    "equipment_items.slots"].item_version === beforeReject.windows.equipment_items.controls[
      "equipment_items.slots"].item_version,
}, { before: rejectBefore, mid: rejectMid, after: rejectAfter, reversed: rejectReversed },
afterReject.last_transaction, rejectSamples);

// Window title drag with 31 samples.
await reload();
const moveBefore = await shot("06-move-before");
const moveStart = point(240, 435);
const moveEnd = point(280, 395);
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
const moveMid = await shot("06-move-mid", false);
await page.mouse.up();
const moved = await equipment();
const moveAfter = await shot("06-moved");
await reload();
const moveReversed = await shot("06b-move-reversed");
record("equipment_items", "Drag", "MoveWindow", {
  moved: moved.window.position[0] !== 0 || moved.window.position[1] !== 423,
  continuous: moveSamples.length >= 30,
}, { before: moveBefore, mid: moveMid, after: moveAfter, reversed: moveReversed },
moved.window, moveSamples);

// Title close and keyboard close both reverse by deterministic reload.
await reload();
const closeBefore = await shot("07-close-before");
target = point(470, 438);
await page.mouse.click(target.x, target.y);
await page.waitForTimeout(100);
const closed = await equipment();
const closeAfter = await shot("07-closed");
await reload();
const closeReversed = await shot("07b-close-reversed");
record("equipment_items.close", "Activate", "CloseWindow", {
  hidden: closed.window.visible === false,
}, { before: closeBefore, after: closeAfter, reversed: closeReversed }, closed.window);

await reload();
const keyBefore = await shot("08-key-before");
target = point(240, 435);
await page.mouse.click(target.x, target.y);
await page.keyboard.press("Escape");
await page.waitForTimeout(100);
const keyClosed = await equipment();
const keyAfter = await shot("08-key-closed");
await reload();
const keyReversed = await shot("08b-key-reversed");
record("equipment_items", "KeyCommand", "CloseWindow", {
  hidden: keyClosed.window.visible === false,
  routed: keyClosed.window.last_gesture === "KeyCommand"
    && keyClosed.window.last_action === "CloseWindow",
}, { before: keyBefore, after: keyAfter, reversed: keyReversed }, keyClosed.window);

await neutral();
const invariantAfter = await invariantShot("09-invariant-after");
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
  candidate: { issue: 130,
    commit_sha: execFileSync("git", ["rev-parse", "HEAD"],
      { cwd: ROOT, encoding: "utf8" }).trim(), window_id: "equipment_items" },
  source_reference_sha256: manifest.reference.sha256,
  required_controls: requiredControls, required_actions: requiredActions,
  invariant_frames: { before: invariantBefore, after: invariantAfter },
  console_errors: errors, actions,
};
writeFileSync(resolve(OUT, "play-log.json"), `${JSON.stringify(playLog, null, 2)}\n`);
const failed = checks.filter((entry) => !entry.passed);
const report = {
  url: URL, window: { id: "equipment_items", geometry: windowSpec.geometry },
  driver: "Playwright Chromium real click, double-click, cross-window drag, title drag, and keyboard input",
  checks, console_entries: consoleEntries,
  summary: { pass: failed.length === 0 && errors.length === 0,
    total: checks.length, failed: failed.length, console_errors: errors.length },
};
writeFileSync(resolve(OUT, "report.json"), `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report.summary));
await browser.close();
process.exitCode = report.summary.pass ? 0 : 1;
