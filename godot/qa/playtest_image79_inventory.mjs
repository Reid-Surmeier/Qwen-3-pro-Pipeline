// Builder-side browser drive for issue #127. Exercises every declared
// Inventory Window Action with real pointer input and writes a v2 Play Log.
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(SCRIPT_DIR, "../..");
const playwrightModules = process.env.PLAYWRIGHT_NODE_MODULES
  ?? resolve(SCRIPT_DIR, "browser/node_modules");
const require = createRequire(`${playwrightModules}/`);
const { chromium } = require("playwright");

const URL = process.env.IMAGE79_URL ?? "http://127.0.0.1:8877/?screen=image79";
const DESIGN = { width: 1536, height: 1024 };
const OUT = resolve(process.env.IMAGE79_PLAYTEST_OUT
  ?? resolve(SCRIPT_DIR, "out/image79-inventory-browser"));
mkdirSync(OUT, { recursive: true });

const sha256 = (path) => createHash("sha256").update(readFileSync(path)).digest("hex");
const headedMesa = process.env.IMAGE79_HEADED_MESA === "1";
const browser = await chromium.launch(headedMesa ? {
  headless: false,
  executablePath: process.env.IMAGE79_CHROME_BIN ?? "/usr/bin/google-chrome-stable",
  args: ["--use-gl=desktop", "--disable-gpu-sandbox"],
} : { headless: true });
const page = await browser.newPage({ viewport: DESIGN });
const consoleEntries = [];
page.on("console", (message) => {
  if (["warning", "error"].includes(message.type())) {
    consoleEntries.push(`[${message.type()}] ${message.text()}`.slice(0, 1000));
  }
});
page.on("pageerror", (error) => consoleEntries.push(`[pageerror] ${String(error)}`.slice(0, 1000)));
await page.goto(URL, { waitUntil: "networkidle", timeout: 90000 });
await page.waitForFunction(() => window.godotQaState?.windows?.inventory,
  undefined, { timeout: 90000 });
await page.waitForTimeout(8000);

const facts = await page.evaluate(() => {
  const canvas = document.querySelector("canvas");
  const rect = canvas.getBoundingClientRect();
  return { canvas: { width: canvas.width, height: canvas.height,
    cssWidth: rect.width, cssHeight: rect.height, x: rect.x, y: rect.y } };
});
const scale = Math.min(facts.canvas.cssWidth / DESIGN.width,
  facts.canvas.cssHeight / DESIGN.height);
const offsetX = facts.canvas.x + (facts.canvas.cssWidth - DESIGN.width * scale) / 2;
const offsetY = facts.canvas.y + (facts.canvas.cssHeight - DESIGN.height * scale) / 2;
const point = (x, y) => ({ x: offsetX + x * scale, y: offsetY + y * scale });
const qa = () => page.evaluate(() => window.godotQaState ?? null);
const inventory = async () => (await qa()).windows.inventory;
const control = async (id) => (await inventory()).controls[id];
const frames = {};
const shot = async (name) => {
  const filename = `${name}.png`;
  const path = resolve(OUT, filename);
  await page.screenshot({ path });
  frames[name] = { path: filename, sha256: sha256(path) };
  return frames[name];
};
const invariantShot = async (name) => {
  const filename = `${name}.png`;
  const path = resolve(OUT, filename);
  await page.screenshot({ path, clip: { x: 1200, y: 700, width: 100, height: 100 } });
  return { path: filename, sha256: sha256(path) };
};
const checks = [];
const actions = [];
const check = (name, passed, detail) => checks.push({ name, passed, detail });
const record = (controlId, gesture, windowAction, expected, observed, assertions,
  actionFrames = {}, motionSamples = undefined) => {
  const matches = Object.values(assertions).every(Boolean);
  const action = { control_id: controlId, gesture, window_action: windowAction,
    expected, observed, responsive: matches, matches_expected: matches,
    assertions, frames: actionFrames };
  if (motionSamples !== undefined) action.motion_samples = motionSamples;
  actions.push(action);
  check(`${controlId}:${gesture}:${windowAction}`, matches, assertions);
};
const click = async (x, y, options = {}) => {
  const target = point(x, y);
  await page.mouse.click(target.x, target.y, options);
  await page.waitForTimeout(30);
};

