// Builder-side browser drive for issue #126. Exercises every declared Skill
// Tree Window Action with real pointer input and emits a deterministic Play Log.
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
  ?? resolve(SCRIPT_DIR, "out/image79-skill-tree-browser"));
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
await page.waitForFunction(() => window.godotQaState?.windows?.skill_tree,
  undefined, { timeout: 90000 });
// QA state is available before the Web renderer has uploaded every texture.
// Freeze evidence only after the same settling interval as the Options drive.
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
const skillTree = async () => (await qa()).windows.skill_tree;
const control = async (id) => (await skillTree()).controls[id];
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
const click = async (x, y, button = "left") => {
  const target = point(x, y);
  await page.mouse.move(target.x, target.y);
  await page.mouse.down({ button });
  await page.waitForTimeout(20);
  await page.mouse.up({ button });
  await page.waitForTimeout(20);
};

const manifest = JSON.parse(readFileSync(resolve(ROOT,
  "godot/data/image-79-control-spec.json"), "utf8"));
const windowSpec = manifest.windows.find((entry) => entry.id === "skill_tree");
const selectionSpec = windowSpec.controls.find((entry) => entry.type === "SelectionView");
const stepperSpecs = windowSpec.controls.filter((entry) => entry.type === "Stepper");

const idle = await shot("00-idle");
const invariantBefore = await invariantShot("00-invariant-before");
const initial = await skillTree();
const initialSteppers = Object.values(initial.controls)
  .filter((entry) => entry.type === "Stepper");
check("idle-factual-state", initial.window.pending === false
  && initialSteppers.length === 26
  && initialSteppers.every((entry) => entry.arrows_visible), {
  pending: initial.window.pending, steppers: initialSteppers.length,
});

await click(558, 87);
const selected = await control("skill_tree.skills");
const selectedFrame = await shot("01-selected");
record("skill_tree.skills", "Activate", "SelectSkill",
  "left click changes selection from r1c3 to r1c1", JSON.stringify(selected), {
    selected: selected.value === "r1c1",
    gesture_distinct: selected.last_gesture === "Activate",
    action_routed: selected.last_action === "SelectSkill",
  }, { before: idle, after: selectedFrame });

await click(558, 87, "right");
const detailed = await control("skill_tree.skills");
const detailedWindow = (await skillTree()).window;
const detailedFrame = await shot("02-context-detail");
record("skill_tree.skills", "ContextActivate", "OpenSkillDetail",
  "right click opens the selected skill detail", JSON.stringify(detailed), {
    context_gesture: detailed.last_gesture === "ContextActivate",
    action_routed: detailed.last_action === "OpenSkillDetail",
    detail_visible: detailed.detail_visible && detailedWindow.detail_item === "r1c1",
    detail_manifest_backed: detailed.detail_text === selectionSpec.value.details.r1c1,
  }, { before: selectedFrame, after: detailedFrame });

// Dismiss the detail through the reversible view Action so the pending-frame
// corpus exposes every Stepper region for blind visual review.
await click(1048, 15);
await click(1048, 15);
await page.waitForTimeout(2000);
check("context-detail-dismissed-before-stepper-visuals",
  (await control("skill_tree.skills")).detail_visible === false,
  await control("skill_tree.skills"));

const boundSpec = stepperSpecs.find((entry) => entry.id === "skill_tree.stepper.r1c3");
const boundBefore = await control(boundSpec.id);
const boundBeforeFrame = await shot("02b-bound-before");
await click(boundBefore.geometry.x + boundBefore.geometry.width - 4,
  boundBefore.geometry.y + boundBefore.geometry.height / 2);
const boundAfter = await control(boundSpec.id);
const boundAfterFrame = await shot("02b-bound-rejected");
record(boundSpec.id, "Activate", "StepSkill",
  "a beyond-bound click rejects without opening a Window transaction",
  JSON.stringify(boundAfter), {
    rejected: boundAfter.last_result.accepted === false,
    typed_error: boundAfter.last_result.error?.code === "TransactionRejectedError",
    target_unchanged: boundAfter.target === boundBefore.target,
    transaction_not_opened: (await skillTree()).window.pending === false,
  }, { before: boundBeforeFrame, after: boundAfterFrame });

