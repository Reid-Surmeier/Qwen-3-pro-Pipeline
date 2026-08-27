"""Frame-fidelity checks: compare the captured Godot frame against the
Reference Screen per declared regions with per-region tolerances."""
import json
from pathlib import Path

from PIL import Image
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
REFERENCE = ROOT.parent / "artifacts/references/ro-hud-fullscreen/reference-native.png"
CAPTURE = ROOT / "qa/out/capture.png"
REGIONS = json.loads((ROOT / "data/fidelity-regions.json").read_text())

cap = np.array(Image.open(CAPTURE).convert("RGB"), dtype=int)
ref = np.array(Image.open(REFERENCE).convert("RGB"), dtype=int)

results = []
for region in REGIONS["regions"]:
    x, y, w, h = region["rect"]
    ref_crop = ref[y:y + h, x:x + w]
    inside = cap.shape[0] >= y + h and cap.shape[1] >= x + w
    cap_crop = cap[y:y + h, x:x + w] if inside else None
    entry = {"name": region["name"], "rect": region["rect"], "check": region["check"]}
    if cap_crop is None:
        entry.update(passed=False, detail="capture smaller than region")
    elif region["check"] == "mean-color":
        d = float(np.abs(ref_crop.mean(axis=(0, 1)) - cap_crop.mean(axis=(0, 1))).max())
        entry.update(passed=d <= region["tolerance"], mean_channel_delta=round(d, 2))
    elif region["check"] == "exact-color":
        target = np.array(region["color"])
        frac = float((np.abs(cap_crop - target).max(axis=2) <= region.get("tolerance", 4)).mean())
        entry.update(passed=frac >= region.get("min_fraction", 0.98), matching_fraction=round(frac, 4))
    else:
        entry.update(passed=False, detail="unknown check")
    results.append(entry)

report = {"pass": all(r["passed"] for r in results),
          "capture_size": list(cap.shape[1::-1]), "regions": results}
(ROOT / "qa/out/fidelity.json").write_text(json.dumps(report, indent=2))
print("fidelity PASS" if report["pass"] else json.dumps(report, indent=1))
