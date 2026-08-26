import json
import unittest

from scripts.build_issue2_useful_edit_workflows import (
    GUIDE_FILENAME,
    REFERENCE_FILENAME,
    build_plan,
    build_workflows,
)


class Issue2UsefulEditWorkflowTests(unittest.TestCase):
    def test_matched_workflows_use_original_source_and_change_only_guide_input(self):
        baseline, guided = build_workflows()

        self.assertEqual(baseline["1"]["inputs"]["image"], REFERENCE_FILENAME)
        self.assertEqual(guided["1"]["inputs"]["image"], REFERENCE_FILENAME)
        self.assertEqual(guided["2"]["inputs"]["image"], GUIDE_FILENAME)
        self.assertEqual(baseline["2"]["class_type"], "QwenImage3Render")
        self.assertEqual(guided["4"]["class_type"], "QwenImage3Render")
        self.assertEqual(
            baseline["2"]["inputs"]["edit_brief_json"],
            guided["4"]["inputs"]["edit_brief_json"],
        )
        serialized = json.dumps({"baseline": baseline, "guided": guided}).lower()
        self.assertNotIn("truth-social-inside-sticker", serialized)

        brief = json.loads(baseline["2"]["inputs"]["edit_brief_json"])
        self.assertEqual(brief["provider"], "openrouter")
        self.assertEqual(brief["model"], "qwen/qwen-image-3-pro")
        self.assertEqual(
            brief["output"],
            {
                "aspect_ratio": "3:2",
                "count": 2,
                "resolution": "1K",
                "seed": 20260826,
            },
        )
        self.assertEqual(baseline["2"]["inputs"]["reference_images"], ["1", 0])
        self.assertEqual(guided["4"]["inputs"]["reference_images"], ["3", 0])

    def test_plan_exhausts_but_does_not_exceed_the_effective_issue_cap(self):
        plan = build_plan()

        self.assertEqual(plan["reference_1"]["sha256"],
            "7c8e8767f72b72ce4fa4c888507f5ad060003a6cab7802f3e0deef44c8de35d7")
        self.assertEqual(plan["allowance"]["completed_before_corrected_test"], 6)
        self.assertEqual(plan["allowance"]["planned_outputs"], 4)
        self.assertEqual(plan["allowance"]["maximum_after_plan"], 10)
        self.assertEqual(plan["cost"]["pre_submission_estimate_usd"], 0.17)


if __name__ == "__main__":
    unittest.main()
