// Issue #134 real-Chromium Play Log for the System Menu Window.
import { createHash } from "node:crypto";
import { execFileSync, spawnSync } from "node:child_process";
import { createRequire } from "node:module";
import { mkdirSync, readFileSync, unlinkSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(SCRIPT_DIR, "../..");
const require = createRequire(`${process.env.PLAYWRIGHT_NODE_MODULES
  ?? resolve(SCRIPT_DIR, "browser/node_modules")}/`);
const { chromium } = require("playwright");
const URL = process.env.IMAGE79_URL ?? "http://127.0.0.1:8894/?screen=image79";
const OUT = resolve(process.env.IMAGE79_PLAYTEST_OUT
  ?? resolve(SCRIPT_DIR, "out/image79-system-menu-browser"));
const CANDIDATE = process.env.CANDIDATE_SHA
  ?? execFileSync("git", ["rev-parse", "HEAD"], { cwd: ROOT, encoding: "utf8" }).trim();
const DESIGN = { width: 1536, height: 1024 };
const INTENDED = { x: 1328, y: 505, width: 204, height: 273 };
const OPTIONS_REGION = { x: 1108, y: 297, width: 424, height: 202 };
const INVARIANT = { x: 1400, y: 800, width: 100, height: 100 };
mkdirSync(OUT, { recursive: true });

const sha256 = (path) => createHash("sha256").update(readFileSync(path)).digest("hex");
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: DESIGN });
const consoleErrors = [];
page.on("console", (message) => {
  const text = message.text();
  if (["warning", "error"].includes(message.type())
    && !(text.includes("GL Driver Message") && text.includes("ReadPixels")))
    consoleErrors.push(`[${message.type()}] ${text}`.slice(0, 1000));
});
page.on("pageerror", (error) => consoleErrors.push(`[pageerror] ${String(error)}`));

const waitForDesktop = () => page.waitForFunction(
  () => window.godotQaState?.windows?.system_menu,
  undefined, { timeout: 90000 });
const load = async () => {
  await page.goto(URL, { waitUntil: "networkidle", timeout: 90000 });
  await waitForDesktop();
  await page.waitForTimeout(500);
};
await load();
const canvas = await page.evaluate(() => {
  const rect = document.querySelector("canvas").getBoundingClientRect();
  return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
});
const scale = Math.min(canvas.width / DESIGN.width, canvas.height / DESIGN.height);
const offsetX = canvas.x + (canvas.width - DESIGN.width * scale) / 2;
const offsetY = canvas.y + (canvas.height - DESIGN.height * scale) / 2;
const point = (x, y) => ({ x: offsetX + x * scale, y: offsetY + y * scale });
const qa = () => page.evaluate(() => window.godotQaState);
const menu = async () => (await qa()).windows.system_menu;
const neutral = async () => {
  const p = point(1450, 850);
  await page.mouse.move(p.x, p.y);
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
  await page.screenshot({ path, clip: INVARIANT });
  return { path: `${name}.png`, sha256: sha256(path) };
};
const cropMetric = (left, right, crop = undefined) => {
  let a = resolve(OUT, left.path);
  let b = resolve(OUT, right.path);
  const temporary = [];
  if (crop) {
    const geometry = `${crop.width}x${crop.height}+${crop.x}+${crop.y}`;
    a = resolve(OUT, `.a-${process.pid}.png`);
    b = resolve(OUT, `.b-${process.pid}.png`);
    temporary.push(a, b);
    for (const [input, output] of [[resolve(OUT, left.path), a],
      [resolve(OUT, right.path), b]]) {
      const result = spawnSync("convert", [input, "-crop", geometry, "+repage", output],
        { encoding: "utf8" });
      if (result.status !== 0) throw new Error(result.stderr);
    }
  }
  const result = spawnSync("compare", ["-metric", "AE", a, b, "null:"],
    { encoding: "utf8" });
  temporary.forEach((path) => unlinkSync(path));
  const value = Number(`${result.stderr ?? ""}${result.stdout ?? ""}`.trim());
  if (!Number.isFinite(value)) throw new Error("ImageMagick AE failed");
  return value;
};
const metrics = (before, after, intendedRegion = INTENDED) => ({
  full_frame_changed_pixels: cropMetric(before, after),
  intended_region_changed_pixels: cropMetric(before, after, intendedRegion),
  invariant_region_changed_pixels: cropMetric(before, after, INVARIANT),
});
const sourceMetric = (frame) => {
  const crop = resolve(OUT, `.source-${process.pid}.png`);
  const screenshot = resolve(OUT, frame.path);
  const source = resolve(ROOT, "godot/assets/image-79/system-menu/source-plate.png");
  const cut = spawnSync("convert", [screenshot, "-crop",
    `${INTENDED.width}x${INTENDED.height}+${INTENDED.x}+${INTENDED.y}`,
    "+repage", crop], { encoding: "utf8" });
  if (cut.status !== 0) throw new Error(cut.stderr);
  const result = spawnSync("compare", ["-metric", "AE", crop, source, "null:"],
    { encoding: "utf8" });
  unlinkSync(crop);
  return Number(`${result.stderr ?? ""}${result.stdout ?? ""}`.trim());
};

