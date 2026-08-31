#!/usr/bin/env node
// Prove that the blind-review packet's declared clean-state command prepares
// every imported Godot resource from a checkout with no warm `.godot` cache.

import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const qaDir = path.dirname(fileURLToPath(import.meta.url));
const repository = path.resolve(qaDir, "../..");
const sourceProject = path.join(repository, "godot");
const packetPath = path.join(repository, "artifacts/reviews/issue-134/packet.json");
const packet = JSON.parse(fs.readFileSync(packetPath, "utf8"));
const cleanStateCommand = packet?.launch?.clean_state_command;

assert.equal(typeof cleanStateCommand, "string", "packet clean-state command is required");
assert.ok(cleanStateCommand.length > 0, "packet clean-state command cannot be empty");

const scratch = fs.mkdtempSync(path.join(os.tmpdir(), "image79-cold-packet-"));
const copiedProject = path.join(scratch, "godot");

function includeInColdCopy(source) {
  const relative = path.relative(sourceProject, source);
  if (!relative || relative === ".") return true;
  const first = relative.split(path.sep)[0];
  if (first === ".godot" || first === "web") return false;
  return relative !== path.join("qa", "out")
    && !relative.startsWith(path.join("qa", "out") + path.sep);
}

function filesUnder(directory) {
  const result = [];
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const absolute = path.join(directory, entry.name);
    if (entry.isDirectory()) result.push(...filesUnder(absolute));
    else result.push(absolute);
  }
  return result;
}

try {
  fs.cpSync(sourceProject, copiedProject, {
    recursive: true,
    filter: includeInColdCopy,
  });

  execFileSync("bash", ["-lc", cleanStateCommand], {
    cwd: scratch,
    encoding: "utf8",
    stdio: "pipe",
  });

  const declaredImports = new Set();
  for (const importFile of filesUnder(copiedProject).filter((file) => file.endsWith(".import"))) {
    const contents = fs.readFileSync(importFile, "utf8");
    for (const match of contents.matchAll(/res:\/\/(\.godot\/imported\/[^"\]]+)/g)) {
      declaredImports.add(match[1]);
    }
  }
  const missing = [...declaredImports]
    .filter((relative) => !fs.existsSync(path.join(copiedProject, relative)))
    .sort();

  assert.ok(declaredImports.size > 0, "cold project must declare imported resources");
  assert.equal(
    missing.length,
    0,
    `clean-state command left ${missing.length} imported resources absent:\n${missing.slice(0, 20).join("\n")}`,
  );
  console.log(JSON.stringify({
    pass: true,
    declared_imports: declaredImports.size,
    missing_imports: 0,
  }));
} finally {
  fs.rmSync(scratch, { recursive: true, force: true });
}
