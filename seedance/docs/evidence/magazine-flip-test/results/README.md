# Magazine-flip test — batch result: all four cells refused by the provider ($0 billed)

First live smooth-grammar batch (2026-08-27). All four jobs reached ByteDance and **failed
at generation time**; no output was produced and no billing records exist for any of the
four generation IDs (the OpenRouter generation ledger returns 404 for each — treated as
$0 unless the invoice says otherwise).

| Cell | Provider error |
| --- | --- |
| flip-basic | "output video may be related to copyright restrictions" |
| flip-refs | "One or more parameters ... not valid: Bad Request" (failed at parameter validation before any content check) |
| flip-riffle | "output video may be related to copyright restrictions" |
| flip-single | "output video may be related to copyright restrictions" |

## Findings

1. **ByteDance's generation-time content filter blocks this source.** A real magazine
   cover carrying a recognizable celebrity photograph (and a real masthead) trips the
   "copyright restrictions" refusal on Seedance 2.0 Mini regardless of prompt wording —
   three differently-worded briefs all refused. This is a provider policy boundary, not a
   prompt or pipeline failure, and it gates any use of real editorial/brand/celebrity
   source material through this host.
2. **Image references + frame anchors are rejected on mini** ("Bad Request" at
   generation, after passing submit-time validation). Contrast: a *video* reference mixed
   with anchors was accepted and rendered in the batch-3 gloria cell. The mixed-input
   support matrix is per-reference-type; image_url + frame_images is not accepted.
3. The strategy gate's smooth profile worked as designed end-to-end (all four briefs
   gated, planned, and recorded with `grammar: smooth`); the failure happened past every
   layer this pipeline controls.

Per-cell terminal records in `<cell>/failed-job.json`. The known viable route for this
kind of content, already proven in this repo (Issues #70/#74), is a **parody/fictional
source** — an original cover in the same design language with no real masthead or
celebrity likeness.
