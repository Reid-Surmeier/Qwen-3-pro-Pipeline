# vibe-premiere-dis-rework-v001 — first 25 pages, single-donor-magazine rework

Owner scope change on issue #92 (2026-08-27): drop the multi-donor plan and run
the DIS transplant against **one magazine** — the Vibe premiere issue
(Sept 1993), Internet Archive mirror of the Google Books scan
`bub_gb_IigEAAAAMBAJ` — reworking its **first 25 pages** (leaves n0–n24).
Advertisement pages are refilled with photographs from **DIS Images**
(disimages.com, the DIS stock-image library; owner states rights from the
creator), each integrated into the existing ad's design language with the
brand replaced by DIS. Editorial pages carry DIS Data Issue content.

## Sources

- **Layout donor**: `scout/vibe-premiere/n{0..30}.jpg` — full-resolution
  (2500px) leaves from `https://archive.org/download/bub_gb_IigEAAAAMBAJ/page/n{N}.jpg`.
- **Art pool**: `dispool/` — the DIS Images library, crawled from the 22
  artist listing pages (244 photos); provenance per photo (title, artists,
  source page, file URL) in `dispool/manifest.json`.

## Content boundaries (unchanged from dis-data-issue-pages-v001)

- Outputs **replace** donor content, never reproduce it: running body text is
  greeked unreadable print texture; donor photographs, celebrity likenesses,
  advertiser brand marks, phone numbers, and barcodes are excluded by negative
  constraints in every brief.
- Exact copy is limited to short original DIS lines (masthead, DIS Data Issue
  titles and author names, invented taglines). No original ad copy and no
  article body text is transcribed or reproduced.
- The sole photographic content of every output is the assigned DIS Images
  photograph(s) (reference 2).

## Page plan (donor leaf → rework)

| # | Leaf | Donor page (design language taken) | Rework |
| --- | --- | --- | --- |
| 1 | n0 | Cover: b/w portrait, hot-pink display headline, black masthead | DIS Data Issue cover: DIS masthead in the donor masthead's heavy lowercase cut, headline TOO BIG TO SCALE, DIS portrait photo |
| 2 | n1 | Denim spread L: three figures holding monumental red banners into sky | DIS denim campaign L, DIS photo as the monument motif |
| 3 | n2 | Denim spread R: same motif continued | DIS denim campaign R, tagline slot goes to DIS |
| 4 | n3 | B/w romance clothing spread L: two figures embracing, sea light | DIS clothing campaign L, b/w DIS couple/figure photo |
| 5 | n4 | Clothing spread R: figure pair + serif wordmark + "American Beauty" script | DIS wordmark page, keeps the American Beauty line |
| 6 | n5 | Tech spread L: giant rotated letters + falling figure | DIS data-device page L, rotated display type |
| 7 | n6 | Tech spread R: floating product collage + angled copy | DIS data-device collage R |
| 8 | n7 | Sneaker page: product on white, thin technical copy band at top | DIS product-object page, technical dek |
| 9 | n8 | FEATURES contents: full-page tinted photo, feature list w/ folios | DIS Data Issue FEATURES: six pieces with invented folios |
| 10 | n9 | Moody b/w denim spread L: film-still figure | DIS campaign L, cinematic b/w DIS photo |
| 11 | n10 | Denim spread R: dark field, white script logo | DIS script logotype page R |
| 12 | n11 | Contents 2: b/w portrait left, FASHION/DEPARTMENTS/COLUMNS listings | DIS Data Issue departments: full scope of the issue's pieces |
| 13 | n12 | B/w underwear ad: torso, giant ghosted monogram | DIS monogram page, DIS body photo |
| 14 | n13 | Record-label page: circular stamp logo, typewriter manifesto lines | DIS Records page (Herndon/Grassegger Minnesang tie-in) |
| 15 | n14 | Identity ad: red bellhop inset + big statement type | DIS statement page: SOME CLOTHES SAY WHO YOU ARE rework |
| 16 | n15 | Streetwear page: group on freight train, huge outlined logotype | DIS group-photo page, outlined DIS logotype |
| 17 | n16 | Rap album page: xerox poster type blocks top/bottom, portrait middle | DIS release page, poster type blocks |
| 18 | n17 | Elegant album page: narrow lit figure, serif title stack | DIS portrait page, serif stack |
| 19 | n18 | Streetwear page: ornamental woodcut frame around street photo | DIS street photo in the ornamental frame |
| 20 | n19 | CONTRIBUTORS: text columns + inset portraits + yellow accent block | DIS Data Issue contributors page |
| 21 | n20 | Teaser page: single floating balloon object, tiny tagline | TOO BIG TO SCALE teaser: balloon-scale DIS object photo |
| 22 | n21 | Sneaker story spread L: b/w chain-link bench scene | DIS story-campaign L |
| 23 | n22 | Story spread R: typewriter narrative + product on fence ledge | DIS story-campaign R, greeked narrative |
| 24 | n23 | Boot page: giant color product + tude word list + circular seal | DIS product page, word list, DIS seal |
| 25 | n24 | MAIL: dense letter columns, red MAIL wordmark, inset cover thumb | DIS Data Issue MAIL page, greeked letters |

Spread pairs (n1+n2, n3+n4, n5+n6, n9+n10, n21+n22) are rendered as two 3:4
pages sharing one DIS campaign (same donor photo set and invented brand line)
so the pair still reads as one spread.

## Procedure

Same proven path as dis-data-issue-pages-v001: per page —
`LoadImage(donor leaf) + LoadImage(DIS art matte) → ImageBatch →
QwenImage3Render → SaveImage` on the live router; provider `openrouter`,
model `qwen/qwen-image-3-pro`, seed 260827, 2K, 3:4, count 1. Donor leaf =
reference 1 (layout authority, content excluded); DIS art letterboxed on a
neutral gray matte at donor dimensions = reference 2. Records, hashes, and
per-page verdicts in `outputs/`.

## Cost & allowance

25 jobs × (1 output @ $0.075 + 2 refs @ $0.003) = **$2.025 estimated**.
This exceeds the ADR 0003 default 10-output-per-issue allowance (1 output of
the superseded 5-page plan already spent): the 25-page count is the owner's
explicit written instruction on #92 and is recorded as such in the
pre-submission comment. Failed pages are presented with their failure notes
rather than silently retried — this run exists to collect owner corrections.
