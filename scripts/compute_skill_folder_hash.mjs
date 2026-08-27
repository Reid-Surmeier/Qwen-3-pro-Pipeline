#!/usr/bin/env node

import { createHash } from "node:crypto";
import { readFile, readdir } from "node:fs/promises";
import path from "node:path";

const EXCLUDED_DIRECTORIES = new Set([".git", "node_modules"]);

async function collectFiles(directory, files = []) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const entryPath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      if (!EXCLUDED_DIRECTORIES.has(entry.name)) {
        await collectFiles(entryPath, files);
      }
    } else if (entry.isFile()) {
      files.push(entryPath);
    }
  }
  return files;
}

async function computeSkillFolderHash(skillDirectory) {
  const files = await collectFiles(skillDirectory);
  const records = files
    .map((filePath) => ({
      filePath,
      relativePath: path.relative(skillDirectory, filePath).split("\\").join("/"),
    }))
    .sort((left, right) => left.relativePath.localeCompare(right.relativePath));

  const hash = createHash("sha256");
  for (const record of records) {
    hash.update(record.relativePath);
    hash.update(await readFile(record.filePath));
  }
  return hash.digest("hex");
}

const results = [];
for (const skillDirectory of process.argv.slice(2)) {
  results.push({
    path: skillDirectory,
    hash: await computeSkillFolderHash(skillDirectory),
  });
}
process.stdout.write(`${JSON.stringify(results)}\n`);
