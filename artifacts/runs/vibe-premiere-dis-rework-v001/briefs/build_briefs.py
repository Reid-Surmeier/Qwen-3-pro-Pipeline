"""Generate the 25 Edit Briefs for vibe-premiere-dis-rework-v001.

One brief per leaf, canonical block order (task -> reference role ->
invariants -> canvas -> regions -> exact copy -> style -> asset rules ->
negatives -> quality gate). Donor leaf = reference 1 (layout authority,
its own content excluded). DIS Images photo(s) on gray matte = reference 2.
"""

import json
import os

OUT = os.path.dirname(os.path.abspath(__file__))

COMMON_NEG = [
    "No legible paragraph-length body text anywhere: running text must be greeked, soft-blurred print texture that is clearly type but unreadable at full size.",
    "Do not reproduce the donor page's own photographs, faces, celebrities, advertiser brand marks, wordmarks, logos, phone numbers, addresses, or barcode digits; the donor supplies grid, type idiom, and period finish only.",
    "No VIBE wordmark and no real 1990s advertiser brand name or logo anywhere on the page.",
    "No watermark text, no gray letterbox bars carried in from the reference matte, no border artifacts.",
    "No modern flat-UI aesthetic, no smartphone-era design elements, no vector-clean gradients.",
]

COMMON_ASSET = [
    "Use the photograph from reference image 2 exactly once as the page's primary art; crop is allowed, distortion and mirroring are not.",
    "Ignore the flat gray matte surrounding the photograph in reference image 2; it is packing material, not content.",
    "Render the reference photograph clean, without the translucent 'disimages' watermark that overlays the source file.",
]

COMMON_INV = "Keep the 1990s newsstand finish: coated paper, halftone grain, slightly imperfect period type setting."

COMMON_QUALITY = [
    "At thumbnail size the page reads as an authentic printed page from a September 1993 American music magazine.",
    "Every exact-copy string is legible, spelled exactly as specified, and appears exactly once.",
    "The DIS photograph is clearly recognizable, undistorted, and integrated with period-correct print reproduction.",
]

P = {}

P["vp00"] = dict(
    objective="Rework this magazine's premiere-issue cover as the cover of DIS Magazine's print Data Issue: identical cover architecture — chunky black lowercase masthead partly behind the subject's head, hot-pink all-caps display line beneath it, small serif cover lines upper-left, black-and-white studio portrait subject — with all content replaced by DIS content.",
    reference_role="Reference image 1 is the layout authority for masthead scale and overlap, the pink display line, cover-line placement, portrait crop, and period print finish; none of its words, faces, or images may appear. Reference image 2 supplies the sole cover subject: a solemn dog wearing a black jacket, to be rendered as the black-and-white newsstand portrait.",
    invariants=[
        "Keep reference 1's cover architecture: lowercase masthead across the top with the subject's head overlapping it, one hot-pink condensed caps display line directly below, small white/serif cover lines at upper left, full-bleed monochrome portrait.",
        COMMON_INV,
    ],
    canvas=["Portrait magazine cover, 3:4, full bleed.",
            "The reference 2 subject becomes a tight black-and-white studio portrait filling the frame like the donor portrait."],
    regions=[
        ("masthead", "Replace the donor masthead with the word 'dis' in the same chunky black lowercase cut, same scale, the subject's head overlapping its middle letters.",
         ["Masthead band position and overlap behavior."]),
        ("pink display line", "Set 'TOO BIG TO SCALE' in the same hot-pink condensed all-caps, same baseline position under the masthead.",
         ["Color, weight, and single-line placement."]),
        ("cover lines upper-left", "Two small lines: 'Big data has its day' then 'by Marvin Jordan & Mike Pepi' in quiet serif.",
         ["Small scale and upper-left placement."]),
        ("portrait", "The reference 2 dog in black jacket, photographed as a solemn monochrome newsstand portrait, eyes to camera.",
         ["Portrait crop and tonal drama of the donor."]),
        ("barcode corner", "A small generic barcode box with no legible digits.", ["Lower-left placement."]),
    ],
    exact=[("masthead", "dis"), ("pink display line", "TOO BIG TO SCALE"),
           ("cover line 1", "Big data has its day"), ("cover line 2", "by Marvin Jordan & Mike Pepi")],
    style=["Black-and-white portrait with deep matte blacks; hot-pink and white type only; premiere-issue gravity."],
    neg_extra=["No human face on the cover.", "No 'BOW', 'WOW', or any donor headline word."],
)

P["vp01"] = dict(
    objective="Rework the left page of the opening denim advertisement spread: keep its vast open sky, monumental held-aloft object motif, and tiny brand chip at top left, but make it a DIS DENIM campaign built around the reference 2 photograph of figures scaling a white monolith.",
    reference_role="Reference image 1 is the layout authority: horizon height, sky field, monumental object scale, chip placement. Its red banners, figures, and brand chip may not appear. Reference image 2 supplies the campaign photograph: figures climbing a towering white monolith against sky.",
    invariants=[
        "Keep reference 1's composition: enormous sky, monument rising through the full page height, human figures tiny at its base, small brand chip top-left.",
        COMMON_INV,
    ],
    canvas=["Portrait page, 3:4, full bleed; this is the left half of a spread, so the motif may run off the right edge."],
    regions=[
        ("main field", "Integrate the reference 2 monolith-and-climbers as the monumental subject at the donor's banner scale, against the same wide sky.", ["Horizon height and monumental proportion."]),
        ("brand chip", "Small top-left chip: 'DIS DENIM' with the line 'scale loosely' beneath it.", ["Chip scale and position."]),
    ],
    exact=[("brand chip", "DIS DENIM"), ("brand chip line", "scale loosely")],
    style=["Sun-washed early-90s color advertising film; big empty sky; heroic wide-angle."],
)

