"""Planning-only ComfyUI nodes. Paid submission remains an explicit CLI gate."""

from __future__ import annotations

import json
from decimal import Decimal

from seedance_icons.brief import compile_prompt
from seedance_icons.capabilities import ModelProfile, estimate_cost, validate_request


class SeedanceIconPrompt:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "source_authority": ("STRING", {"multiline": True}),
                "style_lock": ("STRING", {"multiline": True}),
                "motion": ("STRING", {"multiline": True}),
                "timing": ("STRING", {"multiline": True}),
                "camera": ("STRING", {"multiline": True}),
                "background": ("STRING", {"multiline": True}),
                "negative_constraints": ("STRING", {"multiline": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("compiled_prompt",)
    FUNCTION = "compile"
    CATEGORY = "Seedance/Icon Animation"

    def compile(
        self, source_authority, style_lock, motion, timing, camera, background, negative_constraints
    ):
        brief = {
            "source_authority": source_authority,
            "style_lock": style_lock,
            "motion": motion,
            "timing": timing,
            "camera": camera,
            "background": background,
            "negative_constraints": negative_constraints,
        }
        return (compile_prompt(brief),)


class SeedancePlanRequest:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "compiled_prompt": ("STRING", {"multiline": True}),
                "capability_profile_json": ("STRING", {"multiline": True}),
                "model": (
                    ["bytedance/seedance-2.0-mini", "bytedance/seedance-2.5"],
                    {"default": "bytedance/seedance-2.0-mini"},
                ),
                "duration": ("INT", {"default": 6, "min": 1, "max": 30}),
                "size": ("STRING", {"default": "720x720"}),
                "generate_audio": ("BOOLEAN", {"default": False}),
                "seed": ("INT", {"default": 1, "min": 0}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("request_json", "canonical_model", "estimated_cost_usd")
    FUNCTION = "plan"
    CATEGORY = "Seedance/Icon Animation"
    OUTPUT_NODE = True

    def plan(
        self, compiled_prompt, capability_profile_json, model, duration, size, generate_audio, seed
    ):
        raw = json.loads(capability_profile_json)
        if "models" in raw:
            raw = next(item for item in raw["models"] if item["id"] == model)
        profile = ModelProfile.from_api(raw)
        request = {
            "model": model,
            "prompt": compiled_prompt,
            "duration": duration,
            "size": size,
            "generate_audio": generate_audio,
            "seed": seed,
        }
        validate_request(request, profile)
        cost: Decimal = estimate_cost(request, profile)
        return (json.dumps(request, indent=2), profile.canonical_slug, str(cost))


NODE_CLASS_MAPPINGS = {
    "SeedanceIconPrompt": SeedanceIconPrompt,
    "SeedancePlanRequest": SeedancePlanRequest,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SeedanceIconPrompt": "Seedance Icon Prompt",
    "SeedancePlanRequest": "Seedance Plan Request (No Submit)",
}
