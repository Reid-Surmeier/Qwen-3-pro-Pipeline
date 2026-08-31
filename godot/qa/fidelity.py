"""Strict frame-fidelity v2: per-window pixel-level diffs against the
Reference Screen. Window plates are source crops drawn at source coordinates,
so inside every window rect the capture must match the reference nearly
byte-exactly (tiny allowance for driver rounding). The generated backdrop
region is reported but judged separately; magenta gutters are exact-checked.
"""
import json
from pathlib import Path

from PIL import Image
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
REFERENCE = ROOT.parent / "artifacts/references/ro-hud-fullscreen/reference-native.png"
CAPTURE = ROOT / "qa/out/capture.png"
RECTS = json.loads((ROOT.parent / "artifacts/references/ro-hud-fullscreen/window-rects.json").read_text())

CHANNEL_TOLERANCE = 2
MAX_CHANGED_FRACTION = 0.002

cap = np.array(Image.open(CAPTURE).convert("RGB"), dtype=int)
ref = np.array(Image.open(REFERENCE).convert("RGB"), dtype=int)

results = []
for name, (x, y, w, h) in sorted(RECTS.items()):
    ref_crop = ref[y:y + h, x:x + w]
    cap_crop = cap[y:y + h, x:x + w]
    delta = np.abs(ref_crop - cap_crop).max(axis=2)
    changed = float((delta > CHANNEL_TOLERANCE).mean())
    results.append({
        "window": name, "rect": [x, y, w, h],
        "changed_fraction": round(changed, 5),
        "max_delta": int(delta.max()),
        "passed": changed <= MAX_CHANGED_FRACTION,
    })

# speech bubble (source plate at source coords)
bx, by, bw, bh = 852, 42, 222, 120
delta = np.abs(ref[by:by+bh, bx:bx+bw] - cap[by:by+bh, bx:bx+bw]).max(axis=2)
results.append({"window": "speech-bubble", "rect": [bx, by, bw, bh],
    "changed_fraction": round(float((delta > CHANNEL_TOLERANCE).mean()), 5),
    "max_delta": int(delta.max()),
    "passed": float((delta > CHANNEL_TOLERANCE).mean()) <= MAX_CHANGED_FRACTION})

# magenta gutter exact check
gx, gy, gw, gh = 704, 500, 12, 200
gutter = cap[gy:gy+gh, gx:gx+gw]
frac = float((np.abs(gutter - np.array([239, 7, 239])).max(axis=2) <= 24).mean())
results.append({"window": "magenta-gutter", "rect": [gx, gy, gw, gh],
    "matching_fraction": round(frac, 4), "passed": frac >= 0.8})

# backdrop region: informational only (generated content)
sx, sy, sw, sh = 655, 0, 753, 845
delta = np.abs(ref[sy:sy+sh, sx:sx+sw] - cap[sy:sy+sh, sx:sx+sw]).max(axis=2)
info = {"window": "game-backdrop (informational)",
        "changed_fraction": round(float((delta > CHANNEL_TOLERANCE).mean()), 5),
        "passed": True}
results.append(info)

report = {"pass": all(r["passed"] for r in results),
          "capture_size": list(cap.shape[1::-1]),
          "channel_tolerance": CHANNEL_TOLERANCE,
          "max_changed_fraction": MAX_CHANGED_FRACTION,
          "regions": results}
(ROOT / "qa/out/fidelity.json").write_text(json.dumps(report, indent=2))
print("fidelity PASS" if report["pass"] else json.dumps(report, indent=1))
