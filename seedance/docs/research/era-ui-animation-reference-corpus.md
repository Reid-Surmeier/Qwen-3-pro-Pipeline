# Era UI Animation Reference Corpus (1997–2005 2D era)

Research corpus grounding the icon-animation pipeline in how UI elements actually animated in
shipped games of the Ragnarok Online generation (late-90s / early-2000s 2D MMOs and JRPGs, plus
the 16-bit console lineage they inherited). Compiled 2026-08-27 from primary/high-trust web
sources. **[OBSERVED]** = stated by a cited source or read directly from source code / file-format
docs. **[INFERENCE]** = period-typical behavior reconstructed from footage/community knowledge,
not pinned to a single citable sentence.

One sourcing note: The Cutting Room Floor's Ragnarok Online page was fetched but returned
non-article content (apparent prompt-injection text rather than the real wiki page); nothing from
TCRF is used in this document.

---

## 1. Reference-video / sprite-sheet corpus

### 1.1 Ragnarok Online (Gravity, kRO 2002) — client UI
- **Links:**
  - Sprite/animation format docs: [SPR.MD](https://github.com/Duckwhale/RagnarokFileFormats/blob/master/SPR.MD) and [ACT.MD](https://github.com/Duckwhale/RagnarokFileFormats/blob/master/ACT.MD) (rdw-archive/RagnarokFileFormats); [Ragnarok Research Lab SPR spec](https://ragnarokresearchlab.github.io/file-formats/spr/)
  - UI behavior: [iRO Wiki — Skills](https://irowiki.org/wiki/Skills) (cast gauge, cooldown display)
  - Sprite sheets: [The Spriters Resource — Ragnarok Online](https://www.spriters-resource.com/pc_computer/ragnarokonline/), incl. the **Cursors** sheet ([asset 127416](https://www.spriters-resource.com/pc_computer/ragnarokonline/asset/127416/))
  - Period footage: [“Ragnarök Online (2002)” playlist](https://www.youtube.com/playlist?list=PLcvhbdowgHFh2weG3xTCo0WFCwtkQj-tv); [Nostalgia Trip Back Into Ragnarok Online](https://www.youtube.com/watch?v=PG_i_dBiT8o) — watch any town/field segment in the first minutes for: window open/close, hotbar use, cast bar, item pickup. (Timestamps not individually verified; UI is on screen essentially continuously.)
- **Resolution:** default 640×480 windowed client (also 800×600); classic clients pick from fixed 4:3 modes ([WarpPortal support](https://support.warpportal.com/kb/a837/changing-resolution.aspx)).
- **What animates, frame-wise:**
  - **[OBSERVED]** All sprite animation (including the mouse cursor, emotes, status-effect
    overlays) is ACT/SPR driven; ACT frame delays are stored **in units of 25 ms** (delay 4 =
    100 ms) ([ACT.MD](https://github.com/Duckwhale/RagnarokFileFormats/blob/master/ACT.MD)).
    This is the client's native animation quantum — a 2002-authentic loop is N frames × (k×25 ms).
  - **[OBSERVED]** The **mouse cursor is animated** (multi-frame ACT loop; idle sparkle, click,
    hourglass-style loading rotation) — see the Spriters Resource Cursors sheet and the many
    ripped animated `.ani` conversions ([rAthena cursors category](https://rathena.org/board/files/category/43-cursors/),
    [DeviantArt rip](https://www.deviantart.com/laicure/art/Ragnarok-Online-Animated-Cursors-844121314)).
  - **[OBSERVED]** **Cast time** is shown as a **green progress gauge above the character's
    head** that fills left→right; during cast the character is locked
    ([iRO Wiki Skills](https://irowiki.org/wiki/Skills)).
  - **[OBSERVED]** **Cooldown/re-use delay has no sweep animation** — “no visible indication of
    Cooldown except the grayed out skill icon … in the Hotkey bar”
    ([iRO Wiki Skills](https://irowiki.org/wiki/Skills)). I.e., the skill icon's only state change
    is a palette/brightness swap (normal ↔ grayed), not a radial wipe.
  - **[INFERENCE from footage]** Windows (inventory, skill tree, status) **pop open instantly**
    — no tween, no fade. Item icons in inventory and the hotbar are **fully static** 24×24 BMPs.
    Item pickup shows the item cell appear instantly plus a chat-log line; the animated feedback
    lives in the world (sprite effects), not in the UI icon.
  - **[INFERENCE]** Guild emblems in classic clients are static 24×24 BMP images; animated
    emblems are a much later/renewal-era or private-server feature.

### 1.2 Diablo II (Blizzard North, 2000) — inventory/HUD
- **Links:** [Diablo II (2000) — Longplay 4K60](https://www.youtube.com/watch?v=U42cORD_VTs)
  (inventory/belt UI visible whenever the player loots — early Act 1, first ~20 min, has repeated
  inventory openings); [Game UI Database — Diablo II](https://www.gameuidatabase.com/gameData.php?id=804);
  [Phrozen Keep KB — inventory graphics](https://d2mods.info/forum/kb/viewarticle?a=451).
- **Resolution:** hardcoded 640×480 (later 800×600 in LoD) ([WSGF](https://www.wsgf.org/dr/diablo-ii)).
- **What animates:** **[OBSERVED]** inventory grid cells are **28×28 px** squares and all item
  inventory graphics align to 28-px multiples ([Phrozen Keep KB](https://d2mods.info/forum/kb/viewarticle?a=451)).
  Item icons in inventory are static DC6 images. **[INFERENCE from footage]** The animation
  budget goes to the **health/mana globes** (liquid level drains/slops), button press states
  (down-state art swap), and the world-space item-drop flip — never to the item icon itself.
  Skill icons on the right-click selector are static; the selector swaps icon art instantly.

### 1.3 Ultima Online (Origin, 1997) — gump UI
- **Links:** [uo.com — Classic Client paperdoll](https://uo.com/wiki/ultima-online-wiki/technical/classic-client-user-guide/the-classic-client-paperdoll/); [Wikipedia](https://en.wikipedia.org/wiki/Ultima_Online).
- **Resolution:** classic client game window 640×480-class fixed 4:3 modes.
- **What animates:** **[INFERENCE from docs/footage]** Essentially nothing in the UI. Gumps
  (windows), the paperdoll, spell icons, and container item art are all **static bitmaps**;
  feedback is instant art swap and text. This is the strongest “static UI” pole of the corpus.

### 1.4 Tibia (CipSoft, 1997; v7.x era ~2002)
- **Links:** [Tibia manual — Interface](https://www.tibia.com/gameguides/?subtopic=manual&section=interface); [TibiaWiki — Inventory](https://tibia.fandom.com/wiki/Inventory).
- **Facts:** **[OBSERVED]** world sprites are 32×32 single-frame tiles compiled into `Tibia.spr`;
  the inventory is a fixed slot panel; health (red) and mana (blue) are plain fill bars
  ([manual](https://www.tibia.com/gameguides/?subtopic=manual&section=interface)). The manual
  describes no UI animation at all. **[INFERENCE]** Item and skill icons are static; the only
  “moving” UI elements are bar fills and condition icons appearing/disappearing.

### 1.5 MapleStory (Wizet, kMS 2003)
- **Links:** [Wikipedia](https://en.wikipedia.org/wiki/MapleStory) (2003 release);
  800×600 default client resolution ([RaGEZONE thread on 800×600](https://forum.ragezone.com/threads/do-people-still-play-maplestory-in-800x600-resolution.1203339/));
  sheets: [The Spriters Resource — MapleStory](https://www.spriters-resource.com/pc_computer/maplestory/);
  old-version footage: [MapleStory — Then VS Now](https://www.youtube.com/watch?v=RsraN1qsaG4)
  (side-by-side old client UI), [MapleStory Nostalgia playlist](https://www.youtube.com/playlist?list=PLBrJXQ1KEwznNmOl1bFH2sUHAwTT4ujQ3).
- **What animates:** **[INFERENCE from footage/WZ data]** UI windows pop instantly; **skill and
  item icons in the hotbar are static** (~32×32 `iconRaw` bitmaps — size approximate, not pinned
  to a primary citation); on use, the icon briefly darkens/greys for its delay. Buff icons docked
  top-right are static bitmaps that **blink on/off in their final seconds** before expiry (simple
  visibility toggle, ~2 Hz). Animated feedback (multi-frame skill effects) plays **on the
  character in the world**, not on the icon.

### 1.6 Final Fantasy VI (Square, SNES 1994) — menus & save point
- **Links:** [SNES Longplay [216] Final Fantasy VI Part 1 (World of Longplays)](https://www.youtube.com/watch?v=iGNskqYu2_0)
  — menus opened within the first minutes after gaining control; save-point rooms appear in the
  Narshe caves segment early in Part 1; sheets: [Spriters Resource — FF6](https://www.spriters-resource.com/snes/ff6/)
  (menu/cursor and object sheets; sparkle object listed in the
  [FF6 object sprite category](https://finalfantasy.fandom.com/wiki/Category:Final_Fantasy_VI_SNES_Object_Sprite_Images)).
- **Resolution:** SNES 256×224 @ 60 Hz NTSC ([nesdev forum](https://forums.nesdev.org/viewtopic.php?t=10141)).
- **What animates:** **[INFERENCE from footage + sheets]** The menu **hand cursor is a static
  sprite** — it moves between slots instantly, it does not cycle frames. Menu window backgrounds
  are static gradients; text prints character-by-character. The **save point** is a field object
  of orbiting/twinkling sparkles — a short loop of small sprites cycling bright/dim (2–4 unique
  frames per sparkle, each held multiple 60 Hz frames), the classic “shimmer = palette-band
  alternation held ~100–250 ms” idiom. Gauges (ATB in battle) are plain 1-px-step fills.

### 1.7 Chrono Trigger (Square, SNES 1995) — menus
- **Links:** [Spriters Resource — Chrono Trigger](https://www.spriters-resource.com/snes/chronotrigger/);
  same Square hand-cursor lineage as FF6 ([Final Fantasy Wiki — Cursor](https://finalfantasy.fandom.com/wiki/Cursor)).
- **What animates:** **[INFERENCE]** Same pattern as FF6: static hand cursor, static item/tech
  icons; the only in-menu motion is text print and gauge fill. Confirms the Square-menu default:
  **icons never animate; selection is communicated by cursor position alone.**

### 1.8 Pokémon Red/Blue (Game Freak, GB 1996/98) — text-box ▼ and menu cursor
- **Links:** [pret/pokered disassembly](https://github.com/pret/pokered) —
  `home/window.asm` (`HandleDownArrowBlinkTiming`, `PlaceMenuCursor`), `home/text.asm`
  (down-arrow placement at tile coord 18,16).
- **Resolution:** Game Boy 160×144.
- **What animates (read from source):** **[OBSERVED]**
  - The waiting-for-input **▼ arrow is a single 8×8 text tile toggled between '▼' and blank**
    by a two-stage frame countdown (`hDownArrowBlinkCount1/2`; init 0/6, reload $FF/6). It is a
    pure **on/off binary blink** — no intermediate frames, no movement (Gen 1 blinks; the bounce
    arrived in later gens).
  - The **menu cursor '▶' is static**: `PlaceMenuCursor` writes a tile, `EraseMenuCursor`
    writes a space; the previously-selected slot gets the hollow '▷'. Zero animation frames.

### 1.9 Zelda: A Link to the Past (Nintendo, SNES 1991) — subscreen & HUD
- **Links:** [SNES Longplay [315] ALttP (World of Longplays)](https://www.youtube.com/watch?v=Z6hjG6MCcZ8)
  — open the item subscreen any time after the first dungeon item; HUD visible throughout;
  sheets: [Spriters Resource — ALttP](https://www.spriters-resource.com/snes/legendofzeldaalinktothepast/).
- **What animates:** **[INFERENCE from footage]** Item icons on the subscreen are static; the
  **selection is a blinking highlight frame** around the current item cell (on/off at a steady
  ~2–4 Hz tile toggle). HUD rupee/bomb/arrow counters tick numerically; the magic meter is a
  stepped fill. Hearts do not animate at low health (audio beep instead).

### 1.10 StarCraft / Brood War (Blizzard, 1998) — command card
- **Links:** [PC Longplay Starcraft Brood War Terran](https://www.youtube.com/watch?v=MjcSu2HtP98)
  (command card bottom-right on screen continuously); [Game UI Database — StarCraft-era pages](https://www.gameuidatabase.com/).
- **Resolution:** 640×480.
- **What animates:** **[INFERENCE from footage]** Command-card **button icons are static**;
  interaction feedback is the button bevel's **pressed-state art swap** and a highlight border.
  The animated UI elements are elsewhere: the **unit wireframe flashes** through green→yellow→red
  **palette states** as damage accrues, and the portrait plays a canned video loop. Resource
  counters tick. Warcraft II (1995–96) behaves identically (gold-bordered static buttons with a
  depress state).

### 1.11 Arcade/console HUD blink lineage (1980s) — “1UP”
- **Links:** [Inverse — origin of 1UP](https://www.inverse.com/gaming/1up-meaning-origin-definition-gaming)
  (flashing 1UP/2UP as active-player indicator, inherited from pinball); any Pac-Man/Galaga
  footage shows the active player's score label blinking.
- **What animates:** **[OBSERVED convention]** the active player's “1UP” text **blinks on/off**
  — the oldest UI-animation idiom in the corpus and the ancestor of every later blink: one art
  state + visibility toggle at a fixed frame count.

### 1.12 Ragnarok Online status-effect icons (supplementary)
- **Links:** [iRO Wiki — Status Icons](https://irowiki.org/wiki/Status_Icons) (page exists;
  direct fetch was blocked during research, so behavior below is not pinned to its text).
- **[INFERENCE from footage/community knowledge]** Buff/debuff icons stack in a column on the
  screen edge; icons are static 24-px-class bitmaps that appear/disappear; some ailment
  indicators are rendered as sprite overlays on the character (ACT-animated), not as animated
  UI icons.

---

## 2. The idiom table

Strong default across the whole corpus: **icons are static; the SELECTOR/cursor and world
effects carry the motion.** When an icon itself animates, it is a 2–4 unique-frame loop or a
binary state toggle.

| UI element class | Era-authentic idiom(s) | Typical unique frames | Typical cadence | What NEVER happens |
|---|---|---|---|---|
| Item icon (inventory/hotbar) | Static bitmap; instant appear/remove (RO, D2, UO, Tibia, MapleStory) | 1 | — | No idle loops, no bobbing, no glow pulse |
| Skill icon (hotbar/command card) | Static; **palette/brightness swap** for unavailable state (RO gray-out, MapleStory dim, SC pressed bevel) | 1–2 states | Instant state switch | No radial cooldown sweep (that's WoW 2004+), no smooth fade |
| Button | Two-state art swap: up/down bevel (D2, SC/WC2) | 2 | Instant on press/release | No easing, no hover scale |
| Cursor / selector | The era's animation budget lives here: RO animated ACT cursor (multi-frame loop @ 25 ms units); ALttP blinking highlight frame; Square hand cursor moves but doesn't cycle; Pokémon '▶' static | 1 (Square/Pokémon) to ~4–8 (RO cursor) | RO: N×25 ms per frame; blinks ~2–4 Hz | Cursor never trails, never motion-blurs |
| Gauge / bar | 1-px-step fill, left→right (RO cast gauge, Tibia HP/MP, FF6 ATB); D2 globes drain as liquid level | continuous fill, no tween curve | Updated per tick/frame | No gradient sweep, no elastic overshoot |
| Status-effect indicator | Appear/disappear; **on/off blink near expiry** (MapleStory buffs); character-overlay animation instead of icon animation (RO) | 1 art state, 2 visibility states | Blink ~2 Hz in final seconds | Icons don't spin, shake, or pulse-scale |
| Emblem / logo | Static bitmap (RO guild emblem 24 px BMP) | 1 | — | No animated emblems in 2002-era clients |
| Text | Character-by-character print; waiting-arrow **binary blink** (Pokémon ▼: one tile ↔ blank); 1UP blink | 2 states | Pokémon: frame-counter countdown toggle; arcade ~0.5 s period | No per-glyph effects, no alpha fades |
| Shimmer/“magic” field object (closest thing to a glowing icon) | 2–4 frame sparkle/palette-band cycle (FF6 save point) | 2–4 | Each frame held multiple 60 Hz frames (~100–250 ms) | Never smooth alpha; brightness steps through the indexed palette |

---

## 3. Resolution & frame-type facts

| Platform / client | Native resolution | Icon/cell sizes | Color depth | Timing base |
|---|---|---|---|---|
| Ragnarok Online (2002) | 640×480 windowed default; fixed 4:3 modes ([WarpPortal](https://support.warpportal.com/kb/a837/changing-resolution.aspx)) | Item icons **24×24 px** BMP ([rAthena Custom Items](https://github.com/rathena/rathena/wiki/Custom-Items)); skill icons same 24-px class **[INFERENCE]** | SPR sprites: **≤256-color indexed palette, index 0 = transparent, RLE on index 0** ([SPR spec](https://ragnarokresearchlab.github.io/file-formats/spr/)); UI icons are 8-bit BMPs with magenta key | **ACT delays in 25 ms units** (delay 1 = 25 ms; delay 4 = 100 ms) ([ACT.MD](https://github.com/Duckwhale/RagnarokFileFormats/blob/master/ACT.MD)) |
| Diablo II (2000) | 640×480 (800×600 in LoD), hardcoded ([WSGF](https://www.wsgf.org/dr/diablo-ii)) | Inventory cells **28×28 px** ([Phrozen Keep](https://d2mods.info/forum/kb/viewarticle?a=451)) | 8-bit paletted (DC6) | 25 fps game render |
| MapleStory (2003) | **800×600** default ([RaGEZONE](https://forum.ragezone.com/threads/do-people-still-play-maplestory-in-800x600-resolution.1203339/)) | Skill `iconRaw` ~32×32 **[approximate]** | Full-color PNG-class assets in WZ | Client-tick driven |
| Tibia (1997/2002) | Fixed-window 4:3 client | World sprites 32×32 single-frame ([search summary / OTLand](https://otland.net/threads/tutorial-adding-custom-items-to-your-7-92-ot.1525/)) | 8-bit-era sprites | Server tick; UI redraw per frame |
| SNES | **256×224 @ 60 Hz NTSC** ([nesdev forum](https://forums.nesdev.org/viewtopic.php?t=10141)) | 8×8 tiles; icons typically 16×16 (2×2 tiles) | **16 colors per palette** (4bpp) from 15-bit master | 60 Hz vblank; animations advance every N vblanks (frame-hold counters, as in the Pokémon code pattern) |
| Game Boy (Pokémon gen 1-2) | 160×144 | 8×8 text tiles; menu art tile-based | 4 shades (2bpp) | ~59.7 Hz; blink via per-frame countdown ([pokered `home/window.asm`](https://github.com/pret/pokered)) |
| GBA (Pokémon gen 3) | 240×160 | 16×16-class icons | 16 colors/palette (4bpp) from 15-bit | 59.73 Hz |
| Ultima Online (1997) | 640×480-class fixed | Gump art static bitmaps | 16-bit era art, 8-bit legacy assets | Server-driven updates |
| StarCraft (1998) | 640×480 | Command buttons ~32–36 px class **[approximate]** | 8-bit paletted | ~24 fps game logic, palette-cycling effects |

Key synthesis fact for the pipeline: **the RO client's native animation quantum is 25 ms**, and
period console UIs hold each animation frame for 6–16 vblanks (~100–266 ms). Authentic loops are
therefore 2–4 unique frames, each held 100–250 ms (i.e., ACT delays of 4–10).

---

## 4. Motion prescriptions — 5 Acolyte skill icons (24 px, beveled tiles)

Governing constraints (all **[OBSERVED]** era mechanics): 256-color indexed sprites, 25 ms delay
quanta, no alpha blending in icon bitmaps (magenta/index-0 keying only), and the corpus default
that any icon animation is a 2–4 frame palette-band or on/off cycle while the drawing stays
rigid. Every prescription below is executable as a 2002 ACT: N frames, per-frame delay, palette
index swaps only.

1. **Resurrection (glowing orb)** — closest idiom: **FF6 save-point shimmer** (§1.6): 2-frame
   bright/dim palette alternation held ~150–250 ms. Prescription: **2 unique frames**, hold
   200 ms each (ACT delay 8). Frame B shifts only the orb-core palette band up one step
   (highlight color replaces mid-tone on the ~8–12 innermost orb pixels; one existing pixel ring
   gains the highlight index). Bevel, outline, and background tile stay bit-identical.
2. **Aqua Benedicta (bowl of holy water)** — closest idiom: **RO animated-cursor sparkle /
   Tibia-style single-tile water glint** (§1.1, §1.4): tiny specular pixel repositioned per
   frame. Prescription: **3 unique frames**, hold 150 ms each (ACT delay 6). Only a 2×1-px white
   glint travels across the water surface (positions left → center → right on the 5–7 px
   water-line row); optionally the water-surface row swaps between two blue palette indices in
   frame 2. Bowl, rim, and bevel rigid.
3. **Sanctuary (golden figure emblem)** — closest idiom: **ALttP subscreen selection blink /
   MapleStory buff-expiry blink** (§1.9, §1.5): binary highlight toggle. Prescription: **2 unique
   frames**, asymmetric hold — base 350 ms (delay 14), lit 150 ms (delay 6). Lit frame remaps the
   gold mid-tone band one step brighter across the figure only (~15–25 px), exactly one palette
   step; no pixel changes position. Reads as a slow devotional glint, not a strobe.
4. **Angelus (winged emblem)** — closest idiom: **RO ACT sprite flap quantum** — 1-px displacement
   loops as used by RO's own animated world sprites (§1.1); icons may borrow the displacement but
   never rotation. Prescription: **3 unique frames** in a 1-2-3-2 loop, hold 125 ms each (ACT
   delay 5). Only the outer wing-tip rows move: up 1 px (frame 1), rest (frame 2), down 1 px
   (frame 3) — redrawn pixel rows, not sub-pixel shifts. Body/halo/bevel rigid; silhouette width
   unchanged.
5. **Gloria (star/flake emblem)** — closest idiom: **arcade 1UP blink + Pokémon ▼ single-tile
   toggle** (§1.11, §1.8): pure on/off of a small element. Prescription: **2 unique frames**,
   hold 250 ms each (ACT delay 10). Frame B toggles the four 1-px ray tips ON (rays extend 1 px
   with the existing highlight index) and swaps the star-core pixel to the brightest palette
   index; frame A is the base art. Nothing else changes — a twinkle, executed as index writes.

What never happens in any of the five (per §2): no scale pulse, no smooth alpha glow, no motion
blur, no rotation, no easing curves, no frame counts above 4, no per-frame bevel changes.

---

## Confidence & gaps

**High confidence (primary-source):** RO ACT 25 ms delay quantum; RO SPR 256-color indexed +
index-0 transparency; RO 24×24 item BMPs; RO cast gauge & gray-out-only cooldown (iRO Wiki);
D2 28×28 inventory cells and 640×480 hardcoding; SNES 256×224@60 Hz; GB 160×144; Pokémon R/B
▼-blink and static '▶' cursor read directly from the pret/pokered disassembly; MapleStory
800×600 default; 1UP blink convention.

**Medium confidence (footage/community, not pinned to one sentence):** RO windows opening
instantly with static icons; FF6/CT static hand cursor and save-point sparkle frame counts;
ALttP subscreen blink cadence; StarCraft static command buttons with pressed-state swap;
MapleStory 32×32 icon size and buff-expiry blink; UO fully static gumps.

**Gaps / could not verify:** exact YouTube timestamps for UI moments (video content could not be
watched frame-by-frame — links point at segments where the UI is continuously visible); iRO Wiki
Status Icons page and several Fandom/Spriters detail pages blocked direct fetch (403), so
per-sheet frame counts (e.g., RO cursor loop length, FF6 sparkle exact frames) are estimated
ranges rather than counted; TCRF's RO page returned tampered content and contributed nothing;
RO skill-icon dimensions asserted from the same 24-px item-icon convention rather than a
separate primary citation; RO status-icon expiry behavior in the *2002* client specifically
(vs. later clients) remains unconfirmed.

---

## GBA-generation addendum (owner reference: Pokémon Emerald)

Appended 2026-08-27. Owner's exemplar: *Pokémon Emerald* (Game Freak, GBA, 2004-05 US) —
reference footage: [Full Game Walkthrough, YouTube owRVh3-eZxM](https://www.youtube.com/watch?v=owRVh3-eZxM).
Primary source for every Emerald claim below: the **pret/pokeemerald decompilation**
([github.com/pret/pokeemerald](https://github.com/pret/pokeemerald)), files read verbatim
(raw `master` branch, fetched 2026-08-27). GBA = 240×160 @ ~59.73 Hz; all cadences below are
in hardware frames ("f"), 1 f ≈ 16.7 ms.

### A. Pokémon Emerald UI animation, from source

#### A.1 Party-menu Pokémon icons — continuous 2-frame loop, cadence IS a state channel
**[OBSERVED — `src/pokemon_icon.c`]** Icons are 32×32 4bpp sprites with exactly **2 stored
frames**. Five anim tables (`sAnim_0`–`sAnim_4` in `sMonIconAnims`), commented
"fastest to slowest":

| anim | pattern | per-frame hold | full cycle |
|---|---|---|---|
| 0 | frames 0,1 loop | 6 f (~100 ms) | 12 f (~200 ms) |
| 1 | frames 0,1 loop | 8 f (~133 ms) | 16 f (~267 ms) |
| 2 | frames 0,1 loop | 14 f (~233 ms) | 28 f (~467 ms) |
| 3 | frames 0,1 loop | 22 f (~367 ms) | 44 f (~733 ms) |
| 4 | frame 0 only (twice) | 29 f | effectively **static** |

**[OBSERVED — `src/party_menu.c` `UpdateHPBar` → `SetPartyHPBarSprite` (pokemon_icon.c)]**
The anim number is selected **by HP bar level**: HP_BAR_FULL→0, GREEN→1, YELLOW→2, RED→3,
fainted/empty→4. So a healthy Pokémon's icon flips frames every 6–8 f *forever*; a hurt one
visibly slows; a fainted one freezes. Animation speed is a live status display, not decoration.
Frame flips are done by `UpdateMonIconFrame` (pokemon_icon.c) via DMA sprite-copy of the other
32×32 frame — pixels swap wholesale, nothing tweens.

**[OBSERVED — `party_menu.c` `SpriteCB_BouncePartyMonIcon`]** The **selected** slot's icon
additionally bounces: on each frame-flip tick, `y2` is set to **−3 px** (odd cmd index) or
**+1 px** (even). The bounce is therefore hard-quantized to 2 positions, asymmetric around
rest (−3/+1, total travel 4 px), and its period equals the icon's HP-tied flip period
(e.g. 16 f at green). Unselected icons hold a fixed offset and keep frame-flipping without
positional motion (`AnimateSelectedPartyIcon`). No easing, no sinusoid — two positions.

#### A.2 Battle/dialogue textbox ▼ arrow — 4-step positional bob, not a blink
**[OBSERVED — `src/text.c` `TextPrinterDrawDownArrow`]**
`sDownArrowYCoords[] = { 0, 1, 2, 1 }` — the 8×16 arrow bitmap is re-blitted at y-offset
0→1→2→1, each position held **8 f (~133 ms)** (`downArrowDelay = 8`), i.e. a **32 f (~533 ms)
bob period with 2 px amplitude**. This is the key generational upgrade from Gen 1's on/off
tile blink (§1.8): same waiting-prompt role, but the art now *moves* by whole pixels through
a quantized triangle wave. Same routine serves field and battle textboxes.

#### A.3 Menu selection cursor — still static
**[OBSERVED — `src/menu.c` `RedrawMenuCursor`]** The list-menu cursor is the text glyph
`gText_SelectorArrow3` ("▶") printed at the new row; the old row is erased with a pixel fill.
**Zero animation frames** — instant reposition, exactly the FF6/Pokémon-Gen-1 idiom. Text
print speed (`sTextSpeedFrameDelays`, menu.c): **8/4/1 f per character** (slow/mid/fast).

#### A.4 HP/EXP bars — stepped drain with fixed-point sub-stepping
**[OBSERVED — `src/battle_interface.c` `MoveBattleBar`, `CalcNewBarValue`]**
HP bar = **48 px** (`B_HEALTHBAR_PIXELS`), EXP bar = **64 px**. Per call (one per frame during
the drain), HP moves by **1 HP-unit** (`toAdd = 1`); when maxHP < 48 the code switches to
Q24.8 fixed point and steps `maxValue/48` per frame so the drain never exceeds ~1 px/frame.
Rendering is whole-pixel tile writes — the bar *ticks*, never glides. EXP speed is scaled by
`GetScaledExpFraction` so any gain animates in a bounded time. Bar color is a **discrete
3-state palette swap** at >50% green / >20% yellow / ≤20% red (`HEALTHBOX_GFX_HP_BAR_*`).
Party-menu HP bars (`party_menu.c` `DisplayPartyPokemonHPBar`) are drawn as pixel-rect fills
with the same 3-state palette selection — no drain animation at all in that screen.

#### A.5 Bag (pocket icons and switch gesture)
**[OBSERVED — `src/item_menu_icons.c`]**
- Pocket change is an **instant frame swap**: each pocket is one single-frame anim
  (`ANIMCMD_FRAME(0/64/128/192/256/320, 4)`) — the bag art per pocket does not itself loop.
- On switch, the bag sprite does a **pop-and-settle**: `y2 = −5`, then +1 px/frame back to 0
  (5 f total) (`SetBagVisualPocketId` / `SpriteCB_BagVisualSwitchingPockets`).
- A small **rotating Poké Ball** sprite spins in the corner during the switch and is removed
  after **16 f** (`SpriteCB_SwitchPocketRotatingBallContinue`).
- Rejected action = **affine shake**: `sSpriteAffineAnim_BagShake` rotates −2 units/f × 2 f,
  +2 × 4 f, −2 × 4 f, +2 × 2 f (256 units = 360°, so ±~5.6° wobble) — a **12 f (~200 ms)
  one-shot**, then snap to normal. Hardware rotation used as a micro-gesture, never as an
  idle loop.

#### A.6 Save flow and PC / storage screens
- **[OBSERVED — `src/start_menu.c`]** The save dialog has **no dedicated animation**: static
  info window, text printed at player speed, ▼ bob, palette fade on exit (`BlendPalettes`).
  Feedback is textual, not a spinner.
- **[OBSERVED — `src/pokemon_storage_system.c`]** The PC is Emerald's busiest UI:
  - Background **waveform** sprites (Lanette's PC decoration): "on" state loops **3 unique
    frames × 8 f** (~400 ms cycle) (`sAnim_Waveform_LeftOn/RightOn`); "off" is a held frame.
  - **Box scroll arrows** nudge horizontally: +speed px every 4th frame, 6 steps then reset
    (`SpriteCB_Arrow`) — a marching quantized loop.
  - Box-title color cycles (`CycleBoxTitleColor`) and box changes slide title sprites in/out;
    the choose-box popup uses affine anims (`sAffineAnim_ChooseBoxMenu`).
- **[OBSERVED — `src/pokenav_main_menu.c`]** The **PokéNav spinning device icon** is the
  frame-count outlier: **8 frames × 8 f each = 64 f (~1.07 s) per revolution**
  (`sSpinningPokenavAnims`) — pre-rendered rotation frames, not affine.

#### A.7 Status-condition icons — static, palette-differentiated
**[OBSERVED — `battle_interface.c` `UpdateStatusIconInHealthbox`]** PSN/PAR/SLP/FRZ/BRN
icons are single 3-tile graphics copied into the healthbox with a per-status palette
(`sStatusIconColors`). **No animation.** Party-menu ailment icons likewise swap a single
frame per status (`SetPartyMonAilmentGfx`).

#### A.8 Where Emerald actually uses hardware alpha
**[OBSERVED — `battle_interface.c` `Task_HidePartyStatusSummary`]** The battle-start party
summary tray (Poké Ball row) fades out by stepping `BLDALPHA` from 16→0 while sliding
offscreen — hardware alpha is used for **transitions of whole UI surfaces**, with sprites
flipped to `ST_OAM_OBJ_BLEND` for the fade. Icons at rest never alpha-pulse; `item_menu.c`
explicitly zeroes `BLDCNT` for the bag screen. So: GBA *had* alpha, and Emerald's UI spends
it on enter/exit fades only.

### B. Named-titles catalog (GBA-centered, 1998–2006)

Entries ordered by relevance to the owner's reference. TSR = The Spriters Resource.

1. **Pokémon Emerald (2004, GBA)** — everything in §A. Links: [pret/pokeemerald](https://github.com/pret/pokeemerald);
   [TSR Emerald](https://www.spriters-resource.com/game_boy_advance/pokemonemerald/);
   [PKMN.NET Emerald animations](https://pkmn.net/?action=content&page=viewpage&id=8632&parentsection=87);
   [walkthrough owRVh3-eZxM](https://www.youtube.com/watch?v=owRVh3-eZxM).
2. **Pokémon Ruby/Sapphire (2002, GBA)** — same engine, same 2-frame icon system
   ([pret/pokeruby](https://github.com/pret/pokeruby)); party icons + HP-tied cadence identical
   idiom. [TSR R/S](https://www.spriters-resource.com/game_boy_advance/pokemonrubysapphire/),
   [PKMN.NET gen-3 icons](http://pkmn.net/?action=content&page=viewpage&id=8532).
3. **Pokémon FireRed/LeafGreen (2004, GBA)** — [pret/pokefirered](https://github.com/pret/pokefirered)
   is fully decompiled; same `TextPrinterDrawDownArrow` 4-step ▼ bob and mon-icon anim system
   (see its `src/text.c`, `src/pokemon_icon.c`). Useful as a second in-source witness.
4. **Golden Sun (2001, GBA)** — animated **finger cursor** (small horizontal bob) and
   **rotating battle-menu icon carousel**; Psynergy icons themselves static.
   [TSR Icons and HUD sheet](https://www.spriters-resource.com/game_boy_advance/gs/asset/40088/),
   [TSR Golden Sun](https://www.spriters-resource.com/game_boy_advance/gs/). **[INFERENCE from
   footage/sheets]** for frame counts (cursor ~2 positions).
5. **Fire Emblem: The Blazing Blade / The Sacred Stones (2003/2004, GBA)** — the map **cursor
   corner-brackets pulse open/closed** in a short loop; **map unit sprites idle-animate
   continuously** (~3-frame loops) with a **grey palette swap** for "already moved" — the era's
   clearest "grid of continuously animating icons + palette state" exemplar next to Emerald's
   party. Combat HP bars drain in 1-unit steps.
   [TSR Blazing Blade map sprites](https://www.spriters-resource.com/game_boy_advance/fireemblemtheblazingblade/asset/47384/),
   [TSR Sacred Stones](https://www.spriters-resource.com/game_boy_advance/fireemblemthesacredstones/).
   **[INFERENCE from sheets/footage]** for cadences.
6. **Advance Wars (2001, GBA)** — animated unit map icons (2–3 frame idle loops), moved-unit
   grey-out (palette swap), stepped CO-power meter segments, bracket cursor pulse.
   [TSR Advance Wars](https://www.spriters-resource.com/game_boy_advance/advwars/). **[INFERENCE]**.
7. **Mario & Luigi: Superstar Saga (2003, GBA)** — battle **command-icon carousel** (selected
   icon enlarges/bobs, others recede), **numeric HP tick-down** per digit; action icons above
   heads bounce. [TSR M&L:SS](https://www.spriters-resource.com/game_boy_advance/mlss/),
   [Battle Start sheet](https://www.spriters-resource.com/game_boy_advance/mlss/asset/7583/). **[INFERENCE]**.
8. **Final Fantasy Tactics Advance (2003, GBA)** — pointing-hand cursor with a small 2-position
   bob; static command menus; stepped charge/AT indicators.
   [TSR FFTA](https://www.spriters-resource.com/game_boy_advance/fftacticsadv/),
   [videogamesprites.net FFTA objects (cursors)](http://www.videogamesprites.net/FinalFantasyTacticsAdvance/Objects/). **[INFERENCE]**.
9. **The Legend of Zelda: The Minish Cap (2004, GBA)** — hearts and item buttons static; the
   feedback budget goes to instant icon swaps and the text prompt; low-health is audio + static
   art (ALttP lineage, §1.9).
   [TSR Minish Cap](https://www.spriters-resource.com/game_boy_advance/thelegendofzeldatheminishcap/). **[INFERENCE]**.
10. **Metroid Fusion (2002, GBA)** — map screen **current-position room blinks on/off** (~2 Hz
    binary toggle); energy refills tick in discrete units.
    [TSR Fusion map screen sheet](https://www.spriters-resource.com/game_boy_advance/metfusion/sheet/1660/),
    [TSR Fusion](https://www.spriters-resource.com/game_boy_advance/metfusion/). Zero Mission
    (2004) identical idiom. **[INFERENCE]**.
11. **WarioWare, Inc.: Mega Microgames! (2003, GBA)** — the **bomb timer**: fuse burns through
    a small number of discrete art states, one per beat — countdown as frame swap, not sweep.
    [TSR Bomb Timer sheet](https://www.spriters-resource.com/game_boy_advance/wariowareincmegamicrogames/asset/97625/). **[OBSERVED sheet / INFERENCE cadence]**.
12. **Kirby & the Amazing Mirror (2004, GBA)** — cell-phone **battery meter depletes in discrete
    segments**; ability icon swap is instant.
    [TSR Amazing Mirror](https://www.spriters-resource.com/game_boy_advance/kirbyandtheamazingmirror/). **[INFERENCE]**.
13. **MapleStory (2003, PC)** and **Ragnarok Online (2002, PC)** — already cataloged (§1.5,
    §1.1); retained here as the PC-side contrast: their *item/skill icons stay static* while
    Emerald's same-generation handheld UI animates its icons continuously.

### C. Deltas: what the GBA generation adds/changes vs. §2's conclusions

The old corpus default ("icons static; 2–4 held frames when animated; palette-band/on-off
idioms") stands for PC clients but is **too conservative for the GBA exemplar**:

1. **Continuous icon loops are normal, not exceptional.** Emerald party icons (and FE/AW map
   units) flip 2 frames *forever*. The 2-frame count matches §2, but "icons never idle-loop"
   does not hold on GBA.
2. **Cadence is a semantic channel.** Emerald's 6/8/14/22 f holds encode HP state; FE/AW encode
   "moved" via palette. Animation *speed* itself carries meaning — new vs. the PC corpus.
3. **The waiting prompt graduated from blink to bob.** Gen 1 ▼ = on/off; Gen 3 ▼ = 4-step
   2-px positional cycle at 8 f/step. Positional micro-motion (1–3 px, whole-pixel, quantized)
   replaces visibility toggling for "alive" elements. List cursors (▶, hand) mostly stay static.
4. **One-shot micro-gestures appear**: bag pop (−5 px, settle 1 px/f), 12 f affine shake,
   16 f rotating ball. Short (≤16 f ≈ 267 ms), hard-quantized, then dead still.
5. **Affine + alpha exist but are rationed**: rotation/scale for one-shot gestures and popups;
   alpha only for whole-surface enter/exit fades (§A.8). **Still no idle alpha glow on any
   icon** — that part of §2 survives intact.
6. **Bars still step** (1 unit or 1 px per frame, fixed-point beneath, whole-pixel on screen;
   discrete 3-color palette thresholds). §2's "no gradient sweep, no easing" fully confirmed
   in source.
7. **Frame-count ceiling rises for special elements only**: waveform 3 frames, PokéNav spinner
   8 frames; ordinary icons stay at 2.

**What "a bit off" plausibly means for our current outputs**, ranked:
(a) **cadence** — our §4 prescriptions (150–250 ms holds) read as Emerald's *hurt/slow* state;
the owner's reference feel is the healthy-state 100–133 ms flip; (b) **motion shape** — any
symmetric/eased bounce reads wrong; Emerald's is 2-position, asymmetric (−3/+1), synced to the
frame flip; (c) **motion size** — >3 px travel or sub-pixel rendering breaks the idiom;
(d) **soft 104-px crops** — GBA art is crisp native 32×32 4bpp with hard edges; soft matte
crops/AA halos are the most visible anachronism; (e) **any alpha glow/pulse** — never occurs.

### D. Revised motion prescriptions — 9 icons, Emerald-centered

Supersedes §4 *if the owner's Emerald reference governs* (§4 remains correct for the RO/PC
2002 idiom). Model: **every icon gets exactly 2 stored frames** (base + accent), looped
continuously at Emerald party-icon cadence; state is expressed by cadence + palette, one-shot
gestures by ≤16 f quantized motion. All holds in 60 Hz frames.

**Global state table (from §A.1):** active/ready **6 f** per frame (12 f cycle); idle/normal
**8 f** (16 f cycle); degraded/low-resource **14 f**; critical **22 f**; disabled **frozen on
frame 0**. Selected/hovered: add the −3/+1 px two-position bounce synced to the frame flip
(§A.1); on-activate: 12 f shake or 5 f pop-and-settle (§A.5); never both at once.

1. **Heal** — 2 frames: cross/hands base; accent frame brightens the core band one palette
   step (~10 px). Loop at 8 f/frame. On use: bag-style pop −5 px, settle +1 px/f.
2. **Protect** — 2 frames: shield base; accent adds a 1-px rim highlight. 8 f/frame. On block
   proc: 12 f affine-style wobble (±1 px shear if no affine available).
3. **Blessing** — 2 frames: accent lifts the halo/beam band one step. 8 f/frame idle; 6 f when
   the buff is active on the party (cadence-as-state, §C.2).
4. **Holy Light** — 2 frames: ray tips extend 1 px + core to brightest index (the Gloria
   twinkle from §4.5, retimed). **6 f/frame** — this is the "full HP" fast flip.
5. **Resurrection** — keep §4.1's 2-frame orb shimmer but retime: 8 f/frame normally, drop to
   **22 f/frame** while on cooldown, frozen frame 0 when unusable (Emerald fainted idiom).
6. **Aqua Benedicta** — §4.2's traveling 2×1 glint needs 3 frames; alternative that fits the
   2-frame model: glint toggles between two positions. 8 f/frame. (3-frame version stays legal —
   PC waveform uses 3×8 f, §A.6.)
7. **Sanctuary** — replace §4.3's asymmetric slow blink with the ▼-style quantized bob for its
   ground-glyph: y-offset 0/1/2/1 at **8 f/step** (§A.2), art otherwise rigid.
8. **Angelus** — §4.4's 3-frame wing cycle retimed to **8 f/frame** (24 f cycle ~400 ms);
   selected-state adds the −3/+1 bounce instead of extra wing frames.
9. **Gloria** — 2-frame twinkle at **6 f/frame** (fastest, celebratory); every 4th cycle may
   hold frame 0 for 22 f as a rest beat (period break, keeps it from strobing).

Hard rules carried over, now source-backed: whole-pixel motion only; ≤3 px travel; palette-step
brightness (never alpha); one-shot gestures ≤16 f; status = palette swap or cadence change,
never new artwork; crisp native-resolution pixels, no soft crops.

### Addendum confidence & gaps

**High (read verbatim from pret/pokeemerald):** all of §A — icon anim tables and HP mapping,
bounce offsets, ▼ coords/delay, static ▶, text speeds, bar constants and stepping math, bag
anims, PC waveform/arrows, PokéNav spinner, static status icons, alpha usage.
**Medium (sheets/footage, not frame-counted):** catalog entries 4–12 cadences; Golden Sun
cursor frame count; FE/AW idle-loop lengths. **Gaps:** TSR pages could not be fetched directly
(bot-blocked) — links verified via search results only; walkthrough video owRVh3-eZxM not
inspected frame-by-frame; FireRed source asserted identical from shared-engine knowledge, its
files not re-read this session.

---

## Tier B: the 2004 MMO client grammar (owner reference: World of Warcraft)

Appended 2026-08-27. This tier sits between the static-icon PC corpus (§1–2) and the
handheld sprite-loop grammar (GBA addendum): the 2004 MMO client animates icons **through
state machinery** — masks, overlay textures, vertex-color multiplies, and alpha ramps driven
by game timers — while the icon *bitmap* itself stays untouched. Primary source for every WoW
claim: Blizzard's own Classic-era FrameXML, read verbatim from the public mirror
**[tekkub/wow-ui-source, tag 1.12.1](https://github.com/tekkub/wow-ui-source/tree/1.12.1/FrameXML)**
(raw files fetched 2026-08-27: `ActionButton.lua`, `ActionButtonTemplate.xml`, `Cooldown.lua`,
`Cooldown.xml`, `BuffFrame.lua`, `CastingBarFrame.lua`, `Minimap.lua`, `Minimap.xml`), plus
[warcraft.wiki.gg](https://warcraft.wiki.gg/) widget documentation. **[OBSERVED]** /
**[INFERENCE]** conventions as in §1.

### B.1 WoW 1.x action-button / icon animation inventory (from FrameXML 1.12.1)

1. **Cooldown radial sweep** — **[OBSERVED — `Cooldown.xml`, `Cooldown.lua`]** In 1.12 the
   cooldown indicator is literally a **3D Model frame**:
   `<Model name="CooldownFrameTemplate" file="Interface\Cooldown\UI-Cooldown-Indicator.mdx"
   scale="0.75" ...>` layered over the 36×36 button. `CooldownFrame_SetTimer(this, start,
   duration, enable)` shows it; every frame, `CooldownFrame_OnUpdateModel` computes
   `finished = (GetTime() - this.start) / this.duration` and **scrubs the model's animation
   to that fraction**: `this:SetSequenceTime(0, finished * 1000)`. So the sweep is a canned
   1000 ms clock-wipe animation whose playhead is slaved to real cooldown progress — a
   2-second CD scrubs it in 2 s, a 5-minute CD in 5 min. When `finished >= 1.0` it switches
   to **sequence 1 — the end-of-cooldown flash** — played at real speed via `AdvanceTime()`,
   then hides in `CooldownFrame_OnAnimFinished`. Visually: a dark pie mask whose edge sweeps
   clockwise like a clock hand, uncovering the full-color icon, capped by a one-shot shine.
   The modern retail widget keeps the same grammar as a 2D system — "clock-like sweep and
   leading-edge effects", `SetCooldown(start, duration)`, `SetEdgeTexture()` ("the texture
   which 'follows' the moving edge"), `SetBlingTexture()` for the end flash, `SetReverse()`
   for direction ([warcraft.wiki.gg UIOBJECT_Cooldown](https://warcraft.wiki.gg/wiki/UIOBJECT_Cooldown)).
   Mechanism: **radial mask over an unchanged icon** — never a fade, never icon-art frames.
2. **Attack/auto-repeat flash** — **[OBSERVED — `ActionButton.lua`, `ActionButtonTemplate.xml`]**
   `ATTACK_BUTTON_FLASH_TIME = 0.4;`. The flash is a dedicated overlay texture
   `Interface\Buttons\UI-QuickslotRed` (a red button frame) that the OnUpdate **toggles
   Show/Hide every 0.4 s** — square wave, 0.8 s full period (1.25 Hz), with drift correction
   (`this.flashtime = ATTACK_BUTTON_FLASH_TIME - overtime`). Started when the slot
   `IsAttackAction(...)` and combat begins, or for `IsAutoRepeatAction` (Shoot/wand):
   `ActionButton_StartFlash()` sets `flashing = 1`; `ActionButton_StopFlash()` hides the
   texture. Mechanism: **binary visibility toggle of one overlay texture** — no alpha ramp.
3. **Button depress** — **[OBSERVED — `ActionButtonTemplate.xml`]** Pure state-texture swap:
   `NormalTexture = Interface\Buttons\UI-Quickslot2` ↔
   `PushedTexture = Interface\Buttons\UI-Quickslot-Depress`, instant on mouse-down/up; the
   icon bitmap itself does not move or scale. Hover = `HighlightTexture
   Interface\Buttons\ButtonHilight-Square` with `alphaMode="ADD"`; toggled-on state
   (auto-attack active) = `CheckedTexture Interface\Buttons\CheckButtonHilight`, also ADD.
4. **"Glow" in 1.x — static overlay only; the proc glow is 2010** — **[OBSERVED]** The only
   1.12 button glow is the **Border** texture `Interface\Buttons\UI-ActionButton-Border`
   (`alphaMode="ADD"`), shown at a *fixed* tint for equipped-item actions:
   `border:SetVertexColor(0, 1.0, 0, 0.35); border:Show();` (`ActionButton.lua`). It never
   pulses. The famous gold proc glow (SpellActivationOverlay + the button overlay glow) was
   added in **patch 4.0.1 (Cataclysm systems patch, Oct 2010)** — the driving event
   `SPELL_ACTIVATION_OVERLAY_GLOW_SHOW` is documented "Added in 4.0.1"
   ([warcraft.wiki.gg](https://warcraft.wiki.gg/wiki/SPELL_ACTIVATION_OVERLAY_GLOW_SHOW)).
   A 2004-authentic "glow" is therefore an **additive overlay texture at constant alpha**.
5. **Out-of-mana / unusable / out-of-range tinting** — **[OBSERVED — `ActionButton.lua`]**
   Vertex-color multiply on the icon, three discrete states, instant switch:
   usable `icon:SetVertexColor(1.0, 1.0, 1.0)`; not enough mana
   `icon:SetVertexColor(0.5, 0.5, 1.0)` (the blue-grey OOM wash, applied to the normal
   texture too); otherwise unusable `icon:SetVertexColor(0.4, 0.4, 0.4)` (dark grey).
   **Out-of-range in 1.12 tints the hotkey/range-dot text red, not the whole icon**:
   `RANGE_INDICATOR = "●"`, polled via `IsActionInRange(...)`, red
   `SetVertexColor(1.0, 0.1, 0.1)` — the full-icon red range tint players remember is a
   later-era/addon behavior **[OBSERVED for 1.12 scope; whole-icon red = later, INFERENCE]**.
6. **Expiring-buff blink** — **[OBSERVED — `BuffFrame.lua`]** Constants:
   `BUFF_WARNING_TIME = 31;` (start blinking under 31 s left), `BUFF_DURATION_WARNING_TIME
   = 60;`, `BUFF_FLASH_TIME_ON = 0.75; BUFF_FLASH_TIME_OFF = 0.75; BUFF_MIN_ALPHA = 0.3;`.
   Unlike the toggles above this is a **smooth linear alpha triangle wave**: alpha ramps
   1.0 → 0.3 over 0.75 s and back over 0.75 s (1.5 s period), normalized as
   `(BUFF_ALPHA_VALUE * (1 - BUFF_MIN_ALPHA)) + BUFF_MIN_ALPHA`, applied to the whole buff
   button until the aura expires. The icon art never changes.
7. **Cast bar** — **[OBSERVED — `CastingBarFrame.lua`]** A StatusBar filled left→right by
   wall-clock: `SetMinMaxValues(startTime, startTime + castTime)` then per-frame
   `SetValue(GetTime())`. A **Spark texture rides the fill edge**:
   `sparkPosition = (progress) * 195; CastingBarSpark:SetPoint("CENTER", CastingBarFrame,
   "LEFT", sparkPosition, 2)`. On success the bar snaps green `SetStatusBarColor(0.0, 1.0,
   0.0)`, a full-bar Flash overlay ramps up `+= CASTING_BAR_FLASH_STEP (0.2)` per frame to
   alpha 1, then the whole frame fades out `-= CASTING_BAR_ALPHA_STEP (0.05)` per frame
   (~0.7 s at 60 fps). On interrupt/fail: snap red `SetStatusBarColor(1.0, 0.0, 0.0)`, text
   FAILED/INTERRUPTED, hold `CASTING_BAR_HOLD_TIME = 1` s, then the same fade.
8. **Minimap ping** — **[OBSERVED — `Minimap.lua/.xml`]** Another Model frame:
   `Interface\MiniMap\Ping\MinimapPing.mdx` (50×50, scale 0.4) shown at the clicked spot,
   plays its radar-blip animation for `MINIMAPPING_TIMER = 5` s, then linear alpha fade over
   `MINIMAPPING_FADE_TIMER = 0.5` s and Hide.
9. **Quest "!" / "?" over NPCs** — **[OBSERVED colors / INFERENCE motion]** Gold "!" for
   available, "?" for turn-in (silver = too low level; blue = repeatable) rendered as a world
   marker above the NPC ([warcraft.wiki.gg Quest giver](https://warcraft.wiki.gg/wiki/Quest_giver);
   the page describes no animation). **[INFERENCE from footage]** In the 1.x client the
   marker is a static floating model — no bounce, no spin; it billboards with the camera.
10. **Loot sparkle** — **[OBSERVED]** A lootable corpse emits "a glittering effect" in the
    world, and the cursor swaps to the loot icon on hover
    ([warcraft.wiki.gg Loot](https://warcraft.wiki.gg/wiki/Loot)). The feedback is
    world-particle + cursor swap; nothing animates in the loot window's item buttons.
11. **Bag item pickup** — **[OBSERVED API / INFERENCE visual]** Picking up an item places it
    "on the cursor" (`PickupContainerItem`; with an item held, the next click places/swaps —
    [warcraft.wiki.gg](https://warcraft.wiki.gg/wiki/API_PickupContainerItem)). Visually the
    item's icon rides the cursor as a **static bitmap at full size** — no tilt, no scale, no
    trail — and drop/placement is instant. **[INFERENCE from footage]** for the no-tilt part.

### B.2 Contemporaries (1999–2005)

- **Ragnarok Online (2002)** — already cataloged in §1.1: cast time = green gauge above the
  character filling left→right; **cooldown has no sweep at all** — the hotbar skill icon just
  grays out ([iRO Wiki Skills](https://irowiki.org/wiki/Skills)); skill failure feedback is
  text/emote (ACT-driven world sprites), not an icon effect. RO is the "pre-sweep" pole that
  WoW's Cooldown model replaced.
- **Diablo II (2000)** — belt: 1–4 potion **columns**; potions auto-slot into matching
  columns on pickup, and using the bottom potion pulls the one above **down into its slot
  instantly** — a snap re-layout, no tween
  ([diablo-archive.fandom.com Belts (Diablo II)](https://diablo-archive.fandom.com/wiki/Belts_(Diablo_II));
  auto-fill behavior per search-verified wiki text; instant-snap **[INFERENCE from footage]**,
  cf. §1.2 longplay). Skill buttons: the left/right skill selector swaps static DC6 icon art
  instantly; buttons have a two-state pressed bevel; the animation budget lives in the
  health/mana globes (§1.2).
- **Guild Wars (2005)** — **it had the radial wipe, independently of WoW**: "The visual
  indicator of a recharging skill is a darkened skill icon that gradually lightens as if a
  clock-hand was sweeping through from noon to midnight."
  ([wiki.guildwars.com Recharge](https://wiki.guildwars.com/wiki/Recharge)) — same grammar
  as WoW's Cooldown (dark mask, clockwise from 12), confirming the radial sweep as *the*
  mid-2000s cooldown convention rather than one studio's invention.
- **EverQuest (1999)** — spell gems: casting grays **all** gems for a flat ~2 s global
  refresh regardless of the spell's own recast ("spell gems stay grayed-out for 2 seconds
  after casting any spell" — [Project 1999 forum archive](https://www.project1999.com/forums/archive/index.php/t-170288.html);
  [everquest.fandom.com Spell gem](https://everquest.fandom.com/wiki/Spell_gem)). Gray-out is
  a palette/brightness state, no sweep. **[INFERENCE from footage]** During memorization the
  gem flickers through icon frames — the era's only "animated icon", and it is a canned
  flicker, not a progress display.
- **Final Fantasy XI (2002)** — casting shown as the **Casting Time Gauge**, a linear bar in
  the top-left; the spell actually resolves at **75%** of the gauge ("At 75% on the gauge,
  the spell is effectively complete… reaches 100% at 4 seconds" for a 3 s cast —
  [BG Wiki Casting Time Gauge](https://www.bg-wiki.com/ffxi/Casting_Time_Gauge)). Abilities
  are menu-driven; recast shown as **numeric timers in the menu list**, no icon sweep.

### B.3 The Tier-B grammar table

The defining shift vs. §2 (static-icon PC era): the icon bitmap is *still* never redrawn,
but the client now runs **continuous state machinery around it** — masks, overlays, tints,
and alpha ramps with real durations tied to game timers.

| Element class | 2004-client idiom | Mechanism | Cadence / duration | What STILL never happens |
|---|---|---|---|---|
| Cooldown on icon | Clockwise dark wipe from 12 o'clock + end flash (WoW `UI-Cooldown-Indicator.mdx` seq 0/1; GW recharge) | Radial mask scrubbed to `elapsed/duration`; one-shot shine sequence at end | Sweep duration = the actual cooldown; end flash ≲ 0.5 s one-shot | Never a fade-in of the icon, never icon-art frames; RO/EQ tier does plain gray-out instead |
| Ability-queued / attack flash | Red overlay frame blinking (WoW `UI-QuickslotRed`) | Show/Hide toggle of one overlay texture | 0.4 s on / 0.4 s off (`ATTACK_BUTTON_FLASH_TIME`), 0.8 s period | No alpha ramp on the flash, no color cycling |
| Button press | Background plate swap (Quickslot2 ↔ Quickslot-Depress; D2/SC bevel lineage) | Two-state texture swap | Instant | Icon never moves, scales, or squashes |
| "Glow" / highlight | Additive overlay texture at fixed alpha (WoW Border ADD @ 0.35; hover ButtonHilight ADD) | ADD-blend texture, constant | Static while condition holds | No pulsing proc glow (that is 4.0.1 / 2010), no bloom — glow is a hard-edged TEXTURE |
| Unusable / OOM / range | Vertex-color multiply states: white / (0.5,0.5,1.0) / (0.4,0.4,0.4); red (1,0.1,0.1) range dot | Per-state color multiply, binary switch | Instant on state change; range polled sub-second | No fade between tints; no desaturation shader (later era) |
| Expiring buff | Whole-icon alpha triangle wave under 31 s | Linear alpha ramp 1.0↔0.3 | 0.75 s down + 0.75 s up (1.5 s period) | Icon art unchanged; never blinks fully off |
| Cast bar | Wall-clock fill + spark at edge; green+flash+fade on success, red+1 s hold+fade on fail | StatusBar SetValue(GetTime()) + positioned spark texture; per-frame alpha steps (0.2 up / 0.05 down) | Fill = real cast time; fade ~0.7 s | No easing curve on the fill; color changes snap |
| Ping / attention | One-shot world/UI model with linear fade-out (minimap ping 5 s + 0.5 s fade) | Canned model anim + SetAlpha ramp | Seconds-scale, then gone | No repeat, no elastic |
| Item drag | Icon rides cursor as static full-size bitmap | Cursor attachment | Instant pickup/drop | No tilt, no scale, no inertia |
| Icon bitmap itself | **Still static, always** (WoW, GW, D2, EQ, FFXI alike) | — | — | Never morphs, never scale-pulses, never plays sprite frames (that's the GBA tier) |

### B.4 Prescriptions — complex icon-animation experiments on 24 px RO-style skill icons, 2004-MMO grammar

Governing rule: the 24 px icon bitmap is a constant; every effect is a **layer above or a
multiply upon it** (mask wedge, overlay frame, tint, alpha), with timings taken verbatim
from the 1.12 constants above. Layers may use hard-edged shapes and additive blend; nothing
eases, everything snaps or ramps linearly.

- **(a) Radial cooldown wipe + end-of-cooldown flash** (WoW Cooldown model, B.1.1): overlay
  a dark mask (black at ~55–65% opacity) covering the whole icon at cast; its edge is a
  radius line that sweeps **clockwise starting at 12 o'clock**, shrinking the dark pie so
  the full-color icon is progressively uncovered; sweep duration = the actual cooldown
  (scrub position = `elapsed/duration`, updated every frame — at 24 px the wedge edge is
  hard, aliased, 1-px stepped). At 100%: mask off, then a **one-shot end flash** — a white/
  gold additive burst overlay (star or full-square) that appears at full alpha and plays out
  in ~0.3–0.5 s (2–4 discrete alpha steps down is period-correct), then hides. Icon pixels
  never tinted by the sweep — only covered.
- **(b) Proc-style border glow pulse** (B.1.4): a separate **hard-edged gold frame texture**
  one ring outside the icon (1–2 px ring at 24 px), ADD blend. Strictly-2004 mode: constant
  alpha ≈ 0.35, no pulse, appears/disappears instantly with the condition (the equipped-item
  border idiom). "Experiment" mode (borrowing the buff-blink ramp, still era-legal
  machinery): alpha triangle wave 0.3 ↔ 1.0 at 0.75 s up / 0.75 s down. Never blur the ring,
  never let it bloom past its texture bounds, never scale it.
- **(c) Activation press-flash** (B.1.2–3): on press, **instantly** swap the button's
  background plate to the depress art (bevel inverted / rim darkened — the icon itself does
  not move; at most the plate reads 1 px "sunk"); on release, instant restore, plus a white
  additive overlay square at ~60% alpha shown for exactly 1–2 frames (~50 ms) as the "fire"
  acknowledgment. If the ability stays queued/toggled: blink a **red overlay frame**
  Show/Hide at 0.4 s on / 0.4 s off until it fires, and keep an ADD highlight on while
  toggled (checked state).
- **(d) Out-of-range red tint toggle** (B.1.5): binary, no transition. Strict 1.12 flavor:
  the icon dims to a fixed multiply (0.4, 0.4, 0.4) when unusable and only the **hotkey/dot
  marker** turns red (1.0, 0.1, 0.1); OOM flavor: whole-icon multiply (0.5, 0.5, 1.0). If
  the experiment wants the (slightly later-era) whole-icon red: multiply ≈ (0.8, 0.1, 0.1),
  toggled on a ~0.2 s poll — state flips instantly whenever the range check flips, and the
  two states are the *only* frames that exist.
- **(e) Expiring-buff blink** (B.1.6): when remaining duration < 31 s, run the icon's
  **whole-layer alpha** on a linear triangle wave: 1.0 → 0.3 over 0.75 s, 0.3 → 1.0 over
  0.75 s, looping (1.5 s period) until expiry, then the icon vanishes instantly. Art, tint,
  and position unchanged; alpha floor never below 0.3 (the icon must stay readable). This is
  the one place the 2004 grammar uses a *smooth* ramp on an icon — everything else snaps.

### Tier-B confidence & gaps

**High (read verbatim from 1.12.1 FrameXML or quoted wiki text):** cooldown-as-Model with
`SetSequenceTime` scrub + sequence-1 end flash; `ATTACK_BUTTON_FLASH_TIME 0.4` and the
Show/Hide flash loop; all template texture paths and blend modes; usable/OOM/unusable vertex
colors and the red range indicator; all BuffFrame blink constants and the alpha formula;
cast-bar fill/spark/flash/fade code and colors; minimap-ping model + 5 s / 0.5 s timers;
green equipped-item border; SpellActivationOverlay glow = patch 4.0.1; Guild Wars recharge
clock-hand quote; FFXI 75%-gauge; EQ 2 s gem gray-out; D2 belt auto-fill text.
**Medium [INFERENCE]:** quest-marker and loot-window stillness, drag-icon no-tilt, D2 belt
snap being tween-free — footage-level claims not pinned to a quoted sentence; the exact
visual content of `UI-Cooldown-Indicator.mdx` sequence 1 (described from code flow + period
footage, the .mdx was not decompiled); whole-icon red range tint dated "later era" from
FrameXML absence in 1.12, not from a changelog line. **Gaps:** wago.tools texture pages not
fetched (JS-only viewer); Wowpedia (fandom) largely paywalled/403 to the fetcher — its
warcraft.wiki.gg successor used instead; EQ classic casting-bar specifics and RO fail-emote
specifics left to §1.1's existing citations.