P["vp02"] = dict(
    objective="Rework the right page of the same denim spread: the identical campaign continues — the monumental white monolith and climbing figures from reference 2 meet the ground plane, figures at the base — with no text at all.",
    reference_role="Reference image 1 is the layout authority: where the banners meet the ground, figure placement, horizon. Its content may not appear. Reference image 2 supplies the same campaign photograph as the left page.",
    invariants=[
        "Keep reference 1's grounded composition: the monument's base and small figures in the lower third, sky above.",
        COMMON_INV,
    ],
    canvas=["Portrait page, 3:4, full bleed; right half of the spread, motif continuing from the left edge."],
    regions=[
        ("main field", "The reference 2 monolith motif continued to the ground plane; no chip, no sticker, no barcode.", ["Ground line height."]),
    ],
    exact=[],
    style=["Identical film stock and grading to the left page; clean corners."],
)

P["vp03"] = dict(
    objective="Rework the left page of the black-and-white clothing spread: a full-bleed intimate embrace in soft sea light — using the reference 2 photograph of two figures embracing in translucent protective wrap, elevated to elegant monochrome fashion photography.",
    reference_role="Reference image 1 is the layout authority: full-bleed crop, embrace composition, sea-light tonality. Its models may not appear. Reference image 2 supplies the embrace: two figures wrapped in protective material, to be rendered as tender monochrome fashion imagery.",
    invariants=[
        "Keep reference 1's full-bleed two-figure embrace composition and its soft gray coastal light.",
        COMMON_INV,
    ],
    canvas=["Portrait page, 3:4, full bleed, no text."],
    regions=[
        ("full-bleed photograph", "The reference 2 embrace re-photographed as quiet black-and-white editorial: soft window-of-sea light, gentle grain.", ["Embrace framing and tonal softness."]),
    ],
    exact=[],
    style=["Fine-grain monochrome; romantic restraint; the protective wrap reads as couture fabric."],
)

P["vp04"] = dict(
    objective="Rework the right page of the clothing spread: monochrome beauty portrait, the small script line 'American Beauty', and the wide-tracked serif wordmark — now reading DIS — at the bottom.",
    reference_role="Reference image 1 is the layout authority: portrait placement, script-line position, wordmark scale and letterspacing. Its models and brand name may not appear. Reference image 2 supplies the portrait: a serene bare-shouldered beauty study to be rendered in monochrome.",
    invariants=[
        "Keep reference 1's structure: b/w portrait upper field, delicate script line at right, wide letterspaced serif wordmark across the lower margin.",
        COMMON_INV,
    ],
    canvas=["Portrait page, 3:4, full bleed photo with white lower margin band."],
    regions=[
        ("portrait", "The reference 2 beauty study in soft monochrome, eyes closed, sea light.", ["Crop and tonal register."]),
        ("script line", "'American Beauty' in small elegant script, same position as the donor's script line.", ["Scale and placement."]),
        ("wordmark", "'D I S' in wide-tracked serif capitals across the bottom margin at the donor wordmark's size.", ["Letterspacing rhythm and margin position."]),
    ],
    exact=[("script line", "American Beauty"), ("wordmark", "DIS")],
    style=["Quiet luxury monochrome; generous white space."],
)

P["vp05"] = dict(
    objective="Rework the left page of the electronics advertisement: keep its giant rotated red display letters, tilted subject, and repeated angled exclamation lines, but sell DIS data storage — the subject is the reference 2 photograph of a computer monitor displaying a cloud.",
    reference_role="Reference image 1 is the layout authority: rotated display type running the page height, tilted central subject, angled exclamation lines, small vertical brand name. Its letters, figure, and brand may not appear. Reference image 2 supplies the subject: a desktop monitor showing a blue sky cloud.",
    invariants=[
        "Keep reference 1's dynamic structure: monumental rotated red letters spanning the page, subject tilted across them, two angled exclamation lines, small vertical brand at the top edge.",
        COMMON_INV,
    ],
    canvas=["Portrait page, 3:4, white field."],
    regions=[
        ("giant rotated letters", "The word 'DATA' in the donor's giant condensed red caps, rotated the same way, cropped by the page edges.", ["Scale, rotation, and red."]),
        ("subject", "The reference 2 cloud-monitor tilted diagonally across the letters like the donor figure.", ["Diagonal energy."]),
        ("exclamation lines", "The line 'I CAN RECORD ON A CLOUD!' set twice at the donor's opposing angles in small bold caps.", ["Angled placement."]),
        ("vertical brand", "'DIS' small, vertical, at the top-left edge.", ["Edge position."]),
    ],
    exact=[("giant rotated letters", "DATA"), ("exclamation lines", "I CAN RECORD ON A CLOUD!"), ("vertical brand", "DIS")],
    style=["Hard red-and-black on white; photocopied punk-meets-corporate 1993 energy."],
)