for (const [index, spec] of stepperSpecs.entries()) {
  const before = await control(spec.id);
  const beforeFrame = await shot(`03-${String(index).padStart(2, "0")}-${spec.id}-before`);
  const direction = before.target < before.maximum ? 1 : -1;
  const x = before.geometry.x + (direction > 0 ? before.geometry.width - 4 : 4);
  const y = before.geometry.y + before.geometry.height / 2;
  await click(x, y);
  const pending = await skillTree();
  const after = pending.controls[spec.id];
  const allHidden = Object.values(pending.controls)
    .filter((entry) => entry.type === "Stepper")
    .every((entry) => entry.arrows_visible === false);
  const afterFrame = await shot(`03-${String(index).padStart(2, "0")}-${spec.id}-after`);
  record(spec.id, "Activate", "StepSkill", "one arrow step starts one Window transaction",
    `${before.text} -> ${after.text}`, {
      target_changed: after.target === before.target + direction * before.step,
      pending_same_frame: pending.window.pending && after.pending,
      all_arrows_hidden: allHidden,
      live_current_target_text: after.text === `${after.current} / ${after.target}`,
    }, { before: beforeFrame, after: afterFrame });
  await click(1046, 569);
  const cancelled = await skillTree();
  check(`${spec.id}:cancel-reset`, !cancelled.window.pending
    && cancelled.controls[spec.id].target === before.current
    && cancelled.controls[spec.id].arrows_visible, cancelled.controls[spec.id]);
}

const commitId = "skill_tree.stepper.r2c4";
const commitBefore = await control(commitId);
await click(commitBefore.geometry.x + commitBefore.geometry.width - 4,
  commitBefore.geometry.y + commitBefore.geometry.height / 2);
const preCommit = await control(commitId);
const commitPendingFrame = await shot("04-commit-before");
await click(957, 569);
await page.waitForTimeout(2000);
const committed = await skillTree();
const committedFrame = await shot("04-committed");
record("skill_tree.use", "Activate", "CommitSkillChanges",
  "Use commits every pending target and restores all arrows",
  JSON.stringify(committed.controls[commitId]), {
    committed: committed.controls[commitId].current === preCommit.target,
    transaction_cleared: !committed.window.pending,
    arrows_restored: Object.values(committed.controls)
      .filter((entry) => entry.type === "Stepper")
      .every((entry) => entry.arrows_visible),
  }, { before: commitPendingFrame, after: committedFrame });

const cancelBefore = await control(commitId);
await click(cancelBefore.geometry.x + cancelBefore.geometry.width - 4,
  cancelBefore.geometry.y + cancelBefore.geometry.height / 2);
const cancelPendingFrame = await shot("05-cancel-before");
await click(1046, 569);
await page.waitForTimeout(2000);
const cancelled = await skillTree();
const cancelledFrame = await shot("05-cancelled");
record("skill_tree.cancel", "Activate", "CancelSkillChanges",
  "Cancel discards every pending target and restores all arrows",
  JSON.stringify(cancelled.controls[commitId]), {
    target_restored: cancelled.controls[commitId].target === cancelBefore.current,
    transaction_cleared: !cancelled.window.pending,
    arrows_restored: cancelled.controls[commitId].arrows_visible,
  }, { before: cancelPendingFrame, after: cancelledFrame });

await click(1048, 15);
await page.waitForTimeout(1000);
const list = await skillTree();
record("skill_tree.view", "Activate", "ToggleSkillView",
  "View changes the reversible tree/list presentation", JSON.stringify(list.window), {
    list_mode: list.window.view_mode === "list" && list.controls["skill_tree.skills"].list_mode,
    committed_values_live: list.controls["skill_tree.skills"].list_values.r2c4
      === committed.controls[commitId].text,
  }, { before: cancelledFrame, after: await shot("06-list-view") });
await click(1048, 15);
const tree = await skillTree();
check("skill-tree-view-reversible", tree.window.view_mode === "tree"
  && !tree.controls["skill_tree.skills"].list_mode, tree.window);
const treeRestoredFrame = await shot("07-tree-restored");

