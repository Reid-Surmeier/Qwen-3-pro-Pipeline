// Issue #133 real-Chromium Play Log for the Party Window.
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
const URL = process.env.IMAGE79_URL ?? "http://127.0.0.1:8879/?screen=image79";
const OUT = resolve(process.env.IMAGE79_PLAYTEST_OUT
  ?? resolve(SCRIPT_DIR, "out/image79-party-browser"));
const CANDIDATE = process.env.CANDIDATE_SHA
  ?? execFileSync("git", ["rev-parse", "HEAD"], { cwd: ROOT, encoding: "utf8" }).trim();
const DESIGN = { width: 1536, height: 1024 };
const INTENDED = { x: 1107, y: 505, width: 215, height: 269 };
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

const load = async () => {
  await page.goto(URL, { waitUntil: "networkidle", timeout: 90000 });
  await page.waitForFunction(() => window.godotQaState?.windows?.party,
    undefined, { timeout: 90000 });
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
const party = async () => (await qa()).windows.party;
const neutral = async () => {
  const p = point(1350, 750);
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
const metrics = (before, after) => ({
  full_frame_changed_pixels: cropMetric(before, after),
  intended_region_changed_pixels: cropMetric(before, after, INTENDED),
  invariant_region_changed_pixels: cropMetric(before, after, INVARIANT),
});
const manifest = JSON.parse(readFileSync(resolve(ROOT,
  "godot/data/image-79-control-spec.json"), "utf8"));
const spec = manifest.windows.find((entry) => entry.id === "party");
const requiredControls = spec.controls.filter((control) => control.actions.length > 0)
  .map((control) => control.id);
const requiredActions = spec.actions.map((binding) => ({ control_id: "party",
  gesture: binding.gesture, window_action: binding.action })).concat(
  spec.controls.flatMap((control) => control.actions.map((binding) => ({
    control_id: control.id, gesture: binding.gesture, window_action: binding.action,
  }))));
const approved = new Set(requiredActions.map((entry) =>
  `${entry.control_id}:${entry.gesture}:${entry.window_action}`));
const actions = [];
const record = (controlId, gesture, action, assertions, frames, observed,
  { expectedRejection = false, motionSamples = undefined,
    rapidGestures = undefined } = {}) => {
  const pixelMetrics = metrics(frames.before, frames.after);
  const reversalMetrics = metrics(frames.before, frames.reversed);
  const entry = {
    control_id: controlId, gesture, window_action: action,
    expected: "Issue 133 Party Behaviour Card and frozen manifest",
    observed: JSON.stringify(observed),
    responsive: Object.values(assertions).every(Boolean),
    matches_expected: Object.values(assertions).every(Boolean),
    expected_rejection: expectedRejection, assertions, frames,
    intended_region: INTENDED, invariant_region: INVARIANT,
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
  if (rapidGestures) entry.rapid_gestures = rapidGestures;
  actions.push(entry);
};
const reload = async () => {
  await page.reload({ waitUntil: "networkidle", timeout: 90000 });
  await page.waitForFunction(() => window.godotQaState?.windows?.party,
    undefined, { timeout: 90000 });
  await page.waitForTimeout(450);
};
const clickControl = async (id) => {
  const geometry = (await party()).controls[id].geometry;
  const p = point(geometry.x + geometry.width / 2, geometry.y + geometry.height / 2);
  await page.mouse.click(p.x, p.y);
  await page.waitForTimeout(80);
};
const pressControl = async (id, stem) => {
  const geometry = (await party()).controls[id].geometry;
  const p = point(geometry.x + geometry.width / 2, geometry.y + geometry.height / 2);
  await page.mouse.move(p.x, p.y);
  await page.mouse.down();
  const mid = await shot(`${stem}-mid`, false);
  await page.mouse.up();
  await neutral();
  return mid;
};

const invariantBefore = await invariantShot("00-invariant-before");

// Mode changes and reverses through the same real radio grammar.
let before = await shot("mode-before");
await clickControl("party.mode");
// ChoiceGroup hit regions require an explicit coordinate for Friends.
await reload();
before = await shot("mode-friends-before");
await page.mouse.click(point(1120, 758).x, point(1120, 758).y);
await page.waitForTimeout(80);
let state = await party();
let after = await shot("mode-friends-after");
await page.mouse.click(point(1210, 758).x, point(1210, 758).y);
await page.waitForTimeout(80);
let reversed = await shot("mode-friends-reversed");
record("party.mode", "Activate", "SelectPartyMode", {
  friends_selected: state.window_state.mode === "friends",
  list_cleared: state.controls["party.members"].visible_item_count === 0,
  members_unavailable: state.controls["party.members"].semantic_state
    === "unavailable",
  atomic_version: state.window_state.version === 1,
}, { before, after, reversed }, state.window_state);

// Member selection and exact source reset restoration.
await reload();
before = await shot("member-before");
await page.mouse.click(point(1200, 655).x, point(1200, 655).y);
await page.waitForTimeout(80);
state = await party();
after = await shot("member-after");
await reload();
reversed = await shot("member-reversed");
record("party.members", "Activate", "SelectPartyMember", {
  selected_show_a: state.window_state.selected_member === "show_a",
  atomic_version: state.window_state.version === 1,
}, { before, after, reversed }, state.window_state);

// Four unattested icons: real pressed feedback, named rejection, no commit.
for (const name of ["memo", "info", "target", "search"]) {
  await reload();
  before = await shot(`${name}-before`);
  const mid = await pressControl(`party.action.${name}`, name);
  state = await party();
  after = await shot(`${name}-after`);
  reversed = await shot(`${name}-reversed`);
  record(`party.action.${name}`, "Activate", "ActivatePartyAction", {
    named_rejection: state.controls[`party.action.${name}`].last_error?.code
      === "TransactionRejectedError",
    semantic_state_preserved: state.controls[`party.action.${name}`].semantic_state
      === "disabled",
  }, { before, mid, after, reversed }, state.controls[`party.action.${name}`],
  { expectedRejection: true });
}

// Leave commits once. Reload is the declared test reset/reversal.
await reload();
before = await shot("leave-before");
await clickControl("party.action.leave");
state = await party();
after = await shot("leave-after");
await reload();
reversed = await shot("leave-reversed");
record("party.action.leave", "Activate", "ActivatePartyAction", {
  membership_cleared: state.window_state.membership === "none",
  list_cleared: state.controls["party.members"].visible_item_count === 0,
  leave_disabled: state.controls["party.action.leave"].semantic_state === "disabled",
}, { before, after, reversed }, state.window_state);

// The disabled repeat path is separately exercised and remains immutable.
await reload();
await clickControl("party.action.leave");
before = await shot("leave-repeat-before");
const repeatMid = await pressControl("party.action.leave", "leave-repeat");
state = await party();
after = await shot("leave-repeat-after");
reversed = await shot("leave-repeat-reversed");
record("party.action.leave", "Activate", "ActivatePartyAction", {
  named_rejection: state.controls["party.action.leave"].last_error?.code
    === "TransactionRejectedError",
  membership_preserved: state.window_state.membership === "none",
}, { before, mid: repeatMid, after, reversed }, state.controls["party.action.leave"],
{ expectedRejection: true });

// Two real activations without an inter-gesture wait commit once, reject once,
// and settle rather than wedging the Control.
await reload();
before = await shot("rapid-leave-before");
const rapidGeometry = (await party()).controls["party.action.leave"].geometry;
const rapidPoint = point(rapidGeometry.x + rapidGeometry.width / 2,
  rapidGeometry.y + rapidGeometry.height / 2);
const rapidStarted = performance.now();
await page.mouse.click(rapidPoint.x, rapidPoint.y);
await page.mouse.click(rapidPoint.x, rapidPoint.y);
const rapidElapsed = Math.round(performance.now() - rapidStarted);
await page.waitForTimeout(80);
state = await party();
after = await shot("rapid-leave-after");
await reload();
reversed = await shot("rapid-leave-reversed");
record("party.action.leave", "Activate", "ActivatePartyAction", {
  first_committed: state.window_state.membership === "none"
    && state.window_state.version === 1,
  repeat_rejected: state.controls["party.action.leave"].last_error?.code
    === "TransactionRejectedError",
  control_settled: state.controls["party.action.leave"].interaction_phase !== "pressed",
  rapid_pair: rapidElapsed < 2000,
}, { before, after, reversed }, state.controls["party.action.leave"], {
  rapidGestures: { count: 2, elapsed_ms: rapidElapsed, inter_gesture_wait_ms: 0 },
});

// Continuous title drag and exact reversal.
await reload();
before = await shot("drag-before");
const dragStart = point(1160, 515);
const dragEnd = point(1080, 435);
const samples = [];
await page.mouse.move(dragStart.x, dragStart.y);
await page.mouse.down();
let mid;
for (let index = 0; index <= 30; index += 1) {
  const x = 1160 + (1080 - 1160) * index / 30;
  const y = 515 + (435 - 515) * index / 30;
  samples.push([x, y]);
  await page.mouse.move(point(x, y).x, point(x, y).y);
  if (index === 15) mid = await shot("drag-mid", false);
}
await page.mouse.up();
state = await party();
after = await shot("drag-after");
const reverseStart = point(state.window.position[0] + 53, state.window.position[1] + 10);
await page.mouse.move(reverseStart.x, reverseStart.y);
await page.mouse.down();
for (let index = 0; index <= 30; index += 1) {
  await page.mouse.move(reverseStart.x + (dragStart.x - reverseStart.x) * index / 30,
    reverseStart.y + (dragStart.y - reverseStart.y) * index / 30);
}
await page.mouse.up();
reversed = await shot("drag-reversed");
record("party", "Drag", "MoveWindow", {
  moved: state.window.position[0] < 1107 && state.window.position[1] < 505,
  continuous_samples: samples.length === 31,
  restored_home: (await party()).window.position[0] === 1107
    && (await party()).window.position[1] === 505,
}, { before, mid, after, reversed }, state.window, { motionSamples: samples });

// Close Button and focused Escape are independent paths.
await reload();
before = await shot("close-before");
await clickControl("party.close");
state = await party();
after = await shot("close-after");
await reload();
reversed = await shot("close-reversed");
record("party.close", "Activate", "CloseWindow", { hidden: !state.window.visible },
  { before, after, reversed }, state.window);

await reload();
before = await shot("escape-before");
await page.mouse.click(point(1160, 515).x, point(1160, 515).y);
await page.keyboard.press("Escape");
await page.waitForTimeout(80);
state = await party();
after = await shot("escape-after");
await reload();
reversed = await shot("escape-reversed");
record("party", "KeyCommand", "CloseWindow", {
  hidden: !state.window.visible, focused_path: state.window.last_gesture === "KeyCommand",
}, { before, after, reversed }, state.window);

const invariantAfter = await invariantShot("zz-invariant-after");
const playLog = {
  schema_version: "image79-play-log-v2",
  candidate: { issue: 133, commit_sha: CANDIDATE, window_id: "party" },
  source_reference_sha256: manifest.reference.sha256,
  required_controls: requiredControls, required_actions: requiredActions,
  invariant_frames: { before: invariantBefore, after: invariantAfter },
  console_errors: consoleErrors, actions,
};
writeFileSync(resolve(OUT, "play-log.json"), `${JSON.stringify(playLog, null, 2)}\n`);
await browser.close();
console.log(JSON.stringify({ actions: actions.length,
  frames: new Set(actions.flatMap((entry) => Object.values(entry.frames)
    .map((frame) => frame.path))).size,
  console_errors: consoleErrors.length, output: OUT }));
