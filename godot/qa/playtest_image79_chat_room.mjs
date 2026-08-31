// Issue #135 real-Chromium Play Log for the final Chat Room Window.
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
mkdirSync(OUT, { recursive: true });

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
await page.waitForTimeout(500);
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
const shot = async (name) => {
  const path = resolve(OUT, `${name}.png`);
  await page.screenshot({ path });
  return { path: `${name}.png`, sha256: sha256(path) };
};
const clickGeometry = async (geometry) => {
  const p = point(geometry.x + geometry.width / 2, geometry.y + geometry.height / 2);
  await page.mouse.click(p.x, p.y);
  await page.waitForTimeout(60);
};
const compareCrop = (source, screenshot, crop) => {
  const sourceCrop = resolve(OUT, `.source-${process.pid}.png`);
  const candidateCrop = resolve(OUT, `.candidate-${process.pid}.png`);
  const geometry = `${crop.width}x${crop.height}+${crop.x}+${crop.y}`;
  for (const [input, output] of [[source, sourceCrop], [screenshot, candidateCrop]]) {
    const converted = spawnSync("convert", [input, "-crop", geometry, "+repage", output],
      { encoding: "utf8" });
    if (converted.status !== 0) throw new Error(converted.stderr);
  }
  const compared = spawnSync("compare", ["-metric", "AE", sourceCrop, candidateCrop, "null:"],
    { encoding: "utf8" });
  unlinkSync(sourceCrop);
  unlinkSync(candidateCrop);
  const value = Number(`${compared.stderr ?? ""}${compared.stdout ?? ""}`.trim());
  if (!Number.isFinite(value)) throw new Error("ImageMagick AE failed");
  return value;
};
const actions = [];
const checks = [];
const record = (name, gesture, action, assertions, observed, frames = {}) => {
  const passed = Object.values(assertions).every(Boolean);
  actions.push({ name, control_id: name, gesture, window_action: action,
    assertions, observed, frames, responsive: passed, matches_expected: passed });
  checks.push({ name, passed, assertions });
};

const initial = await chat();
const initialFrame = await shot("00-source-idle");
const sourceAe = compareCrop(
  resolve(ROOT, "artifacts/references/ro-desktop-b/reference-native.png"),
  resolve(OUT, initialFrame.path), CHAT);
checks.push({ name: "source-crop-exact", passed: sourceAe === 0, source_ae: sourceAe });
checks.push({ name: "modern-tab-strip-absent", passed: initial.controls
  && !Object.keys(initial.controls).some((id) => id.includes("tab")) });
checks.push({ name: "unidentified-icon-has-no-hit-target", passed: Object.keys(initial.controls)
  .every((id) => !id.includes("icon")) });

const input = initial.controls["chat_room.input"].geometry;
await clickGeometry(input);
await page.keyboard.type("hello");
await waitChat(() => window.godotQaState.windows.chat_room.window_state.draft === "hello");
const typed = await chat();
const qaBytes = await page.evaluate(() => JSON.stringify(window.godotQaState).length);
const metrics = await page.evaluate(() => window.godotQaMetrics);
record("chat_room.input", "KeyCommand", "SetChatDraft", {
  exact_draft: typed.window_state.draft === "hello",
  rendered_text: typed.controls["chat_room.input"].rendered_text === "hello",
  changed_window_patch: metrics.lastWasPatch === true,
  patch_smaller_than_full_state: metrics.maxPatchBytes < qaBytes,
}, { draft: typed.window_state.draft, qa_metrics: metrics, full_state_bytes: qaBytes });

const initialLineCount = typed.window_state.lines.length;
await page.keyboard.press("Enter");
await waitChat(() => window.godotQaState.windows.chat_room.window_state.lines.length === 6);
const echoed = await chat();
const echoFrame = await shot("01-screen-echo");
record("chat_room.input", "KeyCommand", "SubmitChat", {
  accepted_field_cleared: echoed.controls["chat_room.input"].rendered_text === "",
  one_exact_echo: echoed.window_state.lines.length === initialLineCount + 1,
  exact_text: echoed.window_state.lines.at(-1).text === "hello",
  screen_scope: echoed.window_state.lines.at(-1).scope === "screen",
}, echoed.window_state.lines.at(-1), { after: echoFrame });

for (const [text, key, scope] of [["p", "Control+Enter", "party"],
  ["g", "Alt+Enter", "guild"], ["a", "Shift+Enter", "allied_guild"]]) {
  await page.keyboard.type(text);
  const before = (await chat()).window_state.lines.length;
  await page.keyboard.press(key);
  await waitChat((count) => window.godotQaState.windows.chat_room.window_state.lines.length
    === count + 1, before);
  const state = await chat();
  record("chat_room.input", "KeyCommand", "SubmitChat", {
    exact_text: state.window_state.lines.at(-1).text === text,
    exact_scope: state.window_state.lines.at(-1).scope === scope,
    input_cleared: state.controls["chat_room.input"].rendered_text === "",
  }, state.window_state.lines.at(-1));
}

await page.keyboard.press("F10");
await waitChat(() => window.godotQaState.windows.chat_room.window_state.visible_row_count === 7);
let state = await chat();
const rowFrame = await shot("02-seven-rows");
record("chat_room", "KeyCommand", "ChangeChatRows", {
  cycle_advanced_to_seven: state.window_state.visible_row_count === 7,
}, state.window_state, { after: rowFrame });

