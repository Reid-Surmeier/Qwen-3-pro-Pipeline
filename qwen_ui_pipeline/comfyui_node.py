"""ComfyUI node for Qwen Image 3 through OpenRouter."""

from __future__ import annotations

import base64
import io
import json
import os
from typing import Any

from .providers.alibaba import AlibabaImageClient
from .providers.openrouter import OpenRouterImageClient
from .providers.router import generate_with_provider


def _reference_data_urls(reference_images: Any) -> list[str]:
    from PIL import Image

    output = []
    if reference_images is None:
        return output
    for tensor in reference_images[:4]:
        pixels = tensor.detach().cpu().numpy()
        pixels = (pixels.clip(0, 1) * 255).round().astype("uint8")
        image = Image.fromarray(pixels, mode="RGB")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        output.append(f"data:image/png;base64,{encoded}")
    return output


def _response_tensors(response: dict[str, Any]):
    import numpy
    import torch
    from PIL import Image

    tensors = []
    for item in response.get("data", []):
        if not isinstance(item, dict) or not isinstance(item.get("b64_json"), str):
            continue
        image_bytes = base64.b64decode(item["b64_json"], validate=True)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        pixels = numpy.asarray(image, dtype=numpy.float32) / 255.0
        tensors.append(torch.from_numpy(pixels).unsqueeze(0))
    if not tensors:
        raise RuntimeError("Qwen Image 3 response did not contain an image")
    return torch.cat(tensors, dim=0)


class QwenImage3Render:
    """Execute a structured Edit Brief without exposing credentials in a workflow."""

    CATEGORY = "Qwen UI Pipeline"
    FUNCTION = "render"
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "run_metadata")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "edit_brief_json": (
                    "STRING",
                    {"multiline": True, "default": '{"objective": "Describe the edit"}'},
                ),
            },
            "optional": {"reference_images": ("IMAGE",)},
        }

    def render(self, edit_brief_json: str, reference_images=None):
        brief = json.loads(edit_brief_json)
        if not isinstance(brief, dict):
            raise ValueError("Edit Brief must be a JSON object")
        openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
        alibaba_key = os.environ.get("DASHSCOPE_API_KEY", "")
        result = generate_with_provider(
            brief,
            reference_urls=_reference_data_urls(reference_images),
            openrouter_client=(
                OpenRouterImageClient(openrouter_key) if openrouter_key else None
            ),
            alibaba_client=(AlibabaImageClient(alibaba_key) if alibaba_key else None),
        )
        request = result.request
        response = result.response
        if result.provider == "openrouter":
            resolution = request["resolution"]
            aspect_ratio = request["aspect_ratio"]
            count = request["n"]
            seed = request.get("seed")
        else:
            parameters = request["parameters"]
            resolution = parameters["size"]
            aspect_ratio = brief.get("output", {}).get("aspect_ratio")
            count = parameters["n"]
            seed = parameters.get("seed")
        metadata = json.dumps(
            {
                "provider": result.provider,
                "model": request["model"],
                "resolution": resolution,
                "aspect_ratio": aspect_ratio,
                "count": count,
                "seed": seed,
                "usage": response.get("usage", {}),
            },
            sort_keys=True,
        )
        return (_response_tensors(response), metadata)


class ReferenceRegionComposite:
    """Copy one generated region onto an otherwise untouched reference image."""

    CATEGORY = "Qwen UI Pipeline"
    FUNCTION = "composite"
    RETURN_TYPES = ("IMAGE",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "reference_images": ("IMAGE",),
                "generated_images": ("IMAGE",),
                "region": (
                    "STRING",
                    {"default": "0,0,64,64", "multiline": False},
                ),
            },
            "optional": {"reference_masks": ("MASK",)},
        }

    def composite(
        self,
        reference_images,
        generated_images,
        region: str,
        reference_masks=None,
    ):
        import torch
        import torch.nn.functional as functional

        try:
            x, y, width, height = (int(value.strip()) for value in region.split(","))
        except (TypeError, ValueError) as error:
            raise ValueError("Region must be x,y,width,height") from error
        if min(x, y, width, height) < 0 or width == 0 or height == 0:
            raise ValueError("Region coordinates must be non-negative with positive size")

        # ComfyUI's SaveImage floors float-to-byte conversion. Centering each
        # reference value inside its original byte bucket prevents widespread
        # one-level drift after a LoadImage -> SaveImage round trip.
        reference = (
            ((reference_images[:1] * 255.0).round() + 0.25).clamp(0, 255) / 255.0
        )
        target_height, target_width = reference.shape[1:3]
        if x + width > target_width or y + height > target_height:
            raise ValueError("Region extends outside the reference image")

        generated = functional.interpolate(
            generated_images.movedim(-1, 1),
            size=(target_height, target_width),
            mode="nearest",
        ).movedim(1, -1)
        output = reference.expand(generated.shape[0], -1, -1, -1).clone()
        output[:, y : y + height, x : x + width, :] = generated[
            :, y : y + height, x : x + width, :
        ]
        if reference_masks is not None:
            alpha = 1.0 - reference_masks[:1]
            if alpha.shape[1:] != (target_height, target_width):
                alpha = functional.interpolate(
                    alpha.unsqueeze(1),
                    size=(target_height, target_width),
                    mode="nearest",
                ).squeeze(1)
            # Center values inside their byte buckets so SaveImage's floor
            # reproduces the source alpha exactly.
            alpha = ((alpha * 255.0).round() + 0.25).clamp(0, 255) / 255.0
            alpha = alpha.expand(output.shape[0], -1, -1).unsqueeze(-1)
            output = torch.cat((output[..., :3], alpha), dim=-1)
        return (output,)


NODE_CLASS_MAPPINGS = {
    "QwenImage3Render": QwenImage3Render,
    "ReferenceRegionComposite": ReferenceRegionComposite,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "QwenImage3Render": "Qwen Image 3 Render",
    "ReferenceRegionComposite": "Reference Region Composite",
}
