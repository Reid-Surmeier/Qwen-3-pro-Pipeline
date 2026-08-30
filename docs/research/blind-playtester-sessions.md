# Blind Playtester sessions: Claude Code and Codex

Research for [#105](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/105)
(map [#103](https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/103), Notes → Two
Playtesters). Everything below was run on 2026-08-29 against the live export at
`https://windows-wsl.taile06c45.ts.net/godot-ro-hud/`. Both agents were run once
end-to-end, at the same time, and their Play Logs were read back and checked against an
independent ground-truth capture. That run is a harness check, not a verdict on the
build.

## What was settled

1. Two command lines that start a genuinely blind Playtester — no `CLAUDE.md`,
   no `AGENTS.md`, no user skills, no memory, no prior conversation, no host MCP servers
   — with a browser and network and nothing else.
2. One browser driver for both: a **pinned local Playwright MCP**, launched `--isolated`,
   which is the only driver of the four available that two Playtesters can run at once.
3. A packet prompt (`PLAYTEST.md`) that makes the evidence real: the session cannot write
   a Play Log without having been handed the pixels.
4. Both agents ran concurrently and both correctly reported the known-bad party-list
   scrollbar as **not responsive**.

## The live constraint the owner should know about

**Fable 5 is rate-limited on this account right now.** Two earlier agents on this ticket
died on that limit, and every probe here was run on `--model opus` instead. Two
consequences:

- The Playtester recipe **must name a model at run time** (`--model <name>` for Claude,
  `model = "<name>"` for Codex). Do not bake `fable` into a script that has to run
  unattended; a rate-limited model kills the session, it does not fall back silently.
- Map #103's rule says the Claude-side Playtester is Fable 5. Until the limit clears,
  the Fable pre-check either runs on Opus 5 or does not run. The Codex side (the verdict
  that counts) is unaffected.

The `modelUsage` block in `--output-format json` reports which model actually answered, so
a run that silently fell back is detectable after the fact.

---

## Claude Code

### Final command line

```bash
cd /tmp/playtest/claude                          # the packet dir; nothing else in it but PLAYTEST.md
export CLAUDE_CODE_DISABLE_AUTO_MEMORY=1
claude -p \
  --model opus \
  --setting-sources "" \
  --strict-mcp-config --mcp-config /tmp/playtest/out/pw-mcp-claude.json \
  --tools "Read,Write" \
  --allowedTools "Read,Write,mcp__browser" \
  --disallowedTools "mcp__browser__browser_evaluate,mcp__browser__browser_run_code_unsafe,mcp__browser__browser_snapshot,mcp__browser__browser_find,mcp__browser__browser_console_messages,mcp__browser__browser_network_requests,mcp__browser__browser_network_request" \
  --max-turns 45 \
  --no-session-persistence \
  --output-format json \
  "$(cat ./PLAYTEST.md)"
```

`pw-mcp-claude.json`:

```json
{
  "mcpServers": {
    "browser": {
      "command": "node",
      "args": [
        "/tmp/playtest/out/mcp/node_modules/@playwright/mcp/cli.js",
        "--isolated", "--headless", "--no-sandbox",
        "--viewport-size", "1973x1319",
        "--caps", "vision",
        "--output-dir", "/tmp/playtest/claude"
      ],
      "env": { "PLAYWRIGHT_BROWSERS_PATH": "/home/reidsurmeier/.cache/ms-playwright" }
    }
  }
}
```

### Two flags that look right and are not

- **`--safe-mode` cannot be used.** It is the obvious choice — it disables `CLAUDE.md`,
  skills, plugins, hooks, auto memory — but it also refuses an *explicitly passed*
  `--mcp-config`. Probe A (`--safe-mode --strict-mcp-config --mcp-config …`) came back
  with `"mcp_servers": []` and `"tools": ["Read","Write"]`: no browser, no Playtester.
- **`--bare` cannot be used.** It does exactly the right suppression, but the docs are
  explicit that "bare mode doesn't use your subscription login" and "never reads OAuth
  credentials or the system keychain" — it needs `ANTHROPIC_API_KEY`. That is a paid API
  call, which the owner's rules route through OpenRouter only. Out.

What works instead is `--setting-sources ""` (load no user/project/local settings, which
takes the hooks, the status line and the user `CLAUDE.md` with it) plus
`CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` for auto memory, with the MCP server passed
explicitly and `--strict-mcp-config` to keep every host server out.

### Leak audit

A one-turn probe (`--max-turns 1`, "reply with a JSON object naming every instruction
document, tool, MCP server and path you can see"), run under the same flags:

| | result |
| --- | --- |
| instruction documents | none of the owner's — no `CLAUDE.md`, no `AGENTS.md`, no skills, no auto memory. The only headings are Claude Code's own stock system-prompt sections (`# Harness`, `# Environment`, `# Context management`, `# Delivering work`, `# Corrections`) plus `# userEmail` and `# currentDate` |
| MCP servers | `browser` only, 32 tools |
| tools | `Read`, `Write`, `mcp__browser__*` — no Bash, no Task, no Skill |
| prior conversation | `false` |
| still visible | the working-directory path, `naimjohnson67@gmail.com`, today's date, and that the host is Claude Code on WSL2 |

The email and the date are unavoidable through the CLI (only `--system-prompt-file`, which
replaces the whole prompt, would remove them). Neither tells the session anything about the
build under test. **The working-directory path does**, which is why the packet must live at
a neutral path — `/tmp/playtest/<agent>`, not a directory named after the repo. Under the
old scratchpad path the probe read back
`/tmp/claude-1000/-home-reidsurmeier-Qwen-3-pro-Pipeline/…` and inferred the repository
name from it.

### Browser driver

Playwright MCP, `--isolated` (profile in memory), `--headless`, `--no-sandbox`,
`--viewport-size 1973x1319`, `--caps vision` (this is what adds `browser_mouse_click_xy`,
`browser_mouse_drag_xy`, `browser_mouse_down/up` — the coordinate gestures a canvas game
needs; without it there are only DOM-element tools, which a Godot canvas has none of).
`--output-dir` is the packet dir. The seven dangerous tools are removed with
`--disallowedTools` so the session cannot fall back to reading the DOM, the console or the
network, or injecting JavaScript, to decide whether a control worked.

### Play Log produced

Correct on all three controls, including the known-bad one:

```json
{
  "control": "party-list scrollbar thumb",
  "gesture": "drag (1222,420) -> (1222,600)",
  "observed": "No visible change. The scrollbar thumb in the パーティー window stays at the same place at the top of its track and the member list (SakumaRiri through Meltina) is unchanged. A screenshot taken mid-drag with the button still held … also showed no movement…",
  "responsive": false
}
```

`status` and `OK` likewise `false`. Its notes: "The whole HUD appears to be a static mock:
nothing in any window reacted to any of the three gestures." It volunteered a mid-drag
screenshot without being asked.

### Cost and duration

| run | turns | wall | cost (subscription-billed) |
| --- | --- | --- | --- |
| final Playtester run | 20 | 73 s | $0.47 |
| earlier run, named-file screenshots | 28 | 75 s | $0.85 |
| leak probe A (`--safe-mode`) | 1 | 2 s | $0.05 |
| leak probe B (final flags) | 1 | 12 s | $0.14 |

The named-file variant cost nearly double because the session had to `Read` each PNG back
in a separate turn. Total spend for the whole ticket, all agents, is under $4 and all of it
is subscription-billed CLI usage; no OpenRouter or direct-API call was made.

---

## Codex

### Final command line

```bash
export CODEX_HOME=/tmp/playtest/out/codex-home   # only auth.json (symlink) + config.toml
export HOME=/tmp/playtest/out/fakehome           # empty; hides ~/.agents/skills
codex exec \
  -C /tmp/playtest/codex --skip-git-repo-check --ephemeral \
  --ignore-rules \
  -s workspace-write \
  --json -o run-codex.last.md \
  "$(cat /tmp/playtest/codex/PLAYTEST.md)"
```

`$CODEX_HOME/config.toml`:

```toml
model = "gpt-5.6-sol"
model_reasoning_effort = "xhigh"
web_search = "disabled"

[features]
apps = false
multi_agent = false
plugins = false
remote_plugin = false
memories = false
goals = false
shell_tool = false

[tools]
view_image = true

[sandbox_workspace_write]
network_access = true

[mcp_servers.browser]
command = "node"
args = [
  "/tmp/playtest/out/mcp/node_modules/@playwright/mcp/cli.js",
  "--isolated", "--headless", "--no-sandbox",
  "--viewport-size", "1973x1319",
  "--caps", "vision",
  "--output-dir", "/tmp/playtest/codex",
]
cwd = "/tmp/playtest/codex"
startup_timeout_sec = 180
tool_timeout_sec = 180
default_tools_approval_mode = "approve"
enabled_tools = [
  "browser_navigate", "browser_take_screenshot",
  "browser_mouse_move_xy", "browser_mouse_click_xy", "browser_mouse_drag_xy",
  "browser_mouse_down", "browser_mouse_up", "browser_mouse_wheel",
  "browser_press_key", "browser_type", "browser_wait_for",
  "browser_resize", "browser_close",
]

[mcp_servers.browser.env]
PATH = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
HOME = "/tmp/playtest/out/fakehome"
PLAYWRIGHT_BROWSERS_PATH = "/home/reidsurmeier/.cache/ms-playwright"
```

The subscription is used, not an API key: `auth.json` is symlinked from `~/.codex/auth.json`
into the isolated `CODEX_HOME`, which is the only file carried over. Codex prints a harmless
warning on every run — `Refusing to create helper binaries under temporary dir "/tmp"` —
because `CODEX_HOME` is under `/tmp`.

### Four things that had to be discovered the hard way

1. **`--ignore-user-config` does not blind Codex.** It only skips `config.toml`. An earlier
   probe using it still read the owner's global `~/.codex/AGENTS.md` verbatim, all ~140
   user skills, and the whole connected-apps roster (Trello, Dropbox, Binance, …). The only
   thing that works is an **isolated `CODEX_HOME`**.
2. **An isolated `CODEX_HOME` is not enough either.** Codex also discovers
   `$HOME/.agents/skills`, and the skill *names* alone (`qwen-image-pipeline`,
   `gitnexus-*`, `orca-*`) tell a Playtester what repository it is looking at. **`HOME`
   must be pointed at an empty directory too.**
3. **`shell_tool` must be off.** With the shell available, the Codex session ignored the
   packet's "do not run shell commands" instruction outright: it ran ~24 commands —
   `curl`, `ps`, `xdpyinfo`, `xrandr`, `Xvfb`, ImageMagick `import` — stood up its **own**
   headed Chrome on its own X display, and produced six of its seven screenshots from
   that browser rather than from the MCP one. It also called `browser_run_code_unsafe`,
   which the packet forbids. Its verdict happened to be right; its evidence was not the
   evidence the harness thought it was collecting. With `shell_tool = false` it uses the
   browser MCP for every gesture and `apply_patch` to write the log, and the run is clean.
4. **`default_tools_approval_mode = "approve"` is required.** As soon as `enabled_tools`
   is set, MCP calls start requiring approval; in `codex exec` there is nobody to approve,
   so `browser_navigate` is auto-rejected and the session writes a Play Log full of blank
   white screenshots that it honestly labels `responsive: false`. That failure mode is
   dangerous — it produces a *plausible* log — so any Play Log whose `notes` mention
   approval, blocking or a blank page must be thrown away, not read.

### Leak audit

Same probe, under the final configuration:

| | result |
| --- | --- |
| instruction documents | none of the owner's — no `AGENTS.md`, no `CLAUDE.md`, no user skills, no memories, no plugin catalog, no connected apps. Only Codex's own stock preamble and its sandbox/environment blocks |
| MCP servers | the model self-reports `[]` — see the warning below |
| tools | `exec`, `apply_patch`, `update_plan`, `view_image`, `image_gen__imagegen`, `collaboration.*`, and the `browser_*` set |
| prior conversation | reported `true` — Codex counts its own developer preamble as history; there is no user turn before the packet |
| still visible | the working-directory path; Codex's own `.system` skills auto-installed into the isolated `CODEX_HOME` (`imagegen`, `openai-docs`, `plugin-creator`, `skill-creator`, `skill-installer`); the built-in `image_gen` tool; the `collaboration.*` multi-agent tools, which survive `features.multi_agent = false`; the OpenAI model roster |

**The Codex self-report is not a reliable MCP census.** It reported `"mcp_servers": []`
in the very configuration where a separate probe proved `browser_navigate` works and
returns the page title. Verify the browser by calling it, never by asking the session what
it can see. None of the residue above is owner or repository content, so blindness holds.

### Browser driver

Identical to the Claude side — the same pinned local Playwright MCP, its own `--isolated`
browser and its own output directory. Two differences forced by Codex: the server is
launched as `node …/cli.js` rather than `npx` (Codex hands the server a **replaced**, not
merged, environment, so `npx` has no usable `PATH`, and a run-time `npx` fetch is one more
thing that can fail mid-playtest), and the dangerous tools are removed with
`enabled_tools` instead of a deny list.

### Play Log produced

Correct on all three controls:

```json
{
  "control": "party-list scrollbar thumb",
  "gesture": "drag (1222,420) -> (1222,600)",
  "observed": "The scrollbar thumb and party-list contents appear unchanged after the drag; no visible change.",
  "responsive": false,
  "screenshots": ["page-2026-08-30T00-31-38-266Z.png", "page-2026-08-30T00-31-48-157Z.png"]
}
```

Twelve tool calls total: 1 navigate, 7 screenshots, 2 clicks, 1 drag, 1 `apply_patch`. No
shell, no JavaScript, no pollution of the packet directory.

### Cost and duration

| run | wall | tokens (in / cached / out) |
| --- | --- | --- |
| final Playtester run | 99 s | 228 k / 173 k / 2.7 k |
| shell-enabled run (rejected) | 294 s | 1 475 k / 1 321 k / 7.6 k |
| leak probe (final config) | ~60 s | — |

Codex does not report a dollar figure; it is billed against the ChatGPT subscription. The
shell-enabled run burned 6× the input tokens improvising its own browser.

---

## The browser driver decision

Four drivers were available. One survives.

| driver | verdict |
| --- | --- |
| **Playwright MCP, pinned local install, `--isolated`** | **chosen.** In-memory profile per server instance, so N Playtesters are N independent browsers. `--caps vision` gives the coordinate gestures a canvas needs. Same server, same browser build, both agents |
| Playwright MCP via `npx @playwright/mcp` | same server, worse launch. `npx` needs a writable `HOME` and a network fetch at start-up, and Codex replaces the server's environment — the combination is a run-time failure waiting to happen. Use it to install, not to launch |
| chrome-devtools MCP | **rejected.** It uses one shared profile at `~/.cache/chrome-devtools-mcp/chrome-profile`. Verified live: `SingletonLock → Puget-258754-860490`, and pid 860490 is a Chrome that has held `--user-data-dir=…/chrome-profile --remote-debugging-pipe` for two hours. A second Playtester either fails to take the singleton or attaches to the *same* browser and page list. Two blind Playtesters cannot use it at once, and one of them would be looking at the other's tabs |
| repo-local Playwright in `~/.qwen-pipeline-claude-wt/godot/qa/web/node_modules` | **rejected as the driver, kept as the referee.** It lives inside a checkout of the repo under test, so handing it to a Playtester hands over the build's own QA code. It is the right tool for the independent ground-truth capture (below), which is exactly what it was used for |

### The browser build must be pinned

The single most confusing failure of this research: a Codex run that navigated
successfully, screenshotted successfully, and reported a **uniform white page**. Cause —
`@playwright/mcp@0.0.79` resolves `playwright-core 1.63.0-alpha`, which wants
`chromium_headless_shell-1237`; only builds up to 1234 were present in
`~/.cache/ms-playwright`. The MCP server did not error, it fell back and rendered nothing.
Fix, once, before any Playtester runs:

```bash
PLAYWRIGHT_BROWSERS_PATH=/home/reidsurmeier/.cache/ms-playwright \
  node /tmp/playtest/out/mcp/node_modules/playwright-core/cli.js install chromium chromium-headless-shell
```

A Play Log describing a blank page is a harness failure, never a build failure.

---

## The packet prompt

`PLAYTEST.md` is the whole packet. Two parts of it are load-bearing.

**Design → CSS coordinates.** The build's design surface is 1973 × 1319 and
`GODOT_CONFIG.canvasResizePolicy` is `2`, so the canvas is resized to the whole window. At
a viewport of exactly 1973 × 1319 the mapping is the identity — verified: the canvas
element measures 1973 × 1319 CSS px at `devicePixelRatio` 1, at offset (0,0), with the
magenta background reaching all four edges. Both sessions were told to *check* that on the
first screenshot and given the conversion to apply if they saw black bars instead:

```
scale   = min(viewportWidth / 1973, viewportHeight / 1319)
offsetX = (viewportWidth  - 1973 * scale) / 2
offsetY = (viewportHeight - 1319 * scale) / 2
cssX    = offsetX + designX * scale
cssY    = offsetY + designY * scale
```

Both checked, both reported `scale 1, offsets (0,0)`, both hit their targets.

**Screenshots must be taken *without* a filename.** This is the difference between real
and imagined evidence. `browser_take_screenshot` with a `filename` returns **text only** —
a markdown link to a file on disk. Without a filename it returns text **and the image
inline**, and still writes the file to `--output-dir` under a timestamped name. In the
named-file version of the run, the Codex session never opened a single PNG: twelve tool
calls, zero `view_image`, and three `observed` strings written from the tool's text output
and its own expectations. It was right by luck. With filenames removed, the pixels are
pushed into the session and the log's `screenshots` field records the names the tool
reported. Claude behaved correctly either way (it read each PNG back with `Read`), but the
named-file route cost it eight extra turns and nearly double the money.

---

## Ground truth, and what the Play Logs should have said

Captured independently with the repo-local Playwright 1.62.1 at the same viewport, before
either agent ran:

| gesture | before → after | verdict |
| --- | --- | --- |
| drag scrollbar thumb (1222,420) → (1222,600) | **byte-identical** | not responsive |
| drag, mid-gesture with the button held | differs in `(1206, 366) – (1236, 666)` — a grey pressed rectangle appears behind the whole scrollbar; **the thumb does not move** | transient only |
| click `status` (521,82) | byte-identical | not responsive |
| click `OK` (1731,638) | byte-identical | not responsive |
| hover anywhere | byte-identical | no hover states at all |

Both Playtesters returned `responsive: false` on all three. Claude's first screenshot was
**byte-identical** (sha256 `c05538cc…`) to the independent ground-truth capture, and its
mid-drag screenshot reproduced the ground-truth diff box exactly — though it described that
frame as showing "no pressed/highlighted thumb", which under-reads the grey rectangle that
is actually there. That is the one fidelity gap worth carrying into the real harness: a
session will report *movement* correctly and may still miss a subtle state change. The
twelve gates in map #103 (≥30-frame drag capture, ≤2-frame latency) need frame capture, not
before/after pairs.

This confirms map #103's note from the other direction: the live export's scrollbar thumbs
cannot be dragged, because `plate_window.gd` sets `_dragging` only for `role == "drag"`.

---

## Concurrency

**Yes, both Playtesters can run at once, and they did.** The final pair overlapped from
20:30:44 to 20:32:47; Claude finished in 73 s, Codex in 99 s, neither disturbed the other,
and both produced complete Play Logs.

What makes it safe:

- **Separate packet directories.** `/tmp/playtest/claude` and `/tmp/playtest/codex`. Each
  is also its own MCP `--output-dir`, so screenshots and Play Logs never collide.
- **`--isolated` on the Playwright MCP.** The browser profile is held in memory, so each
  server instance is a separate Chromium with its own pages. This is the whole reason the
  driver was chosen.
- **Separate `CODEX_HOME` and `HOME` for Codex**, which is also what makes it blind.
- Only the browser *binaries* in `~/.cache/ms-playwright` are shared, and they are read-only.

What conflicts:

- **chrome-devtools MCP conflicts, hard.** One shared profile directory, one singleton
  lock, currently held by a two-hour-old Chrome. Two Playtesters would share a browser.
  Do not use it for either agent.
- **A single packet directory would conflict.** Both sessions write `play-log.json` to
  their working directory; one packet means one log overwriting the other.
- **A shared `CODEX_HOME` would conflict** — Codex keeps sqlite state there.
- Nothing else observed. Two headless Chromium instances at 1973 × 1319 ran side by side
  without contention on this machine.

Running them at the same time is also the right default for the real harness: the two
Playtesters are supposed to be independent and blind to each other, and a shared clock
makes them see the same deployed build.

---

## Open problems

1. **Fable 5 rate limit** (above). The recipe names the model at run time; the owner
   decides whether the pre-check runs on Opus 5 or is skipped until the limit clears.
2. **Codex's transient-state blindness and Claude's under-reading of it.** Before/after
   pairs cannot satisfy map #103's frame-level gates. The real harness needs a video or
   frame-sequence capture (`--save-video` / `--save-trace` on the Playwright MCP is the
   obvious next thing to test), not more screenshots.
3. **A Play Log can be plausible and worthless.** The approval-blocked Codex run produced
   a correctly-shaped log describing a blank white page with `responsive: false`
   throughout. The Play Log schema needs a machine-checkable liveness field — a checksum
   or dimensions of the loaded screenshot, or a required "what is visible in the first
   screenshot" answer that the harness verifies — before any verdict is computed from it.
4. **Neither agent can be fully stripped.** Claude leaks the user's email and the working
   directory; Codex leaks its own `.system` skills, `image_gen` and the `collaboration.*`
   tools. None of it is repository content, so blindness holds, but the working-directory
   path is the one that matters: **packets must live at a neutral path**.
5. **`--tools ""` / `enabled_tools` interactions.** Codex's approval behaviour changes as
   soon as `enabled_tools` is set, which is not documented anywhere I could find. If a
   future Codex release changes the default again, the symptom will be blank screenshots,
   not an error.
6. **No CI path.** Both recipes need the owner's local subscription credentials
   (`~/.claude` OAuth, `~/.codex/auth.json`). Map #103 already lists this as unspecified;
   nothing found here changes it.

## Files

The harness is committed beside this note, in `docs/research/blind-playtester-sessions/`:

| file | what it is |
| --- | --- |
| `run-claude.sh`, `pw-mcp-claude.json` | the Claude Code Playtester, exactly as run |
| `run-codex.sh`, `codex-config.toml` | the Codex Playtester, exactly as run |
| `PLAYTEST.md` | the packet prompt — the only file a packet directory contains |
| `leak-probe.md` | the one-turn configuration-audit prompt used for both leak audits |
| `play-log.claude.json`, `play-log.codex.json` | the two Play Logs from the concurrent run |

The scripts hard-code `/tmp/playtest/…` because the packet directory must sit at a neutral
path (see the Claude leak audit). The packets themselves are deliberately not repository
content: a packet is a `git archive` of the candidate SHA, built at run time.