const manifest = JSON.parse(readFileSync(resolve(ROOT,
  "godot/data/image-79-control-spec.json"), "utf8"));
const windowSpec = manifest.windows.find((entry) => entry.id === "inventory");
const idle = await shot("00-idle");
const invariantBefore = await invariantShot("00-invariant-before");
const initial = await inventory();
check("idle-factual-state", initial.window.size[0] === 484
  && initial.window.size[1] === 303
  && JSON.stringify(initial.window.resize.requested) === JSON.stringify([484, 303])
  && JSON.stringify(initial.window.resize.clamped) === JSON.stringify([484, 303])
  && initial.controls["inventory.tabs"].value === "item"
  && initial.controls["inventory.items"].semantic_state === "unselected"
  && initial.controls["inventory.items"].selected_items.length === 0
  && Object.keys(initial.controls["inventory.items"].surface_geometry).length === 28,
  initial.window);

const tabRouteChecks = [];
for (const [choice, y] of [["item", 749], ["etc-1", 827], ["etc-2", 866],
  ["cash", 905], ["equip", 788]]) {
  await click(23, y);
  const state = await control("inventory.tabs");
  tabRouteChecks.push(state.value === choice && state.last_action === "SelectInventoryTab");
}
const tabSelected = await control("inventory.tabs");
const tabFrame = await shot("01-tab-equip");
record("inventory.tabs", "Activate", "SelectInventoryTab",
  "each source tab routes once and Item reverses the selection", JSON.stringify(tabSelected), {
    all_five_routed: tabRouteChecks.every(Boolean),
    selected: tabSelected.value === "equip",
    action_routed: tabSelected.last_action === "SelectInventoryTab",
  }, { before: idle, after: tabFrame });
await click(23, 749);
check("tab-reversible", (await control("inventory.tabs")).value === "item",
  await control("inventory.tabs"));

await click(69, 761);
await page.waitForTimeout(260);
const selected = await control("inventory.items");
const selectedFrame = await shot("02-single-selected");
record("inventory.items", "Activate", "SelectInventoryItem",
  "one click selects after the double-click interval", JSON.stringify(selected), {
    selected: selected.value === "r0c0",
    gesture_distinct: selected.last_gesture === "Activate",
  }, { before: tabFrame, after: selectedFrame });

const logBeforeDouble = (await inventory()).interaction_log.length;
const doublePoint = point(123, 761);
await page.mouse.dblclick(doublePoint.x, doublePoint.y, { delay: 30 });
await page.waitForTimeout(260);
const opened = await control("inventory.items");
const doubleLog = (await inventory()).interaction_log.slice(logBeforeDouble)
  .filter((entry) => ["Activate", "DoubleActivate"].includes(entry.gesture));
const openedFrame = await shot("03-double-opened");
record("inventory.items", "DoubleActivate", "OpenInventoryItem",
  "double click opens once without a trailing single click", JSON.stringify(opened), {
    opened_once: opened.opened_item === "r0c1"
      && doubleLog.filter((entry) => entry.gesture === "DoubleActivate").length === 1,
    no_single: doubleLog.every((entry) => entry.gesture !== "Activate"),
  }, { before: selectedFrame, after: openedFrame });

const logBeforeRace = (await inventory()).interaction_log.length;
await click(69, 761);
await page.keyboard.down("Control");
const modifierRacePoint = point(69, 761);
await page.mouse.move(modifierRacePoint.x, modifierRacePoint.y);
await page.mouse.down();
await page.waitForTimeout(260);
const heldRaceLog = (await inventory()).interaction_log.slice(logBeforeRace)
  .filter((entry) => ["Activate", "ModifierActivate"].includes(entry.gesture));
await page.mouse.up();
await page.keyboard.up("Control");
await page.waitForTimeout(30);
const raceState = await control("inventory.items");
const raceLog = (await inventory()).interaction_log.slice(logBeforeRace)
  .filter((entry) => ["Activate", "ModifierActivate"].includes(entry.gesture));
