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
