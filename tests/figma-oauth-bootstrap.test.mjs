import assert from "node:assert/strict";
import { mkdtemp, readFile, stat } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import {
  buildAuthorizationUrl,
  buildTokenRequest,
  callbackIdForServer,
  persistCodexCredentials,
  registerFigmaClient,
} from "../scripts/figma-oauth-bootstrap.mjs";

test("Figma public-client exchange honors the registered none auth method", () => {
  const request = buildTokenRequest({
    clientId: "registered-client",
    clientSecret: "must-not-be-sent",
    tokenEndpointAuthMethod: "none",
    code: "authorization-code",
    codeVerifier: "pkce-verifier",
    redirectUri: "http://127.0.0.1:4321/callback/id",
    resource: "https://mcp.figma.com/mcp",
  });

  assert.equal(request.headers.authorization, undefined);
  assert.equal(request.body.get("client_secret"), null);
  assert.equal(request.body.get("client_id"), "registered-client");
});

test("known-working legacy exchange uses Basic auth and omits resource", () => {
  const request = buildTokenRequest({
    clientId: "registered-client",
    clientSecret: "registration-secret",
    tokenEndpointAuthMethod: "client_secret_basic",
    code: "authorization-code",
    codeVerifier: "pkce-verifier",
    redirectUri: "http://127.0.0.1:4321/callback/id",
  });

  assert.equal(
    request.headers.authorization,
    `Basic ${Buffer.from("registered-client:registration-secret").toString("base64")}`,
  );
  assert.equal(request.body.get("client_id"), null);
  assert.equal(request.body.get("client_secret"), null);
  assert.equal(request.body.get("resource"), null);
});

test("authorization URL binds Figma MCP, PKCE, callback, and state", () => {
  const url = new URL(
    buildAuthorizationUrl({
      authorizationEndpoint: "https://www.figma.com/oauth/mcp",
      clientId: "registered-client",
      redirectUri: "http://127.0.0.1:4321/callback/id",
      scope: "mcp:connect",
      state: "csrf-state",
      codeChallenge: "pkce-challenge",
      resource: "https://mcp.figma.com/mcp",
    }),
  );

  assert.equal(url.searchParams.get("response_type"), "code");
  assert.equal(url.searchParams.get("client_id"), "registered-client");
  assert.equal(
    url.searchParams.get("redirect_uri"),
    "http://127.0.0.1:4321/callback/id",
  );
  assert.equal(url.searchParams.get("scope"), "mcp:connect");
  assert.equal(url.searchParams.get("state"), "csrf-state");
  assert.equal(url.searchParams.get("code_challenge"), "pkce-challenge");
  assert.equal(url.searchParams.get("code_challenge_method"), "S256");
  assert.equal(url.searchParams.get("resource"), "https://mcp.figma.com/mcp");
});

test("Codex credentials are merged without persisting the registration secret", async () => {
  const codexHome = await mkdtemp(path.join(os.tmpdir(), "figma-oauth-test-"));
  const credentialsPath = path.join(codexHome, ".credentials.json");

  await persistCodexCredentials({
    codexHome,
    serverName: "figma",
    serverUrl: "https://mcp.figma.com/mcp",
    clientId: "registered-client",
    tokenResponse: {
      access_token: "access-token",
      refresh_token: "refresh-token",
      expires_in: 3600,
      scope: "mcp:connect",
      token_type: "Bearer",
      client_secret: "must-not-be-persisted",
    },
    now: 1_000,
  });

  const file = JSON.parse(await readFile(credentialsPath, "utf8"));
  const entries = Object.values(file);
  assert.equal(entries.length, 1);
  assert.equal(entries[0].server_name, "figma");
  assert.equal(entries[0].client_id, "registered-client");
  assert.equal(entries[0].access_token, "access-token");
  assert.equal(entries[0].refresh_token, "refresh-token");
  assert.deepEqual(entries[0].scopes, ["mcp:connect"]);
  assert.equal(entries[0].expires_at, 3_601_000);
  assert.equal(JSON.stringify(file).includes("must-not-be-persisted"), false);
  assert.equal((await stat(credentialsPath)).mode & 0o777, 0o600);
});

test("Figma registration returns and preserves the server-declared auth method", async () => {
  let observedRequest;
  const registration = await registerFigmaClient({
    redirectUri: "http://127.0.0.1:4321/callback/id",
    fetchImpl: async (url, options) => {
      observedRequest = { url, options };
      return new Response(
        JSON.stringify({
          client_id: "registered-client",
          client_secret: "registration-secret",
          redirect_uris: ["http://127.0.0.1:4321/callback/id"],
          scope: "mcp:connect",
          token_endpoint_auth_method: "none",
        }),
        { status: 201, headers: { "content-type": "application/json" } },
      );
    },
  });

  assert.equal(observedRequest.url, "https://api.figma.com/v1/oauth/mcp/register");
  assert.equal(observedRequest.options.method, "POST");
  assert.equal(registration.token_endpoint_auth_method, "none");
});

test("callback identity matches Codex for the hosted Figma MCP URL", () => {
  assert.equal(
    callbackIdForServer("https://mcp.figma.com/mcp"),
    "W2QUbtwYBOaR",
  );
});
