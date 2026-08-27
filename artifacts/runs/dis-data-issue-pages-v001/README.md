# dis-data-issue-pages-v001 — first 5 pages of the DIS Data Issue transplant

First paid test of the interior-layout transplant: reproduce the DIS Magazine
*Data Issue* ("Too Big To Scale") as a mid-1990s print magazine, using archival
New York Magazine and Vibe pages as **layout donors** ("bones") and DIS article
imagery + titles as the content. Pure-qwen art-object pass: body text is
rendered as deliberately unreadable greeked print texture; only mastheads,
titles, authors, and short original dek lines are exact copy.

## Page plan

| Page | Piece | Donor bones | Donor source | Art reference |
| --- | --- | --- | --- | --- |
| p1-cover | Issue cover — "Too Big To Scale" | New York 1993-06-21 cover (curved two-line display headline) | Google Books `miYAAAAAMBAJ` | DIS Data Issue intro image (`dark-resized.jpg`) |
| p2-contents | Contents / FEATURES | Vibe Nov 1994 contents page (n10) | archive.org `bub_gb_dCwEAAAAMBAJ` | Rafaël Rozendaal, *Abstract Browsing* (`rr-2.png`) |
| p3-paglen | Trevor Paglen, *NSA-Tapped Fiber Optic Cable Landing Site* | Vibe Nov 1994 section opener "Alabama Burning" (n32) | archive.org `bub_gb_dCwEAAAAMBAJ` | Article image (`paglen-icon.jpg`) |
| p4-losse | Kate Losse, *Cults at Scale* | Vibe Nov 1994 START department page (n33) | archive.org `bub_gb_dCwEAAAAMBAJ` | Article image (`571-e1423083738257.jpg`) |
| p5-herndon | Holly Herndon & Hannes Grassegger, *Minnesang: Bits and Atoms* | Vibe Nov 1994 "IN THE MIX" collage page (n35) | archive.org `bub_gb_dCwEAAAAMBAJ` | Article banner (`holly-banner2.jpg`) |

Cover donor chosen deliberately: the donor's curved two-part display headline
carries "Too Big / To Scale", and its subject rhymes with Losse's *Cults at
Scale* inside the issue.

## Procedure (repeatable)

1. **Scout** (`scout/`): donor candidates downloaded from the corpus sources
   above; contact sheets built; donors selected by visual review (contact
   sheets retained).
2. **Prepare** (`inputs/`): donors normalized to lossless PNG, long edge 1800.
   Each art reference is letterboxed onto a neutral gray matte at exact donor
   dimensions so ComfyUI's `ImageBatch` cannot stretch it (the matte is
   declared packing material in every brief). Hashes in `inputs/manifest.json`.
3. **Brief** (`briefs/`): one Edit Brief per page, valid against
   `schemas/edit-brief.schema.json`, following the canonical prompt order
   (task → reference role → invariants → canvas → regions → exact copy →
   style → asset rules → negatives → quality gate). Donor = reference 1
   (layout authority, its own content excluded); art = reference 2 (sole
   photograph). Fixed seed 260827, output 2K, 3:4, count 1.
4. **Render**: ComfyUI graph `LoadImage(donor) + LoadImage(art) → ImageBatch →
   QwenImage3Render → SaveImage` against the live router. Provider
   `openrouter`, model `qwen/qwen-image-3-pro` (ADR 0003).
5. **Verify**: vision-first review of every output against donor + brief
   (layout bones taken? exact copy correct? art integrated? period finish?)
   before any mechanical check; verdicts posted to the tracking issue with
   embedded evidence at run time.

## Content boundaries

- Exact copy is limited to the DIS masthead, issue tagline, real article
  titles and author names, and short original dek/pull-quote lines written for
  this run. No article body text is reproduced anywhere; briefs force greeked,
  unreadable body texture.
- Donor pages contribute layout and typographic idiom only. Every brief's
  negative constraints exclude donor photographs, advertisements, brand marks,
  and mastheads from the output.

## Cost

5 jobs × (1 output @ $0.075 + 2 references @ $0.003) = **$0.405 estimated**.
5 outputs against the 10-output ADR 0003 allowance for the tracking issue;
retries stop at the allowance.