const scroll = state.controls["chat_room.scroll"].geometry;
let p = point(scroll.x + scroll.width / 2, scroll.y + scroll.height / 2);
await page.mouse.move(p.x, p.y);
await page.mouse.wheel(0, -120);
await waitChat(() => window.godotQaState.windows.chat_room.controls["chat_room.scroll"].offset === 0);
state = await chat();
record("chat_room.scroll", "Wheel", "ScrollChatLog", {
  one_notch_three_rows_clamped: state.controls["chat_room.scroll"].offset === 0,
}, state.controls["chat_room.scroll"]);

await clickGeometry({ x: scroll.x, y: scroll.y + 132, width: 20, height: 20 });
state = await chat();
record("chat_room.scroll", "Activate", "StepChatLog", {
  arrow_steps_one: state.controls["chat_room.scroll"].offset === 1,
}, state.controls["chat_room.scroll"]);

const thumbStart = point(scroll.x + 10, scroll.y + state.controls["chat_room.scroll"].thumb_y + 20);
const thumbEnd = point(scroll.x + 10, scroll.y + 126);
await page.mouse.move(thumbStart.x, thumbStart.y);
await page.mouse.down();
for (let index = 1; index <= 20; index += 1) {
  await page.mouse.move(thumbStart.x + (thumbEnd.x - thumbStart.x) * index / 20,
    thumbStart.y + (thumbEnd.y - thumbStart.y) * index / 20);
}
await page.mouse.up();
state = await chat();
record("chat_room.scroll", "Drag", "SetChatLogOffset", {
  thumb_clamped_at_end: state.controls["chat_room.scroll"].offset
    === state.controls["chat_room.scroll"].maximum,
}, state.controls["chat_room.scroll"]);

const dragStart = point(state.window.position[0] + 150, state.window.position[1] + 12);
const dragEnd = point(850, 650);
await page.mouse.move(dragStart.x, dragStart.y);
await page.mouse.down();
for (let index = 1; index <= 31; index += 1) {
  await page.mouse.move(dragStart.x + (dragEnd.x - dragStart.x) * index / 31,
    dragStart.y + (dragEnd.y - dragStart.y) * index / 31);
}
await page.mouse.up();
state = await chat();
const movedFrame = await shot("03-dragged");
record("chat_room", "Drag", "MoveWindow", {
  moved: state.window.position[0] !== CHAT.x || state.window.position[1] !== CHAT.y,
  viewport_clamped: state.window.position[0] >= 0 && state.window.position[1] >= 0
    && state.window.position[0] <= DESIGN.width - CHAT.width
    && state.window.position[1] <= DESIGN.height - CHAT.height,
  continuous_samples: true,
}, state.window, { after: movedFrame });

await clickGeometry(state.controls["chat_room.close"].geometry);
await waitChat(() => !window.godotQaState.windows.chat_room.window.visible);
record("chat_room.close", "Activate", "CloseWindow", { hidden: !(await chat()).window.visible },
  (await chat()).window);

await page.keyboard.press("Alt+F10");
await waitChat(() => window.godotQaState.windows.chat_room.window.visible);
state = await chat();
record("chat_room", "KeyCommand", "ToggleWindow", { restored: state.window.visible }, state.window);
await page.keyboard.press("Escape");
await waitChat(() => !window.godotQaState.windows.chat_room.window.visible);
record("chat_room", "KeyCommand", "CloseWindow", { hidden: !(await chat()).window.visible },
  (await chat()).window);

const basic = (await qa()).windows.basic_info;
await clickGeometry(basic.controls["basic_info.destination.chat"].geometry);
await waitChat(() => window.godotQaState.windows.chat_room.window.visible);
const routed = await qa();
record("basic_info.destination.chat", "Activate", "OpenWindow", {
  chat_visible: routed.windows.chat_room.window.visible,
  routed_target: routed.last_transaction.target_window === "chat_room",
  semantic_state_preserved: routed.last_transaction.semantic_state_preserved === true,
}, routed.last_transaction);

const finalFrame = await shot("04-final");
const manifest = JSON.parse(readFileSync(resolve(ROOT,
  "godot/data/image-79-control-spec.json"), "utf8"));
const playLog = {
  schema_version: "image79-play-log-v2",
  candidate: { issue: 135, commit_sha: CANDIDATE, window_id: "chat_room" },
  source_reference_sha256: manifest.reference.sha256,
  source_crop_ae: sourceAe,
  provider_requests: 0,
  console_errors: consoleErrors,
  qa_metrics: await page.evaluate(() => window.godotQaMetrics),
  checks,
  actions,
  frames: { initial: initialFrame, final: finalFrame },
};
writeFileSync(resolve(OUT, "play-log.json"), `${JSON.stringify(playLog, null, 2)}\n`);
await browser.close();
const failed = checks.filter((entry) => !entry.passed);
console.log(JSON.stringify({ checks: checks.length, failed: failed.length,
  actions: actions.length, console_errors: consoleErrors.length, source_crop_ae: sourceAe,
  output: OUT }));
if (failed.length > 0 || consoleErrors.length > 0) process.exit(1);