P["vp06"] = dict(
    objective="Rework the right page of the electronics spread: keep its floating product-collage-on-white with an angled serif copy column, but the floating products are the reference 2 photograph's pile of obsolete mobile phones, scattered as if weightless.",
    reference_role="Reference image 1 is the layout authority: floating object arrangement, angled greeked copy column, small chip marks at bottom. Its products, copy, and logos may not appear. Reference image 2 supplies the objects: a heap of old phones to be exploded into individually floating devices.",
    invariants=[
        "Keep reference 1's weightless collage structure: objects drifting at angles around an angled column of small serif copy.",
        COMMON_INV,
    ],
    canvas=["Portrait page, 3:4, white field."],
    regions=[
        ("floating objects", "Individual phones from reference 2 drifting at donor-like angles across the page.", ["Weightless spacing."]),
        ("copy column", "An angled column of greeked serif copy, unreadable, ending in a small red arrow like period print ads.", ["Column angle and width."]),
        ("bottom chips", "Small 'DIS' box mark and the words 'THE DATA ISSUE' in tiny caps; no phone numbers.", ["Corner placement."]),
    ],
    exact=[("bottom chip", "DIS"), ("bottom line", "THE DATA ISSUE")],
    style=["Clean catalog white with drop shadows; 1993 consumer-electronics print finish."],
)

P["vp07"] = dict(
    objective="Rework the sneaker advertisement page as a DIS product page: keep the thin technical dek across the top and the giant heroic product photograph on white, but the product is the reference 2 purple lint roller, presented with full athletic-shoe seriousness.",
    reference_role="Reference image 1 is the layout authority: top dek band in red and black smallcaps, giant product angle and scale, tiny caption bottom-left, small mark at right. Its shoe, brand, and copy may not appear. Reference image 2 supplies the product: a purple-handled lint roller on white.",
    invariants=[
        "Keep reference 1's structure: multi-line technical dek across the top, monumental product filling the lower two-thirds, small caption and mark.",
        COMMON_INV,
    ],
    canvas=["Portrait page, 3:4, white field."],
    regions=[
        ("technical dek", "Top band reading 'IT PICKS UP EVERYTHING.' with the phrase \"THAT'S KIND OF TECHNICAL.\" as its red highlight, remaining dek words greeked.", ["Band position, red accent usage."]),
        ("product", "The reference 2 lint roller huge and heroic at the donor shoe's angle, crisp studio shadow.", ["Monumental scale on white."]),
        ("caption", "'THE DATA COLLECTOR' in tiny tracked caps bottom-left.", ["Tiny scale."]),
        ("mark", "Small 'dis' wordmark at the right edge where the donor logo sat.", ["Modest scale."]),
    ],
    exact=[("technical dek", "IT PICKS UP EVERYTHING."), ("technical dek highlight", "THAT'S KIND OF TECHNICAL."),
           ("caption", "THE DATA COLLECTOR"), ("mark", "dis")],
    style=["Athletic-catalog seriousness applied to an absurd object; hard studio light."],
)

P["vp08"] = dict(
    objective="Rework the FEATURES contents page: keep the full-page monochrome-tinted standing figure at right, the spaced 'F E A T U R E S' header, and the left column of numbered feature entries — now listing the DIS Data Issue's six pieces.",
    reference_role="Reference image 1 is the layout authority: header treatment, entry stack rhythm with large folio numerals, figure placement, single-color page cast. Its model and entries may not appear. Reference image 2 supplies the figure: a person in a bright blue full-body suit beside an orange cone, to be tinted into the page's monochrome cast.",
    invariants=[
        "Keep reference 1's structure: letterspaced header top-left, stacked entries with big folios down the left, full-height figure on the right, one unified color cast over the whole page.",
        COMMON_INV,
    ],
    canvas=["Portrait page, 3:4, full bleed, unified blue cast."],
    regions=[
        ("header", "'F E A T U R E S' letterspaced, with the small line 'PREMIERE DATA ISSUE SEPTEMBER 1993 VOLUME 1 NUMBER 1' beneath.", ["Header position."]),
        ("feature entries", "Six entries, each a large folio numeral, a bold title, and a byline, in the donor's stacked style, dek lines greeked: 50 LANDING SITES By Trevor Paglen · 64 CULTS AT SCALE By Kate Losse · 72 WHAT CAN AN ALGORITHM DO? By Josh Scannell · 80 METAPHORS OF BIG DATA By Sara M. Watson · 88 BITS AND ATOMS By Holly Herndon & Hannes Grassegger · 98 MACHINE VISION By Benjamin Bratton.", ["Folio scale and stack rhythm."]),
        ("figure", "The reference 2 blue-suited figure standing full height at right, tinted to the page cast.", ["Figure height and placement."]),
    ],
    exact=[("header", "F E A T U R E S"),
           ("issue line", "PREMIERE DATA ISSUE SEPTEMBER 1993 VOLUME 1 NUMBER 1"),
           ("entry 1", "50 LANDING SITES By Trevor Paglen"),
           ("entry 2", "64 CULTS AT SCALE By Kate Losse"),
           ("entry 3", "72 WHAT CAN AN ALGORITHM DO? By Josh Scannell"),
           ("entry 4", "80 METAPHORS OF BIG DATA By Sara M. Watson"),
           ("entry 5", "88 BITS AND ATOMS By Holly Herndon & Hannes Grassegger"),
           ("entry 6", "98 MACHINE VISION By Benjamin Bratton")],
    style=["Single-ink duotone page; editorial confidence of a premiere issue."],
)

