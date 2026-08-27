import unittest

from qwen_ui_pipeline import (
    PromptBudgetExceeded,
    build_openrouter_request,
    compile_edit_brief,
)


class CompileEditBriefTests(unittest.TestCase):
    def test_compiles_ordered_sections_and_preserves_exact_copy(self):
        brief = {
            "objective": "Replace the flower with a golf club.",
            "reference_role": "Treat reference 1 as the authoritative screen.",
            "preservation_invariants": ["Keep the original composition."],
            "exact_copy": [
                {"region": "header", "text": "CLUB STUDIO"},
            ],
        }

        compiled = compile_edit_brief(brief)

        self.assertLess(
            compiled.prompt.index("[PRESERVATION INVARIANTS]"),
            compiled.prompt.index("[EXACT COPY]"),
        )
        self.assertEqual(compiled.prompt.count('"CLUB STUDIO"'), 1)
        self.assertFalse(compiled.metrics.over_budget)

    def test_builds_qwen_image_3_pro_edit_request(self):
        brief = {
            "objective": "Replace the flower with a golf club.",
            "reference_role": "Treat reference 1 as authoritative.",
            "preservation_invariants": ["Keep all panel geometry unchanged."],
            "exact_copy": [{"region": "header", "text": "CLUB STUDIO"}],
            "output": {
                "resolution": "2K",
                "aspect_ratio": "16:9",
                "seed": 1786,
                "count": 1,
            },
        }

        request = build_openrouter_request(
            brief,
            reference_urls=["data:image/png;base64,AAAA"],
        )

        self.assertEqual(request["model"], "qwen/qwen-image-3-pro")
        self.assertEqual(request["resolution"], "2K")
        self.assertEqual(request["aspect_ratio"], "16:9")
        self.assertEqual(request["seed"], 1786)
        self.assertEqual(request["input_references"][0]["type"], "image_url")
        self.assertIn('"CLUB STUDIO"', request["prompt"])

    def test_rejects_an_edit_brief_over_the_instruction_budget(self):
        brief = {
            "objective": "Replace the flower with a golf club. " * 200,
        }

        with self.assertRaisesRegex(PromptBudgetExceeded, "published 100-token budget"):
            compile_edit_brief(brief, budget_tokens=100)

    def test_rejects_more_references_than_qwen_image_3_accepts(self):
        brief = {"objective": "Edit the reference."}

        with self.assertRaisesRegex(ValueError, "at most 4 reference images"):
            build_openrouter_request(
                brief,
                reference_urls=[f"data:image/png;base64,{index}" for index in range(5)],
            )

    def test_openrouter_builder_never_silently_ignores_partner_controls(self):
        cases = {
            "negative_prompt": {"negative_prompt": "no gradients"},
            "prompt_extend": {"output": {"prompt_extend": True}},
            "watermark": {"output": {"watermark": True}},
            "size": {"output": {"size": "1024*1024"}},
        }

        for control, values in cases.items():
            brief = {"objective": "Render a monochrome interface.", **values}
            with self.subTest(control=control), self.assertRaisesRegex(
                ValueError, f"OpenRouter does not support {control}"
            ):
                build_openrouter_request(brief)

    def test_openrouter_builder_validates_count_and_seed_bounds(self):
        for output, message in (
            ({"count": 7}, "count"),
            ({"seed": -1}, "Seed"),
        ):
            with self.subTest(output=output), self.assertRaisesRegex(ValueError, message):
                build_openrouter_request(
                    {"objective": "Render a monochrome interface.", "output": output}
                )

    def test_compiles_spatial_style_and_negative_constraints(self):
        brief = {
            "objective": "Transform the central plant into a golf club.",
            "canvas": ["Preserve the 474 by 403 pixel composition."],
            "regions": [
                {
                    "name": "plant canvas",
                    "change": "Replace only the selected flower with a seven iron.",
                    "preserve": ["white background", "neighboring plants"],
                }
            ],
            "style": ["Late-1990s Windows desktop software."],
            "asset_rules": ["Use one isolated golf club silhouette."],
            "negative_constraints": ["Do not modernize the chrome."],
            "quality_checks": ["All 10 px labels remain legible."],
        }

        compiled = compile_edit_brief(brief)

        for heading in (
            "[CANVAS AND LAYOUT]",
            "[REGION EDITS]",
            "[STYLE SYSTEM]",
            "[ASSET RULES]",
            "[NEGATIVE CONSTRAINTS]",
            "[QUALITY GATE]",
        ):
            self.assertIn(heading, compiled.prompt)
        self.assertIn("plant canvas", compiled.prompt)
        self.assertIn("neighboring plants", compiled.prompt)


if __name__ == "__main__":
    unittest.main()