const manifest = JSON.parse(readFileSync(resolve(ROOT,
  "godot/data/image-79-control-spec.json"), "utf8"));
const spec = manifest.windows.find((entry) => entry.id === "system_menu");
const requiredControls = spec.controls.filter((control) => control.actions.length > 0)
  .map((control) => control.id);
const requiredActions = spec.actions.map((binding) => ({ control_id: "system_menu",
  gesture: binding.gesture, window_action: binding.action })).concat(
  spec.controls.flatMap((control) => control.actions.map((binding) => ({
    control_id: control.id, gesture: binding.gesture, window_action: binding.action,
  }))));
const approved = new Set(requiredActions.map((entry) =>
  `${entry.control_id}:${entry.gesture}:${entry.window_action}`));
approved.add("desktop.escape:KeyCommand:OpenWindow");
const actions = [];
const record = (controlId, gesture, action, assertions, frames, observed,
  { expectedRejection = false, motionSamples = undefined,
    intendedChange = true, region = INTENDED } = {}) => {
  const pixelMetrics = metrics(frames.before, frames.after, region);
  const reversalMetrics = metrics(frames.before, frames.reversed, region);
  const entry = {
    control_id: controlId, gesture, window_action: action,
    expected: "Issue 134 System Menu Behaviour Card and frozen manifest",
    observed: JSON.stringify(observed),
    responsive: Object.values(assertions).every(Boolean),
    matches_expected: Object.values(assertions).every(Boolean),
    expected_rejection: expectedRejection,
    assertions, frames, intended_region: region, invariant_region: INVARIANT,
    pixel_metrics: pixelMetrics, reversal_pixel_metrics: reversalMetrics,
    contract_facts: {
      real_gesture_path: true,
      intended_region_changed: expectedRejection ? false
        : intendedChange ? pixelMetrics.intended_region_changed_pixels > 0
          : pixelMetrics.intended_region_changed_pixels === 0,
      invariants_stable: pixelMetrics.invariant_region_changed_pixels === 0,
      source_approved: approved.has(`${controlId}:${gesture}:${action}`),
      reversible: Object.values(reversalMetrics).every((value) => value === 0),
    },
  };
  if (expectedRejection) entry.mid_pixel_metrics = metrics(frames.before, frames.mid, region);
  if (motionSamples) entry.motion_samples = motionSamples;
  actions.push(entry);
};
const reload = async () => {
  await page.reload({ waitUntil: "networkidle", timeout: 90000 });
  await waitForDesktop();
  await page.waitForTimeout(450);
};
const clickControl = async (id) => {
  const geometry = (await menu()).controls[id].geometry;
  const p = point(geometry.x + geometry.width / 2, geometry.y + geometry.height / 2);
  await page.mouse.click(p.x, p.y);
  await page.waitForTimeout(80);
};
const pressControl = async (id, stem) => {
  const geometry = (await menu()).controls[id].geometry;
  const p = point(geometry.x + geometry.width / 2, geometry.y + geometry.height / 2);
  await page.mouse.move(p.x, p.y);
  await page.mouse.down();
  const mid = await shot(`${stem}-mid`, false);
  await page.mouse.up();
  await neutral();
  return mid;
};

