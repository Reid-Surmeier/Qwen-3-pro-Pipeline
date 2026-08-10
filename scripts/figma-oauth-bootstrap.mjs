import { createHash, randomBytes } from "node:crypto";
import { chmod, mkdir, readFile, rename, writeFile } from "node:fs/promises";
import { createServer } from "node:http";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

const FIGMA_AUTHORIZATION_ENDPOINT = "https://www.figma.com/oauth/mcp";
const FIGMA_REGISTRATION_ENDPOINT = "https://api.figma.com/v1/oauth/mcp/register";
const FIGMA_TOKEN_ENDPOINT = "https://api.figma.com/v1/oauth/token";
const FIGMA_MCP_URL = "https://mcp.figma.com/mcp";
const FIGMA_SCOPE = "mcp:connect";

export function callbackIdForServer(serverUrl) {
  const normalized = new URL(serverUrl).toString();
  return createHash("sha256")
    .update(normalized)
    .digest()
    .subarray(0, 9)
    .toString("base64url");
}

export async function registerFigmaClient({
  redirectUri,
  fetchImpl = fetch,
}) {
  const response = await fetchImpl(FIGMA_REGISTRATION_ENDPOINT, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "user-agent": "codex-mcp-client/0.147.0",
    },
    body: JSON.stringify({
      client_name: "Codex",
      redirect_uris: [redirectUri],
      grant_types: ["authorization_code", "refresh_token"],
      token_endpoint_auth_method: "none",
      response_types: ["code"],
      scope: "mcp:connect",
      application_type: "native",
    }),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(
      `Figma client registration failed (${response.status}): ${payload.error_description ?? payload.error ?? "unknown error"}`,
    );
  }
  if (!payload.client_id || !payload.token_endpoint_auth_method) {
    throw new Error("Figma client registration returned incomplete metadata");
  }
  return payload;
}

export function buildTokenRequest({
  clientId,
  clientSecret,
  tokenEndpointAuthMethod,
  code,
  codeVerifier,
  redirectUri,
  resource,
}) {
  if (
    !["none", "client_secret_basic", "client_secret_post"].includes(
      tokenEndpointAuthMethod,
    )
  ) {
    throw new Error(
      `Unsupported token endpoint auth method: ${tokenEndpointAuthMethod}`,
    );
  }

  const body = new URLSearchParams({
    grant_type: "authorization_code",
    code,
    redirect_uri: redirectUri,
    code_verifier: codeVerifier,
  });
  const headers = { "content-type": "application/x-www-form-urlencoded" };

  if (tokenEndpointAuthMethod === "client_secret_basic") {
    if (!clientSecret) throw new Error("Basic token exchange requires a client secret");
    headers.authorization = `Basic ${Buffer.from(`${clientId}:${clientSecret}`).toString("base64")}`;
  } else {
    body.set("client_id", clientId);
    if (tokenEndpointAuthMethod === "client_secret_post") {
      if (!clientSecret) throw new Error("POST token exchange requires a client secret");
      body.set("client_secret", clientSecret);
    }
  }
  if (resource) body.set("resource", resource);

  return {
    headers,
    body,
  };
}

export function buildAuthorizationUrl({
  authorizationEndpoint,
  clientId,
  redirectUri,
  scope,
  state,
  codeChallenge,
  resource,
}) {
  const url = new URL(authorizationEndpoint);
  url.search = new URLSearchParams({
    response_type: "code",
    client_id: clientId,
    redirect_uri: redirectUri,
    scope,
    state,
    code_challenge: codeChallenge,
    code_challenge_method: "S256",
    resource,
  }).toString();
  return url.toString();
}

function codexCredentialKey(serverName, serverUrl) {
  const identity = JSON.stringify({ type: "http", url: serverUrl, headers: {} });
  const digest = createHash("sha256").update(identity).digest("hex").slice(0, 16);
  return `${serverName}|${digest}`;
}

export async function persistCodexCredentials({
  codexHome,
  serverName,
  serverUrl,
  clientId,
  tokenResponse,
  now = Date.now(),
}) {
  const credentialsPath = path.join(codexHome, ".credentials.json");
  let credentials = {};
  try {
    credentials = JSON.parse(await readFile(credentialsPath, "utf8"));
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
  }

  const expiresIn = Number(tokenResponse.expires_in);
  const expiresAt = Number.isFinite(expiresIn)
    ? now + Math.max(0, expiresIn) * 1_000
    : undefined;
  const scopes = String(tokenResponse.scope ?? "")
    .split(/\s+/)
    .filter(Boolean);

  const entry = {
    server_name: serverName,
    server_url: serverUrl,
    client_id: clientId,
    access_token: tokenResponse.access_token,
    ...(expiresAt === undefined ? {} : { expires_at: expiresAt }),
    ...(tokenResponse.refresh_token
      ? { refresh_token: tokenResponse.refresh_token }
      : {}),
    scopes,
  };
  credentials[codexCredentialKey(serverName, serverUrl)] = entry;

  await mkdir(codexHome, { recursive: true });
  const temporaryPath = `${credentialsPath}.${process.pid}.${randomBytes(6).toString("hex")}.tmp`;
  await writeFile(temporaryPath, JSON.stringify(credentials), {
    encoding: "utf8",
    mode: 0o600,
  });
  await chmod(temporaryPath, 0o600);
  await rename(temporaryPath, credentialsPath);
  await chmod(credentialsPath, 0o600);
}