P["vp09"] = dict(
    objective="Rework the left page of the moody monochrome denim spread: a near-black full-bleed film still — the reference 2 photograph of a face lit only by a glowing white card held in darkness.",
    reference_role="Reference image 1 is the layout authority: near-black field, low-key single-source lighting, thin vertical credit strip at the left edge. Its model may not appear. Reference image 2 supplies the image: a face lit by a glowing card in darkness.",
    invariants=[
        "Keep reference 1's cinematic darkness: one glowing light source, vast black field, tiny vertical strip of micro type at the left edge.",
        COMMON_INV,
    ],
    canvas=["Portrait page, 3:4, full bleed near-black."],
    regions=[
        ("full-bleed still", "The reference 2 lit face composed low in the frame like a film still, everything else falling to black.", ["Low-key balance."]),
        ("credit strip", "Thin vertical strip of greeked micro type at the left edge.", ["Edge placement."]),
    ],
    exact=[],
    style=["Grainy monochrome cinema; 1993 print blacks that hold detail."],
)

P["vp10"] = dict(
    objective="Rework the right page of the moody spread: dark field, the flowing white script logotype now reading DIS, and the small line 'For Humans & Machines' — over the reference 2 photograph of a hand holding a glowing card.",
    reference_role="Reference image 1 is the layout authority: dark field, script logotype scale and position, small bottom-left line. Its logotype and imagery may not appear. Reference image 2 supplies the background image: a hand holding a glowing white card in darkness.",
    invariants=[
        "Keep reference 1's structure: full-bleed dark image, large white script logotype right of center, single small sans line at lower left.",
        COMMON_INV,
    ],
    canvas=["Portrait page, 3:4, full bleed dark."],
    regions=[
        ("background", "The reference 2 hand-and-card image large and dark across the page.", ["Glow as the only light."]),
        ("script logotype", "'DIS' in the donor's flowing white script scale and position.", ["Script fluidity and scale."]),
        ("bottom line", "'For Humans & Machines' in small white sans at lower left.", ["Small scale."]),
    ],
    exact=[("script logotype", "DIS"), ("bottom line", "For Humans & Machines")],
    style=["Velvet blacks; the script logotype glows slightly like silkscreened ink."],
)

P["vp11"] = dict(
    objective="Rework the second contents page: black page, monochrome seated portrait at left, and the three colored column headers — now DATA, DEPARTMENTS, COLUMNS — listing the full scope of the Data Issue's pieces with folio numbers.",
    reference_role="Reference image 1 is the layout authority: black field, portrait placement, three-column list structure with small colored headers and white folio entries. Its model and entries may not appear. Reference image 2 supplies the portrait: a dramatic dark studio portrait to be rendered monochrome.",
    invariants=[
        "Keep reference 1's structure: b/w figure left half, three narrow list columns right half with colored section headers, tiny credits at bottom.",
        COMMON_INV,
    ],
    canvas=["Portrait page, 3:4, black field."],
    regions=[
        ("portrait", "The reference 2 portrait, moody monochrome, seated scale as the donor.", ["Left-half placement."]),
        ("column headers", "Three small headers in the donor's accent colors: 'DATA', 'DEPARTMENTS', 'COLUMNS'.", ["Header color pops."]),
        ("entries", "Short white folio entries under the headers, descriptions greeked: 56 LANDING SITES · 100 CULTS AT SCALE · 18 CONTRIBUTORS · 23 MAIL · 27 START · 106 GEAR · 140 PROPS.", ["Folio-first entry rhythm."]),
    ],
    exact=[("header 1", "DATA"), ("header 2", "DEPARTMENTS"), ("header 3", "COLUMNS"),
           ("entry a", "56 LANDING SITES"), ("entry b", "100 CULTS AT SCALE"),
           ("entry c", "18 CONTRIBUTORS"), ("entry d", "23 MAIL"), ("entry e", "27 START"),
           ("entry f", "106 GEAR"), ("entry g", "140 PROPS")],
    style=["Ink-dense black page; small warm accent colors; premiere-issue confidence."],
)

