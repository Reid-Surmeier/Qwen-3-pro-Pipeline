// Builder-side drive of the exported prototype -- NOT the verdict.
//
// ADR 0006: "The builder never produces the evidence that is judged."  This
// script exists so the builder can SEE the thing working before handing it to
// the blind Playtesters; everything it writes is labelled builder evidence.
//
// Usage:
//   PLAYWRIGHT_BROWSERS_PATH=/home/reidsurmeier/.cache/ms-playwright \
//   node replica/tools/drive_web.mjs
import { createRequire } from "node:module";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire("/home/reidsurmeier/.qwen-pipeline-claude-wt/godot/qa/web/node_modules/");
const { chromium } = require("playwright");

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(HERE, "../evidence/builder") + "/";
mkdirSync(OUT, { recursive: true });

const URL_ = process.env.PROTO_URL ?? "https://windows-wsl.taile06c45.ts.net/godot-v2-options/";
const DESIGN = { w: 1536, h: 1024 };
const WINDOW = { x: 1108, y: 297, w: 424, h: 202 };
const BGM_ROW = { x: 1216, y: 340, w: 300, h: 32 };

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: DESIGN.w, height: DESIGN.h }, ignoreHTTPSErrors: true });
const consoleLog = [];
page.on("console", (m) => consoleLog.push(`[${m.type()}] ${m.text()}`.slice(0, 400)));
page.on("pageerror", (e) => consoleLog.push(`[pageerror] ${String(e).slice(0, 400)}`));

await page.goto(URL_, { waitUntil: "networkidle", timeout: 90000 });
await page.waitForTimeout(9000);

const facts = await page.evaluate(() => {
  const c = document.querySelector("canvas");
  const r = c.getBoundingClientRect();
  return { canvas: { w: c.width, h: c.height, cssW: r.width, cssH: r.height, x: r.x, y: r.y }, dpr: devicePixelRatio };
});
const S = Math.min(facts.canvas.cssW / DESIGN.w, facts.canvas.cssH / DESIGN.h);
const OX = facts.canvas.x + (facts.canvas.cssW - DESIGN.w * S) / 2;
const OY = facts.canvas.y + (facts.canvas.cssH - DESIGN.h * S) / 2;
const toCss = (x, y) => ({ x: OX + x * S, y: OY + y * S });
const clipOf = (r) => ({ x: OX + r.x * S, y: OY + r.y * S, width: r.w * S, height: r.h * S });

const qa = () => page.evaluate(() => window.godotQaState ?? null);
const shot = async (name, rect) => {
  await page.screenshot({ path: OUT + name + ".png", ...(rect ? { clip: clipOf(rect) } : {}) });
  return name;
};

const report = { url: URL_, facts, scale: S, steps: [] };
const step = async (name, fn, rect = WINDOW) => {
  await fn();
  await page.waitForTimeout(220);
  const state = await qa();
  await shot(name, rect);
  // keep the per-step snapshot small: the full interaction log is stored once,
  // at the end, in report.final
  const { interaction_log, ...slim } = state ?? {};
  report.steps.push({ name, state: slim, log_tail: (interaction_log ?? []).slice(-3) });
  console.log(name, JSON.stringify({ bgm: state?.bgm, effect: state?.effect, minimized: state?.minimized, visible: state?.visible, skin: state?.skin, skin_open: state?.skin_open, pos: state?.position, hovered: state?.hovered }));
};

// ---------------------------------------------------------------- idle
report.boot = await qa();
await shot("00-idle-full", null);
await shot("01-idle-window", WINDOW);

// ---------------------------------------------------------------- hover
const HOVER_TARGETS = {
  "bgm-thumb": [1429, 357],
  "bgm-left-arrow": [1231, 357],
  "checkbox-skill": [1233, 475],
  "dropdown-arrow": [1506, 431],
  minimize: [1490, 313],
  close: [1516, 313],
};
for (const [name, at] of Object.entries(HOVER_TARGETS)) {
  const p = toCss(at[0], at[1]);
  await step(`02-hover-${name}`, async () => { await page.mouse.move(p.x, p.y); });
}
await page.mouse.move(toCss(700, 700).x, toCss(700, 700).y);

