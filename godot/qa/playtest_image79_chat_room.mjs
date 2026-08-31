// Issue #135 hash-locked real-Chromium Play Log for Chat Room.
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
  ?? resolve(SCRIPT_DIR, "out/image79-chat-room-browser"));
const CANDIDATE = process.env.CANDIDATE_SHA
  ?? execFileSync("git", ["rev-parse", "HEAD"], { cwd: ROOT, encoding: "utf8" }).trim();
const DESIGN = { width: 1536, height: 1024 };
const CHAT = { x: 1037, y: 782, width: 495, height: 226 };
const INTENDED = { x: 0, y: 0, width: 1536, height: 1024 };
const INVARIANT = { x: 720, y: 350, width: 80, height: 80 };
mkdirSync(OUT, { recursive: true });

const manifest = JSON.parse(readFileSync(resolve(ROOT,
  "godot/data/image-79-control-spec.json"), "utf8"));
const spec = manifest.windows.find((entry) => entry.id === "chat_room");
const requiredControls = spec.controls.filter((control) => control.actions.length > 0)
  .map((control) => control.id);
const requiredActions = spec.actions.map((binding) => ({ control_id: "chat_room",
  gesture: binding.gesture, window_action: binding.action })).concat(
  spec.controls.flatMap((control) => control.actions.map((binding) => ({
    control_id: control.id, gesture: binding.gesture, window_action: binding.action,
  }))));
const approved = new Set(requiredActions.map((entry) =>
  `${entry.control_id}:${entry.gesture}:${entry.window_action}`));
const sha256 = (path) => createHash("sha256").update(readFileSync(path)).digest("hex");

const browser = await chromium.launch({ headless: true,
  ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE
    ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE } : {}) });
const page = await browser.newPage({ viewport: DESIGN });
const consoleErrors = [];
page.on("console", (message) => {
  const text = message.text();
  if (["warning", "error"].includes(message.type())
    && !(text.includes("GL Driver Message") && text.includes("ReadPixels")))
    consoleErrors.push(`[${message.type()}] ${text}`.slice(0, 1000));
});
page.on("pageerror", (error) => consoleErrors.push(`[pageerror] ${String(error)}`));
await page.goto(URL, { waitUntil: "domcontentloaded", timeout: 90000 });
await page.waitForFunction(() => window.godotQaState?.windows?.chat_room,
  undefined, { timeout: 90000 });
await page.waitForTimeout(350);

const canvas = await page.evaluate(() => {
  const rect = document.querySelector("canvas").getBoundingClientRect();
  return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
});
const scale = Math.min(canvas.width / DESIGN.width, canvas.height / DESIGN.height);
const offsetX = canvas.x + (canvas.width - DESIGN.width * scale) / 2;
const offsetY = canvas.y + (canvas.height - DESIGN.height * scale) / 2;
const point = (x, y) => ({ x: offsetX + x * scale, y: offsetY + y * scale });
const qa = () => page.evaluate(() => window.godotQaState);
const chat = async () => (await qa()).windows.chat_room;
const waitChat = (predicate, argument = undefined) => page.waitForFunction(
  predicate, argument, { timeout: 5000 });
