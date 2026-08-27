# Authenticated Mac review of Pugnet ComfyUI

Use an ephemeral local port forward over Tailscale SSH. This creates the stable
review URL `http://127.0.0.1:8188` on the Mac only while the authenticated SSH
session is running. It does not create a public URL or change Pugnet's network
configuration.

## Prerequisites and identity check

- The Mac is signed in to the approved tailnet identity.
- Tailnet policy authorizes that identity and SSH user for Pugnet.
- The Pugnet tailnet name and ComfyUI loopback bind address are obtained at
  runtime from the maintainer or host; neither value belongs in Git, an Issue,
  or a pull request.
- The SSH host key has been approved through the tailnet's authenticated host
  identity. Keep strict host-key checking enabled.

On the Mac, confirm that the intended peer resolves inside the tailnet before
opening the tunnel:

```bash
tailscale status
tailscale ping "${PUGNET_TAILSCALE_HOST}"
```

Match the reported peer identity to Pugnet. Stop if it does not match.

## Connect and review

In a foreground Mac terminal:

```bash
ssh -N \
  -L "127.0.0.1:8188:${PUGNET_COMFYUI_LOOPBACK}:8188" \
  -o ExitOnForwardFailure=yes \
  -o StrictHostKeyChecking=yes \
  "${PUGNET_SSH_USER}@${PUGNET_TAILSCALE_HOST}"
```

Only port 8188 is forwarded. Do not add a port range or ports 8191 through
8195. In a second Mac terminal, verify the routed service and open the local
review URL:

```bash
curl --fail --silent --show-error \
  http://127.0.0.1:8188/system_stats | python3 -m json.tool
curl --fail --silent --show-error \
  http://127.0.0.1:8188/object_info/QwenImage3Edit | python3 -m json.tool
open http://127.0.0.1:8188
```

In the UI:

1. load `workflows/partner-three-reference.workflow.json`;
2. confirm the three Load/Preview lanes match `image_1` through `image_3`;
3. switch between OpenRouter and Alibaba without changing any links;
4. inspect Queue, History, and existing outputs;
5. do not press Queue unless a paid Render Pass has separate approval.

The host-side operator can run the repository's read-only audit to prove that
8188 is the routed endpoint and 8191 through 8195 remain loopback-only:

```bash
python3.12 scripts/audit_comfyui_review_path.py \
  --router-url "${QWEN_COMFYUI_REVIEW_URL}"
```

## Disconnect or revoke

Press `Control-C` in the foreground SSH terminal. Then confirm that the Mac no
longer has the forwarding listener:

```bash
lsof -nP -iTCP:8188 -sTCP:LISTEN
```

For immediate access revocation, the tailnet administrator removes the user's
Tailscale SSH policy grant. Do not use Tailscale Funnel. A persistent Tailscale
Serve route is also outside this procedure and requires separate production
network approval.

Record the Mac test date, reviewer, server identity, loaded workflow, visible
node IDs, queue/history result, disconnect result, and any remaining approval
in the pull request without copying private hostnames, addresses, or tokens.
