#!/usr/bin/env node

import { createHash } from "node:crypto";
import { readFile, writeFile, mkdir, stat } from "node:fs/promises";
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
    .filter(({ url }) => !url.startsWith(FIGMA_MCP_URL) || url.includes("/mcp/upload/"));
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

function findPlacedNode(value) {
  if (Array.isArray(value)) {
    for (const item of value) {
      const found = findPlacedNode(item);
      if (found) return found;
    }
    return null;
  }
  if (!value || typeof value !== "object") return null;
  for (const key of ["nodeId", "createdNodeId", "targetNodeId", "id"]) {
    if (typeof value[key] === "string" && /^\d+[:-]\d+$/.test(value[key])) {
      return {
        nodeId: value[key].replace("-", ":"),
        ...(typeof value.imageHash === "string" ? { imageHash: value.imageHash } : {}),
        ...(Number.isFinite(value.width) ? { width: value.width } : {}),
        ...(Number.isFinite(value.height) ? { height: value.height } : {}),
      };
    }
  }
  for (const item of Object.values(value)) {
    const found = findPlacedNode(item);
    if (found) return found;
  }
  return null;
}

export function extractPlacedNode(raw) {
  let value = raw;
  if (typeof value === "string") {
    try {
      value = JSON.parse(value);
    } catch {
      throw new Error("Figma upload commit returned non-JSON placement data");
    }
  }
  const placement = findPlacedNode(value);
  if (!placement) throw new Error("Figma upload commit did not return a placed node ID");
  return placement;
}

function jpegDimensions(bytes) {
  let offset = 2;
  while (offset + 9 < bytes.length) {
    if (bytes[offset] !== 0xff) {
      offset += 1;
      continue;
    }
    const marker = bytes[offset + 1];
    offset += 2;
    if (marker === 0xd8 || marker === 0xd9 || marker === 0x01) continue;
    if (offset + 2 > bytes.length) break;
    const length = bytes.readUInt16BE(offset);
    if (length < 2 || offset + length > bytes.length) break;
    if ([0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf].includes(marker)) {
      return { width: bytes.readUInt16BE(offset + 5), height: bytes.readUInt16BE(offset + 3) };
    }
    offset += length;
  }
  throw new Error("JPEG dimensions are unavailable");
}

export function imageDimensions(bytes, contentType) {
  if (contentType === "image/png" && bytes.length >= 24
      && bytes.subarray(0, 8).equals(Buffer.from("89504e470d0a1a0a", "hex"))) {
    return { width: bytes.readUInt32BE(16), height: bytes.readUInt32BE(20) };
  }
  if (contentType === "image/gif" && bytes.length >= 10) {
    return { width: bytes.readUInt16LE(6), height: bytes.readUInt16LE(8) };
  }
  if (contentType === "image/jpeg" && bytes.length >= 4
      && bytes[0] === 0xff && bytes[1] === 0xd8) {
    return jpegDimensions(bytes);
  }
  if (contentType === "image/webp" && bytes.length >= 30
      && bytes.toString("ascii", 0, 4) === "RIFF"
      && bytes.toString("ascii", 8, 12) === "WEBP") {
    const chunk = bytes.toString("ascii", 12, 16);
    if (chunk === "VP8X") {
      return {
        width: 1 + bytes.readUIntLE(24, 3),
        height: 1 + bytes.readUIntLE(27, 3),
      };
    }
    if (chunk === "VP8L" && bytes[20] === 0x2f) {
      return {
        width: 1 + (bytes[21] | ((bytes[22] & 0x3f) << 8)),
        height: 1 + ((bytes[22] >> 6) | (bytes[23] << 2) | ((bytes[24] & 0x0f) << 10)),
      };
    }
    const signature = bytes.indexOf(Buffer.from([0x9d, 0x01, 0x2a]), 20);
    if (signature >= 0 && signature + 7 <= bytes.length) {
      return {
        width: bytes.readUInt16LE(signature + 3) & 0x3fff,
        height: bytes.readUInt16LE(signature + 5) & 0x3fff,
      };
    }
  }
  throw new Error(`Cannot read native dimensions for ${contentType}`);
}