check("pending-single-cancelled-by-modifier",
  raceState.last_gesture === "ModifierActivate"
    && raceState.selected_items.includes("r0c0")
    && heldRaceLog.length === 0
    && raceLog.filter((entry) => entry.gesture === "ModifierActivate").length === 1
    && raceLog.every((entry) => entry.gesture !== "Activate"),
  { heldRaceLog, raceState, raceLog });
await page.keyboard.down("Control");
await click(69, 761);
await page.keyboard.up("Control");

await page.keyboard.down("Control");
await click(177, 761);
await page.keyboard.up("Control");
const modifierSelected = await control("inventory.items");
const modifierFrame = await shot("04-modifier-selected");
record("inventory.items", "ModifierActivate", "ToggleInventorySelection",
  "Control click toggles independent multi-selection", JSON.stringify(modifierSelected), {
    toggled: modifierSelected.selected_items.includes("r0c2"),
    primary_preserved: modifierSelected.value === "r0c1",
  }, { before: openedFrame, after: modifierFrame });
await page.keyboard.down("Control");
await click(177, 761);
await page.keyboard.up("Control");
check("modifier-reversible", !(await control("inventory.items")).selected_items.includes("r0c2"),
  await control("inventory.items"));

const beforeInvalidModifiers = await inventory();
const preservedModifierState = JSON.stringify({
  value: beforeInvalidModifiers.controls["inventory.items"].value,
  selected_items: beforeInvalidModifiers.controls["inventory.items"].selected_items,
  opened_item: beforeInvalidModifiers.controls["inventory.items"].opened_item,
  item_values: beforeInvalidModifiers.controls["inventory.items"].item_values,
  item_version: beforeInvalidModifiers.controls["inventory.items"].item_version,
  detail_item: beforeInvalidModifiers.window.detail_item,
  detail_text: beforeInvalidModifiers.controls["inventory.items"].detail_text,
  detail_visible: beforeInvalidModifiers.controls["inventory.items"].detail_visible,
});
const invalidModifierChecks = [];
for (const keys of [["Alt"], ["Shift"], ["Meta"], ["Control", "Shift"]]) {
  for (const key of keys) await page.keyboard.down(key);
  await click(177, 761);
  for (const key of keys.toReversed()) await page.keyboard.up(key);
  const rejectedWindow = await inventory();
  const rejected = rejectedWindow.controls["inventory.items"];
  const afterState = JSON.stringify({ value: rejected.value,
    selected_items: rejected.selected_items, opened_item: rejected.opened_item,
    item_values: rejected.item_values, item_version: rejected.item_version,
    detail_item: rejectedWindow.window.detail_item, detail_text: rejected.detail_text,
    detail_visible: rejected.detail_visible });
  invalidModifierChecks.push(rejected.last_result.accepted === false
    && rejected.last_result.error?.code === "InvalidModifierError"
    && afterState === preservedModifierState);
}
check("invalid-modifiers-fail-closed", invalidModifierChecks.every(Boolean),
  invalidModifierChecks);

const dragStart = point(69, 761);
const dragEnd = point(123, 761);
const activateBeforeDrag = (await inventory()).interaction_log
  .filter((entry) => entry.gesture === "Activate").length;
