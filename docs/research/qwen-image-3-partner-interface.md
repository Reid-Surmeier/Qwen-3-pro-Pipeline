# Qwen Image 3 Partner interface audit

Checked 2026-08-26 for Issue #32. This note treats the official ComfyUI node
surface as an interface reference, not as a requirement to use ComfyUI's paid
proxy or credentials. The source snapshot is ComfyUI commit
[`7d11ec3`](https://github.com/Comfy-Org/ComfyUI/commit/7d11ec31cb700d881fdf2d73731ecde0093b9540),
which introduced the Qwen Image 3 Partner Nodes.

## Visible Partner Node contract

| Concept | Text to image | Edit |
| --- | --- | --- |
| Node | `QwenImageTextToImageApi`, displayed as **Qwen Image 3 Text to Image** | `QwenImageEditApi`, displayed as **Qwen Image 3 Edit** |
| Model-dependent inputs | model (`qwen-image-3.0-pro` or `qwen-image-3.0`), multiline prompt, multiline negative prompt, width, height | model, autogrowing `image_1` through `image_3`, multiline prompt, multiline negative prompt |
| Size | explicit width and height | `match input`, `auto`, or `custom`; custom reveals width and height |
| Common controls | `n` 1-6, seed 0-2147483647, advanced `prompt_extend` (default true), advanced `watermark` (default false) | same |
| Output | one `IMAGE` output; all returned images are concatenated into a ComfyUI batch | same |

The official implementation keeps Comfy account/API credentials hidden and
shows a price badge separately from the request controls. Its T2I and edit
schemas and request assembly are visible in the first-party
[`nodes_qwen.py`](https://github.com/Comfy-Org/ComfyUI/blob/7d11ec31cb700d881fdf2d73731ecde0093b9540/comfy_api_nodes/nodes_qwen.py#L116-L289)
and
[`nodes_qwen.py`](https://github.com/Comfy-Org/ComfyUI/blob/7d11ec31cb700d881fdf2d73731ecde0093b9540/comfy_api_nodes/nodes_qwen.py#L292-L429).
ComfyUI describes Partner Nodes as API-backed external-model nodes and warns
that non-local access should use HTTPS so authentication is not exposed
([Partner Nodes overview](https://docs.comfy.org/tutorials/partner-nodes/overview)).
Its dedicated Qwen guide confirms editing up to three references and generating
one to six images per run
([Qwen Image 3.0 Pro guide](https://docs.comfy.org/tutorials/partner-nodes/qwen/qwen-image-3-0-pro)).

## Reference order and `@ImageN`

- The edit node exposes an ordered autogrowing group named `image_1`,
  `image_2`, and `image_3`, with at least one input. A batch connected to one
  socket contributes one reference per batch element, so the effective
  reference count can exceed the number of connected sockets; the node rejects
  more than three effective images before submission.
- Effective order is socket order, then batch order within each socket. The
  node flattens that order, serializes every image before the text instruction,
  and numbers references from one
  ([source](https://github.com/Comfy-Org/ComfyUI/blob/7d11ec31cb700d881fdf2d73731ecde0093b9540/comfy_api_nodes/nodes_qwen.py#L160-L188),
  [execution](https://github.com/Comfy-Org/ComfyUI/blob/7d11ec31cb700d881fdf2d73731ecde0093b9540/comfy_api_nodes/nodes_qwen.py#L383-L418)).
- `@Image1`, `@Image2`, and `@Image3` are a Partner-interface convention, not
  the provider payload syntax. Before submission the node rewrites them to
  `Image 1`, `Image 2`, and `Image 3`. Matching is case-insensitive;
  unnumbered `@Image` means the first image; an out-of-range reference fails;
  adjacent tags are accepted; and email-like text such as
  `user@image1.com` is left alone
  ([resolver](https://github.com/Comfy-Org/ComfyUI/blob/7d11ec31cb700d881fdf2d73731ecde0093b9540/comfy_api_nodes/nodes_qwen.py#L31-L58)).
- Inputs are reduced to RGB and downscaled to at most 2048 by 2048 total pixel
  bounds before upload. The node prefers PNG and falls back to JPEG if the
  encoded input would exceed the API's 10 MB limit
  ([encoder](https://github.com/Comfy-Org/ComfyUI/blob/7d11ec31cb700d881fdf2d73731ecde0093b9540/comfy_api_nodes/nodes_qwen.py#L89-L98)).

These semantics mean a compatible local node should resolve tags from a
single explicit ordered-reference list before either provider adapter sees the
prompt. It should reject missing/out-of-range roles and too-large batches,
rather than silently truncating them. They also expose a subtle mismatch with
Issue #32's socket-to-tag guarantee: if `image_1` receives a two-image batch,
official flattened semantics make `@Image2` refer to that socket's second batch
element, not to socket `image_2`. Strict visible-role workflows should require
one effective image per named socket; otherwise the flattening rule must be
made visible and covered by migration tests.

## Provider capability boundary

| Capability | Alibaba direct Qwen Image 3 | OpenRouter Qwen Image 3 endpoint | Local compatibility consequence |
| --- | --- | --- | --- |
| References | 1-3 I2I images; array order is authoritative | 0-4 references | Three is the portable contract. A fourth input must be visibly OpenRouter-only. |
| Size | Omit `size` for automatic choice, or send explicit `width*height`; documented area 512x512 through 2048x2048 and aspect 1:8 through 8:1 | `resolution` is `1K` or `2K`; aspect ratio is one of 13 enumerated values | `auto`, `match input`, and `custom` require provider-specific resolution. Do not claim exact match on OpenRouter when the source ratio is outside its allowlist. |
| Count | `n` 1-6 | `n` 1-6 | A common visible 1-6 control is portable and returns an IMAGE batch. |
| Seed | integer 0-2147483647 | supported | Portable with common bounds. |
| Negative prompt | supported | not advertised in the endpoint capability record | Do not silently discard it. Reject a non-empty unsupported value or document an explicit prompt-compilation transformation. |
| Prompt expansion | `prompt_extend`; `direct` works for T2I and I2I, while `agent` is T2I-only and returns 400 for I2I | not advertised; Alibaba endpoint's passthrough allowlist is empty | The visible toggle must be disabled/rejected for OpenRouter, or its behavior must be implemented locally and recorded as such. |
| Watermark | supported, default false | not advertised | Same fail-before-request rule as prompt expansion. |

Alibaba's current API reference defines the ordered 1-3 image payload, input
limits, prompt expansion modes, count, size, seed, negative prompt, and
watermark
([request parameters](https://help.aliyun.com/en/model-studio/qwen-image-generation-and-editing-api-reference)).
OpenRouter says an absent endpoint capability means unsupported, and that
per-endpoint records are definitive
([capability descriptors](https://openrouter.ai/docs/guides/overview/multimodal/image-generation#capability-descriptors)).
Its live Qwen records currently advertise only 1K/2K, the enumerated aspect
ratios, `n`, up to four references, and seed, with no provider-specific
passthrough parameters
([Pro endpoint](https://openrouter.ai/api/v1/images/models/qwen/qwen-image-3-pro/endpoints),
[standard endpoint](https://openrouter.ai/api/v1/images/models/qwen/qwen-image-3/endpoints)).

There is one upstream discrepancy to preserve in tests rather than conceal:
the pinned Partner Node accepts custom areas through 2560x2560
([source](https://github.com/Comfy-Org/ComfyUI/blob/7d11ec31cb700d881fdf2d73731ecde0093b9540/comfy_api_nodes/nodes_qwen.py#L24-L29)),
while Alibaba's current direct API documentation says 2048x2048. Direct
Alibaba validation should use the provider's documented limit until that
conflict is reconciled; Partner visual compatibility does not justify a paid
request that the selected adapter says is invalid.

## Migration and audit implications for the local node

The current `QwenImage3Render` has one Edit Brief JSON widget and one optional
batched `reference_images` socket. It also silently slices references to four,
hardcodes Alibaba `prompt_extend=true` and `watermark=false`, omits those
concepts for OpenRouter, and exposes neither negative prompt nor the Partner
size modes. A deterministic implementation plan follows from the source audit:

1. Add separate visible T2I and edit node IDs while retaining
   `QwenImage3Render` as a compatibility adapter, or provide a deterministic
   saved-workflow migration. Do not repurpose its class ID with an incompatible
   schema.
2. Keep provider selection explicit (`openrouter` or `alibaba`) on the new
   nodes. Preserve legacy JSON/provenance support, but do not let hidden JSON
   override a contradictory visible control. Retain the existing no-blind-retry
   behavior.
3. Build one preflight capability validator. It should resolve the selected
   size mode, effective reference count/order, count, seed, negative prompt,
   prompt expansion, and watermark before constructing or sending a paid
   request. Unsupported values must name the provider and control.
4. Preserve the Partner `@ImageN` rewrite and ordered image-first payload for
   both adapters. For the strict portable contract, reject a multi-image batch
   on any named reference socket so each tag continues to denote the socket a
   reviewer sees. Record socket role, effective flattened index, source hash,
   requested versus resolved size, provider/model, output count, seed, prompt
   expansion/watermark state, response usage/cost, and output hashes in run
   metadata.
5. Save representative UI workflows with each `Load Image` also feeding a
   `Preview Image`, then feeding the correspondingly named edit socket. Verify
   save/reopen stability, three-reference provider switching, bad-tag failures,
   batched-input overflow, every unsupported provider/control combination, and
   legacy JSON migration without making paid calls.

The official
[`api_qwen3_image_edit.json`](https://github.com/Comfy-Org/workflow_templates/blob/55818c64caf6d28309ddee204827e51a2c45f4dd/templates/api_qwen3_image_edit.json)
demonstrates a visible `LoadImage` connection but only one populated reference;
it does not prove the three-reference review graph required by Issue #32. The
official
[`api_qwen3_t2i.json`](https://github.com/Comfy-Org/workflow_templates/blob/1956e1c1787471b5b835e6dfee8a3c4d84130241/templates/api_qwen3_t2i.json)
demonstrates connectable width/height widgets and batched `IMAGE` output.

The official Partner node returns only `IMAGE`; retaining the local
`run_metadata` string is an additive audit feature, not an incompatibility.
Likewise, local provider choice is intentionally separate from ComfyUI's
hidden Partner credentials and proxy transport.

## Authenticated remote review patterns

No host or network state was changed during this research.

**Ephemeral, least-state path: OpenSSH local forwarding over the tailnet.** On
the Mac, an operator can establish an authenticated SSH connection to Pugnet
and bind only Mac loopback, conceptually:

```sh
ssh -N \
  -L 127.0.0.1:8188:127.0.0.1:8188 \
  -o ExitOnForwardFailure=yes \
  -o StrictHostKeyChecking=yes \
  <approved-user>@<pugnet-tailnet-name>
```

Then review `http://127.0.0.1:8188` and stop the foreground SSH process to
disconnect. OpenSSH documents that `-N` is for forwarding-only sessions, that
an explicit localhost bind is local-use only, and that
`ExitOnForwardFailure` aborts if the requested listener cannot be established
([`ssh(1)`](https://man.openbsd.org/ssh),
[`ssh_config(5)`](https://man.openbsd.org/ssh_config)). Tailscale documents
tailnet policy authorization, distributed SSH host keys, optional re-check
authentication, and policy-based revocation that terminates existing Tailscale
SSH sessions
([Tailscale SSH](https://tailscale.com/docs/features/tailscale-ssh)). This path
forwards only 8188; it does not expose worker ports 8191-8195 and creates no
public URL.

**Stable HTTPS tailnet link: Tailscale Serve.** If separately approved as a
host/network change, Serve can reverse-proxy only Pugnet's loopback ComfyUI
endpoint and publish the machine's stable `*.ts.net` HTTPS name inside the
tailnet. Tailscale access-control rules apply to Serve, identity headers are
added, and the documentation explicitly distinguishes private Serve from
public Funnel. The backend should continue listening on localhost
([Serve overview](https://tailscale.com/docs/features/tailscale-serve)). Verify
the exact route with `tailscale serve status --json`; remove only that Serve
mapping with the matching `... off` command
([Serve CLI](https://tailscale.com/docs/reference/tailscale-cli/serve)). Do not
use Funnel, do not proxy a range, and do not add 8191-8195 mappings.
Serve's identity headers do not by themselves add application-level
authentication to ComfyUI; protection comes from tailnet identity and the
least-privilege access policy unless the backend explicitly consumes them.

The SSH pattern is the safer acceptance-test path because it is session-bound;
Serve is the pattern that satisfies a reusable HTTPS link. Either still
requires live Mac verification of server identity, graph, queue/history, and
outputs, followed by disconnect/revocation evidence.

## Limitations

- The official edit template populates only `image_1` and does not include the
  three independent previews required as Issue #32 evidence.
- OpenRouter capability records are live service data and can change. Cache the
  record used for implementation tests or re-check it at runtime before paid
  submission.
- No provider request, paid generation, Mac connection, SSH tunnel, Serve
  route, ACL edit, credential read, or Pugnet state inspection was performed.
- The upstream 2560x2560 versus Alibaba 2048x2048 size discrepancy remains
  unresolved and should stay visible in code comments and tests.
