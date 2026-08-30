#!/usr/bin/env python3.12
"""Prototype B (#137): build the source-pixel THEME assets for the options window.

Every crop is cut from artifacts/references/ro-desktop-b/reference-native.png (the sole
visual authority). Rect measurements are reused verbatim from Version A's
replica/assets/options/manifest.json (branch prototype/options-window @ d58c55b) — the
same pixels, a different mechanism. Derived states (hover tint, pressed nudge, healed
plate, authored minimized form, list panel) are deterministic; each is recorded in
theme-manifest.json with its derivation. No model calls.
"""
import json, hashlib, os
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REF = os.path.join(ROOT, "artifacts/references/ro-desktop-b/reference-native.png")
OUT = os.path.join(ROOT, "replica-b/assets/theme")
os.makedirs(OUT, exist_ok=True)
ref = np.asarray(Image.open(REF).convert("RGB")).copy()
WX, WY, WW, WH = 1108, 297, 424, 202   # window rect (A's manifest)

# ---- measurements reused from A (absolute reference coords) ----
M = {
 "bgm":    {"left":[1224,346,15,22], "right":[1464,346,15,21], "thumb":[1422,350,14,14], "track":[1239,350,225,15]},
 "effect": {"left":[1224,378,15,22], "right":[1464,378,15,22], "thumb":[1349,383,14,14], "track":[1239,382,225,15]},
 "cb": {"attack":[1135,467,18,17], "skill":[1225,467,18,17], "item":[1297,467,17,17], "option":[1392,468,18,17]},
 "on": {"bgm":[1486,351,16,16], "effect":[1486,382,16,17]},
 "dropdown": {"field":[1223,416,268,30], "arrow":[1491,416,30,30], "value_bbox":[1324,421,111,19]},
 "minimize":[1481,305,19,18], "close":[1505,301,22,25],
 "title_icon":[1113,300,20,19],
 "labels": {"bgm":[1132,344,72,24], "effect":[1124,376,84,24], "skin":[1130,415,66,24],
            "on_bgm":[1502,350,26,19], "on_effect":[1502,381,26,19],
            "attack":[1155,465,60,21], "skill":[1245,465,42,21], "item":[1316,465,44,21], "option":[1412,465,58,21]},
 "title_text":[1136,299,124,22],
}
def crop(r):
    x,y,w,h=r; return ref[y:y+h, x:x+w].copy()
def save(name, arr, note):
    img=Image.fromarray(arr.astype(np.uint8)); img.save(os.path.join(OUT,name))
    manifest["assets"][name]={"note":note,"size":list(img.size),
        "sha256":hashlib.sha256(open(os.path.join(OUT,name),'rb').read()).hexdigest()[:16]}
manifest={"reference":os.path.relpath(REF,ROOT),"window_rect":[WX,WY,WW,WH],"assets":{},"tokens":{},
 "provenance":"rects reused from Version A manifest (prototype/options-window@d58c55b); all pixels source-cut; derived states deterministic"}

# ---- tokens ----
tb = ref[303:321, 1300:1460].reshape(-1,3)
TITLE_BLUE = np.median(tb,axis=0).astype(int)
ink_px = ref[297:499,1108:1532].reshape(-1,3)
dark = ink_px[(ink_px[:,2].astype(int)-ink_px[:,0]>25)&(ink_px.sum(1)<430)]
TITLE_INK = np.median(dark,axis=0).astype(int) if len(dark) else np.array([70,89,159])
lab = crop(M["labels"]["bgm"]).reshape(-1,3); labd=lab[lab.sum(1)<430]
LABEL_INK = np.median(labd,axis=0).astype(int) if len(labd) else np.array([46,74,133])
manifest["tokens"]={"title_bar_blue":[int(v) for v in TITLE_BLUE],"title_ink":[int(v) for v in TITLE_INK],
 "label_ink":[int(v) for v in LABEL_INK],
 "derivation":"medians sampled from this window's own pixels (title span x1300..1459 y303..320; saturated title glyph ink; dark pixels of the BGM label)"}