P["vp12"] = dict(
    objective="Rework the monochrome underwear-brand page as DIS: keep the warm-gray field, the sculptural central figure, the giant ghosted monogram behind it, and the small quiet caption — the figure is the reference 2 photorealistic 3D model head.",
    reference_role="Reference image 1 is the layout authority: ghost monogram scale, figure placement, caption position, warm monochrome. Its model, monogram, and brand may not appear. Reference image 2 supplies the subject: a computer-generated human head on gray, to be treated as classical sculpture.",
    invariants=[
        "Keep reference 1's structure: giant ghosted letters behind a centered sculptural subject, small serif caption at center, warm gray monochrome.",
        COMMON_INV,
    ],
    canvas=["Portrait page, 3:4, warm gray monochrome."],
    regions=[
        ("ghost monogram", "Giant ghosted 'DIS' letters behind the subject at the donor monogram's scale and transparency.", ["Ghost transparency."]),
        ("subject", "The reference 2 3D head as a noble bust, lit like a classical study, uncanny smoothness kept.", ["Central sculptural presence."]),
        ("caption", "'dis jeans' in small quiet serif at the donor caption position.", ["Modesty of scale."]),
    ],
    exact=[("ghost monogram", "DIS"), ("caption", "dis jeans")],
    style=["Warm-gray fashion monochrome; uncanny digital skin rendered as if silver-print."],
)

P["vp13"] = dict(
    objective="Rework the record-label page as DIS RECORDS: keep the split composition — dark photograph left, black label panel right with a huge circular stamp and typewriter statement lines — announcing the Herndon & Grassegger single.",
    reference_role="Reference image 1 is the layout authority: split structure, circular stamp scale, typewriter type idiom, xerox texture. Its logo, band names, and copy may not appear. Reference image 2 supplies the photograph: a man at a typewriter in darkness.",
    invariants=[
        "Keep reference 1's structure: photographic left half, dense black right panel with a page-filling circular stamp and stacked typewriter lines, gritty photocopy texture.",
        COMMON_INV,
    ],
    canvas=["Portrait page, 3:4, black-and-white xerox finish."],
    regions=[
        ("photograph", "The reference 2 typewriter figure, harsh single light, heavy grain.", ["Left-half darkness."]),
        ("circular stamp", "Ring text 'DIS RECORDS' around an abstract data-glyph center, at the donor stamp's scale.", ["Stamp dominance."]),
        ("typewriter lines", "White typewriter lines: 'DIS Records is a new label.' / 'We press data to wax.' with remaining lines greeked.", ["Stacked line rhythm."]),
        ("release block", "Bottom credits: 'HOLLY HERNDON & HANNES GRASSEGGER' / 'MINNESANG: BITS AND ATOMS' / 'the new single'.", ["Bottom stack order."]),
    ],
    exact=[("circular stamp", "DIS RECORDS"), ("typewriter line 1", "DIS Records is a new label."),
           ("typewriter line 2", "We press data to wax."),
           ("release artists", "HOLLY HERNDON & HANNES GRASSEGGER"),
           ("release title", "MINNESANG: BITS AND ATOMS"), ("release tag", "the new single")],
    style=["Photocopied street-flyer finish; ink bleed; no gloss."],
)

P["vp14"] = dict(
    objective="Rework the identity-statement clothing page as a DIS IMAGES house advertisement: keep the white field, the small top-left inset photograph, the large two-part statement, the lower-left photograph, and the bottom logo chip.",
    reference_role="Reference image 1 is the layout authority: inset scale, statement typography and split emphasis, second photo placement, chip block. Its models, statements, and brand may not appear. Reference image 2 is a two-photo sheet: the TOP photo (a formal server presenting a jar) goes to the small top-left inset; the BOTTOM photo (a woman dining alone at a table) goes to the lower-left photo slot.",
    invariants=[
        "Keep reference 1's structure: small formal inset top-left, statement type dominating the upper right, larger casual photograph lower-left, logo chip and small block bottom-right.",
        COMMON_INV,
    ],
    canvas=["Portrait page, 3:4, white field."],
    regions=[
        ("top inset", "Reference 2's top photo (formal server with jar) as the small rectangular inset.", ["Inset scale."]),
        ("statement", "'SOME IMAGES SAY WHO YOU ARE.' large, then 'OTHERS SAY WHO YOU COULD BE.' with the donor's mixed-weight emphasis.", ["Two-part statement hierarchy."]),
        ("lower photo", "Reference 2's bottom photo (woman dining alone) larger at lower-left.", ["Photo proportion."]),
        ("chip block", "'DIS IMAGES' oval chip with 'New Stock Options' beneath, address lines greeked.", ["Chip position bottom."]),
    ],
    exact=[("statement 1", "SOME IMAGES SAY WHO YOU ARE."), ("statement 2", "OTHERS SAY WHO YOU COULD BE."),
           ("chip", "DIS IMAGES"), ("chip line", "New Stock Options")],
    style=["Plain-spoken 90s identity advertising; generous white space."],
    asset_override=[
        "Reference image 2 contains two photographs stacked on the gray matte: use the top one for the inset and the bottom one for the lower photo slot; use each exactly once.",
        "Ignore the flat gray matte surrounding and separating the photographs; it is packing material, not content.",
        "Render both photographs clean, without the translucent 'disimages' watermark that overlays the source files.",
    ],
)

