import assert from "node:assert/strict";
import test from "node:test";

import {
  extractUploadUrls,
  guessContentType,
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
