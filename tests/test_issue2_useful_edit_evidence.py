import unittest
from pathlib import Path

from scripts.build_issue2_useful_edit_evidence import build_manifest


ROOT = Path("artifacts/issue-2/useful-edit")


class Issue2UsefulEditEvidenceTests(unittest.TestCase):
    def test_manifest_uses_original_source_and_keeps_visual_approval_pending(self):
        manifest = build_manifest(
            ROOT,
            ROOT / "useful-edit-comparison-v001.png",
        )

        authority = manifest["source_authority"]
        self.assertEqual(
            authority["reference_1"]["sha256"],
            "7c8e8767f72b72ce4fa4c888507f5ad060003a6cab7802f3e0deef44c8de35d7",
        )
        self.assertFalse(authority["prior_output_used_in_corrected_test"])
        self.assertEqual(manifest["generation"]["completed_outputs"], 4)
        self.assertEqual(manifest["generation"]["cumulative_issue_cost_usd"], 0.424)
        self.assertEqual(
            manifest["generation"]["effective_issue_output_count_after_run"],
            10,
        )
        self.assertEqual(
            manifest["assembly"]["outside_allowed_mask_changed_pixels"],
            0,
        )
        self.assertEqual(
            set(manifest["selection_masks"]),
            {
                "source_letter",
                "source_region",
                "target_letter",
                "target_region",
                "combined_region",
            },
        )
        self.assertEqual(
            [item["revision"] for item in manifest["assembly"]["experiments"]],
            [1, 2, 3, 4, 5],
        )
        self.assertEqual(len(manifest["assembly"]["options_tested"]), 5)
        for experiment in manifest["assembly"]["experiments"]:
            self.assertIn("sha256", experiment["workflow"])
            self.assertIn("sha256", experiment["plan"])
        self.assertEqual(manifest["human_visual_approval"], "pending")


if __name__ == "__main__":
    unittest.main()