export function buildSessionGrid(images, {
  columns = 4,
  cellSize = 512,
  imageGap = 48,
  padding = 64,
} = {}) {
  const dimensions = Number.isInteger(images)
    ? Array.from({ length: images }, () => ({ width: cellSize, height: cellSize }))
    : images;
  const count = dimensions?.length ?? 0;
  for (const [name, value] of Object.entries({ count, columns, imageGap, padding })) {
    if (!Number.isInteger(value) || value < (name === "imageGap" || name === "padding" ? 0 : 1)) {
      throw new Error(`${name} must be a ${name === "imageGap" || name === "padding" ? "non-negative" : "positive"} integer`);
    }
  }
  for (const [index, dimension] of dimensions.entries()) {
    if (!Number.isInteger(dimension?.width) || dimension.width < 1
        || !Number.isInteger(dimension?.height) || dimension.height < 1) {
      throw new Error(`image ${index + 1} must have positive integer dimensions`);
    }
  }
  const effectiveColumns = Math.min(columns, count);
  const rows = Math.ceil(count / effectiveColumns);
  const columnWidths = Array.from({ length: effectiveColumns }, () => 0);
  const rowHeights = Array.from({ length: rows }, () => 0);
  dimensions.forEach((dimension, index) => {
    const row = Math.floor(index / effectiveColumns);
    const column = index % effectiveColumns;
    columnWidths[column] = Math.max(columnWidths[column], dimension.width);
    rowHeights[row] = Math.max(rowHeights[row], dimension.height);
  });
  const columnX = columnWidths.map((_, column) => padding
    + columnWidths.slice(0, column).reduce((sum, width) => sum + width, 0)
    + column * imageGap);
  const rowY = rowHeights.map((_, row) => padding
    + rowHeights.slice(0, row).reduce((sum, height) => sum + height, 0)
    + row * imageGap);
  const placements = dimensions.map((dimension, index) => {
    const row = Math.floor(index / effectiveColumns);
    const column = index % effectiveColumns;
    return {
      index,
      row,
      column,
      x: columnX[column],
      y: rowY[row],
      width: dimension.width,
      height: dimension.height,
    };
  });
  return {
    columns: effectiveColumns,
    rows,
    width: padding * 2 + columnWidths.reduce((sum, width) => sum + width, 0)
      + (effectiveColumns - 1) * imageGap,
    height: padding * 2 + rowHeights.reduce((sum, height) => sum + height, 0)
      + (rows - 1) * imageGap,
    placements,
  };
}

export function assetsFromRun(runDirectory, run) {
  if (!Array.isArray(run?.outputs) || run.outputs.length === 0) {
    throw new Error("run.json must contain at least one ordered output");
  }
  const base = path.resolve(runDirectory);
  return run.outputs.map((output, index) => {
    if (!output || typeof output.file !== "string" || !output.file) {
      throw new Error(`run.json output ${index + 1} has no file`);
    }
    const candidate = path.resolve(base, output.file);
    if (candidate !== base && !candidate.startsWith(`${base}${path.sep}`)) {
      throw new Error(`run.json output ${index + 1} resolves outside the run directory`);
    }
    return candidate;
  });
}

export function extractFigJamFrames(xml) {
  const frames = [];
  for (const match of String(xml).matchAll(/<frame\b([^>]*)\/?\s*>/g)) {
    const attributes = Object.fromEntries(
      [...match[1].matchAll(/([\w-]+)="([^"]*)"/g)].map((entry) => [entry[1], entry[2]]),
    );
    if (!/^\d+[:-]\d+$/.test(attributes.id ?? "")) continue;
    const values = [attributes.x, attributes.y, attributes.width, attributes.height].map(Number);
    if (!values.every(Number.isFinite)) continue;
    frames.push({
      nodeId: attributes.id.replace("-", ":"),
      x: values[0],
      y: values[1],
      width: values[2],
      height: values[3],
    });
  }
  return frames.sort((left, right) => left.y - right.y || left.x - right.x || left.nodeId.localeCompare(right.nodeId));
}

export function parseIntegerOption(name, value, { min = 0, max = Number.MAX_SAFE_INTEGER } = {}) {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < min || parsed > max) {
    const range = max === Number.MAX_SAFE_INTEGER ? `at least ${min}` : `from ${min} through ${max}`;
    throw new Error(`${name} must be an integer ${range}`);
  }
  return parsed;
}

function parseOptions(argv) {
  const options = { asset: [], placedNode: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token.startsWith("--")) throw new Error(`Unexpected argument: ${token}`);
    const key = token.slice(2).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) throw new Error(`Missing value for ${token}`);
    index += 1;
    if (key === "asset") options.asset.push(value);
    else if (key === "placedNode") options.placedNode.push(value.replace("-", ":"));
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

