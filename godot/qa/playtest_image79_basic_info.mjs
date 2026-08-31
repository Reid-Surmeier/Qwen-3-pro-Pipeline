// Issue #132 real-Chromium Play Log. Every manifest action is driven through
// pointer or keyboard input and hash-bound to the reviewed candidate.
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
const URL = process.env.IMAGE79_URL ?? "http://127.0.0.1:8878/?screen=image79";
const OUT = resolve(process.env.IMAGE79_PLAYTEST_OUT
  ?? resolve(SCRIPT_DIR, "out/image79-basic-info-browser"));
const CANDIDATE = process.env.CANDIDATE_SHA
  ?? execFileSync("git", ["rev-parse", "HEAD"], { cwd: ROOT, encoding: "utf8" }).trim();
const DESIGN = { width: 1536, height: 1024 };
const INTENDED = { x: 0, y: 0, width: 1536, height: 1024 };
const INVARIANT = { x: 1400, y: 800, width: 100, height: 100 };
mkdirSync(OUT, { recursive: true });

const sha256 = (path) => createHash("sha256").update(readFileSync(path)).digest("hex");
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: DESIGN });
const consoleErrors = [];
page.on("console", (message) => {
  const text = message.text();
  // Chromium reports screenshot ReadPixels stalls as driver-performance
  // warnings; they are neither Godot nor application diagnostics.
  if (["warning", "error"].includes(message.type())
    && !(text.includes("GL Driver Message") && text.includes("ReadPixels")))
    consoleErrors.push(`[${message.type()}] ${text}`.slice(0, 1000));
});
page.on("pageerror", (error) => consoleErrors.push(`[pageerror] ${String(error)}`));