const dragBefore = await shot("05-drag-before");
await page.mouse.move(dragStart.x, dragStart.y);
await page.mouse.down();
const dragSamples = [];
const dragMotionCounts = [];
let dragMid;
for (let index = 0; index < 40; index += 1) {
	const t = index / 39;
  const sample = [dragStart.x + (dragEnd.x - dragStart.x) * t,
    dragStart.y + (dragEnd.y - dragStart.y) * t];
  await page.mouse.move(sample[0], sample[1]);
	await page.waitForTimeout(15);
  dragSamples.push(sample);
  dragMotionCounts.push((await control("inventory.items")).gesture_drag.motion_samples);
  if (index === 20) dragMid = await shot("05-drag-mid");
}
await page.mouse.up();
const movedItem = await control("inventory.items");
const dragAfter = await shot("05-drag-after");
record("inventory.items", "DragDrop", "MoveInventoryItem",
  "31-sample drag swaps one pair atomically and suppresses click", JSON.stringify(movedItem), {
    swapped_once: movedItem.item_version === 1
      && movedItem.item_values.r0c0 === "r0c1" && movedItem.item_values.r0c1 === "r0c0",
    motion_factual: Math.max(...dragMotionCounts) >= 30,
    no_trailing_click: (await inventory()).interaction_log
      .filter((entry) => entry.gesture === "Activate").length === activateBeforeDrag,
    detail_follows_item: movedItem.opened_item_value === "r0c0"
      && movedItem.detail_text === "所持品 1-1\n個数 2" && movedItem.detail_visible,
  }, { before: dragBefore, mid: dragMid, after: dragAfter }, dragSamples);

const movedValues = JSON.stringify(movedItem.item_values);
await page.keyboard.down("Alt");
await page.mouse.move(dragStart.x, dragStart.y);
await page.mouse.down();
for (let index = 0; index < 31; index += 1) {
  const t = index / 30;
  await page.mouse.move(dragStart.x + (dragEnd.x - dragStart.x) * t,
    dragStart.y + (dragEnd.y - dragStart.y) * t);
}
await page.mouse.up();
await page.keyboard.up("Alt");
const modifiedDrop = await control("inventory.items");
check("modified-drag-drop-fails-closed", modifiedDrop.last_result.accepted === false
  && modifiedDrop.last_result.error?.code === "InvalidModifierError"
  && JSON.stringify(modifiedDrop.item_values) === movedValues
  && modifiedDrop.item_version === movedItem.item_version,
  modifiedDrop.last_result);

await page.mouse.move(dragStart.x, dragStart.y);
await page.mouse.down();
const sameItemOffset = point(89, 751);
for (let index = 0; index < 16; index += 1) {
  const t = (index + 1) / 16;
  await page.mouse.move(dragStart.x + (sameItemOffset.x - dragStart.x) * t,
    dragStart.y + (sameItemOffset.y - dragStart.y) * t);
}
for (let index = 0; index < 16; index += 1) {
  const t = (index + 1) / 16;
  await page.mouse.move(sameItemOffset.x + (dragStart.x - sameItemOffset.x) * t,
    sameItemOffset.y + (dragStart.y - sameItemOffset.y) * t);
}
await page.mouse.up();
const sameItemDrop = await control("inventory.items");
check("same-item-drop-fails-closed", sameItemDrop.last_result.accepted === false
  && sameItemDrop.last_result.error?.code === "InvalidDropTargetError"
  && JSON.stringify(sameItemDrop.item_values) === movedValues
  && sameItemDrop.item_version === movedItem.item_version,
  sameItemDrop.last_result);

const invalidStart = point(177, 761);
const invalidEnd = point(450, 900);
const beforeInvalidDrop = movedValues;
await page.mouse.move(invalidStart.x, invalidStart.y);
await page.mouse.down();
for (let index = 0; index < 31; index += 1) {
  const t = index / 30;
  await page.mouse.move(invalidStart.x + (invalidEnd.x - invalidStart.x) * t,
    invalidStart.y + (invalidEnd.y - invalidStart.y) * t);
}
await page.mouse.up();
const invalidDrop = await control("inventory.items");
check("invalid-drop-fails-closed", invalidDrop.last_result.accepted === false
  && invalidDrop.last_result.error?.code === "InvalidDropTargetError"
  && JSON.stringify(invalidDrop.item_values) === beforeInvalidDrop
  && invalidDrop.item_version === movedItem.item_version,
  invalidDrop.last_result);