async function writeJson(outputPath, value) {
  await ensureOutput(outputPath);
  await writeFile(outputPath, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function parseToolResult(result) {
  const text = resultText(result).trim();
  if (!text) throw new Error("Figma returned an empty tool result");
  try {
    return JSON.parse(text);
  } catch {
    const match = text.match(/\{[\s\S]*\}/);
    if (!match) throw new Error("Figma returned an unreadable tool result");
    return JSON.parse(match[0]);
  }
}

function createSessionSectionCode(grid, sessionGap) {
  return `
const page = figma.currentPage;
let maxBottom = null;
for (const child of page.children) {
  const bottom = child.y + child.height;
  maxBottom = maxBottom === null ? bottom : Math.max(maxBottom, bottom);
}
const section = figma.createSection();
section.name = "";
section.fills = [{ type: "SOLID", color: { r: 1, g: 1, b: 1 } }];
section.resize(${grid.width}, ${grid.height});
section.x = 0;
section.y = maxBottom === null ? 0 : maxBottom + ${sessionGap};
return {
  createdNodeIds: [section.id],
  sectionId: section.id,
  x: section.x,
  y: section.y,
  width: section.width,
  height: section.height
};`.trim();
}

function placeImageBatchCode(sectionId, entries) {
  return `
const section = await figma.getNodeByIdAsync(${JSON.stringify(sectionId)});
if (!section || section.type !== "SECTION") throw new Error("Session section is unavailable");
const entries = ${JSON.stringify(entries)};
const nodes = await Promise.all(entries.map((entry) => figma.getNodeByIdAsync(entry.nodeId)));
if (nodes.some((node) => !node)) throw new Error("One or more uploaded image nodes are unavailable");
for (let index = 0; index < nodes.length; index += 1) {
  const node = nodes[index];
  const entry = entries[index];
  section.appendChild(node);
  node.resize(entry.width, entry.height);
  if ("fills" in node && node.fills !== figma.mixed) {
    node.fills = node.fills.map((paint) => paint.type === "IMAGE"
      ? { ...paint, scaleMode: "FIT", scalingFactor: 1 }
      : paint);
  }
  node.x = entry.x;
  node.y = entry.y;
}
return {
  mutatedNodeIds: [section.id, ...nodes.map((node) => node.id)],
  placements: nodes.map((node, index) => ({
    nodeId: node.id,
    x: node.x,
    y: node.y,
    width: node.width,
    height: node.height,
    scaleMode: "FIT",
    index: entries[index].index
  }))
};`.trim();
}

function normalizeSessionSectionCode(sectionId, sessionGap) {
  return `
const section = await figma.getNodeByIdAsync(${JSON.stringify(sectionId)});
if (!section || section.type !== "SECTION") throw new Error("Session section is unavailable");
let maxBottom = null;
for (const child of figma.currentPage.children) {
  if (child.id === section.id) continue;
  const bottom = child.y + child.height;
  maxBottom = maxBottom === null ? bottom : Math.max(maxBottom, bottom);
}
section.x = 0;
section.y = maxBottom === null ? 0 : maxBottom + ${sessionGap};
return {
  mutatedNodeIds: [section.id],
  sectionId: section.id,
  x: section.x,
  y: section.y,
  width: section.width,
  height: section.height
};`.trim();
}

async function readExistingJson(filePath) {
  try {
    return JSON.parse(await readFile(filePath, "utf8"));
  } catch (error) {
    if (error?.code === "ENOENT") return null;
    throw error;
  }
}

async function finishGridPlacement(client, target, options, record, provenancePath, grid, nodeIds) {
  const sessionGap = parseIntegerOption(
    "session-gap", options.sessionGap ?? record.layout.sessionGap ?? 240, { min: 0 },
  );
  const maxDimension = parseIntegerOption(
    "max-dimension", options.maxDimension ?? 4096, { min: 1 },
  );
  const createResult = parseToolResult(await client.call("use_figma", {
    fileKey: target.fileKey,
    code: createSessionSectionCode(grid, sessionGap),
    description: `Create one untitled white image-session section for ${record.sessionId}`,
    skillNames: "figma-use,figma-use-figjam",
  }));
  if (!/^\d+[:-]\d+$/.test(createResult.sectionId ?? "")) {
    throw new Error("Figma did not return the created session section ID");
  }
  record.status = "positioning";
  record.section = createResult;
  record.placements = [];
  await writeJson(provenancePath, record);

  const entries = grid.placements.map((placement, index) => ({
    ...placement,
    nodeId: nodeIds[index],
  }));
  for (let start = 0; start < entries.length; start += 8) {
    const batch = entries.slice(start, start + 8);
    const result = parseToolResult(await client.call("use_figma", {
      fileKey: target.fileKey,
      code: placeImageBatchCode(createResult.sectionId, batch),
      description: `Place native image nodes ${start + 1}-${start + batch.length} for ${record.sessionId}`,
      skillNames: "figma-use,figma-use-figjam",
    }));
    record.placements.push(...result.placements);
    await writeJson(provenancePath, record);
  }

  const normalizedSection = parseToolResult(await client.call("use_figma", {
    fileKey: target.fileKey,
    code: normalizeSessionSectionCode(
      createResult.sectionId,
      sessionGap,
    ),
    description: `Append the completed native-resolution session ${record.sessionId} below prior sessions`,
    skillNames: "figma-use,figma-use-figjam",
  }));
  record.section = normalizedSection;
  await writeJson(provenancePath, record);

  const readbackResult = await client.call("get_figjam", {
    fileKey: target.fileKey,
    nodeId: createResult.sectionId,
    includeImagesOfNodes: true,
  });
  const readback = resultText(readbackResult);
  if (/<(?:text|sticky|connector|shape-with-text)\b/i.test(readback)) {
    throw new Error("Live readback contains prohibited visible board chrome");
  }
  for (const nodeId of nodeIds) {
    if (!readback.includes(nodeId)) throw new Error(`Live readback is missing image node ${nodeId}`);
  }
  const evidenceDirectory = path.dirname(provenancePath);
  const readbackPath = path.join(evidenceDirectory, "figjam-final-output.xml");
  await writeFile(readbackPath, readback, "utf8");

  const screenshotResult = await client.call("get_screenshot", {
    fileKey: target.fileKey,
    nodeId: createResult.sectionId,
    maxDimension,
    enableBase64Response: false,
    contentsOnly: true,
  });
  const screenshotUrl = firstHttpsUrl(screenshotResult);
  if (!screenshotUrl) throw new Error("Figma screenshot response contained no download URL");
  const screenshotResponse = await fetch(screenshotUrl);
  if (!screenshotResponse.ok) throw new Error(`Screenshot download failed with HTTP ${screenshotResponse.status}`);
  const screenshotBytes = Buffer.from(await screenshotResponse.arrayBuffer());
  const screenshotPath = path.join(evidenceDirectory, "figjam-final-output.png");
  await writeFile(screenshotPath, screenshotBytes);

  record.status = "completed";
  record.completedAt = new Date().toISOString();
  delete record.error;
  delete record.stoppedAt;
  record.readback = {
    xmlPath: path.relative(path.dirname(provenancePath), readbackPath),
    xmlSha256: sha256(readback),
    screenshotPath: path.relative(path.dirname(provenancePath), screenshotPath),
    screenshotSha256: sha256(screenshotBytes),
    nodeIdsPresent: true,
    prohibitedVisibleChromePresent: false,
  };
  await writeJson(provenancePath, record);
  return { provenancePath, ...record };
}

async function reconcileGrid(client, target, options) {
  if (!options.provenanceOut) throw new Error("reconcile-grid requires --provenance-out");
  const provenancePath = path.resolve(options.provenanceOut);
  const record = await readExistingJson(provenancePath);
  if (!record) throw new Error("The placement record does not exist");
  if (!["ambiguous", "uploading", "uploaded"].includes(record.status)) {
    throw new Error(`Only an incomplete delivery can be reconciled; found ${record.status}`);
  }
  if (record.section || record.placements?.length) {
    throw new Error("This delivery already has placement state; inspect its section before reconciliation");
  }
  if (options.placedNode.length !== record.sources?.length) {
    throw new Error(`Expected ${record.sources?.length ?? 0} --placed-node values in source order`);
  }
  if (new Set(options.placedNode).size !== options.placedNode.length
      || options.placedNode.some((nodeId) => !/^\d+[:-]\d+$/.test(nodeId))) {
    throw new Error("Reconciliation node IDs must be unique FigJam node IDs");
  }
  const rootResult = await client.call("get_figjam", {
    fileKey: target.fileKey,
    nodeId: target.rootNodeId,
    includeImagesOfNodes: true,
  });
  const rootFrames = new Set(extractFigJamFrames(resultText(rootResult)).map(({ nodeId }) => nodeId));
  for (const nodeId of options.placedNode) {
    if (!rootFrames.has(nodeId)) throw new Error(`Reconciliation node ${nodeId} is not a top-level uploaded frame`);
  }
  for (const source of record.sources) {
    if (Number.isInteger(source.width) && Number.isInteger(source.height)) continue;
    const sourceBytes = await readFile(path.resolve(source.path));
    Object.assign(source, imageDimensions(sourceBytes, source.contentType));
  }
  const grid = buildSessionGrid(record.sources, {
    columns: record.layout.columns,
    imageGap: record.layout.imageGap,
    padding: record.layout.padding,
  });
  record.reconciliation = {
    method: "explicit-live-node-ids",
    reconciledAt: new Date().toISOString(),
    nodeIds: options.placedNode,
  };
  record.layout.resolution = "native";
  delete record.layout.cellSize;
  record.uploads = record.sources.map((source, index) => ({
    index,
    sourceSha256: source.sha256,
    nodeId: options.placedNode[index],
  }));
  await writeJson(provenancePath, record);
  try {
    return await finishGridPlacement(
      client, target, options, record, provenancePath, grid, options.placedNode,
    );
  } catch (error) {
    record.status = "ambiguous";
    record.stoppedAt = new Date().toISOString();
    record.error = error instanceof Error ? error.message : String(error);
    await writeJson(provenancePath, record);
    throw error;
  }
}

async function deliverGrid(client, target, options) {
  const runDirectory = options.runDir ? path.resolve(options.runDir) : null;
  if (runDirectory && options.asset.length) throw new Error("Use --run-dir or --asset, not both");
  let assets = options.asset.map((value) => path.resolve(value));
  if (runDirectory) {
    const run = JSON.parse(await readFile(path.join(runDirectory, "run.json"), "utf8"));
    assets = assetsFromRun(runDirectory, run);
  }
  if (!assets.length) throw new Error("deliver-grid requires --run-dir or at least one --asset");

  const uploadUrlChunkSize = parseIntegerOption(
    "upload-url-chunk-size", options.uploadUrlChunkSize ?? 20, { min: 1, max: 60 },
  );

  const sessionId = options.sessionId ?? (runDirectory ? path.basename(runDirectory) : null);
  if (!sessionId) throw new Error("Explicit assets require --session-id");
  const provenancePath = path.resolve(options.provenanceOut ?? (runDirectory
    ? path.join(runDirectory, "figjam-placement.json")
    : ""));
  if (!options.provenanceOut && !runDirectory) {
    throw new Error("Explicit assets require --provenance-out");
  }
  const existing = await readExistingJson(provenancePath);
  if (existing) {
    throw new Error(`Delivery record already exists with status ${existing.status ?? "unknown"}; reconcile it before another upload`);
  }

  const sources = [];
  for (const absolutePath of assets) {
    const contentType = guessContentType(absolutePath);
    if (contentType === "image/svg+xml") throw new Error("deliver-grid accepts raster images only");
    const fileStat = await stat(absolutePath);
    if (!fileStat.isFile()) throw new Error(`Asset is not a file: ${absolutePath}`);
    if (fileStat.size > 10 * 1024 * 1024) throw new Error(`Asset exceeds Figma's 10MB limit: ${absolutePath}`);
    const bytes = await readFile(absolutePath);
    const dimensions = imageDimensions(bytes, contentType);
    sources.push({
      absolutePath,
      path: path.relative(process.cwd(), absolutePath) || path.basename(absolutePath),
      file: path.basename(absolutePath),
      bytes: bytes.length,
      contentType,
      sha256: sha256(bytes),
      ...dimensions,
    });
  }

  const grid = buildSessionGrid(sources, {
    columns: Number(options.columns ?? 4),
    imageGap: Number(options.imageGap ?? 48),
    padding: Number(options.padding ?? 64),
  });
  const record = {
    schemaVersion: 1,
    status: "uploading",
    sessionId,
    target: {
      fileKey: target.fileKey,
      rootNodeId: target.rootNodeId,
      url: target.url,
    },
    layout: {
      order: "row-major",
      sessionOrder: "top-to-bottom",
      columns: grid.columns,
      rows: grid.rows,
      resolution: "native",
      imageGap: Number(options.imageGap ?? 48),
      sessionGap: Number(options.sessionGap ?? 240),
      padding: Number(options.padding ?? 64),
      scaleMode: "FIT",
      visibleTextCount: 0,
      uploadUrlChunkSize,
    },
    sources: sources.map(({ absolutePath: _absolutePath, ...source }) => source),
    startedAt: new Date().toISOString(),
  };
  await writeJson(provenancePath, record);

  try {
    const beforeResult = await client.call("get_figjam", {
      fileKey: target.fileKey,
      nodeId: target.rootNodeId,
      includeImagesOfNodes: false,
    });
    const beforeXml = resultText(beforeResult);
    const beforeNodeIds = new Set(extractFigJamFrames(beforeXml).map(({ nodeId }) => nodeId));
    record.preflight = {
      rootReadbackSha256: sha256(beforeXml),
      frameNodeIds: [...beforeNodeIds],
    };
    await writeJson(provenancePath, record);

    const nodeIds = [];
    record.uploads = [];
    for (let start = 0; start < sources.length; start += uploadUrlChunkSize) {
      const chunk = sources.slice(start, start + uploadUrlChunkSize);
      const uploadResult = await client.call("upload_assets", {
        fileKey: target.fileKey,
        count: chunk.length,
        batchCommit: false,
        scaleMode: "FIT",
      });
      const uploadUrls = extractUploadUrls(uploadResult, chunk.length);
      for (let offset = 0; offset < chunk.length; offset += 1) {
        const source = chunk[offset];
        const index = start + offset;
        try {
          const response = await fetch(uploadUrls[offset], {
            method: "POST",
            headers: { "content-type": source.contentType },
            body: await readFile(source.absolutePath),
          });
          const body = await response.text();
          if (!response.ok) {
            throw new Error(`Asset upload failed for ${source.file} with HTTP ${response.status}`);
          }
          let placement = null;
          try {
            placement = extractPlacedNode(body);
          } catch {
            // Current Figma submit responses may acknowledge placement without a node ID.
          }
          record.uploads.push({
            index,
            sourceSha256: source.sha256,
            responseSha256: sha256(body),
            nodeId: placement?.nodeId ?? null,
          });
          await writeJson(provenancePath, record);
        } catch (error) {
          record.uploads.push({
            index,
            sourceSha256: source.sha256,
            status: "unknown",
            error: error instanceof Error ? error.message : String(error),
          });
          throw error;
        }
      }

      const afterResult = await client.call("get_figjam", {
        fileKey: target.fileKey,
        nodeId: target.rootNodeId,
        includeImagesOfNodes: false,
      });
      const afterXml = resultText(afterResult);
      const newFrames = extractFigJamFrames(afterXml)
        .filter(({ nodeId }) => !beforeNodeIds.has(nodeId));
      if (newFrames.length !== chunk.length) {
        throw new Error(`Live board diff found ${newFrames.length} new frame(s), expected ${chunk.length}`);
      }
      for (const frame of newFrames) {
        nodeIds.push(frame.nodeId);
        beforeNodeIds.add(frame.nodeId);
      }
      for (let offset = 0; offset < chunk.length; offset += 1) {
        record.uploads[start + offset].nodeId = newFrames[offset].nodeId;
      }
      record.postUpload = {
        rootReadbackSha256: sha256(afterXml),
        newFrameNodeIds: [...nodeIds],
      };
      await writeJson(provenancePath, record);
    }
    record.status = "uploaded";
    await writeJson(provenancePath, record);
    return await finishGridPlacement(client, target, options, record, provenancePath, grid, nodeIds);
  } catch (error) {
    record.status = "ambiguous";
    record.stoppedAt = new Date().toISOString();
    record.error = error instanceof Error ? error.message : String(error);
    await writeJson(provenancePath, record);
    throw error;
  }
}

function firstHttpsUrl(value) {
  return collectUrls(value).map(({ url }) => url).find((url) => /^https:\/\//.test(url));
}

async function main(argv) {
  const [command, ...rest] = argv;
  if (!command) throw new Error("Expected command: tools, call, get-figjam, screenshot, upload, deliver-grid, reconcile-grid, or use");
  const options = parseOptions(rest);
  const target = await resolveTarget(options);
  const client = await connect();

  if (command === "tools") {
    const result = await client.request("tools/list");
    if (options.json === "true") {
      process.stdout.write(`${JSON.stringify(result.tools ?? [], null, 2)}\n`);
      return;
    }
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

  if (command === "deliver-grid") {
    const result = await deliverGrid(client, target, options);
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
    return;
  }

  if (command === "reconcile-grid") {
    const result = await reconcileGrid(client, target, options);
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
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
