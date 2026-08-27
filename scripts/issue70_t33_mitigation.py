"""Issue #70: does editing a famous-mark parody pull it back to the real brand?

Sources are APPROVED PARODY OUTPUTS (verified visually to carry the parody
text), each given one benign recolor edit that does not touch the parody
lettering. Four protection arms per source; the protection is the only
changed input. Seed fixed; explicit OpenRouter via live ComfyUI.

Arms:
    bare          no brand-specific protection
    exact-copy    exact_copy blocks quoting the parody text verbatim
    negative      negative constraint naming the real brand and forbidding it
    wordmark-ref  the parody wordmark crop as natural Reference 2

Commands:
    submit SOURCE ARM   submit one paid render (refuses to resubmit)
    collect             download outputs, hashes, provider usage
    sheet               labeled contact sheet
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
OUT = ROOT / "artifacts" / "benchmarks" / "issue-70-t33-mitigation"
MODEL = "qwen/qwen-image-3-pro"
SEED = 2026070001
ARMS = ("bare", "exact-copy", "negative", "wordmark-ref")

SOURCES = {
    "palantir": {
        "path": "artifacts/runs/palantir-threat-report-energy-star-v001/palantir-threat-report-energy-star-v001.png",
        "aspect": "1:1",
        "objective": "Perform one surgical edit: recolor the bright blue background field of the label to a deep forest green. Change nothing else — every line, letter, arc, star, band, and border stays exactly as drawn.",
        "reference_role": "Reference image 1 is the authoritative label to edit. Match it exactly except the field color.",
        "exact_copy": [
            {"region": "cursive script across the label center", "text": "palantir"},
            {"region": "lower band", "text": "THREAT REPORT INCLUDED"},
        ],
        "negative": "Do not render the ENERGY STAR program logo, the word energy, the words ENERGY STAR, or any element of the real ENERGY STAR certification mark. This label is a fictional parody named palantir and must keep its own lettering.",
        "wordmark_ref": "artifacts/benchmarks/issue-70-t33-mitigation/refs/palantir-wordmark-from-output.png",
        "wordmark_role": "Reference image 2 shows this label's own cursive wordmark lettering exactly as it must remain; reproduce these letterforms unchanged.",
    },
    "truthsocial": {
        "path": "artifacts/runs/truth-social-inside-sticker-v001/truth-social-inside-sticker-v001.png",
        "aspect": "1:1",
        "objective": "Perform one surgical edit: recolor the solid blue band at the bottom of the sticker to a deep red. Change nothing else — every letter, the oval, the white field, and the sticker outline stay exactly as drawn.",
        "reference_role": "Reference image 1 is the authoritative sticker to edit. Match it exactly except the band color.",
        "exact_copy": [
            {"region": "upper line inside the oval", "text": "Truth social"},
            {"region": "lower line inside the oval", "text": "Inside"},
        ],
        "negative": "Do not render the Intel Inside logo, the word intel, or any element of the real Intel Inside mark. This sticker is a fictional parody reading Truth social Inside and must keep its own lettering.",
        "wordmark_ref": "artifacts/benchmarks/issue-70-t33-mitigation/refs/truthsocial-wordmark.png",
        "wordmark_role": "Reference image 2 shows this sticker's own oval wordmark lettering exactly as it must remain; reproduce these letterforms unchanged.",
    },
}

BASE_INVARIANTS = [
    "Keep every letterform, word, and piece of lettering exactly as drawn in Reference image 1 — same glyphs, spelling, kerning, slant, and position.",
    "Keep the overall geometry, proportions, print grain, and border treatment unchanged.",
]


def build_brief(source_key: str, arm: str) -> dict:
    spec = SOURCES[source_key]
    brief = {
        "objective": spec["objective"],
        "reference_role": spec["reference_role"],
        "provider": "openrouter",
        "model": MODEL,
        "output": {"resolution": "1K", "aspect_ratio": spec["aspect"],
                   "count": 1, "seed": SEED},
        "preservation_invariants": list(BASE_INVARIANTS),
        "negative_constraints": [
            "No relayout, recentering, cleanup, or added elements.",
        ],
    }
    if arm == "exact-copy":
        brief["exact_copy"] = spec["exact_copy"]
    elif arm == "negative":
        brief["negative_constraints"].append(spec["negative"])
    elif arm == "wordmark-ref":
        brief["reference_role"] += " " + spec["wordmark_role"]
    return brief


def _upload(path: str) -> str:
    import uuid
    data = (ROOT / path).read_bytes()
    boundary = uuid.uuid4().hex
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; "
        f"filename=\"issue70-{Path(path).name}\"\r\nContent-Type: image/png\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
    request = urllib.request.Request(
        f"{COMFY}/upload/image", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read())["name"]


def submit(source_key: str, arm: str) -> None:
    if arm not in ARMS:
        raise SystemExit(f"arm must be one of {ARMS}")
    spec = SOURCES[source_key]
    attempt_path = OUT / "attempts" / f"{source_key}--{arm}.json"
    attempt_path.parent.mkdir(parents=True, exist_ok=True)
    if attempt_path.exists():
        raise SystemExit(f"attempt record exists for {source_key}/{arm}; will not resubmit")
    brief = build_brief(source_key, arm)
    uploaded_source = _upload(spec["path"])
    graph = {"1": {"class_type": "LoadImage", "inputs": {"image": uploaded_source}}}
    if arm == "wordmark-ref":
        uploaded_ref = _upload(spec["wordmark_ref"])
        graph["5"] = {"class_type": "LoadImage", "inputs": {"image": uploaded_ref}}
        graph["6"] = {"class_type": "ImageBatch", "inputs": {
            "image1": ["1", 0], "image2": ["5", 0]}}
        image_input = ["6", 0]
    else:
        image_input = ["1", 0]
    graph["2"] = {"class_type": "QwenImage3Render", "inputs": {
        "edit_brief_json": json.dumps(brief), "reference_images": image_input}}
    graph["3"] = {"class_type": "SaveImage", "inputs": {
        "images": ["2", 0], "filename_prefix": f"issue70/{source_key}--{arm}"}}
    graph["4"] = {"class_type": "SaveText", "inputs": {
        "text": ["2", 1], "filename_prefix": f"issue70/{source_key}--{arm}-meta",
        "format": "json"}}
    attempt = {
        "source": source_key, "arm": arm, "seed": SEED, "provider": "openrouter",
        "model": MODEL, "requested_outputs": 1, "status": "submitted",
        "source_path": spec["path"],
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
    print("submitted", source_key, arm, "prompt_id", result["prompt_id"])
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
        key = f"{attempt['source']}--{attempt['arm']}"
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
    tiles = []
    for source_key, spec in SOURCES.items():
        tiles.append((f"{source_key} source", Image.open(ROOT / spec["path"]).convert("RGB")))
        for arm in ARMS:
            path = OUT / "outputs" / f"{source_key}--{arm}.png"
            if path.exists():
                tiles.append((f"{source_key} {arm}", Image.open(path).convert("RGB")))
    cell, label_h, columns = 420, 26, 5
    rows = (len(tiles) + columns - 1) // columns
    sheet_image = Image.new("RGB", (columns * cell, rows * (cell + label_h)), (24, 24, 24))
    draw = ImageDraw.Draw(sheet_image)
    for index, (label, image) in enumerate(tiles):
        col, row = index % columns, index // columns
        image.thumbnail((cell - 8, cell - 8))
        x = col * cell + (cell - image.width) // 2
        y = row * (cell + label_h) + (cell - image.height) // 2
        sheet_image.paste(image, (x, y))
        draw.text((col * cell + 8, row * (cell + label_h) + cell + 5), label, fill=(255, 255, 255))
    target = OUT / "contact-sheet.png"
    sheet_image.save(target)
    print("wrote", target, sheet_image.size)


if __name__ == "__main__":
    if sys.argv[1] == "submit":
        submit(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "collect":
        collect()
    elif sys.argv[1] == "sheet":
        sheet()
    else:
        raise SystemExit("unknown command")
