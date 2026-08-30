// Builder-side browser drive for issue #125. This writes a schema-v1 Play Log
// for deterministic correction; it is not the independent blind verdict.
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
const WINDOW = { x: 1108, y: 297, width: 424, height: 202 };
const OUT = resolve(process.env.IMAGE79_PLAYTEST_OUT ?? resolve(SCRIPT_DIR, "out/image79-browser"));
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
await page.goto(URL, { waitUntil: "networkidle", timeout: 90000 });
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
const options = async () => (await qa()).windows.options;
const control = async (id) => (await options()).controls[id];
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
  await page.screenshot({ path, clip: { x: 0, y: 0, width: 100, height: 100 } });
  return { path: filename, sha256: sha256(path) };
};
const checks = [];
const actions = [];
const check = (name, passed, detail) => checks.push({ name, passed, detail });
const record = (controlId, gesture, windowAction, expected, observed, assertions, actionFrames,
  motionSamples = undefined) => {
  const matches = Object.values(assertions).every(Boolean);
  const action = { control_id: controlId, gesture, window_action: windowAction, expected, observed,
    responsive: matches, matches_expected: matches, assertions, frames: actionFrames };
  if (motionSamples !== undefined) action.motion_samples = motionSamples;
  actions.push(action);
};

const idle = await shot("00-idle");
const invariantBefore = await invariantShot("00-invariant-before");

async function exerciseToggle(id, x, y, index) {
  const target = point(x, y);
  const beforeState = await control(id);
  const before = await shot(`${index}-${id.replaceAll(".", "-")}-before`);
  await page.mouse.move(target.x, target.y);
  const hovered = await control(id);
  await page.mouse.down();
  await page.waitForTimeout(20);
  const pressed = await control(id);
  await page.mouse.up();
  const afterState = await control(id);
  const after = await shot(`${index}-${id.replaceAll(".", "-")}-after`);
  await page.mouse.click(target.x, target.y);
  const reversed = await control(id);
  await page.mouse.move(0, 0);
  await page.waitForTimeout(20);
  const reversedFrame = await shot(`${index}-${id.replaceAll(".", "-")}-reversed`);
  const assertions = {
    hover_exposed: hovered.interaction_phase === "hover",
    pressed_exposed: pressed.interaction_phase === "pressed",
    toggled: afterState.semantic_state !== beforeState.semantic_state,
    reversible: reversed.semantic_state === beforeState.semantic_state,
  };
  record(id, "Activate", "ToggleValue", "toggle in one frame and reverse on a second click",
    `${beforeState.semantic_state} -> ${afterState.semantic_state} -> ${reversed.semantic_state}`,
    assertions, { before, after, reversed: reversedFrame });
  check(`${id}-activate`, Object.values(assertions).every(Boolean), assertions);
}

async function exerciseRangeButton(id, x, y, direction, index) {
  const target = point(x, y);
  const beforeState = await control(id);
  const before = await shot(`${index}-${id.replaceAll(".", "-")}-activate-before`);
  await page.mouse.move(target.x, target.y);
  await page.mouse.down();
  await page.waitForTimeout(20);
  const pressed = await control(id);
  await page.mouse.up();
  const afterState = await control(id);
  const after = await shot(`${index}-${id.replaceAll(".", "-")}-activate-after`);
  const assertions = {
    pressed_exposed: pressed.interaction_phase === "pressed",
    stepped: direction < 0 ? afterState.value < beforeState.value : afterState.value > beforeState.value,
  };
  record(id, "Activate", "StepRange", "arrow steps the Range and exposes pressed state",
    `${beforeState.value} -> ${afterState.value}`, assertions, { before, after });
  check(`${id}-activate`, Object.values(assertions).every(Boolean), assertions);
}

async function exerciseWheel(id, x, y, index) {
  const target = point(x, y);
  const beforeState = await control(id);
  const before = await shot(`${index}-${id.replaceAll(".", "-")}-wheel-before`);
  await page.mouse.move(target.x, target.y);
  await page.mouse.wheel(0, -100);
  await page.waitForTimeout(50);
  const afterState = await control(id);
  const after = await shot(`${index}-${id.replaceAll(".", "-")}-wheel-after`);
  const assertions = { wheel_stepped: afterState.value > beforeState.value };
  record(id, "Wheel", "StepRange", "wheel input steps and clamps the Range",
    `${beforeState.value} -> ${afterState.value}`, assertions, { before, after });
  check(`${id}-wheel`, assertions.wheel_stepped, assertions);
}