P["vp15"] = dict(
    objective="Rework the streetwear page: keep the huge white outlined logotype across the top — now DIS — over a black-and-white group photograph, with the side statement now reading 'STOCK FOR BOTH SIDES OF THE FEED'.",
    reference_role="Reference image 1 is the layout authority: outlined logotype scale, b/w group placement, side statement stack, bottom strip. Its logotype, models, and copy may not appear. Reference image 2 supplies the group: seven figures in patterned and black modest wear standing in formation, to be rendered monochrome.",
    invariants=[
        "Keep reference 1's structure: page-wide outlined display logotype at top, gritty monochrome group photograph beneath, stacked white statement at left, thin info strip at bottom.",
        COMMON_INV,
    ],
    canvas=["Portrait page, 3:4, black-and-white."],
    regions=[
        ("logotype", "'DIS' in the donor's huge white-outlined display style spanning the page top.", ["Outline weight and span."]),
        ("group photograph", "The reference 2 seven-figure group, monochrome, gritty documentary grain, posed like a crew.", ["Group formation scale."]),
        ("statement", "'STOCK FOR BOTH SIDES OF THE FEED' stacked in white caps at left.", ["Stacked alignment."]),
        ("bottom strip", "Thin strip of greeked micro type.", ["Strip height."]),
    ],
    exact=[("logotype", "DIS"), ("statement", "STOCK FOR BOTH SIDES OF THE FEED")],
    style=["High-contrast street monochrome; outlined display type with halftone edges."],
)

P["vp16"] = dict(
    objective="Rework the xerox rap-promo page as a DIS release poster: keep the top banner block of huge condensed caps, the gritty halftone portrait center, and the stacked slab announcement lines at bottom.",
    reference_role="Reference image 1 is the layout authority: banner block, portrait window, slab stack, photocopy texture. Its artist, name, and label may not appear. Reference image 2 supplies the portrait: a woman taking a selfie in front of protest banners, to be rendered in gritty b/w halftone.",
    invariants=[
        "Keep reference 1's structure: full-width reversed banner top, halftone portrait middle, three stacked reversed slab lines bottom.",
        COMMON_INV,
    ],
    canvas=["Portrait page, 3:4, black-and-white xerox."],
    regions=[
        ("top banner", "'DIS PRESENTS' in huge condensed reversed caps.", ["Banner span."]),
        ("portrait", "The reference 2 banner-selfie scene in coarse halftone monochrome.", ["Street-poster grain."]),
        ("slab lines", "Three reversed slabs: 'THE DATA SINGLE: \"TOO BIG\"' / 'THE DATA ALBUM: \"TO SCALE\"' / 'PRODUCED BY: DIS'.", ["Slab stack rhythm."]),
    ],
    exact=[("top banner", "DIS PRESENTS"),
           ("slab 1", "THE DATA SINGLE: \"TOO BIG\""),
           ("slab 2", "THE DATA ALBUM: \"TO SCALE\""),
           ("slab 3", "PRODUCED BY: DIS")],
    style=["Photocopied hip-hop promo idiom; crushed blacks; street-poster urgency."],
)

P["vp17"] = dict(
    objective="Rework the elegant record-release page: keep the black field with a narrow lit vertical window holding the subject and the serif title stack beneath — announcing Fatima Al Qadiri's 'Tissue Stock' — the subject is the reference 2 photograph of an ornate tissue box lit like a jewel.",
    reference_role="Reference image 1 is the layout authority: narrow lit window proportion, serif stack hierarchy, black field. Its artist and titles may not appear. Reference image 2 supplies the subject: a decorated tissue box on dark ground, to be presented with full diva elegance.",
    invariants=[
        "Keep reference 1's structure: tall narrow illuminated window centered high, serif name and title stack below, small label mark at bottom.",
        COMMON_INV,
    ],
    canvas=["Portrait page, 3:4, black field."],
    regions=[
        ("lit window", "The reference 2 tissue box glowing in the tall narrow window like a spotlit figure.", ["Window proportion."]),
        ("title stack", "'FATIMA AL QADIRI' in letterspaced serif caps, then 'Tissue Stock' in italic serif, then 'Featuring \"Fine\" and \"Soft\"' small.", ["Stack hierarchy."]),
        ("label mark", "Small 'DIS RECORDS' mark at bottom.", ["Modest scale."]),
    ],
    exact=[("artist", "FATIMA AL QADIRI"), ("title", "Tissue Stock"),
           ("featuring line", "Featuring \"Fine\" and \"Soft\""), ("label mark", "DIS RECORDS")],
    style=["Quiet-storm elegance; velvet black; a consumer object granted celebrity light."],
)

P["vp18"] = dict(
    objective="Rework the ornament-framed streetwear page: keep the dense black woodcut ornamental border and central photo window — the window now holds the reference 2 street photograph — with the script logotype DIS below and the itinerary line replaced.",
    reference_role="Reference image 1 is the layout authority: ornamental border idiom, window proportion, script logotype position, bottom itinerary line. Its ornament may be redrawn in the same idiom but its photo, logotype, and place names may not appear. Reference image 2 supplies the window photograph: a figure wading a flooded city street.",
    invariants=[
        "Keep reference 1's structure: hand-cut ornamental border framing a b/w street photograph, script logotype centered below the window, small itinerary line at bottom.",
        COMMON_INV,
    ],
    canvas=["Portrait page, 3:4, cream field."],
    regions=[
        ("ornamental border", "Dense black woodcut ornament in the donor's folk idiom, freshly drawn.", ["Border density."]),
        ("photo window", "The reference 2 flooded-street figure in monochrome documentary grain.", ["Window crop."]),
        ("script logotype", "'DIS' in hand-drawn script with star flourishes.", ["Central placement."]),
        ("itinerary line", "'BERLIN · NEW YORK · THE CLOUD' in small hand-lettered caps.", ["Bottom line."]),
    ],
    exact=[("script logotype", "DIS"), ("itinerary line", "BERLIN · NEW YORK · THE CLOUD")],
    style=["Hand-printed folk-punk streetwear idiom; uneven ink coverage."],
)

