#!/usr/bin/env node

import { readFile, writeFile, mkdir } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const FIGMA_MCP_URL = "https://mcp.figma.com/mcp";
const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const TARGETS_PATH = path.resolve(SCRIPT_DIR, "../references/targets.json");

export function parseSsePayload(raw) {
  const payloads = String(raw)
    .split(/\r?\n/)
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line));
  if (payloads.length) return payloads.at(-1);
  return JSON.parse(raw);
}

export function resultText(result) {
  return (result?.content ?? [])
    .filter((item) => item.type === "text")
    .map((item) => item.text)
    .join("\n");
}

function collectUrls(value, keyHint = "", output = []) {
  if (typeof value === "string") {
    if (/^https:\/\//.test(value)) output.push({ keyHint, url: value });
    for (const match of value.matchAll(/https:\/\/[^\s"')]+/g)) {
      output.push({ keyHint, url: match[0] });
    }
    try {
      collectUrls(JSON.parse(value), keyHint, output);
    } catch {
      // Plain text is expected for some MCP content blocks.
    }
  } else if (Array.isArray(value)) {
    for (const item of value) collectUrls(item, keyHint, output);
  } else if (value && typeof value === "object") {
    for (const [key, item] of Object.entries(value)) collectUrls(item, key, output);
  }
  return output;
}

export function extractUploadUrls(result, expectedCount) {
  const candidates = collectUrls(result)
    .filter(({ keyHint, url }) => !/commit/i.test(keyHint) && !/commit/i.test(url))
    .filter(({ url }) => !url.startsWith(FIGMA_MCP_URL));
  const unique = [...new Set(candidates.map(({ url }) => url))];
  if (unique.length < expectedCount) {
    throw new Error(`Figma returned ${unique.length} upload URL(s), expected ${expectedCount}`);
  }
  return unique.slice(0, expectedCount);
}

export function guessContentType(filePath) {
  switch (path.extname(filePath).toLowerCase()) {
    case ".png": return "image/png";
    case ".jpg":
    case ".jpeg": return "image/jpeg";
    case ".webp": return "image/webp";
    case ".gif": return "image/gif";
    case ".svg": return "image/svg+xml";
    default: throw new Error(`Unsupported asset type: ${path.extname(filePath) || "none"}`);
  }
}

function parseOptions(argv) {
  const options = { asset: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token.startsWith("--")) throw new Error(`Unexpected argument: ${token}`);
    const key = token.slice(2).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) throw new Error(`Missing value for ${token}`);
    index += 1;
    if (key === "asset") options.asset.push(value);
    else options[key] = value;
  }
  return options;
}

async function loadTargets() {
  return JSON.parse(await readFile(TARGETS_PATH, "utf8"));
}

async function resolveTarget(options) {
  const target = options.target ? (await loadTargets())[options.target] : null;
  if (options.target && !target) throw new Error(`Unknown target: ${options.target}`);
  return {
    fileKey: options.fileKey ?? target?.fileKey,
    rootNodeId: target?.rootNodeId ?? "0:1",
    ...target,
  };
}

async function loadCredential() {
  const codexHome = process.env.CODEX_HOME || path.join(os.homedir(), ".codex");
  const store = JSON.parse(await readFile(path.join(codexHome, ".credentials.json"), "utf8"));
  const credential = Object.values(store).find(
    (entry) => entry.server_name === "figma" && entry.server_url === FIGMA_MCP_URL,
  );
  if (!credential?.access_token) throw new Error("Authenticated Figma MCP credential is unavailable");
  if (credential.expires_at && credential.expires_at <= Date.now() + 15_000) {
    throw new Error("Authenticated Figma MCP credential is expired; run the existing OAuth bootstrap");
  }
  return credential;
}

async function postJson(url, headers, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });
  const raw = await response.text();
  if (!response.ok) throw new Error(`Figma MCP HTTP ${response.status}`);
  return { response, body: parseSsePayload(raw) };
}

class FigmaMcpClient {
  constructor(accessToken) {
    this.headers = {
      authorization: `Bearer ${accessToken}`,
      accept: "application/json, text/event-stream",
      "content-type": "application/json",
    };
    this.nextId = 1;
  }

  async initialize() {
    const { response, body } = await postJson(FIGMA_MCP_URL, this.headers, {
      jsonrpc: "2.0",
      id: this.nextId++,
      method: "initialize",
      params: {
        protocolVersion: "2025-06-18",
        capabilities: {},
        clientInfo: { name: "figma-qwen-ui-pipeline", version: "1.0.0" },
      },
    });
    if (body.error) throw new Error(body.error.message);
    const sessionId = response.headers.get("mcp-session-id");
    if (sessionId) this.headers["mcp-session-id"] = sessionId;
    await fetch(FIGMA_MCP_URL, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify({ jsonrpc: "2.0", method: "notifications/initialized" }),
    });
  }

  async request(method, params = {}) {
    const { body } = await postJson(FIGMA_MCP_URL, this.headers, {
      jsonrpc: "2.0",
      id: this.nextId++,
      method,
      params,
    });
    if (body.error) throw new Error(body.error.message);
    return body.result;
  }

  async call(name, args = {}) {
    const result = await this.request("tools/call", { name, arguments: args });
    if (result?.isError) throw new Error(resultText(result) || `${name} failed`);
    return result;
  }
}