async function exerciseRangeDrag(id, y, index, reverse) {
  const beforeState = await control(id);
  const controlX = WINDOW.x + 115;
  const startX = controlX + 24 + 209 * beforeState.value / 100;
  const endX = reverse ? controlX + 24 : controlX + 233;
  const start = point(startX, y);
  const finish = point(endX, y);
  const before = await shot(`${index}-${id.replaceAll(".", "-")}-drag-before`);
  await page.mouse.move(start.x, start.y);
  await page.mouse.down();
  const values = [];
  let mid;
  for (let step = 0; step < 31; step += 1) {
    const t = step / 30;
    await page.mouse.move(start.x + (finish.x - start.x) * t, start.y);
    await page.waitForTimeout(20);
    values.push((await control(id)).value);
    if (step === 15) mid = await shot(`${index}-${id.replaceAll(".", "-")}-drag-mid`);
  }
  await page.mouse.up();
  const afterState = await control(id);
  const after = await shot(`${index}-${id.replaceAll(".", "-")}-drag-after`);
  const monotonic = values.every((value, sample) => sample === 0
    || (reverse ? value <= values[sample - 1] : value >= values[sample - 1]));
  const endpoint = reverse ? afterState.value <= 1 : afterState.value >= 99;
  const assertions = { continuous: values.length === 31, monotonic, endpoint_clamped: endpoint };
  record(id, "Drag", "SetRange", "31-frame continuous drag reaches a clamped endpoint",
    `${beforeState.value} -> ${afterState.value} across ${values.length} samples`,
    assertions, { before, mid, after }, values);
  check(`${id}-drag`, Object.values(assertions).every(Boolean), assertions);
}

await exerciseRangeButton("options.bgm", 1231, 357, -1, "01");
await exerciseWheel("options.bgm", 1350, 357, "02");
await exerciseRangeDrag("options.bgm", 357, "03", true);
await exerciseRangeDrag("options.bgm", 357, "04", false);
await exerciseRangeButton("options.effect", 1471, 389, 1, "05");
await exerciseWheel("options.effect", 1350, 389, "06");
await exerciseRangeDrag("options.effect", 389, "07", false);
await exerciseRangeDrag("options.effect", 389, "07b", true);

await exerciseToggle("options.bgm_on", 1494, 359, "08");
await exerciseToggle("options.effect_on", 1494, 390, "09");
await exerciseToggle("options.attack", 1144, 475, "10");
await exerciseToggle("options.skill", 1234, 475, "11");
await exerciseToggle("options.item", 1305, 475, "12");
await exerciseToggle("options.option", 1401, 475, "13");

const dropdownPoint = point(1350, 431);
const dropdownBefore = await shot("14-options-skin-activate-before");
await page.mouse.move(dropdownPoint.x, dropdownPoint.y);
await page.mouse.down();
await page.waitForTimeout(20);
const dropdownPressed = await control("options.skin");
await page.mouse.up();
const dropdownOpened = await control("options.skin");
const dropdownAfter = await shot("14-options-skin-activate-after");
const dropdownAssertions = {
  pressed_exposed: dropdownPressed.interaction_phase === "pressed",
  opened: dropdownOpened.semantic_state === "open",
};
record("options.skin", "Activate", "ToggleDropdown", "open the themed list in one frame",
  dropdownOpened.semantic_state, dropdownAssertions,
  { before: dropdownBefore, after: dropdownAfter });
check("options.skin-activate", Object.values(dropdownAssertions).every(Boolean), dropdownAssertions);

const skinChoiceBefore = await shot("15-options-skin-select-before");
const skinChoicePoint = point(1300, 514);
await page.mouse.click(skinChoicePoint.x, skinChoicePoint.y);
const skinSelected = await control("options.skin");
const skinChoiceAfter = await shot("15-options-skin-select-after");
const skinChoiceAssertions = {
  selected: skinSelected.value === "tanublue",
  closed: skinSelected.semantic_state === "closed",
};
record("options.skin", "Activate", "SelectChoice", "select a themed row and close the list",
  JSON.stringify(skinSelected), skinChoiceAssertions,
  { before: skinChoiceBefore, after: skinChoiceAfter });
check("options.skin-select", Object.values(skinChoiceAssertions).every(Boolean), skinChoiceAssertions);

await page.mouse.click(dropdownPoint.x, dropdownPoint.y);

const skinEscapeBefore = await shot("15-options-skin-key-before");
await page.keyboard.press("Escape");
const skinDismissed = await control("options.skin");
const skinEscapeAfter = await shot("15-options-skin-key-after");
const skinKeyAssertions = { dismissed: skinDismissed.semantic_state === "closed" };
record("options.skin", "KeyCommand", "DismissDropdown", "Escape dismisses without changing the value",
  skinDismissed.semantic_state, skinKeyAssertions,
  { before: skinEscapeBefore, after: skinEscapeAfter });