async function exchangeFigmaCode({
  registration,
  code,
  codeVerifier,
  redirectUri,
  fetchImpl = fetch,
}) {
  const request = buildTokenRequest({
    clientId: registration.client_id,
    clientSecret: registration.client_secret,
    // Match the exchange shape used by the last Codex release known to work
    // with Figma. Newer Codex adds RFC 8707 `resource` during this request.
    tokenEndpointAuthMethod: "client_secret_basic",
    code,
    codeVerifier,
    redirectUri,
  });
  const response = await fetchImpl(FIGMA_TOKEN_ENDPOINT, {
    method: "POST",
    headers: request.headers,
    body: request.body,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(
      `Figma token exchange failed (${response.status}): ${payload.error_description ?? payload.error ?? "unknown error"}`,
    );
  }
  if (!payload.access_token) {
    throw new Error("Figma token exchange returned no access token");
  }
  return payload;
}

function listen(server, port) {
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(port, "0.0.0.0", () => {
      server.off("error", reject);
      resolve();
    });
  });
}

function close(server) {
  return new Promise((resolve) => server.close(resolve));
}

export async function runFigmaOAuthBootstrap({
  port = 4321,
  codexHome = process.env.CODEX_HOME || path.join(os.homedir(), ".codex"),
  fetchImpl = fetch,
  output = console.log,
  timeoutMs = 10 * 60 * 1_000,
} = {}) {
  const callbackId = callbackIdForServer(FIGMA_MCP_URL);
  const callbackPath = `/callback/${callbackId}`;
  const redirectUri = `http://127.0.0.1:${port}${callbackPath}`;
  const state = randomBytes(24).toString("base64url");
  const codeVerifier = randomBytes(32).toString("base64url");
  const codeChallenge = createHash("sha256")
    .update(codeVerifier)
    .digest("base64url");

  let completeCallback;
  let failCallback;
  const completion = new Promise((resolve, reject) => {
    completeCallback = resolve;
    failCallback = reject;
  });
  let callbackHandled = false;
  let registration;

  const server = createServer(async (request, response) => {
    const callbackUrl = new URL(request.url, redirectUri);
    if (callbackUrl.pathname !== callbackPath) {
      response.writeHead(404, { "content-type": "text/plain; charset=utf-8" });
      response.end("Not found");
      return;
    }
    if (callbackHandled) {
      response.writeHead(409, { "content-type": "text/plain; charset=utf-8" });
      response.end("OAuth callback already handled");
      return;
    }
    callbackHandled = true;

    try {
      const providerError = callbackUrl.searchParams.get("error");
      if (providerError) {
        throw new Error(
          `Figma authorization failed: ${callbackUrl.searchParams.get("error_description") ?? providerError}`,
        );
      }
      if (callbackUrl.searchParams.get("state") !== state) {
        throw new Error("Figma OAuth state mismatch");
      }
      const code = callbackUrl.searchParams.get("code");
      if (!code) throw new Error("Figma OAuth callback contained no code");

      const tokenResponse = await exchangeFigmaCode({
        registration,
        code,
        codeVerifier,
        redirectUri,
        fetchImpl,
      });
      await persistCodexCredentials({
        codexHome,
        serverName: "figma",
        serverUrl: FIGMA_MCP_URL,
        clientId: registration.client_id,
        tokenResponse,
      });
      response.writeHead(200, { "content-type": "text/plain; charset=utf-8" });
      response.end("Authentication complete. You may close this window.");
      completeCallback();
    } catch (error) {
      response.writeHead(400, { "content-type": "text/plain; charset=utf-8" });
      response.end(error.message);
      failCallback(error);
    }
  });

  await listen(server, port);
  try {
    registration = await registerFigmaClient({ redirectUri, fetchImpl });
    const authorizationUrl = buildAuthorizationUrl({
      authorizationEndpoint: FIGMA_AUTHORIZATION_ENDPOINT,
      clientId: registration.client_id,
      redirectUri,
      scope: FIGMA_SCOPE,
      state,
      codeChallenge,
      resource: FIGMA_MCP_URL,
    });
    output(`FIGMA_AUTH_URL=${authorizationUrl}`);

    let timer;
    const timeout = new Promise((_, reject) => {
      timer = setTimeout(
        () => reject(new Error("Timed out waiting for the Figma OAuth callback")),
        timeoutMs,
      );
    });
    try {
      await Promise.race([completion, timeout]);
    } finally {
      clearTimeout(timer);
    }
    output("FIGMA_OAUTH_COMPLETE");
  } finally {
    await close(server);
  }
}

if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
) {
  runFigmaOAuthBootstrap().catch((error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
}