def to_rgba(a):
    out=np.zeros((a.shape[0],a.shape[1],4),np.uint8); out[:,:,:3]=a; out[:,:,3]=255; return out
def hover(a):   # tint 18% toward title blue + keep alpha
    rgb=a[:,:,:3].astype(float); t=rgb*0.82+TITLE_BLUE*0.18
    out=a.copy(); out[:,:,:3]=np.clip(t,0,255); return out
def pressed(a): # 1px inset nudge (content shifts +1,+1), edge row/col repeated
    out=a.copy(); out[1:,1:]=a[:-1,:-1]; return out

# ---- slider parts (BGM row is the donor for both rows; effect row art is identical family) ----
for part in ["left","right","thumb"]:
    a=to_rgba(crop(M["bgm"][part]))
    if part=="thumb":   # alpha-mask: thumb is round; mask out pixels matching the track behind
        tr=crop([M["bgm"]["track"][0], M["bgm"]["track"][1], 14, 14]).astype(int)
        th=a[:,:,:3].astype(int); dist=np.abs(th-tr).sum(2)
        a[:,:,3]=np.where(dist<28, 0, 255).astype(np.uint8)
    save(f"slider-{part}.png", a, "source-cut (BGM row)")
    save(f"slider-{part}-hover.png", hover(a), "derived: 18% tint toward title_bar_blue")
    save(f"slider-{part}-pressed.png", pressed(a), "derived: 1px inset nudge")
track_px = crop(M["bgm"]["track"])
# heal the baked BGM thumb out of the track (footprint x1419..1439 abs -> local 180..200)
tf_x0 = 1419 - M["bgm"]["track"][0]; tf_w = 20
track_px[:, tf_x0:tf_x0+tf_w] = track_px[:, tf_x0-26:tf_x0-26+tf_w]
save("slider-track.png", to_rgba(track_px), "source-cut (BGM row), baked thumb healed with the track's own left span")
# ---- checkboxes ----
save("check-on.png",  to_rgba(crop(M["cb"]["skill"])),  "source-cut: the checked 'skill' box")
save("check-off.png", to_rgba(crop(M["cb"]["attack"])), "source-cut: the unchecked 'attack' box")
save("check-on-small.png",  to_rgba(np.asarray(Image.fromarray(crop(M["cb"]["skill"]).astype(np.uint8)).resize((16,16),Image.NEAREST))), "derived: 'skill' glyph point-resampled 18x17->16x16 for the small 'on' boxes")
save("check-off-small.png", to_rgba(crop(M["on"]["bgm"])), "source-cut: the unchecked BGM 'on' box")
# ---- dropdown ----
fld=crop(M["dropdown"]["field"])
save("dropdown-arrow.png", to_rgba(crop(M["dropdown"]["arrow"])), "source-cut")
save("dropdown-arrow-hover.png", hover(to_rgba(crop(M["dropdown"]["arrow"]))), "derived hover tint")
vx,vy,vw,vh=M["dropdown"]["value_bbox"]; fx,fy=M["dropdown"]["field"][:2]
blank=fld.copy()
donor=blank[2:6,:,:].mean(axis=0)          # clean top rows of the field interior
blank[vy-fy:vy-fy+vh,:] = donor[None,:,:]
save("dropdown-field.png", to_rgba(blank), "source-cut field, value text healed with the field's own background rows — StyleBoxTexture 4px margins; live text renders the value")
# list panel: field pixels as the panel background; hover bar = vertical gradient sampled from the title bar
save("list-panel.png", to_rgba(blank), "derived: the field's own surface reused as the open-list panel (nine-patch)")
grad=ref[303:321,1310,:].astype(np.uint8)  # one clean title-bar column = the skin's gradient
bar=np.repeat(grad[None if False else slice(None),None,:],200,axis=1).transpose(0,1,2)
bar=np.transpose(np.repeat(grad[:,None,:],200,axis=1),(0,1,2))
save("list-hover-bar.png", to_rgba(bar), "derived: hover bar = the title bar's own vertical gradient column x1310, repeated — the skin token, not a flat colour")
# ---- title bar buttons + icon ----
for nm,r in [("btn-minimize",M["minimize"]),("btn-close",M["close"])]:
    a=to_rgba(crop(r)); save(f"{nm}.png",a,"source-cut"); save(f"{nm}-hover.png",hover(a),"derived hover tint"); save(f"{nm}-pressed.png",pressed(a),"derived 1px nudge")
