import assert from "node:assert/strict";
import test from "node:test";

import {
  assetsFromRun,
  buildSessionGrid,
  extractPlacedNode,
  extractFigJamFrames,
  extractUploadUrls,
  guessContentType,
  imageDimensions,
  parseIntegerOption,
  parseSsePayload,
  resultText,
} from "../.agents/skills/figma-qwen-ui-pipeline/scripts/figma-mcp.mjs";

test("SSE parser returns the JSON-RPC payload", () => {
  assert.deepEqual(
    parseSsePayload('event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"ok":true}}\n'),
    { jsonrpc: "2.0", id: 1, result: { ok: true } },
  );
});

test("resultText joins only text content blocks", () => {
  assert.equal(
    resultText({ content: [
      { type: "text", text: "first" },
      { type: "image", data: "ignored" },
      { type: "text", text: "second" },
    ] }),
    "first\nsecond",
  );
});

test("upload URL extraction ignores commit URLs and deduplicates", () => {
  const result = {
    content: [{
      type: "text",
      text: JSON.stringify({
        uploadUrls: ["https://uploads.example/one", "https://uploads.example/two"],
        commitUrl: "https://uploads.example/commit",
      }),
    }],
  };
  assert.deepEqual(extractUploadUrls(result, 2), [
    "https://uploads.example/one",
    "https://uploads.example/two",
  ]);
});

test("upload URL extraction accepts current Figma MCP submit URLs", () => {
  const result = {
    content: [{
      type: "text",
      text: JSON.stringify({
        uploads: [{
          submitUrl: "https://mcp.figma.com/mcp/upload/asset-id/submit?scaleMode=FILL",
        }],
      }),
    }],
  };

  assert.deepEqual(extractUploadUrls(result, 1), [
    "https://mcp.figma.com/mcp/upload/asset-id/submit?scaleMode=FILL",
  ]);
});

test("content types cover supported UI asset formats", () => {
  assert.equal(guessContentType("asset.png"), "image/png");
  assert.equal(guessContentType("asset.svg"), "image/svg+xml");
  assert.equal(guessContentType("asset.webp"), "image/webp");
  assert.throws(() => guessContentType("asset.psd"), /Unsupported asset type/);
});

test("upload commit parsing keeps only non-secret placement details", () => {
  assert.deepEqual(
    extractPlacedNode(JSON.stringify({
      ok: true,
      nodeId: "12:34",
      imageHash: "figma-image-hash",
      width: 400,
      height: 300,
      uploadUrl: "https://single-use.example/secret",
    })),
    {
      nodeId: "12:34",
      imageHash: "figma-image-hash",
      width: 400,
      height: 300,
    },
  );
});

test("session grid is deterministic row-major with a white grouping boundary", () => {
  assert.deepEqual(
    buildSessionGrid(5, {
      columns: 4,
      cellSize: 512,
      imageGap: 48,
      padding: 64,
    }),
    {
      columns: 4,
      rows: 2,
      width: 2320,
      height: 1200,
      placements: [
        { index: 0, row: 0, column: 0, x: 64, y: 64, width: 512, height: 512 },
        { index: 1, row: 0, column: 1, x: 624, y: 64, width: 512, height: 512 },
        { index: 2, row: 0, column: 2, x: 1184, y: 64, width: 512, height: 512 },
        { index: 3, row: 0, column: 3, x: 1744, y: 64, width: 512, height: 512 },
        { index: 4, row: 1, column: 0, x: 64, y: 624, width: 512, height: 512 },
      ],
    },
  );
});

test("session grid preserves native dimensions and sizes rows and columns to fit", () => {
  assert.deepEqual(
    buildSessionGrid([
      { width: 800, height: 600 },
      { width: 300, height: 900 },
      { width: 1000, height: 400 },
    ], { columns: 2, imageGap: 48, padding: 64 }),
    {
      columns: 2,
      rows: 2,
      width: 1476,
      height: 1476,
      placements: [
        { index: 0, row: 0, column: 0, x: 64, y: 64, width: 800, height: 600 },
        { index: 1, row: 0, column: 1, x: 1112, y: 64, width: 300, height: 900 },
        { index: 2, row: 1, column: 0, x: 64, y: 1012, width: 1000, height: 400 },
      ],
    },
  );
});

test("large sessions retain one native-size placement per source image", () => {
  const dimensions = Array.from({ length: 65 }, (_, index) => ({
    width: 640 + index,
    height: 480 + index,
  }));
  const grid = buildSessionGrid(dimensions, { columns: 4 });
  assert.equal(grid.placements.length, dimensions.length);
  assert.equal(new Set(grid.placements.map(({ index }) => index)).size, dimensions.length);
  for (const [index, placement] of grid.placements.entries()) {
    assert.equal(placement.width, dimensions[index].width);
    assert.equal(placement.height, dimensions[index].height);
  }
});

test("delivery geometry options reject overlap and invalid screenshot bounds", () => {
  assert.equal(parseIntegerOption("session-gap", "0", { min: 0 }), 0);
  assert.equal(parseIntegerOption("max-dimension", "4096", { min: 1 }), 4096);
  assert.throws(
    () => parseIntegerOption("session-gap", "-1", { min: 0 }),
    /session-gap must be an integer at least 0/,
  );
  assert.throws(
    () => parseIntegerOption("upload-url-chunk-size", "61", { min: 1, max: 60 }),
    /upload-url-chunk-size must be an integer from 1 through 60/,
  );
});

test("PNG dimensions are read without rewriting the image", () => {
  const png = Buffer.alloc(24);
  Buffer.from("89504e470d0a1a0a", "hex").copy(png);
  png.writeUInt32BE(948, 16);
  png.writeUInt32BE(806, 20);
  assert.deepEqual(imageDimensions(png, "image/png"), { width: 948, height: 806 });
});

test("run outputs remain ordered and cannot escape their run directory", () => {
  assert.deepEqual(
    assetsFromRun("/tmp/example-run", {
      outputs: [{ file: "image-01.png" }, { file: "nested/image-02.webp" }],
    }),
    ["/tmp/example-run/image-01.png", "/tmp/example-run/nested/image-02.webp"],
  );
  assert.throws(
    () => assetsFromRun("/tmp/example-run", { outputs: [{ file: "../outside.png" }] }),
    /outside the run directory/,
  );
});

test("FigJam frame discovery recovers upload order from live geometry", () => {
  assert.deepEqual(
    extractFigJamFrames(`
      <canvas id="0:1" name="Page 1" x="0" y="0" width="0" height="0">
        <frame id="4:5" name="Uploaded Image" x="1320" y="0" width="400" height="300" />
        <frame id="4:3" name="Uploaded Image" x="440" y="0" width="400" height="300" />
        <frame id="4:2" name="Uploaded Image" x="0" y="0" width="400" height="300" />
      </canvas>
    `),
    [
      { nodeId: "4:2", x: 0, y: 0, width: 400, height: 300 },
      { nodeId: "4:3", x: 440, y: 0, width: 400, height: 300 },
      { nodeId: "4:5", x: 1320, y: 0, width: 400, height: 300 },
    ],
  );
});