P["vp19"] = dict(
    objective="Rework the CONTRIBUTORS page: keep the tall portrait at left, the two text columns under the CONTRIBUTORS header with bold name lead-ins, and the colorful music-rail down the right edge — all refilled with Data Issue contributors and a DIS RECORDS rail.",
    reference_role="Reference image 1 is the layout authority: portrait slot, column measure, bold-lead-in convention, right-rail structure with big lowercase letters. Its people, names, and rail content may not appear. Reference image 2 supplies the portrait: a figure in a white wig holding a white rabbit against blue.",
    invariants=[
        "Keep reference 1's structure: tall photo left, 'CONTRIBUTORS' header, two justified columns with bold name lead-ins, colorful vertical rail at right with stacked lowercase display letters.",
        COMMON_INV,
    ],
    canvas=["Portrait page, 3:4, white field with colorful right rail."],
    regions=[
        ("left portrait", "The reference 2 wig-and-rabbit portrait, tall crop.", ["Slot proportion."]),
        ("header", "'CONTRIBUTORS' in the donor's tracked caps.", ["Header weight."]),
        ("columns", "Bold lead-in names 'Trevor Paglen', 'Kate Losse', 'Sara M. Watson', 'Josh Scannell' each opening a greeked bio paragraph.", ["Lead-in convention; all bios greeked."]),
        ("right rail", "Stacked big lowercase 'dis' letters with the lines 'the choice of the new data generation' and 'featuring the hit \"GIMME MY DATA\"', small portrait strip greeked.", ["Rail color energy."]),
    ],
    exact=[("header", "CONTRIBUTORS"), ("lead-in 1", "Trevor Paglen"), ("lead-in 2", "Kate Losse"),
           ("lead-in 3", "Sara M. Watson"), ("lead-in 4", "Josh Scannell"),
           ("rail letters", "dis"), ("rail line", "the choice of the new data generation"),
           ("rail hit line", "featuring the hit \"GIMME MY DATA\"")],
    style=["Editorial front-of-book density with one loud color rail."],
)

P["vp20"] = dict(
    objective="Rework the album-teaser page: keep the deep purple gradient field with one small floating object on a string and the tiny lowercase tagline — the object is the reference 2 sculpture of a hand releasing a rising green arrow.",
    reference_role="Reference image 1 is the layout authority: gradient field, floating-object scale and position, tagline position, tiny corner mark. Its balloon and marks may not appear. Reference image 2 supplies the object: a hand holding a curving green growth arrow.",
    invariants=[
        "Keep reference 1's structure: vast gradient emptiness, one small centered floating object trailing a thin string, whisper-small tagline at lower left.",
        COMMON_INV,
    ],
    canvas=["Portrait page, 3:4, deep purple-blue gradient."],
    regions=[
        ("floating object", "The reference 2 hand-and-arrow floating at the donor balloon's exact scale, a thin string trailing down.", ["Smallness in emptiness."]),
        ("tagline", "'it might scale up' in tiny lowercase at lower left.", ["Whisper scale."]),
        ("corner mark", "Tiny 'DIS' mark at lower right.", ["Tiny scale."]),
    ],
    exact=[("tagline", "it might scale up"), ("corner mark", "DIS")],
    style=["Mysterious teaser minimalism; airbrushed 90s gradient."],
)

P["vp21"] = dict(
    objective="Rework the left page of the sneaker story spread: a full-bleed black-and-white scene photographed through chain-link fence — the scene is the reference 2 photograph of a standing woman directing a seated intern who works on a laptop in a dog bed.",
    reference_role="Reference image 1 is the layout authority: through-the-fence framing, documentary monochrome, bottom caption strip. Its people may not appear. Reference image 2 supplies the scene, to be re-photographed as tender urban documentary.",
    invariants=[
        "Keep reference 1's structure: chain-link diamonds softly out of focus in the foreground, intimate two-figure scene behind, thin caption strip at bottom.",
        COMMON_INV,
    ],
    canvas=["Portrait page, 3:4, full bleed monochrome."],
    regions=[
        ("scene", "The reference 2 office-care scene rendered as b/w documentary seen through fence, soft afternoon light.", ["Fence-foreground depth."]),
        ("caption strip", "Thin greeked micro-type strip at bottom.", ["Strip height."]),
    ],
    exact=[],
    style=["Humanist 90s documentary monochrome; honest grain."],
)