const load = async () => {
  await page.goto(URL, { waitUntil: "networkidle", timeout: 90000 });
  await page.waitForFunction(() => window.godotQaState?.windows?.basic_info,
    undefined, { timeout: 90000 });
  await page.waitForTimeout(600);
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
const basic = async () => (await qa()).windows.basic_info;
const neutral = async () => {
  const p = point(1350, 750);
  await page.mouse.move(p.x, p.y);
  await page.waitForTimeout(70);
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
    for (const [input, output] of [[resolve(OUT, left.path), a], [resolve(OUT, right.path), b]]) {
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
const metrics = (before, after) => ({
  full_frame_changed_pixels: cropMetric(before, after),
  intended_region_changed_pixels: cropMetric(before, after, INTENDED),
  invariant_region_changed_pixels: cropMetric(before, after, INVARIANT),
});
const manifest = JSON.parse(readFileSync(resolve(ROOT,
  "godot/data/image-79-control-spec.json"), "utf8"));
const spec = manifest.windows.find((entry) => entry.id === "basic_info");
const requiredControls = spec.controls.filter((control) => control.actions.length > 0)
  .map((control) => control.id);
const requiredActions = spec.actions.map((binding) => ({ control_id: "basic_info",
  gesture: binding.gesture, window_action: binding.action })).concat(
  spec.controls.flatMap((control) => control.actions.map((binding) => ({
    control_id: control.id, gesture: binding.gesture, window_action: binding.action,
  }))));
const approved = new Set(requiredActions.map((entry) =>
  `${entry.control_id}:${entry.gesture}:${entry.window_action}`));
const actions = [];
const record = (controlId, gesture, action, assertions, frames, observed,
  { expectedRejection = false, motionSamples = undefined } = {}) => {
  const pixelMetrics = metrics(frames.before, frames.after);
  const reversalMetrics = metrics(frames.before, frames.reversed);
  const entry = {
    control_id: controlId, gesture, window_action: action,
    expected: "Issue 132 Basic Info Behaviour Card and frozen manifest",
    observed: JSON.stringify(observed),
    responsive: Object.values(assertions).every(Boolean),
    matches_expected: Object.values(assertions).every(Boolean),
    expected_rejection: expectedRejection,
    assertions, frames, intended_region: INTENDED, invariant_region: INVARIANT,
    pixel_metrics: pixelMetrics, reversal_pixel_metrics: reversalMetrics,
    contract_facts: {
      real_gesture_path: true,
      intended_region_changed: expectedRejection ? false
        : pixelMetrics.intended_region_changed_pixels > 0,
      invariants_stable: pixelMetrics.invariant_region_changed_pixels === 0,
      source_approved: approved.has(`${controlId}:${gesture}:${action}`),
      reversible: Object.values(reversalMetrics).every((value) => value === 0),
    },
  };
  if (expectedRejection) entry.mid_pixel_metrics = metrics(frames.before, frames.mid);
  if (motionSamples) entry.motion_samples = motionSamples;
  if (action === "ToggleMinimized") entry.frames.restored = frames.reversed;
  actions.push(entry);
};
const reload = async () => {
  await page.reload({ waitUntil: "networkidle", timeout: 90000 });
  await page.waitForFunction(() => window.godotQaState?.windows?.basic_info,
    undefined, { timeout: 90000 });
  await page.waitForTimeout(500);
};
const bringBasic = async () => {
  const p = point(100, 25);
  await page.mouse.click(p.x, p.y);
  await page.waitForTimeout(70);
};
const clickControl = async (id) => {
  const geometry = (await basic()).controls[id].geometry;
  const p = point(geometry.x + geometry.width / 2, geometry.y + geometry.height / 2);
  await page.mouse.click(p.x, p.y);
  await page.waitForTimeout(80);
};
const targetTitles = {
  status: [100, 222], options: [1200, 308], inventory: [100, 713],
  equipment_items: [100, 435], skill_tree: [650, 12],
};
const closeTarget = async (target) => {
  const p = point(...targetTitles[target]);
  await page.mouse.click(p.x, p.y);
  await page.keyboard.press("Escape");
  await page.waitForTimeout(80);
};

const invariantBefore = await invariantShot("00-invariant-before");

// Five live source destinations close, then reopen/raise, then close exactly.
for (const [name, target] of [["status", "status"], ["option", "options"],
  ["items", "inventory"], ["equip", "equipment_items"], ["skill", "skill_tree"]]) {
  await reload();
  await closeTarget(target);
  await bringBasic();
  const before = await shot(`destination-${name}-before`);
  await clickControl(`basic_info.destination.${name}`);
  const state = await qa();
  const after = await shot(`destination-${name}-after`);
  await closeTarget(target);
  await bringBasic();
  const reversed = await shot(`destination-${name}-reversed`);
  record(`basic_info.destination.${name}`, "Activate", "OpenWindow", {
    target_visible: state.windows[target].window.visible,
    routed_target: state.last_transaction.target_window === target,
    target_position_preserved: JSON.stringify(state.last_transaction.position_before)
      === JSON.stringify(state.last_transaction.position_after),
    raised: state.last_transaction.raised === true,
  }, { before, after, reversed }, state.last_transaction);
}

// Unavailable source buttons show pressed feedback and commit no pixels/state.
for (const name of ["map", "chat", "friend"]) {
  await reload();
  await bringBasic();
  const before = await shot(`unavailable-${name}-before`);
  const geometry = (await basic()).controls[`basic_info.destination.${name}`].geometry;
  const p = point(geometry.x + geometry.width / 2, geometry.y + geometry.height / 2);
  await page.mouse.move(p.x, p.y);
  await page.mouse.down();
  const mid = await shot(`unavailable-${name}-mid`, false);
  await page.mouse.up();
  await neutral();
  const rejected = await basic();
  const after = await shot(`unavailable-${name}-after`);
  const reversed = await shot(`unavailable-${name}-reversed`);
  record(`basic_info.destination.${name}`, "Activate", "UnavailableDestination", {
    named_rejection: rejected.controls[`basic_info.destination.${name}`]
      .last_error?.code === "TransactionRejectedError",
    semantic_state_preserved: rejected.controls[`basic_info.destination.${name}`]
      .semantic_state === "disabled",
  }, { before, mid, after, reversed }, rejected.controls[`basic_info.destination.${name}`],
  { expectedRejection: true });
}

// Purpose-built minimize and exact restore.
await reload();
await bringBasic();
let before = await shot("minimize-before");
await clickControl("basic_info.minimize");
let minimized = await basic();
let after = await shot("minimize-after");
await clickControl("basic_info.minimize");
let restored = await basic();
let reversed = await shot("minimize-reversed");
record("basic_info.minimize", "Activate", "ToggleMinimized", {
  purpose_built_height: minimized.window.size[1] === 48,
  restored_size: restored.window.size[1] === 286,
  meter_state_preserved: restored.controls["basic_info.meter.hp"].current === 1092,
}, { before, after, reversed }, restored.window);

// Continuous title drag with 31 pointer samples and exact reversal.
await reload();
await bringBasic();
before = await shot("drag-before");
const dragStart = point(100, 25);
const dragEnd = point(200, 100);
const samples = [];
await page.mouse.move(dragStart.x, dragStart.y);
await page.mouse.down();
let mid;
for (let index = 0; index <= 30; index += 1) {
  const x = 100 + (100 * index / 30);
  const y = 25 + (75 * index / 30);
  samples.push([x, y]);
  await page.mouse.move(point(x, y).x, point(x, y).y);
  if (index === 15) mid = await shot("drag-mid", false);
}
await page.mouse.up();
const moved = await basic();
after = await shot("drag-after");
const reverseStart = point(moved.window.position[0] + 100, moved.window.position[1] + 25);
await page.mouse.move(reverseStart.x, reverseStart.y);
await page.mouse.down();
for (let index = 0; index <= 30; index += 1) {
  await page.mouse.move(reverseStart.x + (dragStart.x - reverseStart.x) * index / 30,
    reverseStart.y + (dragStart.y - reverseStart.y) * index / 30);
}
await page.mouse.up();
reversed = await shot("drag-reversed");
record("basic_info", "Drag", "MoveWindow", {
  moved: moved.window.position[0] > 0 && moved.window.position[1] > 0,
  continuous_samples: samples.length === 31,
  restored_home: (await basic()).window.position[0] === 0
    && (await basic()).window.position[1] === 0,
}, { before, mid, after, reversed }, moved.window, { motionSamples: samples });

// Title Close and focused Escape Close are independent declared paths.
await reload();
await bringBasic();
before = await shot("close-button-before");
await clickControl("basic_info.close");
let closed = await basic();
after = await shot("close-button-after");
await reload();
await bringBasic();
reversed = await shot("close-button-reversed");
record("basic_info.close", "Activate", "CloseWindow", { hidden: !closed.window.visible },
  { before, after, reversed }, closed.window);

await reload();
await bringBasic();
before = await shot("escape-before");
await page.keyboard.press("Escape");
await page.waitForTimeout(80);
closed = await basic();
after = await shot("escape-after");
await reload();
await bringBasic();
reversed = await shot("escape-reversed");
record("basic_info", "KeyCommand", "CloseWindow", { hidden: !closed.window.visible,
  focused_path: closed.window.last_gesture === "KeyCommand" },
{ before, after, reversed }, closed.window);

const invariantAfter = await invariantShot("zz-invariant-after");
const playLog = {
  schema_version: "image79-play-log-v2",
  candidate: { issue: 132, commit_sha: CANDIDATE, window_id: "basic_info" },
  source_reference_sha256: manifest.reference.sha256,
  required_controls: requiredControls,
  required_actions: requiredActions,
  invariant_frames: { before: invariantBefore, after: invariantAfter },
  console_errors: consoleErrors,
  actions,
};
writeFileSync(resolve(OUT, "play-log.json"), `${JSON.stringify(playLog, null, 2)}\n`);
await browser.close();
console.log(JSON.stringify({ actions: actions.length, frames: new Set(actions.flatMap(
  (entry) => Object.values(entry.frames).map((frame) => frame.path))).size,
console_errors: consoleErrors.length, output: OUT }));