save("title-icon.png", to_rgba(crop(M["title_icon"])), "source-cut")

# ---- healed chrome plate: window with ALL text, control art and glyphs removed ----
plate=crop([WX,WY,WW,WH])
CLEAN_X = 1300 - WX   # a control-free span of the title bar
def heal_flat(rect, grow=3):
    x,y,w,h=rect; x-=WX; y-=WY
    x-=grow; y-=grow; w+=2*grow; h+=2*grow
    x=max(1,x); y=max(1,y); w=min(w,WW-1-x); h=min(h,WH-1-y)
    if y < 26:   # on the title bar: copy the bar's own clean gradient rows
        plate[y:y+h, x:x+w] = plate[y:y+h, CLEAN_X:CLEAN_X+w]
        return
    frame=np.concatenate([plate[y-1:y, x:x+w].reshape(-1,3), plate[y+h:y+h+1, x:x+w].reshape(-1,3),
                          plate[y:y+h, x-1:x].reshape(-1,3), plate[y:y+h, x+w:x+w+1].reshape(-1,3)])
    plate[y:y+h, x:x+w] = np.median(frame,axis=0)
for grp in [M["labels"][k] for k in M["labels"]] + [M["cb"][k] for k in M["cb"]] + [M["on"][k] for k in M["on"]] + [M["bgm"][p] for p in ("left","right","thumb","track")] + [M["effect"][p] for p in ("left","right","thumb","track")] + [M["dropdown"]["field"],M["dropdown"]["arrow"],M["minimize"],M["close"],M["title_icon"]]:
    heal_flat(grp)
# title text heal: copy a clean span of the title bar over the text
tx,ty,tw,th=M["title_text"]; tx-=WX; ty-=WY
ty=2; th=26   # soft descenders reach rows 321-322 (local 24-25)
clean=plate[ty:ty+th, 1300-WX:1300-WX+tw]
plate[ty:ty+th, tx:tx+tw]=clean
save("chrome-plate.png", to_rgba(plate), "derived: window crop with every label, value, glyph and control healed out; chrome only — borders, pinstripe column, panel fills, separator, title gradient")
# ---- authored minimized form: title strip completed with the window's own bottom edge ----
strip=plate[0:24].copy(); bottom=plate[WH-4:WH].copy()   # from the HEALED plate: chrome only, live title/buttons draw on top
mini=np.concatenate([strip,bottom],axis=0)
save("minimized-window.png", to_rgba(mini), "derived AUTHORED minimized form: the title strip completed with the window's own bottom border rows — a finished compact window, not a crop. intent-specified pending #108")

json.dump(manifest, open(os.path.join(OUT,"theme-manifest.json"),"w"), indent=1)
print("assets:",len(manifest["assets"]))
# contact sheet
names=sorted(manifest["assets"]); S=4
tiles=[]
from PIL import ImageDraw
for n in names:
    im=Image.open(os.path.join(OUT,n)).convert("RGBA")
    tiles.append((n,im.resize((im.width*S,im.height*S),Image.NEAREST)))
cw=max(t.width for _,t in tiles)+8; chh=max(t.height for _,t in tiles)+22; cols=5
rows=(len(tiles)+cols-1)//cols
sheet=Image.new("RGB",(cols*cw,rows*chh),(255,0,255)); dr=ImageDraw.Draw(sheet)
for k,(n,t) in enumerate(tiles):
    x=(k%cols)*cw; y=(k//cols)*chh; dr.text((x+3,y+3),n[:34],fill=(0,0,0)); sheet.paste(t,(x+4,y+20),t)
sheet.save(os.path.join(ROOT,"replica-b/evidence/builder/theme-contact-4x.png")); print("sheet ok")