const invariantBefore = await invariantShot("00-invariant-before");
const idle = await shot("00-idle");
const idleSourceChangedPixels = sourceMetric(idle);

// Five unavailable destinations expose pressed feedback, then reject without commit.
for (const name of ["save_point", "character_select", "environment_settings",
  "shortcuts", "game_exit"]) {
  await reload();
  const before = await shot(`${name}-before`);
  const mid = await pressControl(`system_menu.${name}`, name);
  const state = await qa();
  const after = await shot(`${name}-after`);
  await reload();
  const reversed = await shot(`${name}-reversed`);
  const control = state.windows.system_menu.controls[`system_menu.${name}`];
  record(`system_menu.${name}`, "Activate", "OpenWindow", {
    named_rejection: state.last_transaction.error?.code === "ActionRoutingError",
    destination_unavailable: state.windows.system_menu.window_state
      .destinations[`system_menu.${name}`].available === false,
    adapter_state_immutable: state.windows.system_menu.window_state.version === 0,
    control_settled: control.interaction_phase === "idle",
  }, { before, mid, after, reversed }, { transaction: state.last_transaction, control },
  { expectedRejection: true, intendedChange: false });
}

// Sound Settings raises the real Options Window and preserves its state/position.
await reload();
const optionsClose = (await qa()).windows.options.controls["options.close"].geometry;
await page.mouse.click(point(optionsClose.x + optionsClose.width / 2,
  optionsClose.y + optionsClose.height / 2).x,
point(optionsClose.x + optionsClose.width / 2,
  optionsClose.y + optionsClose.height / 2).y);
await page.waitForTimeout(80);
const optionsBefore = (await qa()).windows.options;
let before = await shot("sound-before");
let mid = await pressControl("system_menu.sound_settings", "sound");
let state = await qa();
let after = await shot("sound-after");
const optionsAfter = state.windows.options;
const closeAfter = optionsAfter.controls["options.close"].geometry;
await page.mouse.click(point(closeAfter.x + closeAfter.width / 2,
  closeAfter.y + closeAfter.height / 2).x,
point(closeAfter.x + closeAfter.width / 2,
  closeAfter.y + closeAfter.height / 2).y);
await page.waitForTimeout(80);
let reversed = await shot("sound-reversed");
record("system_menu.sound_settings", "Activate", "OpenWindow", {
  options_visible: optionsAfter.window.visible,
  position_preserved: JSON.stringify(optionsAfter.window.position)
    === JSON.stringify(optionsBefore.window.position),
  semantic_state_preserved: state.last_transaction.semantic_state_preserved === true,
  routed_to_options: state.last_transaction.target_window === "options",
  one_adapter_version: state.windows.system_menu.window_state.version === 1,
}, { before, mid, after, reversed }, state.last_transaction,
{ region: OPTIONS_REGION });

// Purpose-built minimized top Window and exact restoration.
await reload();
before = await shot("minimize-before");
mid = await pressControl("system_menu.minimize", "minimize");
state = await menu();
after = await shot("minimize-after");
await clickControl("system_menu.minimize");
reversed = await shot("minimize-reversed");
record("system_menu.minimize", "Activate", "ToggleMinimized", {
  minimized: state.window.minimized,
  distinct_top_window: state.window.plate_asset === spec.plates.minimized,
  source_width_preserved: state.window.size[0] === 204,
  minimized_height: state.window.size[1] === 27,
  restored: (await menu()).window.minimized === false,
}, { before, mid, after, restored: reversed, reversed }, state.window);

