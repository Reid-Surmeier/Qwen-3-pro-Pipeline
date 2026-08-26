import json
import unittest

from scripts.build_issue2_assembly_experiment import (
    build_feather_plan,
    build_feather_workflow,
    build_plan,
    build_precise_plan,
    build_precise_workflow,
    build_source_blur_plan,
    build_source_blur_workflow,
    build_workflow,
)


class Issue2AssemblyExperimentTests(unittest.TestCase):
    def test_uses_source_crop_and_batches_baseline_before_guided_donor(self):
        workflow = build_workflow()

        self.assertEqual(
            workflow["1"]["inputs"]["image"],
            "issue2-useful-edit-intel-source-v001.png",
        )
        self.assertEqual(workflow["2"]["inputs"]["image"], "baseline-selected-donor-v001.png")
        self.assertEqual(workflow["3"]["inputs"]["image"], "guided-selected-donor-v001.png")
        self.assertEqual(workflow["4"]["inputs"]["images.image0"], ["2", 0])
        self.assertEqual(workflow["4"]["inputs"]["images.image1"], ["3", 0])
        self.assertEqual(workflow["23"]["class_type"], "RepeatImageBatch")
        self.assertEqual(workflow["23"]["inputs"]["amount"], 2)
        self.assertEqual(workflow["9"]["inputs"]["destination"], ["23", 0])
        self.assertEqual(workflow["19"]["inputs"]["destination"], ["23", 0])
        self.assertNotIn("truth-social-inside-sticker", json.dumps(workflow).lower())

    def test_exercises_color_key_and_grown_union_with_exact_fidelity_gates(self):
        workflow = build_workflow()

        self.assertEqual(workflow["6"]["class_type"], "StickerPerspectiveWarp")
        self.assertEqual(workflow["6"]["inputs"]["target_quad"], "0,0,1135,0,1135,799,0,799")
        self.assertEqual(workflow["8"]["class_type"], "ImageColorToMask")
        self.assertEqual(workflow["8"]["inputs"]["color"], 65280)
        self.assertEqual(workflow["17"]["class_type"], "MaskComposite")
        self.assertEqual(workflow["17"]["inputs"]["operation"], "or")
        self.assertEqual(workflow["18"]["class_type"], "GrowMask")
        self.assertEqual(workflow["18"]["inputs"]["expand"], 4)
        self.assertTrue(workflow["18"]["inputs"]["tapered_corners"])
        for node_id in ("10", "20"):
            self.assertEqual(workflow[node_id]["class_type"], "MaskedReferenceFidelityGate")
            self.assertTrue(workflow[node_id]["inputs"]["exact_outside_mask"])

    def test_plan_keeps_human_visual_approval_pending(self):
        plan = build_plan()

        self.assertEqual(plan["paid_generation_outputs"], 0)
        self.assertEqual(
            [donor["condition"] for donor in plan["donor_order"]],
            ["baseline", "guided"],
        )
        self.assertEqual(plan["acceptance"]["human_visual_approval"], "pending")

    def test_feathered_variant_keeps_soft_pixels_inside_a_larger_allowed_mask(self):
        workflow = build_feather_workflow()

        self.assertEqual(workflow["24"]["class_type"], "GrowMask")
        self.assertEqual(workflow["24"]["inputs"]["expand"], 8)
        self.assertEqual(workflow["25"]["class_type"], "FeatherMask")
        self.assertEqual(
            {key: workflow["25"]["inputs"][key] for key in ("left", "top", "right", "bottom")},
            {"left": 8, "top": 8, "right": 8, "bottom": 8},
        )
        self.assertEqual(workflow["26"]["inputs"]["mask"], ["25", 0])
        self.assertEqual(workflow["27"]["inputs"]["allowed_masks"], ["24", 0])
        self.assertTrue(workflow["27"]["inputs"]["exact_outside_mask"])

        plan = build_feather_plan()
        self.assertEqual(plan["revision"], 3)
        self.assertEqual(plan["selected_experiment"]["name"], "feathered-union")

    def test_source_blur_variant_uses_source_blur_and_guided_target_donor(self):
        workflow = build_source_blur_workflow()

        self.assertEqual(workflow["2"]["inputs"]["image"], "guided-selected-donor-v001.png")
        self.assertEqual(workflow["9"]["class_type"], "ImageBlur")
        self.assertEqual(workflow["10"]["inputs"]["source"], ["9", 0])
        self.assertEqual(workflow["15"]["inputs"]["source"], ["4", 0])
        self.assertEqual(workflow["17"]["inputs"]["allowed_masks"], ["16", 0])
        self.assertTrue(workflow["17"]["inputs"]["exact_outside_mask"])

        plan = build_source_blur_plan()
        self.assertEqual(plan["revision"], 4)
        self.assertEqual(plan["selected_experiment"]["name"], "source-blur-guided")

    def test_precise_variant_limits_source_replacement_to_the_selected_glyph(self):
        workflow = build_precise_workflow()

        self.assertEqual(workflow["5"]["inputs"]["image"], "issue2-useful-edit-source-e-v001.png")
        self.assertEqual(workflow["7"]["inputs"]["expand"], 4)
        self.assertEqual(workflow["13"]["inputs"]["mask"], ["8", 0])
        self.assertEqual(workflow["14"]["inputs"]["mask"], ["12", 0])
        self.assertEqual(workflow["16"]["inputs"]["allowed_masks"], ["15", 0])

        plan = build_precise_plan()
        self.assertEqual(plan["revision"], 5)
        self.assertEqual(plan["selected_experiment"]["name"], "precise-guided")
        self.assertEqual(
            plan["selected_experiment"]["result"][
                "outside_allowed_mask_changed_pixels"
            ],
            0,
        )
        self.assertEqual(
            plan["selected_experiment"]["result"]["human_visual_approval"],
            "pending",
        )


if __name__ == "__main__":
    unittest.main()