// ------------------------------------------------- BGM drag: 100 -> 0 -> 100
const TRACK = { x0: 1239, x1: 1464, y: 357 };
const grab = toCss(1429, TRACK.y);
await page.mouse.move(grab.x, grab.y);
await page.mouse.down();
await shot("03-thumb-pressed", BGM_ROW);
report.dragFrames = [];
const dragTo = async (designX, tag, n) => {
  const start = (await qa()).bgm;
  for (let i = 1; i <= n; i++) {
    const from = report.dragFrames.length ? report.dragFrames.at(-1).x : 1429;
    const x = from + (designX - from) / (n - i + 1);
    const p = toCss(x, TRACK.y);
    await page.mouse.move(p.x, p.y);
    await page.waitForTimeout(35);
    const s = await qa();
    report.dragFrames.push({ tag, i, x, bgm: s.bgm, thumb_x: s.bgm_thumb_x });
    await page.screenshot({ path: `${OUT}drag/${tag}-${String(i).padStart(2, "0")}.png`, clip: clipOf(BGM_ROW) });
  }
  console.log(`drag ${tag}: ${start.toFixed(2)} -> ${(await qa()).bgm.toFixed(2)}`);
};
mkdirSync(OUT + "drag", { recursive: true });
await dragTo(TRACK.x0 - 40, "to-min", 18); // past the left end: must clamp at 0
await dragTo(TRACK.x1 + 40, "to-max", 18); // past the right end: must clamp at 100
report.afterDragMax = await qa();
await shot("04-drag-clamped-max", BGM_ROW);
await page.mouse.up();
await shot("05-thumb-released", BGM_ROW);

// ---------------------------------------------------------------- arrows
for (let i = 0; i < 3; i++) {
  const p = toCss(1231, 357);
  await step(`06-arrow-left-${i}`, async () => { await page.mouse.click(p.x, p.y); }, BGM_ROW);
}
{
  const p = toCss(1471, 357);
  await step("07-arrow-right", async () => { await page.mouse.click(p.x, p.y); }, BGM_ROW);
}

// ------------------------------------------------------------------ wheel
{
  const p = toCss(1350, 357);
  await step("08-wheel-down", async () => { await page.mouse.move(p.x, p.y); await page.mouse.wheel(0, 120); }, BGM_ROW);
  await step("09-wheel-up", async () => { await page.mouse.wheel(0, -120); }, BGM_ROW);
}

// --------------------------------------------------------------- keyboard
{
  const p = toCss(1350, 357);
  await page.mouse.click(p.x, p.y);           // focus the BGM slider
  await page.waitForTimeout(200);
  for (const k of ["ArrowRight", "ArrowRight", "ArrowLeft", "End", "Home"]) {
    await step(`09b-key-${k}`, async () => { await page.keyboard.press(k); }, BGM_ROW);
  }
}

// ------------------------------------------------------------- cursor shapes
{
  const probes = {
    "title-bar": [1250, 308], minimize: [1490, 314], "slider-track": [1350, 357],
    "checkbox-skill": [1233, 475], "dropdown-field": [1350, 431], desktop: [400, 800],
  };
  report.cursors = {};
  for (const [n, at] of Object.entries(probes)) {
    const q = toCss(at[0], at[1]);
    await page.mouse.move(q.x, q.y);
    await page.waitForTimeout(220);
    report.cursors[n] = await page.evaluate(() => getComputedStyle(document.querySelector("canvas")).cursor);
  }
  console.log("cursors:", JSON.stringify(report.cursors));
}

// -------------------------------------------------------------- checkboxes
const CHECKS = { attack: [1143, 475], skill: [1233, 475], "bgm-on": [1494, 358] };
for (const [name, at] of Object.entries(CHECKS)) {
  const p = toCss(at[0], at[1]);
  await step(`10-toggle-${name}`, async () => { await page.mouse.click(p.x, p.y); });
  await step(`11-untoggle-${name}`, async () => { await page.mouse.click(p.x, p.y); });
}