P["vp22"] = dict(
    objective="Rework the right page of the story spread: keep the typewriter narrative block over fence texture and the humble product resting on the ledge — the product is the reference 2 photograph of hands with a roll of gaffer tape — closing with the DIS classic line.",
    reference_role="Reference image 1 is the layout authority: narrative block position, fence texture, product-on-ledge placement, closing line and chip. Its story, shoes, and brand may not appear. Reference image 2 supplies the product: hands holding a gray gaffer tape roll.",
    invariants=[
        "Keep reference 1's structure: typewriter story block upper area over pale fence texture, product resting on the ledge below, closing line and small box mark.",
        COMMON_INV,
    ],
    canvas=["Portrait page, 3:4, pale monochrome."],
    regions=[
        ("story block", "Greeked typewriter lines with one legible closing sentence: 'SHE WOULDN'T GIVE UP HER STOCK IMAGES FOR ANYTHING.'", ["Typewriter idiom; only that sentence legible."]),
        ("product", "The reference 2 gaffer tape roll resting on the fence ledge like a proud product.", ["Humble-product staging."]),
        ("closing chip", "'DIS CLASSIC. STOCK NEVER GETS OLD.' with a small 'DIS' box mark.", ["Closing position."]),
    ],
    exact=[("story closing", "SHE WOULDN'T GIVE UP HER STOCK IMAGES FOR ANYTHING."),
           ("closing line", "DIS CLASSIC. STOCK NEVER GETS OLD."), ("box mark", "DIS")],
    style=["Pale documentary grays; typewriter sincerity."],
)

P["vp23"] = dict(
    objective="Rework the boot advertisement page as a DIS product page: keep the giant warm-toned product filling the right, the red staccato word list top-right, small product studies top-left, and the circular seal — the product is the reference 2 ornamental red tissue box at heroic scale.",
    reference_role="Reference image 1 is the layout authority: heroic product scale, word-list block, small-studies corner, circular seal position. Its boots, words, and seal may not appear. Reference image 2 supplies the product: a red ornamented tissue box, to be rendered enormous with rich color.",
    invariants=[
        "Keep reference 1's structure: one enormous product dominating the page, staccato word list in red at top-right, two small monochrome product studies top-left, circular seal lower-right, thin bottom line.",
        COMMON_INV,
    ],
    canvas=["Portrait page, 3:4, warm white field."],
    regions=[
        ("header and list", "'Boxes and Tissues' small red header, then the staccato list 'Data.' 'Styles.' 'Scale.' 'Tude.' stacked in red.", ["Staccato stack."]),
        ("giant product", "The reference 2 red tissue box at the donor boot's heroic scale and warmth.", ["Monumental warmth."]),
        ("small studies", "Two small monochrome studies of the same box, top-left.", ["Corner modesty."]),
        ("seal", "Circular seal reading 'VERIFIED IMAGES · DIS' in ring text.", ["Seal position."]),
    ],
    exact=[("header", "Boxes and Tissues"), ("list word 1", "Data."), ("list word 2", "Styles."),
           ("list word 3", "Scale."), ("list word 4", "Tude."), ("seal", "VERIFIED IMAGES · DIS")],
    style=["Rich warm product color against clean white; earnest catalog voice."],
)

P["vp24"] = dict(
    objective="Rework the MAIL letters page: keep the red MAIL wordmark, the dense multi-column justified letter columns (all greeked), the small magazine-cover thumbnail inset upper-left — a tiny echo of this issue's DIS cover — and a small monochrome photograph at lower right from reference 2.",
    reference_role="Reference image 1 is the layout authority: wordmark position, column grid, inset placement, lower photo slot. Its text and images may not appear. Reference image 2 supplies the lower photograph: a sculptural black plastic bag on black.",
    invariants=[
        "Keep reference 1's structure: red display wordmark upper right area, four dense justified columns, small cover thumbnail upper-left, small photo lower-right.",
        COMMON_INV,
    ],
    canvas=["Portrait page, 3:4, white field."],
    regions=[
        ("wordmark", "'MAIL' in the donor's red display caps.", ["Wordmark position."]),
        ("letter columns", "Dense justified columns entirely greeked, with greeked bold sign-offs.", ["Column texture."]),
        ("cover thumbnail", "A tiny magazine-cover inset: black-and-white portrait with a pink display line and small 'dis' masthead, unreadable at this size.", ["Thumbnail scale."]),
        ("lower photograph", "The reference 2 black-bag still life, small, monochrome.", ["Lower-right slot."]),
    ],
    exact=[("wordmark", "MAIL")],
    style=["Front-of-book ink density; red accent against gray text."],
)


def build(page: str, spec: dict) -> dict:
    brief = {
        "provider": "openrouter",
        "model": "qwen/qwen-image-3-pro",
        "objective": spec["objective"],
        "reference_role": spec["reference_role"],
        "preservation_invariants": spec["invariants"],
        "canvas": spec["canvas"],
        "regions": [
            {"name": n, "change": c, "preserve": p} for (n, c, p) in spec["regions"]
        ],
        "exact_copy": [{"region": r, "text": t} for (r, t) in spec["exact"]],
        "style": spec["style"],
        "asset_rules": spec.get("asset_override", COMMON_ASSET),
        "negative_constraints": COMMON_NEG + spec.get("neg_extra", []),
        "quality_checks": COMMON_QUALITY,
        "output": {"resolution": "2K", "aspect_ratio": "3:4", "count": 1, "seed": 260827},
    }
    return brief


def main() -> None:
    for page, spec in P.items():
        path = os.path.join(OUT, f"{page}.json")
        json.dump(build(page, spec), open(path, "w"), indent=1, ensure_ascii=False)
        print(page, "written")


if __name__ == "__main__":
    main()