async function connect() {
  const credential = await loadCredential();
  const client = new FigmaMcpClient(credential.access_token);
  await client.initialize();
  return client;
}

async function ensureOutput(outputPath) {
  await mkdir(path.dirname(path.resolve(outputPath)), { recursive: true });
}

function firstHttpsUrl(value) {
  return collectUrls(value).map(({ url }) => url).find((url) => /^https:\/\//.test(url));
}

async function main(argv) {
  const [command, ...rest] = argv;
  if (!command) throw new Error("Expected command: tools, call, get-figjam, screenshot, upload, or use");
  const options = parseOptions(rest);
  const target = await resolveTarget(options);
  const client = await connect();

  if (command === "tools") {
    const result = await client.request("tools/list");
    for (const tool of result.tools ?? []) process.stdout.write(`${tool.name}\n`);
    return;
  }

  if (command === "call") {
    if (!options.name || !options.argsFile) throw new Error("call requires --name and --args-file");
    const args = JSON.parse(await readFile(options.argsFile, "utf8"));
    const result = await client.call(options.name, args);
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
    return;
  }

  if (!target.fileKey) throw new Error("Provide --target or --file-key");

  if (command === "get-figjam") {
    if (!options.out) throw new Error("get-figjam requires --out");
    const nodeId = options.nodeId ?? target.rootNodeId;
    const result = await client.call("get_figjam", {
      fileKey: target.fileKey,
      nodeId,
      includeImagesOfNodes: options.includeImages === "true",
    });
    const text = resultText(result);
    await ensureOutput(options.out);
    await writeFile(options.out, text, "utf8");
    process.stdout.write(`${JSON.stringify({ command, nodeId, out: path.resolve(options.out), bytes: Buffer.byteLength(text) })}\n`);
    return;
  }

  if (command === "screenshot") {
    if (!options.out || !options.nodeId) throw new Error("screenshot requires --node-id and --out");
    const result = await client.call("get_screenshot", {
      fileKey: target.fileKey,
      nodeId: options.nodeId,
      maxDimension: Number(options.maxDimension ?? 2048),
      enableBase64Response: false,
    });
    const url = firstHttpsUrl(result);
    if (!url) throw new Error("Figma screenshot response contained no download URL");
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Screenshot download failed with HTTP ${response.status}`);
    const bytes = Buffer.from(await response.arrayBuffer());
    await ensureOutput(options.out);
    await writeFile(options.out, bytes);
    process.stdout.write(`${JSON.stringify({ command, nodeId: options.nodeId, out: path.resolve(options.out), bytes: bytes.length })}\n`);
    return;
  }

  if (command === "upload") {
    if (!options.asset.length) throw new Error("upload requires at least one --asset");
    if (options.nodeId && options.asset.length !== 1) throw new Error("--node-id supports exactly one asset");
    const request = {
      fileKey: target.fileKey,
      count: options.asset.length,
      batchCommit: false,
      ...(options.nodeId ? { nodeId: options.nodeId, scaleMode: options.scaleMode ?? "FILL" } : {}),
    };
    const uploadResult = await client.call("upload_assets", request);
    const uploadUrls = extractUploadUrls(uploadResult, options.asset.length);
    const uploaded = [];
    await Promise.all(options.asset.map(async (assetPath, index) => {
      const absolutePath = path.resolve(assetPath);
      const bytes = await readFile(absolutePath);
      const contentType = guessContentType(absolutePath);
      const response = await fetch(uploadUrls[index], {
        method: "POST",
        headers: { "content-type": contentType },
        body: bytes,
      });
      if (!response.ok) throw new Error(`Asset upload failed for ${path.basename(assetPath)} with HTTP ${response.status}`);
      uploaded.push({ file: path.basename(assetPath), bytes: bytes.length, contentType });
    }));
    process.stdout.write(`${JSON.stringify({ command, nodeId: options.nodeId ?? null, uploaded })}\n`);
    return;
  }

  if (command === "use") {
    if (!options.codeFile || !options.description) throw new Error("use requires --code-file and --description");
    const code = await readFile(options.codeFile, "utf8");
    const result = await client.call("use_figma", {
      fileKey: target.fileKey,
      code,
      description: options.description,
      ...(options.skills ? { skillNames: options.skills } : {}),
    });
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
    return;
  }

  throw new Error(`Unknown command: ${command}`);
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  main(process.argv.slice(2)).catch((error) => {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  });
}