// ------------------------------------------------- reversibility (gate 5)
// A toggle out and back must restore byte-identical pixels.
for (const [name, at] of Object.entries(CHECKS)) {
  const p = toCss(at[0], at[1]);
  await page.mouse.move(p.x, p.y);
  await page.waitForTimeout(200);
  await shot(`30-reversal-${name}-before`, WINDOW);
  await page.mouse.click(p.x, p.y);
  await page.waitForTimeout(200);
  await page.mouse.click(p.x, p.y);
  await page.waitForTimeout(260);
  await shot(`30-reversal-${name}-after`, WINDOW);
}
{
  const l = toCss(1231, 357), r = toCss(1471, 357), mid = toCss(1350, 357);
  await page.mouse.click(mid.x, mid.y);   // off both clamps, so a step out and back is reversible
  await page.waitForTimeout(200);
  await page.mouse.move(l.x, l.y);
  await page.waitForTimeout(200);
  await shot("31-reversal-arrow-before", BGM_ROW);
  await page.mouse.click(l.x, l.y);
  await page.waitForTimeout(200);
  await page.mouse.click(r.x, r.y);
  await page.waitForTimeout(200);
  await page.mouse.move(l.x, l.y);
  await page.waitForTimeout(260);
  await shot("31-reversal-arrow-after", BGM_ROW);
}
// ------------------------------------------- rapid repeated clicks (gate 7)
{
  const p = toCss(1143, 475);
  for (let i = 0; i < 24; i++) await page.mouse.click(p.x, p.y, { delay: 5 });
  await page.waitForTimeout(300);
  const s = await qa();
  report.rapidClicks = { control: "cb_attack", clicks: 24, attack: s.footer.attack, pressed: s.pressed };
  await shot("32-rapid-clicks", WINDOW);
  console.log("rapid clicks:", JSON.stringify(report.rapidClicks));
}

// ---------------------------------------------------------------- dropdown
const DD = { x: 1108, y: 297, w: 424, h: 260 };
{
  const p = toCss(1506, 431);
  await step("12-dropdown-open", async () => { await page.mouse.click(p.x, p.y); }, DD);
  for (let r = 0; r < 4; r++) {
    const q = toCss(1300, 446 + 10 + r * 19);
    await step(`13-dropdown-hover-row${r}`, async () => { await page.mouse.move(q.x, q.y); }, DD);
  }
  const esc = toCss(1300, 446 + 10 + 3 * 19); // row 3 = "tanublue"
  await step("14-dropdown-escape", async () => { await page.keyboard.press("Escape"); }, DD);
  await step("15-dropdown-reopen", async () => { await page.mouse.click(p.x, p.y); }, DD);
  await step("16-dropdown-click-outside", async () => { await page.mouse.click(toCss(700, 800).x, toCss(700, 800).y); }, DD);
  await step("17-dropdown-open-again", async () => { await page.mouse.click(p.x, p.y); }, DD);
  await step("18-dropdown-commit-tanublue", async () => { await page.mouse.click(esc.x, esc.y); }, DD);
  await step("19-dropdown-commit-classic", async () => {
    await page.mouse.click(p.x, p.y);
    await page.waitForTimeout(150);
    await page.mouse.click(toCss(1300, 446 + 10).x, toCss(1300, 446 + 10).y);
  }, DD);
}

// ------------------------------------------------------------ minimize/drag
await step("20-minimize", async () => { await page.mouse.click(toCss(1490, 313).x, toCss(1490, 313).y); }, { x: 1100, y: 290, w: 440, h: 220 });
await step("21-restore", async () => { await page.mouse.click(toCss(1490, 313).x, toCss(1490, 313).y); }, { x: 1100, y: 290, w: 440, h: 220 });

await step("22-window-dragged", async () => {
  const from = toCss(1250, 308);
  await page.mouse.move(from.x, from.y);
  await page.mouse.down();
  for (let i = 1; i <= 20; i++) {
    const t = i / 20;
    const p = toCss(1250 - 700 * t, 308 + 220 * t);
    await page.mouse.move(p.x, p.y);
    await page.waitForTimeout(25);
  }
  await page.mouse.up();
}, null);

await step("23-window-clamped-topleft", async () => {
  const s = await qa();
  const from = toCss(s.position[0] + 140, s.position[1] + 11);
  await page.mouse.move(from.x, from.y);
  await page.mouse.down();
  await page.mouse.move(toCss(-400, -400).x, toCss(-400, -400).y);
  await page.mouse.up();
}, null);

// --------------------------------------------------------- close and reopen
await step("24-closed", async () => {
  const s = await qa();
  await page.mouse.click(toCss(s.position[0] + 408, s.position[1] + 16).x, toCss(s.position[0] + 408, s.position[1] + 16).y);
}, null);
await step("25-reopened", async () => { await page.mouse.click(toCss(40, 17).x, toCss(40, 17).y); }, null);
await step("26-escape-closes", async () => { await page.keyboard.press("Escape"); }, null);
await step("27-reopened-again", async () => { await page.mouse.click(toCss(40, 17).x, toCss(40, 17).y); }, null);

report.console = consoleLog;
report.errors = consoleLog.filter((l) => /error|exception/i.test(l));
report.final = await qa();
writeFileSync(OUT + "drive-report.json", JSON.stringify(report, null, 2));
console.log("console errors:", report.errors.length);
await browser.close();