const titleStart = point(200, 710);
const titleEnd = point(250, 410);
const windowDragBefore = await shot("06-window-drag-before");
await page.mouse.move(titleStart.x, titleStart.y);
await page.mouse.down();
const positionSamples = [];
let windowDragMid;
for (let index = 0; index < 31; index += 1) {
  const t = index / 30;
  await page.mouse.move(titleStart.x + (titleEnd.x - titleStart.x) * t,
    titleStart.y + (titleEnd.y - titleStart.y) * t);
  await page.waitForTimeout(15);
  positionSamples.push((await inventory()).window.position);
  if (index === 15) windowDragMid = await shot("06-window-drag-mid");
}
await page.mouse.up();
const movedWindow = (await inventory()).window;
const windowDragAfter = await shot("06-window-drag-after");
record("inventory", "Drag", "MoveWindow", "Window follows 31 pointer samples",
  JSON.stringify(movedWindow.position), {
    continuous: positionSamples.length === 31,
    delta_applied: Math.abs(movedWindow.position[0] - 50) < 1
      && Math.abs(movedWindow.position[1] - 401) < 1,
  }, { before: windowDragBefore, mid: windowDragMid, after: windowDragAfter }, positionSamples);

const resizeStart = point(movedWindow.position[0] + 472, movedWindow.position[1] + 291);
const resizeEnd = point(movedWindow.position[0] + 722, movedWindow.position[1] + 500);
const resizeBefore = await shot("07-resize-before");
await page.mouse.move(resizeStart.x, resizeStart.y);
await page.mouse.down();
const sizeSamples = [];
let resizeMid;
for (let index = 0; index < 31; index += 1) {
  const t = index / 30;
  await page.mouse.move(resizeStart.x + (resizeEnd.x - resizeStart.x) * t,
    resizeStart.y + (resizeEnd.y - resizeStart.y) * t);
  await page.waitForTimeout(15);
  sizeSamples.push((await inventory()).window.size);
  if (index === 15) resizeMid = await shot("07-resize-mid");
}
await page.mouse.up();
const resized = await inventory();
const resizeAfter = await shot("07-resize-after");
const aligned = Object.entries(resized.controls["inventory.items"].surface_geometry)
  .every(([id, geometry]) => {
    const local = windowSpec.controls.find((entry) => entry.id === "inventory.items")
      .surfaces[id].geometry;
    return geometry.x === resized.window.position[0] + 42 + local.x
      && geometry.y === resized.window.position[1] + 30 + local.y;
  });
record("inventory", "Resize", "ResizeWindow",
  "resize clamps at the declared maximum and preserves local hit alignment",
  JSON.stringify(resized.window), {
    maximum: resized.window.size[0] === 734 && resized.window.size[1] === 512,
    continuous: resized.window.resize.motion_samples >= 30,
    aligned,
    stale_chrome_covered: resized.window.resize.stale_title_controls_covered
      && resized.window.resize.stale_footer_covered
      && resized.window.resize.stale_footer_grip_covered
      && resized.window.resize.stale_right_edge_covered,
  }, { before: resizeBefore, mid: resizeMid, after: resizeAfter }, sizeSamples);

const minimizeGeometry = resized.controls["inventory.minimize"].geometry;
const minimizeX = minimizeGeometry.x + minimizeGeometry.width / 2;
const minimizeY = minimizeGeometry.y + minimizeGeometry.height / 2;
await page.mouse.move(point(1400, 900).x, point(1400, 900).y);
await page.waitForTimeout(30);
const minimizeBefore = await shot("08-minimize-before");
await click(minimizeX, minimizeY);
const minimized = (await inventory()).window;
const minimizeAfter = await shot("08-minimized");
const minimizedControl = await control("inventory.minimize");
await click(minimizedControl.geometry.x + minimizedControl.geometry.width / 2,
  minimizedControl.geometry.y + minimizedControl.geometry.height / 2);
const restored = (await inventory()).window;
const restoredItems = await control("inventory.items");
await page.mouse.move(point(1400, 900).x, point(1400, 900).y);
await page.waitForTimeout(30);
const minimizeRestored = await shot("08-minimize-restored");
record("inventory.minimize", "Activate", "ToggleMinimized",
  "purpose-built title Window preserves the resized geometry on restore",
  JSON.stringify({ minimized, restored }), {
    minimized: minimized.minimized && minimized.size[0] === 484 && minimized.size[1] === 28,
    restored: !restored.minimized && restored.size[0] === 734 && restored.size[1] === 512,
    position_preserved: JSON.stringify(minimized.position) === JSON.stringify(restored.position),
    detail_restored: restored.detail_item === "r0c1" && restoredItems.detail_visible,
  }, { before: minimizeBefore, after: minimizeAfter, restored: minimizeRestored });

