"""Render one DIS cover-rework iteration through the live ComfyUI router.

Same proven path as dis-data-issue-pages-v001/render.py:
upload donor+art, LoadImage x2 -> ImageBatch -> QwenImage3Render -> SaveImage,
poll history, download outputs, record everything. Timeouts are recorded as
ambiguous (count as spent) and never resubmitted.

Usage: python3 render.py <iteration-slug>   # e.g. cover-v1
Reads briefs/<slug>.json, writes outputs/<slug>-*.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
import uuid

BASE = "http://10.255.255.254:8188"
RUN = "/home/reidsurmeier/.qwen-seedance-addon-wt/artifacts/runs/vibe-cover-dis-flip-v001"
POLL_SECONDS = 5
TIMEOUT_SECONDS = 900


def upload(path: str, name: str) -> str:
    boundary = uuid.uuid4().hex
    with open(path, "rb") as fh:
        data = fh.read()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{name}"\r\n'
        "Content-Type: image/png\r\n\r\n"
    ).encode() + data + (
        f"\r\n--{boundary}\r\n"
        'Content-Disposition: form-data; name="overwrite"\r\n\r\ntrue\r\n'
        f"--{boundary}--\r\n"
    ).encode()
    req = urllib.request.Request(
        f"{BASE}/upload/image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.load(resp)["name"]


def submit(workflow: dict) -> str:
    req = urllib.request.Request(
        f"{BASE}/prompt",
        data=json.dumps({"prompt": workflow}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.load(resp)["prompt_id"]


def wait(prompt_id: str) -> dict:
    deadline = time.time() + TIMEOUT_SECONDS
    while time.time() < deadline:
        with urllib.request.urlopen(f"{BASE}/history/{prompt_id}", timeout=60) as resp:
            history = json.load(resp)
        entry = history.get(prompt_id)
        if entry:
            status = entry.get("status", {})
            if status.get("status_str") == "error":
                return {"state": "error", "entry": entry}
            if entry.get("outputs"):
                return {"state": "done", "entry": entry}
            if status.get("completed"):
                return {"state": "done", "entry": entry}
        time.sleep(POLL_SECONDS)
    return {"state": "ambiguous-timeout", "entry": None}


def download(filename: str, subfolder: str, folder_type: str, dest: str) -> str:
    query = urllib.parse.urlencode(
        {"filename": filename, "subfolder": subfolder, "type": folder_type}
    )
    with urllib.request.urlopen(f"{BASE}/view?{query}", timeout=300) as resp:
        data = resp.read()
    with open(dest, "wb") as fh:
        fh.write(data)
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    slug = sys.argv[1]
    brief = json.load(open(f"{RUN}/briefs/{slug}.json"))
    donor = upload(f"{RUN}/inputs/cover-donor.png", f"disflip-{slug}-donor.png")
    art = upload(f"{RUN}/inputs/cover-art.png", f"disflip-{slug}-art.png")
    workflow = {
        "1": {"class_type": "LoadImage", "inputs": {"image": donor}},
        "2": {"class_type": "LoadImage", "inputs": {"image": art}},
        "3": {
            "class_type": "ImageBatch",
            "inputs": {"image1": ["1", 0], "image2": ["2", 0]},
        },
        "4": {
            "class_type": "QwenImage3Render",
            "inputs": {
                "edit_brief_json": json.dumps(brief, sort_keys=True),
                "reference_images": ["3", 0],
            },
        },
        "5": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": f"disflip-{slug}", "images": ["4", 0]},
        },
    }
    json.dump(workflow, open(f"{RUN}/outputs/{slug}-workflow.api.json", "w"), indent=1)
    submitted_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    prompt_id = submit(workflow)
    print(f"{slug}: submitted {prompt_id}", flush=True)
    result = wait(prompt_id)
    record = {
        "slug": slug,
        "prompt_id": prompt_id,
        "submitted_at": submitted_at,
        "state": result["state"],
        "uploaded_references": [donor, art],
        "outputs": [],
    }
    if result["state"] == "done":
        for node_output in result["entry"]["outputs"].values():
            for image in node_output.get("images", []):
                dest = f"{RUN}/outputs/{slug}-{image['filename']}"
                digest = download(
                    image["filename"], image.get("subfolder", ""), image.get("type", "output"), dest
                )
                record["outputs"].append({"file": dest.split("/")[-1], "sha256": digest})
    elif result["state"] == "error":
        record["error"] = json.dumps(result["entry"].get("status", {}))[:2000]
    json.dump(record, open(f"{RUN}/outputs/{slug}-record.json", "w"), indent=1)
    print(json.dumps(record, indent=1), flush=True)


if __name__ == "__main__":
    main()