check("options.skin-key", skinKeyAssertions.dismissed, skinKeyAssertions);

const minimizePoint = point(1490, 313);
await page.mouse.move(0, 0);
await page.waitForTimeout(20);
const minimizeBefore = await shot("16-options-minimize-before");
await page.mouse.click(minimizePoint.x, minimizePoint.y);
const minimized = (await options()).window;
const minimizeAfter = await shot("16-options-minimize-after");
await page.mouse.click(minimizePoint.x, minimizePoint.y);
const restored = (await options()).window;
await page.mouse.move(0, 0);
await page.waitForTimeout(20);
const restoredFrame = await shot("16-options-minimize-restored");
const minimizeAssertions = {
  distinct_minimized_plate: minimized.minimized && minimized.size[1] === 28,
  restored_state: !restored.minimized && restored.size[1] === 202,
  position_preserved: minimized.position[0] === restored.position[0]
    && minimized.position[1] === restored.position[1],
};
record("options.minimize", "Activate", "ToggleMinimized", "swap to a purpose-built minimized Window and restore",
  JSON.stringify({ minimized, restored }), minimizeAssertions,
  { before: minimizeBefore, after: minimizeAfter, restored: restoredFrame });
check("options.minimize-activate", Object.values(minimizeAssertions).every(Boolean), minimizeAssertions);

const title = point(1250, 309);
const dragBefore = await shot("17-options-window-drag-before");
await page.mouse.move(title.x, title.y);
await page.mouse.down();
const windowPositions = [];
let dragMid;
for (let step = 0; step < 31; step += 1) {
  const t = step / 30;
  await page.mouse.move(title.x - 80 * t, title.y + 90 * t);
  await page.waitForTimeout(15);
  const position = (await options()).window.position;
  windowPositions.push(position[0]);
  if (step === 15) dragMid = await shot("17-options-window-drag-mid");
}
await page.mouse.up();
const moved = (await options()).window.position;
const dragAfter = await shot("17-options-window-drag-after");
const windowDragAssertions = {
  continuous: windowPositions.length === 31,
  pointer_delta_applied: Math.abs(moved[0] - 1028) < 1 && Math.abs(moved[1] - 387) < 1,
};
record("options", "Drag", "MoveWindow", "Window follows the pointer without tweening",
  JSON.stringify(moved), windowDragAssertions,
  { before: dragBefore, mid: dragMid, after: dragAfter }, windowPositions);
check("window-drag", Object.values(windowDragAssertions).every(Boolean), windowDragAssertions);

const closePoint = point(moved[0] + 408, moved[1] + 16);
const closeBefore = await shot("18-options-close-before");
await page.mouse.click(closePoint.x, closePoint.y);
const closed = (await options()).window;
const closeAfter = await shot("18-options-close-after");
const closeAssertions = { hidden: closed.visible === false };
record("options.close", "Activate", "CloseWindow", "close hides the Window in one frame",
  JSON.stringify(closed), closeAssertions, { before: closeBefore, after: closeAfter });
check("options.close-activate", closeAssertions.hidden, closeAssertions);

const manifest = JSON.parse(readFileSync(resolve(ROOT, "godot/data/image-79-control-spec.json"), "utf8"));
const manifestActions = manifest.windows[0].controls.flatMap((entry) =>
  entry.actions.map((binding) => `${entry.id}:${binding.gesture}:${binding.action}`));
const covered = new Set(actions.map((entry) =>
  `${entry.control_id}:${entry.gesture}:${entry.window_action}`));
const missingActions = manifestActions.filter((binding) => !covered.has(binding));
check("manifest-action-coverage", missingActions.length === 0, missingActions);

const errors = consoleEntries.filter((entry) => entry.startsWith("[error]")
  || entry.startsWith("[pageerror]"));
check("zero-console-errors", errors.length === 0, errors);
const requiredControls = manifest.windows[0].controls.map((entry) => entry.id);
const requiredActions = manifest.windows[0].controls.flatMap((entry) =>
  entry.actions.map((binding) => ({ control_id: entry.id, gesture: binding.gesture,
    window_action: binding.action })));
const playLog = {
  schema_version: "image79-play-log-v1",
  candidate: {
    issue: 125,
    commit_sha: execFileSync("git", ["rev-parse", "HEAD"],
      { cwd: ROOT, encoding: "utf8" }).trim(),
    window_id: "options",
  },
  source_reference_sha256: manifest.reference.sha256,
  required_controls: requiredControls,
  required_actions: requiredActions,
  invariant_frames: {
    before: invariantBefore,
    after: await invariantShot("19-invariant-after"),
  },
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