const closeBefore = await shot("09-close-before");
const closeControl = await control("inventory.close");
await click(closeControl.geometry.x + closeControl.geometry.width / 2,
  closeControl.geometry.y + closeControl.geometry.height / 2);
const closed = (await inventory()).window;
const closeAfter = await shot("09-close-after");
record("inventory.close", "Activate", "CloseWindow", "close hides in one frame",
  JSON.stringify(closed), { hidden: closed.visible === false },
  { before: closeBefore, after: closeAfter });

await page.reload({ waitUntil: "networkidle", timeout: 90000 });
await page.waitForFunction(() => window.godotQaState?.windows?.inventory,
  undefined, { timeout: 90000 });
await page.waitForTimeout(2500);
await click(200, 710);
const keyBefore = await shot("10-key-before");
await page.keyboard.press("Escape");
await page.waitForTimeout(50);
const keyClosed = (await inventory()).window;
const keyAfter = await shot("10-key-after");
record("inventory", "KeyCommand", "CloseWindow",
  "Escape closes the frontmost Inventory Window", JSON.stringify(keyClosed), {
    hidden: keyClosed.visible === false,
    gesture_routed: keyClosed.last_gesture === "KeyCommand",
    action_routed: keyClosed.last_action === "CloseWindow",
  }, { before: keyBefore, after: keyAfter });

const windowActions = windowSpec.actions.map((binding) =>
  `${windowSpec.id}:${binding.gesture}:${binding.action}`);
const manifestActions = windowActions.concat(windowSpec.controls.flatMap((entry) =>
  entry.actions.map((binding) => `${entry.id}:${binding.gesture}:${binding.action}`)));
const covered = new Set(actions.map((entry) =>
  `${entry.control_id}:${entry.gesture}:${entry.window_action}`));
const missingActions = manifestActions.filter((binding) => !covered.has(binding));
check("manifest-action-coverage", missingActions.length === 0, missingActions);
const errors = consoleEntries.filter((entry) => entry.startsWith("[error]")
  || entry.startsWith("[pageerror]"));
check("zero-console-errors", errors.length === 0, errors);

const requiredControls = windowSpec.controls.map((entry) => entry.id);
const requiredActions = windowSpec.actions.map((binding) => ({
  control_id: windowSpec.id, gesture: binding.gesture, window_action: binding.action,
})).concat(windowSpec.controls.flatMap((entry) => entry.actions.map((binding) => ({
  control_id: entry.id, gesture: binding.gesture, window_action: binding.action,
}))));
const playLog = {
  schema_version: "image79-play-log-v2",
  candidate: { issue: 127,
    commit_sha: execFileSync("git", ["rev-parse", "HEAD"],
      { cwd: ROOT, encoding: "utf8" }).trim(), window_id: "inventory" },
  source_reference_sha256: manifest.reference.sha256,
  required_controls: requiredControls,
  required_actions: requiredActions,
  invariant_frames: { before: invariantBefore,
    after: await invariantShot("11-invariant-after") },
  console_errors: errors,
  actions,
};
writeFileSync(resolve(OUT, "play-log.json"), JSON.stringify(playLog, null, 2));
const report = { url: URL, facts, scale, checks, consoleEntries,
  final: await qa(), pass: checks.every((entry) => entry.passed), idle };
writeFileSync(resolve(OUT, "report.json"), JSON.stringify(report, null, 2));
console.log(JSON.stringify({ pass: report.pass, checks: checks.length,
  actions: actions.length, failed: checks.filter((entry) => !entry.passed)
    .map((entry) => entry.name), facts }));
await browser.close();
process.exit(report.pass ? 0 : 1);
