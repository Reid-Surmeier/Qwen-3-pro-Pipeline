"""Issue #18 prompt-length experiment: canonical vs near-ceiling Edit Briefs.

Five frozen source-locked tasks, two prompt arms each. The near-ceiling arm is
a deterministic restatement of the same atomic requirements — no new visual
requirement is added — targeted at 4,300-4,450 approximate tokens against the
published 4,500-token instruction budget (repository three-chars-per-token
estimate, not a provider tokenizer).

Commands:
    build             write briefs, compiled prompts, and metrics
    submit TASK ARM   submit one paid render through live ComfyUI (refuses
                      to resubmit if an attempt record already exists)
    blind             create a shuffled, neutral-named review set

Paid policy: explicit OpenRouter only, one output per condition, ten outputs
total for the linked Issue. An ambiguous failure counts as spent and is never
retried by this script.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qwen_ui_pipeline.prompt_manifest import compile_edit_brief

COMFY = "http://10.255.255.254:8188"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "artifacts" / "benchmarks" / "issue-18-prompt-length"
SEED = 2026081801
MODEL = "qwen/qwen-image-3-pro"
PROVIDER = "openrouter"
TARGET_MIN, TARGET_MAX = 4_300, 4_450

SOURCES = {
    "plantstudio": {
        "path": "artifacts/references/plantstudio-main-window.png",
        "sha256": "c9ddeaa3cd27d0d5b502710ad12bc8f810529339c87b97a289b6d6932df8f45d",
    },
    "xp-badge": {
        "path": "artifacts/references/maga-operating-system-xe-sticker-v001/windows-xp-designed-for-badge-node-67-714.png",
        "sha256": "a9975f59fc67f3bcb30c468b9a2cc63254a6ce7d4a1a77d076b4de08f53a5801",
    },
    "energy-star": {
        "path": "artifacts/runs/palantir-threat-report-energy-star-v001/energy-star-source-node-110-989.png",
        "sha256": "ce7a213c4ae4c8f8f67883796003f5489092e05f3011b75028f1049f2a5f03bb",
    },
    "intel-crop": {
        "path": "artifacts/references/truth-social-inside-sticker-v001/intel-inside-celeron-crop.png",
        "sha256": "7c8e8767f72b72ce4fa4c888507f5ad060003a6cab7802f3e0deef44c8de35d7",
    },
}


def _brief(objective, reference_role, source, aspect, **sections):
    brief = {
        "objective": objective,
        "reference_role": reference_role,
        "provider": PROVIDER,
        "model": MODEL,
        "output": {
            "resolution": "1K",
            "aspect_ratio": aspect,
            "count": 1,
            "seed": SEED,
        },
    }
    brief.update(sections)
    brief["_source"] = source
    return brief


TASKS = {
    "localized-replacement": _brief(
        "Perform one surgical edit: replace the single selected tall thin flower inside the red selection rectangle with one upright seven-iron golf club. Change nothing else.",
        "Reference image 1 is the authoritative PlantStudio main-window screenshot (474 by 403). Match it exactly outside the red selection rectangle.",
        "plantstudio",
        "5:4",
        preservation_invariants=[
            "Keep the complete application window: title bar, menus, toolbar, plant canvas, species list, growth graph, age controls, tabs, and status bar in their original positions.",
            "Keep every unselected plant, label, number, icon, and pixel-scale spacing unchanged.",
            "Keep the Windows-era grey chrome, navy title bar, aliased pixel edges, limited palette, and low-resolution raster character.",
            "Do not change any text anywhere in the window.",
        ],
        regions=[{
            "name": "red selection rectangle",
            "change": "Remove the selected flower and draw one upright seven-iron golf club in the same narrow vertical footprint: grip at top, straight steel shaft, compact angled iron head near the bottom, rendered in the same pixel-art style.",
            "preserve": ["the red selection rectangle itself"],
        }],
        negative_constraints=[
            "No global redraw, modernization, smoothing, anti-aliasing upgrade, or invented UI.",
            "No golf ball, golfer, tee, flag, or any second golf object.",
        ],
        quality_checks=[
            "At 100 percent zoom, pixels outside the red rectangle look identical to the reference.",
            "The club reads clearly as a seven-iron at original scale.",
        ],
    ),
    "exact-copy-edit": _brief(
        "Change only the window title text to exactly the new copy given in EXACT COPY. Change nothing else anywhere in the window.",
        "Reference image 1 is the authoritative PlantStudio main-window screenshot (474 by 403). Everything except the title-bar text must match it exactly.",
        "plantstudio",
        "5:4",
        exact_copy=[{
            "region": "navy title bar text",
            "text": "PlantStudio - Prompt Length Test (11 plants)",
        }],
        preservation_invariants=[
            "Keep the title-bar font, size, weight, color, and left alignment identical to the original title rendering.",
            "Keep the window icon and the minimize, maximize, and close buttons unchanged.",
            "Keep every other pixel of the window unchanged, including all plants, lists, graphs, and controls.",
        ],
        negative_constraints=[
            "Do not translate, respell, re-kern, or truncate the new title.",
            "Do not modernize or smooth any part of the interface.",
        ],
        quality_checks=[
            "The title reads exactly: PlantStudio - Prompt Length Test (11 plants).",
            "Everything below the title bar is indistinguishable from the reference.",
        ],
    ),
    "object-removal": _brief(
        "Remove the five-pointed star completely from the label. Change nothing else.",
        "Reference image 1 is the authoritative blue Energy-Star-style label crop (308 by 316). It is the exact target except for the removed star.",
        "energy-star",
        "1:1",
        preservation_invariants=[
            "Keep the cursive palantir script exactly as drawn, including its baseline sweep.",
            "Keep the white arc, the horizontal divider, the THREAT REPORT INCLUDED text block, the blue field color, and the silver border unchanged.",
            "Fill the area the star occupied with clean continuous blue field matching the surrounding color and grain.",
        ],
        negative_constraints=[
            "No leftover star outline, ghost edges, smudge, or patch texture where the star was.",
            "Do not move, rescale, or re-kern any text.",
        ],
        quality_checks=[
            "No trace of the star remains at 100 percent zoom.",
            "The script and arc terminate exactly as in the reference.",
        ],
    ),
    "style-material": _brief(
        "Re-render the entire sticker as brushed gold metallic foil while keeping every shape, letterform, and layout element exactly in place.",
        "Reference image 1 is the authoritative Designed for Microsoft Windows XP case badge photo (389 by 508). Geometry and copy are the exact target; only surface material changes.",
        "xp-badge",
        "3:4",
        preservation_invariants=[
            "Keep the four-color window flag mark's shape and position; its panes may take on gold-tinted metallic shading but must remain four distinct panes.",
            "Keep the texts Designed for, Microsoft, Windows XP, and the registered and TM marks exactly as written, sized, and positioned.",
            "Keep the rounded-rectangle outline, divider line, and proportions unchanged.",
        ],
        style=[
            "Brushed gold metallic foil with fine horizontal brushing, subtle specular highlight from the upper left, and slightly darker gold in recesses.",
        ],
        negative_constraints=[
            "Do not change layout, spelling, kerning, or element sizes.",
            "No added ornament, sparkle, engraving, or texture beyond the brushed foil.",
        ],
        quality_checks=[
            "All text remains crisply legible at 100 percent zoom.",
            "The badge silhouette overlays the reference exactly.",
        ],
    ),
    "dense-multi-region": _brief(
        "Apply exactly three simultaneous edits to the sticker: replace the word Celeron with Pentium in the same letter style, recolor the lower band from blue to deep red, and add a thin solid black border around the outer sticker edge. Change nothing else.",
        "Reference image 1 is the authoritative Intel Inside Celeron sticker crop (1136 by 800). Match it exactly except for the three named edits.",
        "intel-crop",
        "3:2",
        regions=[
            {"name": "band word", "change": "Replace the word Celeron with Pentium using the same font, size, slant, color, and position.", "preserve": ["every other letter on the sticker"]},
            {"name": "lower band", "change": "Recolor the band background from blue to deep red while keeping its exact shape, size, and position.", "preserve": ["the text printed on the band"]},
            {"name": "outer edge", "change": "Add a thin solid black border following the sticker's outer edge.", "preserve": ["the sticker's outer dimensions"]},
        ],
        preservation_invariants=[
            "Keep the intel inside oval, its swirl gap, and its lettering exactly as in the reference.",
            "Keep the white field, print grain, and overall geometry unchanged.",
        ],
        negative_constraints=[
            "No fourth edit of any kind; no relayout, recentering, or cleanup.",
            "Do not alter letterforms other than the replaced word.",
        ],
        quality_checks=[
            "Exactly three visible differences from the reference exist.",
            "The replaced word reads Pentium in the original Celeron style.",
        ],
    ),
}

RESTATEMENT_TEMPLATES = [
    "Requirement {i} restated (pass {p}): {req}",
    "For absolute clarity, requirement {i} again (pass {p}): {req}",
    "Compliance reminder {i}.{p}: {req}",
    "Do not violate requirement {i} (pass {p}): {req}",
    "Verbatim requirement {i}, repetition {p}: {req}",
    "The following still applies unchanged ({i}.{p}): {req}",
]


def atomic_requirements(brief):
    reqs = [brief["objective"], brief["reference_role"]]
    reqs += brief.get("preservation_invariants", [])
    for region in brief.get("regions", []):
        reqs.append(f"In region {region['name']}: {region['change']}")
        for keep in region.get("preserve", []):
            reqs.append(f"In region {region['name']}, preserve {keep}.")
    for item in brief.get("exact_copy", []):
        reqs.append(f'The {item["region"]} must read exactly: "{item["text"]}"')
    reqs += brief.get("style", [])
    reqs += brief.get("asset_rules", [])
    reqs += brief.get("negative_constraints", [])
    reqs += brief.get("quality_checks", [])
    return reqs


def expand_brief(brief):
    """Deterministically restate the same requirements to near the ceiling."""
    expanded = json.loads(json.dumps({k: v for k, v in brief.items()}))
    reqs = atomic_requirements(brief)
    restatements = []
    pass_number = 1
    while True:
        candidate = dict(expanded)
        candidate["preservation_invariants"] = (
            list(brief.get("preservation_invariants", [])) + restatements
        )
        metrics = compile_edit_brief(strip_private(candidate)).metrics
        if metrics.approximate_tokens >= TARGET_MIN:
            if metrics.approximate_tokens > TARGET_MAX:
                raise AssertionError("overshot the near-ceiling window")
            expanded["preservation_invariants"] = candidate["preservation_invariants"]
            return expanded
        index = len(restatements)
        req = reqs[index % len(reqs)]
        template = RESTATEMENT_TEMPLATES[index % len(RESTATEMENT_TEMPLATES)]
        if index and index % len(reqs) == 0:
            pass_number += 1
        restatements.append(
            template.format(i=(index % len(reqs)) + 1, p=pass_number, req=req)
        )


def strip_private(brief):
    return {k: v for k, v in brief.items() if not k.startswith("_")}


def build():
    briefs_dir = OUT / "briefs"
    briefs_dir.mkdir(parents=True, exist_ok=True)
    summary = {}
    for task, brief in TASKS.items():
        for arm, payload in (("canonical", brief), ("near-ceiling", expand_brief(brief))):
            clean = strip_private(payload)
            compiled = compile_edit_brief(clean)
            (briefs_dir / f"{task}--{arm}.json").write_text(
                json.dumps(clean, indent=2) + "\n"
            )
            (briefs_dir / f"{task}--{arm}.prompt.txt").write_text(compiled.prompt + "\n")
            summary[f"{task}--{arm}"] = {
                "characters": compiled.metrics.characters,
                "approximate_tokens": compiled.metrics.approximate_tokens,
                "source": SOURCES[brief["_source"]],
            }
    (OUT / "briefs" / "metrics.json").write_text(json.dumps(summary, indent=2) + "\n")
    for key, value in summary.items():
        print(f"{key}: ~{value['approximate_tokens']} tokens ({value['characters']} chars)")


def _post(path, payload):
    request = urllib.request.Request(
        f"{COMFY}{path}", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(request, timeout=240) as response:
        return json.loads(response.read())


def upload_source(source_key):
    import mimetypes, uuid
    source = SOURCES[source_key]
    data = (ROOT / source["path"]).read_bytes()
    boundary = uuid.uuid4().hex
    name = f"issue18-{source_key}.png"
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; "
        f"filename=\"{name}\"\r\nContent-Type: image/png\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
    request = urllib.request.Request(
        f"{COMFY}/upload/image", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read())["name"]


def submit(task, arm):
    attempt_path = OUT / "attempts" / f"{task}--{arm}.json"
    attempt_path.parent.mkdir(parents=True, exist_ok=True)
    if attempt_path.exists():
        raise SystemExit(
            f"attempt record already exists for {task}/{arm}; "
            "possible prior billing — will not resubmit"
        )
    brief = json.loads((OUT / "briefs" / f"{task}--{arm}.json").read_text())
    source_key = TASKS[task]["_source"]
    uploaded = upload_source(source_key)
    graph = {
        "1": {"class_type": "LoadImage", "inputs": {"image": uploaded}},
        "2": {"class_type": "QwenImage3Render", "inputs": {
            "edit_brief_json": json.dumps(brief),
            "reference_images": ["1", 0],
        }},
        "3": {"class_type": "SaveImage", "inputs": {
            "images": ["2", 0], "filename_prefix": f"issue18/{task}--{arm}",
        }},
        "4": {"class_type": "SaveText", "inputs": {
            "text": ["2", 1], "filename_prefix": f"issue18/{task}--{arm}-meta",
            "format": "json",
        }},
    }
    attempt = {
        "task": task, "arm": arm, "provider": PROVIDER, "model": MODEL,
        "seed": SEED, "requested_outputs": 1,
        "source": SOURCES[source_key], "status": "submitted",
        "submitted_monotonic": time.monotonic(),
    }
    attempt_path.write_text(json.dumps(attempt, indent=2) + "\n")
    result = _post("/prompt", {"prompt": graph})
    attempt["prompt_id"] = result["prompt_id"]
    attempt_path.write_text(json.dumps(attempt, indent=2) + "\n")
    print("submitted", task, arm, "prompt_id", result["prompt_id"])
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline:
        time.sleep(5)
        with urllib.request.urlopen(
            f"{COMFY}/history/{result['prompt_id']}", timeout=30
        ) as response:
            history = json.loads(response.read())
        if result["prompt_id"] in history:
            entry = history[result["prompt_id"]]
            status = entry.get("status", {})
            attempt["status"] = status.get("status_str", "unknown")
            attempt["completed"] = status.get("completed", False)
            attempt["outputs"] = entry.get("outputs", {})
            attempt_path.write_text(json.dumps(attempt, indent=2) + "\n")
            print("finished", attempt["status"])
            return
    attempt["status"] = "ambiguous-timeout"
    attempt_path.write_text(json.dumps(attempt, indent=2) + "\n")
    raise SystemExit("ambiguous timeout: count this output as spent; do not retry")


def collect():
    import hashlib
    outputs_dir = OUT / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for attempt_path in sorted((OUT / "attempts").glob("*.json")):
        attempt = json.loads(attempt_path.read_text())
        key = f"{attempt['task']}--{attempt['arm']}"
        record = {
            "status": attempt.get("status"),
            "prompt_id": attempt.get("prompt_id"),
            "files": [],
            "usage": None,
        }
        for node_output in attempt.get("outputs", {}).values():
            for text in node_output.get("text", []):
                try:
                    meta = json.loads(text)
                except ValueError:
                    continue
                record["usage"] = meta.get("usage")
                meta_path = outputs_dir / f"{key}-meta.json"
                meta_path.write_text(json.dumps(meta, indent=2) + "\n")
            for kind in ("images", "files"):
                for item in node_output.get(kind, []):
                    if not isinstance(item, dict):
                        continue
                    query = urllib.parse.urlencode({
                        "filename": item["filename"],
                        "subfolder": item.get("subfolder", ""),
                        "type": item.get("type", "output"),
                    })
                    with urllib.request.urlopen(f"{COMFY}/view?{query}", timeout=120) as response:
                        data = response.read()
                    suffix = Path(item["filename"]).suffix
                    if suffix != ".png":
                        continue
                    local = outputs_dir / f"{key}{suffix}"
                    local.write_bytes(data)
                    record["files"].append({
                        "file": local.name,
                        "bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest(),
                    })
        manifest[key] = record
        print(key, record["status"], [f["file"] for f in record["files"]])
    (OUT / "collection-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def blind():
    import random, shutil
    review_dir = OUT / "blind-review"
    review_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    mapping = {}
    for task in TASKS:
        arms = ["canonical", "near-ceiling"]
        rng.shuffle(arms)
        for label, arm in zip(("A", "B"), arms):
            source = OUT / "outputs" / f"{task}--{arm}.png"
            if source.exists():
                shutil.copyfile(source, review_dir / f"{task}--{label}.png")
                mapping[f"{task}--{label}"] = arm
    (OUT / "blind-mapping.json").write_text(json.dumps(mapping, indent=2) + "\n")
    print("blind review set ready; mapping withheld from review until scores are recorded")


if __name__ == "__main__":
    import urllib.parse
    if sys.argv[1] == "build":
        build()
    elif sys.argv[1] == "submit":
        submit(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "collect":
        collect()
    elif sys.argv[1] == "blind":
        blind()
    else:
        raise SystemExit("unknown command")
