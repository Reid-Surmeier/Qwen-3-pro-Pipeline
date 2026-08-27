"""Issue #52: canvas-match ablation — output geometry as a drift lever.

One frozen task (the Issue #18 localized-replacement canonical brief), one
seed, arms varying ONLY the requested output geometry:

    a-close-5x4-1k      nearest supported aspect to the 474x403 source
    b-mismatch-4x3-1k   the historical golf-club v001 mismatch
    c-mismatch-16x9-1k  strong wide mismatch
    d-mismatch-1x1-1k   strong square mismatch
    e-close-5x4-2k      resolution effect at matched aspect

Five outputs, seed 2026052001, explicit OpenRouter via live ComfyUI.

Commands:
    submit ARM    submit one paid render (refuses if an attempt record exists)
    collect       download outputs, hashes, provider usage
    sheet         labeled contact sheet
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
OUT = ROOT / "artifacts" / "benchmarks" / "issue-52-canvas-match"
MODEL = "qwen/qwen-image-3-pro"
SEED = 2026052001

ARMS = {
    "a-close-5x4-1k": ("5:4", "1K"),
    "b-mismatch-4x3-1k": ("4:3", "1K"),
    "c-mismatch-16x9-1k": ("16:9", "1K"),
    "d-mismatch-1x1-1k": ("1:1", "1K"),
    "e-close-5x4-2k": ("5:4", "2K"),
}

SOURCE = {
    "path": "artifacts/references/plantstudio-main-window.png",
    "sha256": "c9ddeaa3cd27d0d5b502710ad12bc8f810529339c87b97a289b6d6932df8f45d",
}

BRIEF = {
    "objective": "Perform one surgical edit: replace the single selected tall thin flower inside the red selection rectangle with one upright seven-iron golf club. Change nothing else.",
    "reference_role": "Reference image 1 is the authoritative PlantStudio main-window screenshot (474 by 403). Match it exactly outside the red selection rectangle.",
    "provider": "openrouter",
    "model": MODEL,
    "preservation_invariants": [
        "Keep the complete application window: title bar, menus, toolbar, plant canvas, species list, growth graph, age controls, tabs, and status bar in their original positions.",
        "Keep every unselected plant, label, number, icon, and pixel-scale spacing unchanged.",
        "Keep the Windows-era grey chrome, navy title bar, aliased pixel edges, limited palette, and low-resolution raster character.",
        "Do not change any text anywhere in the window.",
    ],
    "regions": [{
        "name": "red selection rectangle",
        "change": "Remove the selected flower and draw one upright seven-iron golf club in the same narrow vertical footprint: grip at top, straight steel shaft, compact angled iron head near the bottom, rendered in the same pixel-art style.",
        "preserve": ["the red selection rectangle itself"],
    }],
    "negative_constraints": [
        "No global redraw, modernization, smoothing, anti-aliasing upgrade, or invented UI.",
        "No golf ball, golfer, tee, flag, or any second golf object.",
    ],
    "quality_checks": [
        "At 100 percent zoom, pixels outside the red rectangle look identical to the reference.",
        "The club reads clearly as a seven-iron at original scale.",
    ],
}


def upload_source() -> str:
    import uuid
    data = (ROOT / SOURCE["path"]).read_bytes()
    boundary = uuid.uuid4().hex
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; "
        f"filename=\"issue52-plantstudio.png\"\r\nContent-Type: image/png\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
    request = urllib.request.Request(
        f"{COMFY}/upload/image", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read())["name"]


def submit(arm: str) -> None:
    aspect, resolution = ARMS[arm]
    attempt_path = OUT / "attempts" / f"{arm}.json"
    attempt_path.parent.mkdir(parents=True, exist_ok=True)
    if attempt_path.exists():
        raise SystemExit(f"attempt record exists for {arm}; will not resubmit")
    brief = json.loads(json.dumps(BRIEF))
    brief["output"] = {
        "resolution": resolution, "aspect_ratio": aspect, "count": 1, "seed": SEED,
    }
    uploaded = upload_source()
    graph = {
        "1": {"class_type": "LoadImage", "inputs": {"image": uploaded}},
        "2": {"class_type": "QwenImage3Render", "inputs": {
            "edit_brief_json": json.dumps(brief),
            "reference_images": ["1", 0],
        }},
        "3": {"class_type": "SaveImage", "inputs": {
            "images": ["2", 0], "filename_prefix": f"issue52/{arm}",
        }},
        "4": {"class_type": "SaveText", "inputs": {
            "text": ["2", 1], "filename_prefix": f"issue52/{arm}-meta",
            "format": "json",
        }},
    }
    attempt = {
        "arm": arm, "aspect_ratio": aspect, "resolution": resolution,
        "seed": SEED, "provider": "openrouter", "model": MODEL,
        "requested_outputs": 1, "source": SOURCE, "status": "submitted",
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
    print("submitted", arm, "prompt_id", result["prompt_id"])
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
        key = attempt["arm"]
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


def sheet() -> None:
    from PIL import Image, ImageDraw
    reference = ROOT / SOURCE["path"]
    tiles = [("reference 474x403", Image.open(reference).convert("RGB"))]
    for arm in ARMS:
        path = OUT / "outputs" / f"{arm}.png"
        if path.exists():
            image = Image.open(path).convert("RGB")
            tiles.append((f"{arm} ({image.width}x{image.height})", image))
    cell_w, cell_h, label_h = 560, 440, 28
    columns = 3
    rows = (len(tiles) + columns - 1) // columns
    sheet_image = Image.new("RGB", (columns * cell_w, rows * (cell_h + label_h)), (24, 24, 24))
    draw = ImageDraw.Draw(sheet_image)
    for index, (label, image) in enumerate(tiles):
        col, row = index % columns, index // columns
        image.thumbnail((cell_w - 8, cell_h - 8))
        x = col * cell_w + (cell_w - image.width) // 2
        y = row * (cell_h + label_h) + (cell_h - image.height) // 2
        sheet_image.paste(image, (x, y))
        draw.text((col * cell_w + 10, row * (cell_h + label_h) + cell_h + 6),
                  label, fill=(255, 255, 255))
    target = OUT / "contact-sheet.png"
    sheet_image.save(target)
    print("wrote", target, sheet_image.size)


if __name__ == "__main__":
    if sys.argv[1] == "submit":
        submit(sys.argv[2])
    elif sys.argv[1] == "collect":
        collect()
    elif sys.argv[1] == "sheet":
        sheet()
    else:
        raise SystemExit("unknown command")
