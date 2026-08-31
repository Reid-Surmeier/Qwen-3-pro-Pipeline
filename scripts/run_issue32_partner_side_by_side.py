#!/usr/bin/env python3
"""Prepare and execute the bounded Issue 32 legacy/Partner paid comparison."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont

from qwen_ui_pipeline.comfyui_node import (
    QwenImage3Edit,
    QwenImage3Render,
    _partner_reference_records,
    _reference_data_urls,
)
from qwen_ui_pipeline.partner_controls import build_partner_edit_brief
from qwen_ui_pipeline.paid_attempts import PaidAttemptLedger
from qwen_ui_pipeline.providers.openrouter import (
    OpenRouterImageClient,
    build_openrouter_request,
    write_run_artifacts,
)


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "artifacts/issue-32/partner-side-by-side-v001"
SOURCE = ROOT / "artifacts/references/plantstudio-main-window.png"
PROMPT = (
    "Using Image 1, keep the complete PlantStudio interface and all existing "
    "pixel-art controls unchanged. Change only the blue title bar text from "
    "PlantStudio - Library of wildflowers (11 plants) to Partner Compatibility "
    "Test. Center the complete unchanged window on a plain light-gray square "
    "canvas without cropping or adding elements."
)
SEED = 2026082632
ARMS = ("legacy", "partner")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _artifact(path: Path, role: str) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": str(path.relative_to(ROOT)),
        "role": role,
        "sha256": _sha256(path),
        "bytes": path.stat().st_size,
    }
    if path.suffix.lower() == ".png":
        with Image.open(path) as image:
            record["size"] = list(image.size)
            record["mode"] = image.mode
    return record


def _redact_request(request: dict[str, Any]) -> dict[str, Any]:
    sanitized = json.loads(json.dumps(request))
    for reference in sanitized.get("input_references", []):
        image_url = reference.get("image_url")
        if isinstance(image_url, dict) and "url" in image_url:
            image_url["url"] = "[reference recorded separately]"
    return sanitized


def _comparison_inputs() -> dict[str, Any]:
    with Image.open(SOURCE) as source_image:
        rgb = source_image.convert("RGB")
        source_size = rgb.size
        pixels = np.asarray(rgb, dtype=np.float32) / 255.0
    image_batch = torch.from_numpy(pixels).unsqueeze(0)

    legacy_references = _reference_data_urls(image_batch)
    partner_records = _partner_reference_records(image_batch, None, None)
    partner_references = [record["data_url"] for record in partner_records]
    if legacy_references != partner_references:
        raise RuntimeError("Legacy and Partner nodes encoded different reference bytes")

    partner_brief = build_partner_edit_brief(
        provider="openrouter",
        model="qwen-image-3.0-pro",
        prompt=PROMPT,
        negative_prompt="",
        size_mode="custom",
        width=1024,
        height=1024,
        count=1,
        seed=SEED,
        prompt_extend=False,
        watermark=False,
        reference_dimensions=[source_size],
    )
    legacy_request = build_openrouter_request(
        partner_brief,
        reference_urls=legacy_references,
    )
    partner_request = build_openrouter_request(
        partner_brief,
        reference_urls=partner_references,
    )
    if legacy_request != partner_request:
        raise RuntimeError("Legacy and Partner nodes serialized different provider requests")

    reference_png = base64.b64decode(
        legacy_references[0].split(",", maxsplit=1)[1],
        validate=True,
    )
    return {
        "brief": partner_brief,
        "legacy_request": legacy_request,
        "partner_request": partner_request,
        "reference_png_sha256": _sha256_bytes(reference_png),
        "reference_record": {
            key: partner_records[0][key] for key in ("role", "width", "height", "sha256")
        },
    }


def _saved_response(slug: str) -> dict[str, Any]:
    response = _load_json(RUN / slug / "response.json")
    image_path = RUN / slug / "image-01.png"
    response["data"] = [
        {
            "b64_json": base64.b64encode(image_path.read_bytes()).decode("ascii"),
            "media_type": "image/png",
        }
    ]
    return response


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected a JSON object in {path}")
    return value


def _source_batch() -> torch.Tensor:
    with Image.open(SOURCE) as source_image:
        pixels = np.asarray(source_image.convert("RGB"), dtype=np.float32) / 255.0
    return torch.from_numpy(pixels).unsqueeze(0)


def _tensor_pixel_sha256(images: torch.Tensor) -> str:
    pixels = images.detach().cpu().numpy()
    rgb = (pixels.clip(0, 1) * 255).round().astype("uint8")
    return _sha256_bytes(rgb.tobytes())


def _image_pixel_sha256(path: Path) -> str:
    with Image.open(path) as image:
        return _sha256_bytes(np.asarray(image.convert("RGB")).tobytes())


def prepare() -> dict[str, Any]:
    PaidAttemptLedger(RUN).assert_unprepared(ARMS)
    inputs = _comparison_inputs()
    sanitized_legacy = _redact_request(inputs["legacy_request"])
    sanitized_partner = _redact_request(inputs["partner_request"])
    matrix = {
        "issue": 32,
        "source": _artifact(SOURCE, "immutable PlantStudio reference"),
        "prompt": PROMPT,
        "provider": "openrouter",
        "model": "qwen/qwen-image-3-pro",
        "seed": SEED,
        "resolution": "1K",
        "aspect_ratio": "1:1",
        "requested_outputs": 2,
        "arms": [
            {
                "name": "legacy QwenImage3Render requested arm",
                "requested_outputs": 1,
            },
            {
                "name": "Partner-compatible QwenImage3Edit requested arm",
                "requested_outputs": 1,
            },
        ],
        "paid_submission_method": (
            "direct OpenRouter client submission after proving the node request "
            "construction paths identical"
        ),
        "estimated_cost_usd": 0.083,
        "reference_node_encoding_sha256": inputs["reference_png_sha256"],
        "reference_node_encodings_identical": True,
        "sanitized_requests_identical": sanitized_legacy == sanitized_partner,
        "full_request_sha256": _sha256_bytes(_json_bytes(inputs["legacy_request"])),
        "stop_rule": "Stop after one output per arm; never retry an ambiguous call.",
        "paid_ci": False,
        "human_visual_approval": "required",
    }
    RUN.mkdir(parents=True, exist_ok=True)
    _write_json(RUN / "brief.json", inputs["brief"])
    _write_json(RUN / "legacy.request.json", sanitized_legacy)
    _write_json(RUN / "partner.request.json", sanitized_partner)
    _write_json(RUN / "plan.json", matrix)
    return matrix


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    return ImageFont.truetype(path, size) if path.exists() else ImageFont.load_default()


def _contact_sheet(legacy: Path, partner: Path, destination: Path) -> None:
    with Image.open(legacy) as left_image, Image.open(partner) as right_image:
        left = left_image.convert("RGB")
        right = right_image.convert("RGB")
    width = max(left.width, right.width)
    height = max(left.height, right.height)
    label_height = 64
    canvas = Image.new("RGB", (width * 2, height + label_height), "white")
    canvas.paste(left, ((width - left.width) // 2, (height - left.height) // 2))
    canvas.paste(
        right,
        (width + (width - right.width) // 2, (height - right.height) // 2),
    )
    draw = ImageDraw.Draw(canvas)
    font = _font(28)
    draw.rectangle((0, height, width * 2, height + label_height), fill="black")
    draw.text((18, height + 14), "Legacy request path", fill="white", font=font)
    draw.text(
        (width + 18, height + 14),
        "Partner request path",
        fill="white",
        font=font,
    )
    canvas.save(destination)


def _write_failed_comparison(
    plan: dict[str, Any], records: list[dict[str, Any]], reason: str
) -> None:
    _write_json(
        RUN / "comparison.json",
        {
            **plan,
            "completed_outputs": sum(item.get("completed_outputs", 0) for item in records),
            "possibly_billed_outputs": sum(
                item.get("possibly_billed_outputs", 0) for item in records
            ),
            "arms": records,
            "stopping_reason": reason,
        },
    )


def execute() -> dict[str, Any]:
    plan_path = RUN / "plan.json"
    if not plan_path.is_file():
        raise RuntimeError("Run --prepare and inspect plan.json before paid execution")
    ledger = PaidAttemptLedger(RUN)
    ledger.assert_unexecuted(ARMS)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    inputs = _comparison_inputs()
    if plan["full_request_sha256"] != _sha256_bytes(_json_bytes(inputs["legacy_request"])):
        raise RuntimeError("Prepared request no longer matches the executable request")

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is unavailable")
    client = OpenRouterImageClient(api_key)
    arms = [
        ("legacy", inputs["legacy_request"], "legacy request-construction path"),
        (
            "partner",
            inputs["partner_request"],
            "Partner request-construction path",
        ),
    ]
    records = []
    for slug, request, role in arms:
        request_sha256 = _sha256_bytes(_json_bytes(request))
        attempt = ledger.begin(slug, request_sha256=request_sha256, requested_outputs=1)
        try:
            response = client.generate(request)
        except Exception as error:
            ledger.update(
                slug,
                status="failed or ambiguous; not retried",
                error_type=type(error).__name__,
            )
            failure = {
                "arm": slug,
                "attempt_id": attempt["attempt_id"],
                "status": "failed without retry",
                "possibly_billed_outputs": 1,
                "error_type": type(error).__name__,
                "error": str(error),
            }
            records.append(failure)
            _write_failed_comparison(plan, records, "A request failed; it was not retried.")
            raise

        ledger.update(
            slug,
            status="response received; artifact write pending",
            response_created=response.get("created"),
            response_output_records=len(response.get("data", [])),
        )

        record = write_run_artifacts(
            RUN / slug,
            inputs["brief"],
            request,
            response,
            provenance={
                "issue": 32,
                "interface": role,
                "provider": "openrouter",
                "model": "qwen/qwen-image-3-pro",
                "source_path": str(SOURCE.relative_to(ROOT)),
                "source_sha256": _sha256(SOURCE),
                "reference_node_encoding_sha256": inputs["reference_png_sha256"],
                "full_request_sha256": plan["full_request_sha256"],
            },
        )
        if not record["outputs"]:
            ledger.update(
                slug,
                status="response contained no image; not retried",
                completed_outputs=0,
            )
            records.append(
                {
                    "arm": slug,
                    "attempt_id": attempt["attempt_id"],
                    "role": role,
                    "status": "response contained no image; not retried",
                    "requested_outputs": 1,
                    "completed_outputs": 0,
                    "possibly_billed_outputs": 1,
                    "usage": record["usage"],
                }
            )
            _write_failed_comparison(
                plan,
                records,
                "A response contained no image; it was not retried.",
            )
            raise RuntimeError(f"The {slug} response contained no image; stopping without retry")
        ledger.update(
            slug,
            status="completed",
            completed_outputs=len(record["outputs"]),
            output_sha256=[output["sha256"] for output in record["outputs"]],
        )
        records.append(
            {
                "arm": slug,
                "attempt_id": attempt["attempt_id"],
                "role": role,
                "status": "success",
                "requested_outputs": 1,
                "completed_outputs": len(record["outputs"]),
                "output": _artifact(
                    RUN / slug / record["outputs"][0]["file"],
                    f"{role} output",
                ),
                "usage": record["usage"],
            }
        )

    legacy_path = ROOT / records[0]["output"]["path"]
    partner_path = ROOT / records[1]["output"]["path"]
    _contact_sheet(legacy_path, partner_path, RUN / "side-by-side.png")
    with Image.open(legacy_path) as legacy_image, Image.open(partner_path) as partner_image:
        legacy_pixels = np.asarray(legacy_image.convert("RGB"))
        partner_pixels = np.asarray(partner_image.convert("RGB"))
    same_dimensions = legacy_pixels.shape == partner_pixels.shape
    different_pixels = (
        int(np.any(legacy_pixels != partner_pixels, axis=2).sum()) if same_dimensions else None
    )
    actual_costs = [
        item["usage"].get("cost")
        for item in records
        if isinstance(item.get("usage", {}).get("cost"), (int, float))
    ]
    comparison = {
        **plan,
        "completed_outputs": sum(item["completed_outputs"] for item in records),
        "possibly_billed_outputs": 0,
        "arms": records,
        "side_by_side": _artifact(RUN / "side-by-side.png", "labeled two-arm comparison"),
        "comparison": {
            "same_dimensions": same_dimensions,
            "same_output_sha256": (
                records[0]["output"]["sha256"] == records[1]["output"]["sha256"]
            ),
            "different_rgb_pixels": different_pixels,
        },
        "actual_cost_usd": round(sum(actual_costs), 6) if actual_costs else None,
        "stopping_reason": "Completed the pre-approved one-output pair; no follow-up run.",
    }
    _write_json(RUN / "comparison.json", comparison)
    return comparison


def verify_node_replay() -> dict[str, Any]:
    """Replay saved paid responses through both actual nodes without payment."""

    comparison = _load_json(RUN / "comparison.json")
    inputs = _comparison_inputs()
    source_batch = _source_batch()
    captured: dict[str, dict[str, Any]] = {}

    def replay(slug: str):
        def generate(request: dict[str, Any]) -> dict[str, Any]:
            captured[slug] = request
            return _saved_response(slug)

        return generate

    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "offline-replay"}):
        with patch.object(OpenRouterImageClient, "generate", side_effect=replay("legacy")):
            legacy_images, legacy_metadata_json = QwenImage3Render().render(
                json.dumps(inputs["brief"]), source_batch
            )
        with patch.object(OpenRouterImageClient, "generate", side_effect=replay("partner")):
            (
                partner_images,
                partner_brief_json,
                partner_metadata_json,
            ) = QwenImage3Edit().render(
                provider="openrouter",
                model="qwen-image-3.0-pro",
                prompt=PROMPT,
                negative_prompt="",
                width=1024,
                height=1024,
                count=1,
                seed=SEED,
                prompt_extend=False,
                watermark=False,
                size_mode="custom",
                image_1=source_batch,
            )

    expected_hash = comparison["full_request_sha256"]
    captured_hashes = {
        slug: _sha256_bytes(_json_bytes(request)) for slug, request in captured.items()
    }
    record = {
        "paid_requests": 0,
        "method": "saved provider-response replay through the actual node classes",
        "network_client": "mocked; no provider call",
        "legacy": {
            "node_class": "QwenImage3Render",
            "captured_request_sha256": captured_hashes["legacy"],
            "matches_paid_request": captured_hashes["legacy"] == expected_hash,
            "output_pixel_sha256": _tensor_pixel_sha256(legacy_images),
            "saved_output_pixel_sha256": _image_pixel_sha256(RUN / "legacy/image-01.png"),
            "metadata": json.loads(legacy_metadata_json),
        },
        "partner": {
            "node_class": "QwenImage3Edit",
            "captured_request_sha256": captured_hashes["partner"],
            "matches_paid_request": captured_hashes["partner"] == expected_hash,
            "output_pixel_sha256": _tensor_pixel_sha256(partner_images),
            "saved_output_pixel_sha256": _image_pixel_sha256(RUN / "partner/image-01.png"),
            "brief": json.loads(partner_brief_json),
            "metadata": json.loads(partner_metadata_json),
        },
        "captured_requests_identical": captured["legacy"] == captured["partner"],
        "outputs_match_saved_pixels": (
            _tensor_pixel_sha256(legacy_images) == _image_pixel_sha256(RUN / "legacy/image-01.png")
            and _tensor_pixel_sha256(partner_images)
            == _image_pixel_sha256(RUN / "partner/image-01.png")
        ),
        "limitation": (
            "The paid submissions used the proven-equal direct client payloads; "
            "the actual node classes were verified by offline response replay."
        ),
    }
    if not all(
        (
            record["legacy"]["matches_paid_request"],
            record["partner"]["matches_paid_request"],
            record["captured_requests_identical"],
            record["outputs_match_saved_pixels"],
        )
    ):
        raise RuntimeError("Offline node replay did not match the paid evidence")
    _write_json(RUN / "node-replay.json", record)
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--prepare", action="store_true")
    actions.add_argument("--execute", action="store_true")
    actions.add_argument("--verify-node-replay", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        result = prepare()
    elif args.execute:
        result = execute()
    else:
        result = verify_node_replay()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
