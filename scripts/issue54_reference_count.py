"""Issue #54: does a second NATURAL reference image improve edit fidelity?

Two frozen tasks, two arms each (source-only vs source + one natural detail
reference), same seed and settings within each pair. The added reference is
the only changed generation input. Both references are repository-owned:

  club task:     a 3x nearest-neighbor crop of the accepted assembly v003
                 club (pixel-art style-matched natural object reference)
  material task: the approved maga v001 metallic sticker photo as a brushed
                 silver foil material swatch

Commands:
    submit TASK ARM   submit one paid render (refuses to resubmit)
    collect           download outputs, hashes, provider usage
    sheet             labeled contact sheet
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

COMFY = "http://10.255.255.254:8188"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "artifacts" / "benchmarks" / "issue-54-reference-count"
MODEL = "qwen/qwen-image-3-pro"
SEED = 2026054001

CLUB_REF = "artifacts/benchmarks/issue-54-reference-count/refs/club-detail-3x.png"
MATERIAL_REF = "artifacts/runs/maga-operating-system-xe-sticker-v001/maga-operating-system-xe-sticker-v001.png"

TASKS = {
    "club-insertion": {
        "source": "artifacts/references/plantstudio-main-window.png",
        "extra_reference": CLUB_REF,
        "aspect": "5:4",
        "brief": {
            "objective": "Perform one surgical edit: replace the single selected tall thin flower inside the red selection rectangle with one upright seven-iron golf club. Change nothing else.",
            "reference_role": "Reference image 1 is the authoritative PlantStudio main-window screenshot (474 by 403). Match it exactly outside the red selection rectangle.",
            "preservation_invariants": [
                "Keep the complete application window and every unselected plant, label, number, icon, and pixel-scale spacing unchanged.",
                "Keep the Windows-era grey chrome, navy title bar, aliased pixel edges, limited palette, and low-resolution raster character.",
                "Do not change any text anywhere in the window.",
            ],
            "regions": [{
                "name": "red selection rectangle",
                "change": "Remove the selected flower and draw one upright seven-iron golf club in the same narrow vertical footprint: grip at top, straight steel shaft, compact angled iron head near the bottom, rendered in the same pixel-art style.",
                "preserve": ["the red selection rectangle itself"],
            }],
            "negative_constraints": [
                "No global redraw, modernization, smoothing, or invented UI.",
                "No golf ball, golfer, tee, flag, or any second golf object.",
            ],
        },
        "extra_role_sentence": "Reference image 2 is a pixel-art seven-iron golf club rendered in exactly the target style; copy its grip, shaft, and grooved angled head faithfully at the correct scale.",
    },
    "material-change": {
        "source": "artifacts/references/maga-operating-system-xe-sticker-v001/windows-xp-designed-for-badge-node-67-714.png",
        "extra_reference": MATERIAL_REF,
        "aspect": "3:4",
        "brief": {
            "objective": "Re-render the entire sticker as brushed silver metallic foil while keeping every shape, letterform, and layout element exactly in place.",
            "reference_role": "Reference image 1 is the authoritative Designed for Microsoft Windows XP case badge photo (389 by 508). Geometry and copy are the exact target; only surface material changes.",
            "preservation_invariants": [
                "Keep the four-color window flag mark's shape and position; its panes may take on silver-tinted metallic shading but must remain four distinct panes.",
                "Keep the texts Designed for, Microsoft, Windows XP, and the registered and TM marks exactly as written, sized, and positioned.",
                "Keep the rounded-rectangle outline, divider line, and proportions unchanged.",
            ],
            "style": [
                "Brushed silver metallic foil with fine horizontal brushing and a subtle specular highlight from the upper left.",
            ],
            "negative_constraints": [
                "Do not change layout, spelling, kerning, or element sizes.",
                "No added ornament, sparkle, engraving, or texture beyond the brushed foil.",
            ],
        },
        "extra_role_sentence": "Reference image 2 is a printed sticker photographed on the exact brushed silver metallic foil material to reproduce; match its sheen, brushing grain, and highlight behavior.",
    },
}


def _upload(path: str) -> str:
    import uuid
    data = (ROOT / path).read_bytes()
    boundary = uuid.uuid4().hex
    name = Path(path).name
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; "
        f"filename=\"issue54-{name}\"\r\nContent-Type: image/png\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
    request = urllib.request.Request(
        f"{COMFY}/upload/image", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read())["name"]


def submit(task: str, arm: str) -> None:
    if arm not in ("source-only", "with-reference"):
        raise SystemExit("arm must be source-only or with-reference")
    spec = TASKS[task]
    attempt_path = OUT / "attempts" / f"{task}--{arm}.json"
    attempt_path.parent.mkdir(parents=True, exist_ok=True)
    if attempt_path.exists():
        raise SystemExit(f"attempt record exists for {task}/{arm}; will not resubmit")
    brief = json.loads(json.dumps(spec["brief"]))
    brief["provider"] = "openrouter"
    brief["model"] = MODEL
    brief["output"] = {"resolution": "1K", "aspect_ratio": spec["aspect"],
                       "count": 1, "seed": SEED}
    if arm == "with-reference":
        brief["reference_role"] += " " + spec["extra_role_sentence"]

    uploaded_source = _upload(spec["source"])
    graph = {
        "1": {"class_type": "LoadImage", "inputs": {"image": uploaded_source}},
    }
    if arm == "with-reference":
        uploaded_extra = _upload(spec["extra_reference"])
        graph["5"] = {"class_type": "LoadImage", "inputs": {"image": uploaded_extra}}
        graph["6"] = {"class_type": "ImageBatch", "inputs": {
            "image1": ["1", 0], "image2": ["5", 0],
        }}
        image_input = ["6", 0]
    else:
        image_input = ["1", 0]
    graph["2"] = {"class_type": "QwenImage3Render", "inputs": {
        "edit_brief_json": json.dumps(brief),
        "reference_images": image_input,
    }}
    graph["3"] = {"class_type": "SaveImage", "inputs": {
        "images": ["2", 0], "filename_prefix": f"issue54/{task}--{arm}",
    }}
    graph["4"] = {"class_type": "SaveText", "inputs": {
        "text": ["2", 1], "filename_prefix": f"issue54/{task}--{arm}-meta",
        "format": "json",
    }}

    attempt = {
        "task": task, "arm": arm, "seed": SEED, "provider": "openrouter",
        "model": MODEL, "requested_outputs": 1, "status": "submitted",
        "source": {"path": spec["source"]},
        "extra_reference": spec["extra_reference"] if arm == "with-reference" else None,
    }
    attempt_path.write_text(json.dumps(attempt, indent=2) + "\n")
    request = urllib.request.Request(
        f"{COMFY}/prompt", data=json.dumps({"prompt": graph}).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(request, timeout=240) as response:
        result = json.loads(response.read())
    attempt["prompt_id"] = result["prompt_id"]
    attempt_path.write_text(json.dumps(attempt, indent=2) + "\n")
    print("submitted", task, arm, "prompt_id", result["prompt_id"])
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline:
        time.sleep(5)
        with urllib.request.urlopen(f"{COMFY}/history/{result['prompt_id']}", timeout=30) as response:
            history = json.loads(response.read())
        if result["prompt_id"] in history:
            entry = history[result["prompt_id"]]
            attempt["status"] = entry.get("status", {}).get("status_str", "unknown")
            attempt["completed"] = entry.get("status", {}).get("completed", False)
            attempt["outputs"] = entry.get("outputs", {})
            attempt_path.write_text(json.dumps(attempt, indent=2) + "\n")
            print("finished", attempt["status"])
            return
    attempt["status"] = "ambiguous-timeout"
    attempt_path.write_text(json.dumps(attempt, indent=2) + "\n")
    raise SystemExit("ambiguous timeout: counted as spent; do not retry")


def collect() -> None:
    outputs_dir = OUT / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for attempt_path in sorted((OUT / "attempts").glob("*.json")):
        attempt = json.loads(attempt_path.read_text())
        key = f"{attempt['task']}--{attempt['arm']}"
        record = {"status": attempt.get("status"), "prompt_id": attempt.get("prompt_id"),
                  "files": [], "usage": None}
        for node_output in attempt.get("outputs", {}).values():
            for text in node_output.get("text", []):
                try:
                    meta = json.loads(text)
                except ValueError:
                    continue
                record["usage"] = meta.get("usage")
                (outputs_dir / f"{key}-meta.json").write_text(json.dumps(meta, indent=2) + "\n")
            for item in node_output.get("images", []):
                if not isinstance(item, dict):
                    continue
                query = urllib.parse.urlencode({
                    "filename": item["filename"],
                    "subfolder": item.get("subfolder", ""),
                    "type": item.get("type", "output"),
                })
                with urllib.request.urlopen(f"{COMFY}/view?{query}", timeout=120) as response:
                    data = response.read()
                local = outputs_dir / f"{key}.png"
                local.write_bytes(data)
                record["files"].append({
                    "file": local.name, "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                })
        manifest[key] = record
        print(key, record["status"])
    (OUT / "collection-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    if sys.argv[1] == "submit":
        submit(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "collect":
        collect()
    else:
        raise SystemExit("unknown command")
