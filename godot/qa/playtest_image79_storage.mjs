// Builder-side browser drive for Issue #128. Real browser wheel, pointer, and
// keyboard input produce the Storage Play Log and evidence frames.
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
  ?? resolve(SCRIPT_DIR, "out/image79-storage-browser"));
const DESIGN = { width: 1536, height: 1024 };
mkdirSync(OUT, { recursive: true });

const sha256 = (path) => createHash("sha256").update(readFileSync(path)).digest("hex");
const browser = await chromium.launch(process.env.IMAGE79_HEADED_MESA === "1" ? {
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
await page.waitForFunction(() => window.godotQaState?.windows?.storage,
  undefined, { timeout: 90000 });
await page.waitForTimeout(5000);

const canvasFacts = await page.evaluate(() => {
  const canvas = document.querySelector("canvas");
  const rect = canvas.getBoundingClientRect();
  return { width: rect.width, height: rect.height, x: rect.x, y: rect.y };
});
const scale = Math.min(canvasFacts.width / DESIGN.width, canvasFacts.height / DESIGN.height);
const offsetX = canvasFacts.x + (canvasFacts.width - DESIGN.width * scale) / 2;
const offsetY = canvasFacts.y + (canvasFacts.height - DESIGN.height * scale) / 2;
const point = (x, y) => ({ x: offsetX + x * scale, y: offsetY + y * scale });
const qa = () => page.evaluate(() => window.godotQaState);
const storage = async () => (await qa()).windows.storage;
const control = async (id) => (await storage()).controls[id];
const checks = [];
const actions = [];
const frames = {};
const check = (name, passed, detail) => checks.push({ name, passed, detail });
const shot = async (name) => {
  const path = resolve(OUT, `${name}.png`);
  await page.screenshot({ path });
  frames[name] = { path: `${name}.png`, sha256: sha256(path) };
  return frames[name];
};
const invariantShot = async (name) => {
  const path = resolve(OUT, `${name}.png`);
  await page.screenshot({ path, clip: { x: 1400, y: 800, width: 100, height: 100 } });
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
    comparedLeft = resolve(OUT, `.pixel-left-${process.pid}.png`);
    comparedRight = resolve(OUT, `.pixel-right-${process.pid}.png`);
    temporary.push(comparedLeft, comparedRight);
    for (const [input, output] of [[leftPath, comparedLeft], [rightPath, comparedRight]]) {
      const cropped = spawnSync("convert", [input, "-crop", geometry, "+repage", output],
        { encoding: "utf8" });
      if (cropped.status !== 0) throw new Error(cropped.stderr || "ImageMagick crop failed");
    }
  }
  const compared = spawnSync("compare", ["-metric", "AE", comparedLeft, comparedRight,
    "null:"], { encoding: "utf8" });
  for (const path of temporary) unlinkSync(path);
  const raw = `${compared.stderr ?? ""}${compared.stdout ?? ""}`.trim();
  const value = Number(raw);
  if (!Number.isFinite(value)) throw new Error(`ImageMagick AE failed: ${raw}`);
  return value;
};
const pixelMetrics = (before, after, crop = { x: 492, y: 569, width: 600, height: 433 }) => ({
  full_frame_changed_pixels: ae(before, after),
  intended_region_changed_pixels: ae(before, after, crop),
  invariant_region_changed_pixels: ae(before, after,
    { x: 1400, y: 800, width: 100, height: 100 }),
});
const record = (controlId, gesture, action, assertions, actionFrames, observed,
  motionSamples = undefined) => {
  const matches = Object.values(assertions).every(Boolean);
  const entry = { control_id: controlId, gesture, window_action: action,
    expected: "manifest and Behaviour Card", observed: typeof observed === "string"
      ? observed : JSON.stringify(observed), responsive: matches,
    matches_expected: matches, assertions, frames: actionFrames };
  if (actionFrames.before && actionFrames.after) {
    entry.pixel_metrics = pixelMetrics(actionFrames.before, actionFrames.after);
  }
  if (actionFrames.before && actionFrames.reversed) {
    entry.reversal_pixel_metrics = pixelMetrics(actionFrames.before, actionFrames.reversed);
  }
  if (motionSamples !== undefined) entry.motion_samples = motionSamples;
  actions.push(entry);
  check(`${controlId}:${gesture}:${action}`, matches, assertions);
};
const attachReversal = (frame, assertions) => {
  const entry = actions.at(-1);
  entry.frames.reversed = frame;
  entry.reversal_assertions = assertions;
  entry.reversal_pixel_metrics = pixelMetrics(entry.frames.before, frame);
  const matches = Object.values(assertions).every(Boolean);
  entry.matches_expected = entry.matches_expected && matches;
  entry.responsive = entry.matches_expected;
  check(`${entry.control_id}:${entry.gesture}:reversal`, matches, assertions);
};
const click = async (x, y) => {
  const target = point(x, y);
  await page.mouse.click(target.x, target.y);
  await page.waitForTimeout(40);
};
const ctrlDouble = async (x, y) => {
  const target = point(x, y);
  await page.keyboard.down("Control");
  await page.mouse.dblclick(target.x, target.y, { delay: 35 });
  await page.keyboard.up("Control");
  await page.waitForTimeout(80);
};
const reloadStorage = async () => {
  await page.reload({ waitUntil: "networkidle", timeout: 90000 });
  await page.waitForFunction(() => window.godotQaState?.windows?.storage,
    undefined, { timeout: 90000 });
  await page.waitForTimeout(1000);
};

const manifest = JSON.parse(readFileSync(resolve(ROOT,
  "godot/data/image-79-control-spec.json"), "utf8"));
const windowSpec = manifest.windows.find((entry) => entry.id === "storage");
const idle = await shot("00-idle");
const invariantBefore = await invariantShot("00-invariant-before");
const initial = await storage();
check("idle-factual", initial.window.size[0] === 539 && initial.window.size[1] === 393
  && initial.controls["storage.items"].surface_geometry
  && Object.keys(initial.controls["storage.items"].surface_geometry).length === 35,
  initial.window);

await click(610, 670);
await page.waitForTimeout(260);
const selected = await control("storage.items");
const selectedFrame = await shot("00a-item-selected");
record("storage.items", "Activate", "SelectStorageItem", {
  selected: selected.value === "r0c0",
  routed: selected.last_action === "SelectStorageItem",
}, { before: idle, after: selectedFrame }, selected);

await page.keyboard.down("Control");
await click(670, 670);
await page.keyboard.up("Control");
const modifierSelected = await control("storage.items");
const modifierFrame = await shot("00b-item-modifier-selected");
record("storage.items", "ModifierActivate", "ToggleStorageSelection", {
  toggled: modifierSelected.selected_items.includes("r0c1"),
  routed: modifierSelected.last_action === "ToggleStorageSelection",
}, { before: selectedFrame, after: modifierFrame }, modifierSelected);

await click(675, 977);
const searchFocused = await control("storage.search");
const focusFrame = await shot("00c-search-focused");
record("storage.search_focus", "Activate", "FocusStorageSearch", {
  focused: searchFocused.focused === true,
}, { before: modifierFrame, after: focusFrame }, searchFocused);

await click(537, 704);
const category = await control("storage.categories");
const categoryFrame = await shot("01-category-equipment");
record("storage.categories", "Activate", "SelectStorageCategory", {
  selected: category.value === "equipment",
  routed: category.last_action === "SelectStorageCategory",
}, { before: focusFrame, after: categoryFrame }, category.value);
await click(537, 668);
await page.mouse.move(...Object.values(point(1200, 700)));
const categoryReversed = await shot("01b-category-reversed");
attachReversal(categoryReversed, {
  restored_initial_category: (await control("storage.categories")).value === "consumable",
});
await click(537, 704);

const scrollPoint = point(1007, 800);
await page.mouse.move(scrollPoint.x, scrollPoint.y);
await page.mouse.wheel(0, 120);
await page.waitForTimeout(60);
const wheel = await control("storage.scroll");
const wheelFrame = await shot("02-wheel-three-rows");
record("storage.scroll", "Wheel", "ScrollStorage", {
  exact_three_rows: wheel.offset === 3,
  one_frame_state: wheel.last_action === "ScrollStorage",
}, { before: categoryFrame, after: wheelFrame }, wheel.offset);
await page.mouse.wheel(0, -120);
await page.waitForTimeout(60);
const wheelReversed = await shot("02b-wheel-reversed");
attachReversal(wheelReversed, {
  exact_start: (await control("storage.scroll")).offset === 0,
});
await page.mouse.wheel(0, 120);
await page.waitForTimeout(60);

await click(1007, 946);
await click(1007, 946);
await click(1007, 946);
const arrow = await control("storage.scroll");
const arrowEndFrame = await shot("03-arrow-endpoint");
for (let index = 0; index < 7; index += 1) await click(1007, 646);
const arrowStart = await control("storage.scroll");
const arrowStartFrame = await shot("03b-arrow-start-endpoint");
record("storage.scroll", "Activate", "StepStorageScroll", {
  clamps_exact_end: arrow.offset === arrow.maximum,
  clamps_exact_start: arrowStart.offset === arrowStart.minimum,
}, { before: wheelFrame, after: arrowEndFrame, reversed: arrowStartFrame },
JSON.stringify({ end: arrow, start: arrowStart }));

const thumbStart = point(1007, 683);
const thumbEnd = point(1007, 925);
await page.mouse.move(thumbStart.x, thumbStart.y);
await page.mouse.down();
const thumbMotionSamples = [];
const offsetSamples = [];
let thumbMid;
let thumbDuring;
for (let index = 0; index < 31; index += 1) {
  const t = index / 30;
  const sample = [thumbStart.x, thumbStart.y + (thumbEnd.y - thumbStart.y) * t];
  await page.mouse.move(sample[0], sample[1]);
  await page.waitForTimeout(12);
  thumbMotionSamples.push(sample);
  offsetSamples.push((await control("storage.scroll")).offset);
  if (index === 15) {
    thumbDuring = await control("storage.scroll");
    thumbMid = await shot("04-thumb-drag-mid");
  }
}
await page.mouse.up();
const dragged = await control("storage.scroll");
const thumbEndFrame = await shot("04-thumb-end");
await page.mouse.move(thumbEnd.x, thumbEnd.y);
await page.mouse.down();
await page.mouse.move(thumbStart.x, thumbStart.y, { steps: 31 });
await page.mouse.up();
const thumbReversed = await control("storage.scroll");
const thumbReversedFrame = await shot("04b-thumb-reversed");
record("storage.scroll", "Drag", "SetStorageScrollOffset", {
  continuous: thumbMotionSamples.length === 31,
  dragging_state_visible: thumbDuring?.interaction_phase === "dragging",
  clamps_exact_end: dragged.offset === dragged.maximum,
  clamps_exact_start: thumbReversed.offset === thumbReversed.minimum,
  offset_changed: new Set(offsetSamples).size > 1,
}, { before: arrowStartFrame, mid: thumbMid, after: thumbEndFrame,
  reversed: thumbReversedFrame },
JSON.stringify({ end: dragged, start: thumbReversed, offsets: offsetSamples }),
thumbMotionSamples);

await click(779, 977);
await page.keyboard.type("Potion 70", { delay: 25 });
await page.waitForTimeout(80);
const searched = await storage();
const searchFrame = await shot("05-search-filtered");
record("storage.search", "KeyCommand", "FilterStorage", {
  accepted_text_rendered: searched.controls["storage.search"].rendered_text === "Potion 70",
  filtered_one: searched.controls["storage.items"].filtered_items.length === 1,
  scroll_reset: searched.controls["storage.scroll"].offset === 0,
}, { before: thumbReversedFrame, after: searchFrame },
searched.controls["storage.search"].rendered_text);

await click(632, 977);
const treeRestoredFrame = await shot("07c-tree-restored");
const listed = await storage();
const listFrame = await shot("06-list-mode");
record("storage.list", "Activate", "ToggleStorageView", {
  list_mode: listed.window.view_mode === "list" && listed.controls["storage.items"].list_mode,
}, { before: searchFrame, after: listFrame }, listed.window.view_mode);
await click(878, 977);
const sorted = await control("storage.items");
const sortedFrame = await shot("07-sorted");
await click(878, 977);
const sortReversed = await control("storage.items");
const sortReversedFrame = await shot("07b-sort-reversed");
record("storage.sort", "Activate", "SortStorage", {
  reversed_order: sorted.sort_ascending === false,
  restored_order: sortReversed.sort_ascending === true,
}, { before: listFrame, after: sortedFrame, reversed: sortReversedFrame },
JSON.stringify({ sorted: sorted.sort_ascending, restored: sortReversed.sort_ascending }));
await click(632, 977);

await click(779, 977);
await page.keyboard.press("Control+A");
await page.keyboard.press("Backspace");
const beforeReject = await qa();
await ctrlDouble(610, 670);
const rejected = await qa();
record("storage.items", "ModifierDoubleActivate", "TransferStorageItem", {
  rejected_full: rejected.last_transaction.ok === false
    && rejected.last_transaction.error?.code === "TransactionRejectedError",
  source_preserved: JSON.stringify(rejected.windows.storage.controls["storage.items"].collection_items)
    === JSON.stringify(beforeReject.windows.storage.controls["storage.items"].collection_items),
  target_preserved: JSON.stringify(rejected.windows.inventory.controls["inventory.items"].collection_items)
    === JSON.stringify(beforeReject.windows.inventory.controls["inventory.items"].collection_items),
}, { before: treeRestoredFrame, after: await shot("08-transfer-rejected") },
rejected.last_transaction);

await ctrlDouble(69, 761);
const outbound = await qa();
record("inventory.items", "ModifierDoubleActivate", "TransferInventoryItem", {
  committed: outbound.last_transaction.ok === true,
  direction: outbound.last_transaction.source_window === "inventory"
    && outbound.last_transaction.target_window === "storage",
  both_versions: outbound.last_transaction.source_version_after
    === outbound.last_transaction.source_version_before + 1
    && outbound.last_transaction.target_version_after
    === outbound.last_transaction.target_version_before + 1,
}, { before: frames["08-transfer-rejected"], after: await shot("09-transfer-outbound") },
outbound.last_transaction);

const returningItem = outbound.last_transaction.item;
await click(779, 977);
await page.keyboard.press("Control+A");
await page.keyboard.press("Backspace");
await page.keyboard.type(returningItem, { delay: 25 });
await page.waitForFunction((item) => window.godotQaState.windows.storage.controls[
  "storage.items"].filtered_items.includes(item), returningItem);
await ctrlDouble(610, 670);
const returned = await qa();
record("storage.items", "ModifierDoubleActivate", "TransferStorageItem", {
  committed: returned.last_transaction.ok === true,
  direction: returned.last_transaction.source_window === "storage"
    && returned.last_transaction.target_window === "inventory",
}, { before: frames["09-transfer-outbound"], after: await shot("10-transfer-returned") },
returned.last_transaction);

const dragStart = point(700, 620);
const dragEnd = point(760, 580);
const windowDragBefore = await shot("11-window-drag-before");
await page.mouse.move(dragStart.x, dragStart.y);
await page.mouse.down();
const windowMotionSamples = [];
let windowDragMid;
for (let index = 0; index < 31; index += 1) {
  const t = index / 30;
  const sample = [dragStart.x + (dragEnd.x - dragStart.x) * t,
    dragStart.y + (dragEnd.y - dragStart.y) * t];
  await page.mouse.move(sample[0], sample[1]);
  windowMotionSamples.push(sample);
  if (index === 15) windowDragMid = await shot("11-window-drag-mid");
}
await page.mouse.up();
const moved = await storage();
const windowDragAfter = await shot("11-window-moved");
const reverseStart = point(760, 580);
const reverseEnd = point(700, 620);
await page.mouse.move(reverseStart.x, reverseStart.y);
await page.mouse.down();
await page.mouse.move(reverseEnd.x, reverseEnd.y, { steps: 31 });
await page.mouse.up();
const restoredMove = await storage();
const windowDragReversed = await shot("11b-window-restored");
record("storage", "Drag", "MoveWindow", {
  moved: moved.window.position[0] === 552 && moved.window.position[1] === 569,
  continuous: windowMotionSamples.length === 31,
  restored: restoredMove.window.position[0] === 492
    && restoredMove.window.position[1] === 609,
}, { before: windowDragBefore, mid: windowDragMid, after: windowDragAfter,
  reversed: windowDragReversed },
JSON.stringify({ moved: moved.window.position, restored: restoredMove.window.position }),
windowMotionSamples);

const invariantAfter = await invariantShot("11-invariant-after");

await reloadStorage();
const titleCloseBefore = await shot("12-title-close-before");
await click(1016, 626);
const titleClosedState = await storage();
const titleClosed = titleClosedState.window;
record("storage.close", "Activate", "CloseWindow", {
  hidden: titleClosed.visible === false,
  routed: titleClosedState.controls["storage.close"].last_action === "CloseWindow",
}, { before: titleCloseBefore, after: await shot("12-title-close-after") }, titleClosedState);
await reloadStorage();
const titleCloseRestored = await shot("12b-title-close-restored");
attachReversal(titleCloseRestored, {
  restored: (await storage()).window.visible === true,
});

const bottomCloseBefore = await shot("13-bottom-close-before");
await click(965, 977);
const bottomClosedState = await storage();
const bottomClosed = bottomClosedState.window;
record("storage.bottom_close", "Activate", "CloseWindow", {
  hidden: bottomClosed.visible === false,
  routed: bottomClosedState.controls["storage.bottom_close"].last_action === "CloseWindow",
}, { before: bottomCloseBefore, after: await shot("13-bottom-close-after") }, bottomClosedState);
await reloadStorage();
const bottomCloseRestored = await shot("13b-bottom-close-restored");
attachReversal(bottomCloseRestored, {
  restored: (await storage()).window.visible === true,
});

await click(700, 620);
const keyCloseBefore = await shot("14-key-close-before");
await page.keyboard.press("Escape");
const keyClosed = (await storage()).window;
record("storage", "KeyCommand", "CloseWindow", {
  hidden: keyClosed.visible === false,
  routed: keyClosed.last_action === "CloseWindow" && keyClosed.last_gesture === "KeyCommand",
}, { before: keyCloseBefore, after: await shot("14-key-close-after") }, keyClosed);

const failed = checks.filter((entry) => !entry.passed);
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
  candidate: { issue: 128,
    commit_sha: execFileSync("git", ["rev-parse", "HEAD"],
      { cwd: ROOT, encoding: "utf8" }).trim(),
    window_id: "storage" },
  source_reference_sha256: manifest.reference.sha256,
  required_controls: requiredControls,
  required_actions: requiredActions,
  invariant_frames: { before: invariantBefore, after: invariantAfter },
  console_errors: errors,
  actions,
};
writeFileSync(resolve(OUT, "play-log.json"), `${JSON.stringify(playLog, null, 2)}\n`);
const report = {
  url: URL,
  window: { id: "storage", geometry: windowSpec.geometry },
  driver: "Playwright Chromium real pointer, wheel, and keyboard input",
  checks,
  frames,
  console_entries: consoleEntries,
  summary: { pass: failed.length === 0 && errors.length === 0,
    total: checks.length, failed: failed.length, console_errors: errors.length },
};
writeFileSync(resolve(OUT, "report.json"), `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report.summary));
await browser.close();
process.exitCode = report.summary.pass ? 0 : 1;