const neutral = async () => {
  const p = point(500, 500);
  await page.mouse.move(p.x, p.y);
	await page.waitForTimeout(180);
};
const shot = async (name) => {
  await neutral();
  const path = resolve(OUT, `${name}.png`);
  await page.screenshot({ path });
	return { path: `${name}.png`, sha256: sha256(path) };
};
const invariantShot = async (name) => {
	const path = resolve(OUT, `${name}.png`);
	await page.screenshot({ path, clip: INVARIANT });
	return { path: `${name}.png`, sha256: sha256(path) };
};
const reload = async () => {
  await page.reload({ waitUntil: "domcontentloaded", timeout: 90000 });
  await page.waitForFunction(() => window.godotQaState?.windows?.chat_room,
    undefined, { timeout: 90000 });
  await page.waitForTimeout(250);
};
const clickGeometry = async (geometry) => {
  const p = point(geometry.x + geometry.width / 2, geometry.y + geometry.height / 2);
  await page.mouse.click(p.x, p.y);
  await page.waitForTimeout(50);
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
const sourceCropAe = (frame) => {
  const reference = resolve(OUT, `.reference-${process.pid}.png`);
  const candidate = resolve(OUT, `.candidate-${process.pid}.png`);
  const geometry = `${CHAT.width}x${CHAT.height}+${CHAT.x}+${CHAT.y}`;
  for (const [input, output] of [[resolve(ROOT,
    "artifacts/references/ro-desktop-b/reference-native.png"), reference],
  [resolve(OUT, frame.path), candidate]]) {
    const result = spawnSync("convert", [input, "-crop", geometry, "+repage", output],
      { encoding: "utf8" });
    if (result.status !== 0) throw new Error(result.stderr);
  }
  const result = spawnSync("compare", ["-metric", "AE", reference, candidate, "null:"],
    { encoding: "utf8" });
  unlinkSync(reference);
  unlinkSync(candidate);
  return Number(`${result.stderr ?? ""}${result.stdout ?? ""}`.trim());
};

const actions = [];
const checks = [];
const record = (controlId, gesture, action, assertions, frames, observed,
  motionSamples = undefined) => {
  const pixelMetrics = metrics(frames.before, frames.after);
  const reversalMetrics = metrics(frames.before, frames.reversed);
  const entry = {
    control_id: controlId, gesture, window_action: action,
    expected: "Issue 135 Chat Room Behaviour Card and frozen manifest",
    observed: JSON.stringify(observed), responsive: Object.values(assertions).every(Boolean),
    matches_expected: Object.values(assertions).every(Boolean), expected_rejection: false,
    assertions, frames, intended_region: INTENDED, invariant_region: INVARIANT,
    pixel_metrics: pixelMetrics, reversal_pixel_metrics: reversalMetrics,
    contract_facts: { real_gesture_path: true,
      intended_region_changed: pixelMetrics.intended_region_changed_pixels > 0,
      invariants_stable: pixelMetrics.invariant_region_changed_pixels === 0,
      source_approved: approved.has(`${controlId}:${gesture}:${action}`),
      reversible: Object.values(reversalMetrics).every((value) => value === 0) },
  };
  if (motionSamples) entry.motion_samples = motionSamples;
  actions.push(entry);
  checks.push({ name: `${controlId}:${gesture}:${action}`,
    passed: entry.responsive && Object.values(entry.contract_facts).every(Boolean) });
};
const focusInput = async () => clickGeometry((await chat()).controls["chat_room.input"].geometry);
const send = async (text, key = "Enter") => {
  await page.keyboard.type(text);
  const expected = (await chat()).window_state.lines.length + 1;
  await page.keyboard.press(key);
  await waitChat((count) => window.godotQaState.windows.chat_room.window_state.lines.length
    === count, expected);
};
const seedLog = async () => {
  await focusInput();
  for (const text of ["one", "two", "three", "four"]) await send(text);
  await neutral();
};

let initial = await chat();
let before = await shot("00-source-idle");
const invariantBefore = await invariantShot("00-invariant-before");
const sourceAe = sourceCropAe(before);
checks.push({ name: "source-crop-exact", passed: sourceAe === 0, source_ae: sourceAe });
checks.push({ name: "modern-tabs-absent", passed: !Object.keys(initial.controls)
  .some((id) => id.includes("tab")) });
checks.push({ name: "unidentified-icon-no-hit-target", passed: Object.keys(initial.controls)
  .every((id) => !id.includes("icon")) });

await focusInput();
await page.keyboard.type("draft");
await waitChat(() => window.godotQaState.windows.chat_room.window_state.draft === "draft");
let observed = await chat();
let after = await shot("01-draft-after");
const fullStateBytes = await page.evaluate(() => JSON.stringify(window.godotQaState).length);
const patchMetrics = await page.evaluate(() => window.godotQaMetrics);
await reload();
let reversed = await shot("01-draft-reversed");
record("chat_room.input", "KeyCommand", "SetChatDraft", {
  exact_draft: observed.window_state.draft === "draft",
  rendered_text: observed.controls["chat_room.input"].rendered_text === "draft",
  changed_window_patch: patchMetrics.lastWasPatch === true,
  smaller_than_full_state: patchMetrics.maxPatchBytes < fullStateBytes,
}, { before, after, reversed }, { state: observed.window_state, patchMetrics });

before = await shot("02-submit-before");
await focusInput();
await send("hello");
observed = await chat();
after = await shot("02-submit-after");
await reload();
reversed = await shot("02-submit-reversed");
record("chat_room.input", "KeyCommand", "SubmitChat", {
  input_cleared: observed.controls["chat_room.input"].rendered_text === "",
  one_exact_echo: observed.window_state.lines.length === 6,
  exact_text: observed.window_state.lines.at(-1).text === "hello",
  screen_scope: observed.window_state.lines.at(-1).scope === "screen",
}, { before, after, reversed }, observed.window_state.lines.at(-1));

await focusInput();
for (const [text, key, scope] of [["p", "Control+Enter", "party"],
  ["g", "Alt+Enter", "guild"], ["a", "Shift+Enter", "allied_guild"]]) {
  await send(text, key);
  const line = (await chat()).window_state.lines.at(-1);
  checks.push({ name: `modifier-${scope}`, passed: line.text === text && line.scope === scope });
}

await reload();
before = await shot("03-rows-before");
await page.keyboard.press("F10");
await waitChat(() => window.godotQaState.windows.chat_room.window_state.visible_row_count === 7);
observed = await chat();
after = await shot("03-rows-after");
await page.keyboard.press("F10");
await page.keyboard.press("F10");
await waitChat(() => window.godotQaState.windows.chat_room.window_state.visible_row_count === 5);
reversed = await shot("03-rows-reversed");
record("chat_room", "KeyCommand", "ChangeChatRows", {
  seven_rows: observed.window_state.visible_row_count === 7,
  cycle_reversed: (await chat()).window_state.visible_row_count === 5,
}, { before, after, reversed }, observed.window_state);

await reload();
await seedLog();
let scroll = (await chat()).controls["chat_room.scroll"].geometry;
before = await shot("04-wheel-before");
let p = point(scroll.x + 10, scroll.y + 80);
await page.mouse.move(p.x, p.y);
const wheelStart = (await chat()).controls["chat_room.scroll"].offset;
await page.mouse.wheel(0, -120);
await waitChat((offset) => window.godotQaState.windows.chat_room.controls[
  "chat_room.scroll"].offset !== offset, wheelStart);
observed = await chat();
after = await shot("04-wheel-after");
const reverseWheelStart = observed.controls["chat_room.scroll"].offset;
await page.mouse.move(p.x, p.y);
await page.mouse.wheel(0, 120);
await waitChat((offset) => window.godotQaState.windows.chat_room.controls[
  "chat_room.scroll"].offset !== offset, reverseWheelStart);
reversed = await shot("04-wheel-reversed");
record("chat_room.scroll", "Wheel", "ScrollChatLog", {
  exactly_three_rows: observed.controls["chat_room.scroll"].offset === 1,
  clamp_reversed: (await chat()).controls["chat_room.scroll"].offset === 4,
}, { before, after, reversed }, observed.controls["chat_room.scroll"]);

before = await shot("05-arrow-before");
await clickGeometry({ x: scroll.x, y: scroll.y, width: 20, height: 20 });
observed = await chat();
after = await shot("05-arrow-after");
await clickGeometry({ x: scroll.x, y: scroll.y + 132, width: 20, height: 20 });
reversed = await shot("05-arrow-reversed");
record("chat_room.scroll", "Activate", "StepChatLog", {
  exactly_one_row: observed.controls["chat_room.scroll"].offset === 3,
  reversed_to_end: (await chat()).controls["chat_room.scroll"].offset === 4,
}, { before, after, reversed }, observed.controls["chat_room.scroll"]);

before = await shot("06-thumb-before");
observed = await chat();
const thumbStart = point(scroll.x + 10,
  scroll.y + observed.controls["chat_room.scroll"].thumb_y + 20);
const thumbEnd = point(scroll.x + 10, scroll.y + 43);
const thumbSamples = [];
await page.mouse.move(thumbStart.x, thumbStart.y);
await page.mouse.down();
let mid;
for (let index = 0; index <= 30; index += 1) {
  const sample = [thumbStart.x + (thumbEnd.x - thumbStart.x) * index / 30,
    thumbStart.y + (thumbEnd.y - thumbStart.y) * index / 30];
  thumbSamples.push(sample);
  await page.mouse.move(sample[0], sample[1]);
  if (index === 15) mid = await shot("06-thumb-mid");
}
await page.mouse.up();
observed = await chat();
after = await shot("06-thumb-after");
const reverseThumb = point(scroll.x + 10,
  scroll.y + observed.controls["chat_room.scroll"].thumb_y + 20);
const bottom = point(scroll.x + 10, scroll.y + 126);
await page.mouse.move(reverseThumb.x, reverseThumb.y);
await page.mouse.down();
for (let index = 0; index <= 30; index += 1) await page.mouse.move(
  reverseThumb.x + (bottom.x - reverseThumb.x) * index / 30,
  reverseThumb.y + (bottom.y - reverseThumb.y) * index / 30);
await page.mouse.up();
reversed = await shot("06-thumb-reversed");
record("chat_room.scroll", "Drag", "SetChatLogOffset", {
  clamped_at_start: observed.controls["chat_room.scroll"].offset === 0,
  reversed_at_end: (await chat()).controls["chat_room.scroll"].offset === 4,
}, { before, mid, after, reversed }, observed.controls["chat_room.scroll"], thumbSamples);

await reload();
observed = await chat();
before = await shot("07-drag-before");
const dragStart = point(observed.window.position[0] + 150, observed.window.position[1] + 12);
const dragEnd = point(850, 650);
const dragSamples = [];
await page.mouse.move(dragStart.x, dragStart.y);
await page.mouse.down();
for (let index = 0; index <= 30; index += 1) {
  const sample = [dragStart.x + (dragEnd.x - dragStart.x) * index / 30,
    dragStart.y + (dragEnd.y - dragStart.y) * index / 30];
  dragSamples.push(sample);
  await page.mouse.move(sample[0], sample[1]);
  if (index === 15) mid = await shot("07-drag-mid");
}
await page.mouse.up();
observed = await chat();
after = await shot("07-drag-after");
const reverseStart = point(observed.window.position[0] + 150, observed.window.position[1] + 12);
await page.mouse.move(reverseStart.x, reverseStart.y);
await page.mouse.down();
for (let index = 0; index <= 30; index += 1) await page.mouse.move(
  reverseStart.x + (dragStart.x - reverseStart.x) * index / 30,
  reverseStart.y + (dragStart.y - reverseStart.y) * index / 30);
await page.mouse.up();
reversed = await shot("07-drag-reversed");
record("chat_room", "Drag", "MoveWindow", {
  moved: observed.window.position[0] !== CHAT.x || observed.window.position[1] !== CHAT.y,
  viewport_clamped: observed.window.position[0] >= 0 && observed.window.position[1] >= 0,
  restored_home: (await chat()).window.position[0] === CHAT.x
    && (await chat()).window.position[1] === CHAT.y,
}, { before, mid, after, reversed }, observed.window, dragSamples);

await reload();
before = await shot("08-close-before");
await clickGeometry((await chat()).controls["chat_room.close"].geometry);
await waitChat(() => !window.godotQaState.windows.chat_room.window.visible);
observed = await chat();
after = await shot("08-close-after");
await page.keyboard.press("Alt+F10");
await waitChat(() => window.godotQaState.windows.chat_room.window.visible);
reversed = await shot("08-close-reversed");
record("chat_room.close", "Activate", "CloseWindow", { hidden: !observed.window.visible },
  { before, after, reversed }, observed.window);

before = await shot("09-escape-before");
await page.keyboard.press("Escape");
await waitChat(() => !window.godotQaState.windows.chat_room.window.visible);
observed = await chat();
after = await shot("09-escape-after");
await page.keyboard.press("Alt+F10");
await waitChat(() => window.godotQaState.windows.chat_room.window.visible);
reversed = await shot("09-escape-reversed");
record("chat_room", "KeyCommand", "CloseWindow", { hidden: !observed.window.visible },
  { before, after, reversed }, observed.window);

before = await shot("10-toggle-before");
await page.keyboard.press("Alt+F10");
await waitChat(() => !window.godotQaState.windows.chat_room.window.visible);
observed = await chat();
after = await shot("10-toggle-after");
await page.keyboard.press("Alt+F10");
await waitChat(() => window.godotQaState.windows.chat_room.window.visible);
reversed = await shot("10-toggle-reversed");
record("chat_room", "KeyCommand", "ToggleWindow", {
  hidden: !observed.window.visible, restored: (await chat()).window.visible,
}, { before, after, reversed }, observed.window);

const semanticBefore = (await chat()).window_state;
await clickGeometry((await chat()).controls["chat_room.close"].geometry);
const basic = (await qa()).windows.basic_info;
await clickGeometry(basic.controls["basic_info.destination.chat"].geometry);
await waitChat(() => window.godotQaState.windows.chat_room.window.visible);
const routed = await qa();
checks.push({ name: "basic-info-chat-route", passed:
  routed.last_transaction.target_window === "chat_room"
  && routed.last_transaction.semantic_state_preserved === true
	&& JSON.stringify(routed.windows.chat_room.window_state) === JSON.stringify(semanticBefore) });

const invariantAfter = await invariantShot("zz-invariant-after");

const playLog = { schema_version: "image79-play-log-v2",
  candidate: { issue: 135, commit_sha: CANDIDATE, window_id: "chat_room" },
  source_reference_sha256: manifest.reference.sha256,
	required_controls: requiredControls, required_actions: requiredActions,
	invariant_frames: { before: invariantBefore, after: invariantAfter },
  source_crop_ae: sourceAe, provider_requests: 0, console_errors: consoleErrors,
  qa_metrics: await page.evaluate(() => window.godotQaMetrics), checks, actions };
writeFileSync(resolve(OUT, "play-log.json"), `${JSON.stringify(playLog, null, 2)}\n`);
await browser.close();
const failed = checks.filter((entry) => !entry.passed);
console.log(JSON.stringify({ checks: checks.length, failed: failed.length,
  actions: actions.length, console_errors: consoleErrors.length,
  source_crop_ae: sourceAe, output: OUT }));
if (failed.length > 0 || consoleErrors.length > 0) process.exit(1);