await page.mouse.move(0, 0);
await page.waitForTimeout(20);
const descriptionBefore = await control("skill_tree.descriptions");
const descriptionBeforeFrame = await shot("08-descriptions-before");
await click(758, 19);
const descriptionAfter = await control("skill_tree.descriptions");
const descriptionAfterFrame = await shot("08-descriptions-on");
await click(758, 19);
await page.mouse.move(0, 0);
await page.waitForTimeout(20);
const descriptionReversedFrame = await shot("08-descriptions-reversed");
record("skill_tree.descriptions", "Activate", "ToggleValue",
  "description checkbox toggles and is reversible", JSON.stringify(descriptionAfter), {
    toggled: descriptionAfter.semantic_state !== descriptionBefore.semantic_state,
  }, { before: descriptionBeforeFrame, after: descriptionAfterFrame,
    reversed: descriptionReversedFrame });
check("skill-tree-descriptions-reversible",
  (await control("skill_tree.descriptions")).semantic_state === descriptionBefore.semantic_state,
  await control("skill_tree.descriptions"));

await page.mouse.move(0, 0);
await page.waitForTimeout(20);
const minimizeBefore = await shot("09-minimize-before");
await click(503, 12);
const minimized = (await skillTree()).window;
const minimizeAfter = await shot("09-minimized");
await click(503, 12);
const restored = (await skillTree()).window;
await page.mouse.move(0, 0);
await page.waitForTimeout(1000);
const minimizeRestoredFrame = await shot("10-minimize-restored");
record("skill_tree.minimize", "Activate", "ToggleMinimized",
  "swap to a purpose-built title strip and restore the full Window",
  JSON.stringify({ minimized, restored }), {
    distinct_plate: minimized.minimized && minimized.size[1] === 28,
    restored: !restored.minimized && restored.size[1] === 595,
    position_preserved: minimized.position[0] === restored.position[0]
      && minimized.position[1] === restored.position[1],
  }, { before: minimizeBefore, after: minimizeAfter,
    restored: minimizeRestoredFrame });

const title = point(620, 14);
const dragBefore = await shot("11-drag-before");
await page.mouse.move(title.x, title.y);
await page.mouse.down();
const positionSamples = [];
let dragMid;
for (let index = 0; index < 31; index += 1) {
  const t = index / 30;
  await page.mouse.move(title.x + 50 * t, title.y + 65 * t);
  await page.waitForTimeout(15);
  positionSamples.push((await skillTree()).window.position[0]);
  if (index === 15) dragMid = await shot("11-drag-mid");
}
await page.mouse.up();
const moved = (await skillTree()).window;
const dragAfter = await shot("11-drag-after");
record("skill_tree", "Drag", "MoveWindow", "Window follows continuous pointer motion",
  JSON.stringify(moved.position), {
    continuous_samples: positionSamples.length === 31,
    pointer_delta_applied: Math.abs(moved.position[0] - 542) < 1
      && Math.abs(moved.position[1] - 65) < 1,
  }, { before: dragBefore, mid: dragMid, after: dragAfter }, positionSamples);

await click(moved.position[0] + 598, moved.position[1] + 15);
const closed = (await skillTree()).window;
const closedFrame = await shot("12-button-closed");
record("skill_tree.close", "Activate", "CloseWindow", "close hides in one frame",
  JSON.stringify(closed), { hidden: closed.visible === false },
  { before: dragAfter, after: closedFrame });

await page.reload({ waitUntil: "networkidle", timeout: 90000 });
await page.waitForFunction(() => window.godotQaState?.windows?.skill_tree,
  undefined, { timeout: 90000 });
await page.waitForTimeout(2500);
const keyBefore = await shot("13-key-before");
await page.keyboard.press("Escape");
await page.waitForTimeout(50);
const keyClosed = (await skillTree()).window;
const keyAfter = await shot("13-key-closed");
record("skill_tree", "KeyCommand", "CloseWindow",
  "Escape routes through the Window binding and hides the frontmost Window",
  JSON.stringify(keyClosed), {
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
  candidate: { issue: 126,
    commit_sha: execFileSync("git", ["rev-parse", "HEAD"],
      { cwd: ROOT, encoding: "utf8" }).trim(), window_id: "skill_tree" },
  source_reference_sha256: manifest.reference.sha256,
  required_controls: requiredControls,
  required_actions: requiredActions,
  invariant_frames: { before: invariantBefore,
    after: await invariantShot("14-invariant-after") },
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