// Continuous drag and exact reverse path.
await reload();
before = await shot("drag-before");
const dragStart = point(1400, 517);
const dragEnd = point(1300, 417);
const samples = [];
await page.mouse.move(dragStart.x, dragStart.y);
await page.mouse.down();
for (let index = 0; index <= 30; index += 1) {
  const x = 1400 + (1300 - 1400) * index / 30;
  const y = 517 + (417 - 517) * index / 30;
  samples.push([x, y]);
  await page.mouse.move(point(x, y).x, point(x, y).y);
  if (index === 15) mid = await shot("drag-mid", false);
}
await page.mouse.up();
state = await menu();
after = await shot("drag-after");
const reverseStart = point(state.window.position[0] + 72, state.window.position[1] + 12);
await page.mouse.move(reverseStart.x, reverseStart.y);
await page.mouse.down();
for (let index = 0; index <= 30; index += 1) {
  await page.mouse.move(reverseStart.x + (dragStart.x - reverseStart.x) * index / 30,
    reverseStart.y + (dragStart.y - reverseStart.y) * index / 30);
}
await page.mouse.up();
reversed = await shot("drag-reversed");
record("system_menu", "Drag", "MoveWindow", {
  moved: state.window.position[0] === 1228 && state.window.position[1] === 405,
  continuous_samples: samples.length === 31,
  restored_home: (await menu()).window.position[0] === 1328
    && (await menu()).window.position[1] === 505,
}, { before, mid, after, reversed }, state.window, { motionSamples: samples });

// Return button and frontmost Escape are separate close paths.
await reload();
before = await shot("return-before");
mid = await pressControl("system_menu.return_to_game", "return");
state = await menu();
after = await shot("return-after");
await reload();
reversed = await shot("return-reversed");
record("system_menu.return_to_game", "Activate", "CloseWindow", {
  hidden: !state.window.visible,
}, { before, mid, after, reversed }, state.window);

await reload();
before = await shot("escape-before");
await page.mouse.click(point(1400, 517).x, point(1400, 517).y);
await page.keyboard.press("Escape");
await page.waitForTimeout(80);
state = await menu();
after = await shot("escape-after");
await reload();
reversed = await shot("escape-reversed");
record("system_menu", "KeyCommand", "CloseWindow", {
  hidden: !state.window.visible,
  focused_path: state.window.last_gesture === "KeyCommand",
}, { before, after, reversed }, state.window);

// With no visible Window left, the same real Escape opens only System Menu.
await reload();
await page.keyboard.press("Escape");
await page.waitForTimeout(60);
for (let index = 0; index < 12; index += 1) {
  const visible = Object.values((await qa()).windows)
    .filter((entry) => entry.window.visible);
  if (visible.length === 0) break;
  await page.keyboard.press("Escape");
  await page.waitForTimeout(60);
}
state = await qa();
before = await shot("context-before");
await page.keyboard.press("Escape");
await page.waitForTimeout(80);
state = await qa();
after = await shot("context-after");
await page.keyboard.press("Escape");
await page.waitForTimeout(80);
reversed = await shot("context-reversed");
record("desktop.escape", "KeyCommand", "OpenWindow", {
  only_system_visible: Object.entries(state.windows).every(([id, entry]) =>
    entry.window.visible === (id === "system_menu")),
  desktop_context: state.last_transaction.source_window === "desktop",
  position_preserved: state.last_transaction.position_before[0] === 1328
    && state.last_transaction.position_after[0] === 1328,
  semantic_state_preserved: state.last_transaction.semantic_state_preserved === true,
}, { before, after, reversed }, state.last_transaction);

const invariantAfter = await invariantShot("zz-invariant-after");
const playLog = {
  schema_version: "image79-play-log-v2",
  candidate: { issue: 134, commit_sha: CANDIDATE, window_id: "system_menu" },
  source_reference_sha256: manifest.reference.sha256,
  source_pixel_metric: { changed_pixels: idleSourceChangedPixels,
    candidate_frame: idle, source_plate: spec.plates.expanded },
  required_controls: requiredControls,
  required_actions: requiredActions,
  invariant_frames: { before: invariantBefore, after: invariantAfter },
  console_errors: consoleErrors,
  actions,
};
writeFileSync(resolve(OUT, "play-log.json"), `${JSON.stringify(playLog, null, 2)}\n`);
await browser.close();
console.log(JSON.stringify({ actions: actions.length,
  frames: new Set(actions.flatMap((entry) => Object.values(entry.frames)
    .map((frame) => frame.path))).size,
  source_changed_pixels: idleSourceChangedPixels,
  console_errors: consoleErrors.length, output: OUT }));
