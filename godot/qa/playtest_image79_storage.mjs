// Builder-side browser drive for Issue #128. Real browser wheel, pointer, and
// keyboard input produce the Storage Play Log and evidence frames.
import { createRequire } from "node:module";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
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
const record = (controlId, gesture, action, assertions, actionFrames, observed) => {
  const matches = Object.values(assertions).every(Boolean);
  actions.push({ control_id: controlId, gesture, window_action: action,
    expected: "manifest and Behaviour Card", observed, responsive: matches,
    matches_expected: matches, assertions, frames: actionFrames });
  check(`${controlId}:${gesture}:${action}`, matches, assertions);
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

const manifest = JSON.parse(readFileSync(resolve(ROOT,
  "godot/data/image-79-control-spec.json"), "utf8"));
const windowSpec = manifest.windows.find((entry) => entry.id === "storage");
const idle = await shot("00-idle");
const initial = await storage();
check("idle-factual", initial.window.size[0] === 539 && initial.window.size[1] === 393
  && initial.controls["storage.items"].surface_geometry
  && Object.keys(initial.controls["storage.items"].surface_geometry).length === 35,
  initial.window);

await click(537, 704);
const category = await control("storage.categories");
const categoryFrame = await shot("01-category-equipment");
record("storage.categories", "Activate", "SelectStorageCategory", {
  selected: category.value === "equipment",
  routed: category.last_action === "SelectStorageCategory",
}, { before: idle, after: categoryFrame }, category.value);

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

await click(1007, 946);
const arrow = await control("storage.scroll");
record("storage.scroll", "Activate", "StepStorageScroll", {
  exact_one_row: arrow.offset === 4,
}, { before: wheelFrame, after: await shot("03-arrow-one-row") }, arrow.offset);

const thumbStart = point(1007, 862);
const thumbEnd = point(1007, 680);
await page.mouse.move(thumbStart.x, thumbStart.y);
await page.mouse.down();
const samples = [];
for (let index = 0; index < 31; index += 1) {
  const t = index / 30;
  await page.mouse.move(thumbStart.x, thumbStart.y + (thumbEnd.y - thumbStart.y) * t);
  await page.waitForTimeout(12);
  samples.push((await control("storage.scroll")).offset);
}
await page.mouse.up();
const dragged = await control("storage.scroll");
record("storage.scroll", "Drag", "SetStorageScrollOffset", {
  continuous: samples.length === 31,
  moved_toward_start: dragged.offset < arrow.offset,
  clamped: dragged.offset >= 0 && dragged.offset <= dragged.maximum,
}, { before: wheelFrame, after: await shot("04-thumb-drag") }, samples);

await click(779, 977);
await page.keyboard.type("Potion 70", { delay: 25 });
await page.waitForTimeout(80);
const searched = await storage();
const searchFrame = await shot("05-search-filtered");
record("storage.search", "KeyCommand", "FilterStorage", {
  accepted_text_rendered: searched.controls["storage.search"].rendered_text === "Potion 70",
  filtered_one: searched.controls["storage.items"].filtered_items.length === 1,
  scroll_reset: searched.controls["storage.scroll"].offset === 0,
}, { before: frames["04-thumb-drag"], after: searchFrame },
searched.controls["storage.search"].rendered_text);

await click(632, 977);
const listed = await storage();
const listFrame = await shot("06-list-mode");
record("storage.list", "Activate", "ToggleStorageView", {
  list_mode: listed.window.view_mode === "list" && listed.controls["storage.items"].list_mode,
}, { before: searchFrame, after: listFrame }, listed.window.view_mode);
await click(878, 977);
const sorted = await control("storage.items");
record("storage.sort", "Activate", "SortStorage", {
  reversed_order: sorted.sort_ascending === false,
}, { before: listFrame, after: await shot("07-sorted") }, sorted.sort_ascending);
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
}, { before: frames["07-sorted"], after: await shot("08-transfer-rejected") },
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

await click(779, 977);
await page.keyboard.type("r0c0", { delay: 25 });
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
await page.mouse.move(dragStart.x, dragStart.y);
await page.mouse.down();
for (let index = 1; index <= 20; index += 1) {
  await page.mouse.move(dragStart.x + (dragEnd.x - dragStart.x) * index / 20,
    dragStart.y + (dragEnd.y - dragStart.y) * index / 20);
}
await page.mouse.up();
const moved = await storage();
record("storage", "Drag", "MoveWindow", {
  moved: moved.window.position[0] === 552 && moved.window.position[1] === 569,
}, { before: frames["10-transfer-returned"], after: await shot("11-window-moved") },
moved.window.position);

await browser.close();
const failed = checks.filter((entry) => !entry.passed);
const errors = consoleEntries.filter((entry) => entry.startsWith("[error]")
  || entry.startsWith("[pageerror]"));
const report = {
  schema_version: 2,
  issue: 128,
  candidate: { issue: 128,
    commit_sha: execFileSync("git", ["rev-parse", "HEAD"],
      { cwd: ROOT, encoding: "utf8" }).trim(),
    window_id: "storage" },
  url: URL,
  reference: manifest.reference,
  window: { id: "storage", geometry: windowSpec.geometry },
  driver: "Playwright Chromium real pointer, wheel, and keyboard input",
  actions,
  checks,
  frames,
  console_entries: consoleEntries,
  summary: { pass: failed.length === 0 && errors.length === 0,
    total: checks.length, failed: failed.length, console_errors: errors.length },
};
writeFileSync(resolve(OUT, "play-log.json"), `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report.summary));
process.exitCode = report.summary.pass ? 0 : 1;
