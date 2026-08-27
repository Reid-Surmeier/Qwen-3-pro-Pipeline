import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "artifacts/issue-34/component-assembly-v004"


class Issue34ComponentEvidenceTests(unittest.TestCase):
    def test_run_records_repeated_internal_repair_without_new_paid_call(self):
        run = json.loads((RUN / "run.json").read_text(encoding="utf-8"))

        self.assertEqual(run["issue"], 34)
        self.assertFalse(run["paid_accounting"]["new_paid_run_submitted"])
        self.assertEqual(run["paid_accounting"]["cumulative_requested_outputs"], 8)
        self.assertEqual(run["paid_accounting"]["remaining_issue_allowance"], 2)
        self.assertEqual(len(run["outputs"]), 2)
        for output in run["outputs"]:
            checks = output["checks"]
            self.assertEqual(checks["outside_changed_rgba_pixels"], 0)
            self.assertEqual(checks["alpha_changed_pixels"], 0)
            self.assertTrue(checks["title_exact"])
            self.assertTrue(checks["footer_japanese_exact"])
            self.assertTrue(checks["components"]["bgm"]["byte_identical"])
            self.assertTrue(checks["components"]["skin"]["byte_identical"])
            structure = checks["output_structural_check"]
            self.assertTrue(structure["matches_expected"])
            self.assertEqual(
                structure["derived_counts"],
                {"bgm_sliders": 1, "effect_rows": 0, "skin_dropdowns": 1},
            )
            self.assertEqual(
                structure["exposed_cleanplate_pixels_below_threshold"], 0
            )
            self.assertGreaterEqual(
                structure["minimum_exposed_cleanplate_luminance"], 240
            )
            node_change = checks["node_induced_change_vs_normalized_donor"]
            self.assertGreater(
                node_change["inside_edit_region_changed_rgba_pixels"], 0
            )
            self.assertGreater(
                node_change["source_component_union_changed_rgba_pixels"], 0
            )

    def test_artifact_hashes_and_workflow_graphs_are_pinned(self):
        run = json.loads((RUN / "run.json").read_text(encoding="utf-8"))

        for artifact in [
            run["source"],
            *run["raw_baselines"],
            *run["normalized_donors"],
            *run["outputs"],
            *run["controls"],
            *run["workflows"],
        ]:
            path = ROOT / artifact["path"]
            self.assertTrue(path.is_file(), artifact["path"])
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(),
                artifact["sha256"],
            )

        for workflow in run["workflows"][:2]:
            graph = json.loads((ROOT / workflow["path"]).read_text(encoding="utf-8"))
            class_types = [node["class_type"] for node in graph.values()]
            self.assertIn("ImageCropV2", class_types)
            self.assertIn("ImageScale", class_types)
            self.assertIn("ImageCompositeMasked", class_types)
            self.assertIn("ReferenceRegionComposite", class_types)
            self.assertNotIn("QwenImage3Render", class_types)

    def test_raw_render_lineage_and_layout_match_executed_graphs(self):
        run = json.loads((RUN / "run.json").read_text(encoding="utf-8"))
        layout = run["layout"]

        self.assertEqual(
            [item["size"] for item in run["raw_baselines"]],
            [[2048, 1024], [2048, 1024]],
        )
        self.assertEqual(len(run["render_lineage"]), 2)
        for index, lineage in enumerate(run["render_lineage"], start=1):
            for path in lineage.values():
                self.assertTrue((ROOT / path).is_file(), path)
            workflow = json.loads(
                (ROOT / lineage["component_workflow"]).read_text(encoding="utf-8")
            )
            self.assertEqual(
                workflow["2"]["inputs"]["image"], f"raw_0000{index}_.png"
            )
            normalization = layout["donor_normalization"]
            self.assertEqual(workflow["3"]["class_type"], "ImageScale")
            self.assertEqual(workflow["3"]["inputs"]["width"], normalization["width"])
            self.assertEqual(
                workflow["3"]["inputs"]["height"], normalization["height"]
            )
            cleanplate = layout["cleanplate"]
            self.assertEqual(
                workflow["4"]["inputs"]["crop_region"],
                dict(
                    zip(
                        ("x", "y", "width", "height"),
                        cleanplate["source_region"],
                        strict=True,
                    )
                ),
            )
            self.assertEqual(
                [workflow["5"]["inputs"]["width"], workflow["5"]["inputs"]["height"]],
                cleanplate["target_region"][2:],
            )
            self.assertEqual(
                [workflow["6"]["inputs"]["x"], workflow["6"]["inputs"]["y"]],
                cleanplate["target_region"][:2],
            )
            for component_index, component in enumerate(layout["components"]):
                crop_node = str(7 + component_index * 2)
                composite_node = str(8 + component_index * 2)
                self.assertEqual(
                    workflow[crop_node]["inputs"]["crop_region"],
                    dict(
                        zip(
                            ("x", "y", "width", "height"),
                            component["source_region"],
                            strict=True,
                        )
                    ),
                )
                self.assertEqual(
                    [
                        workflow[composite_node]["inputs"]["x"],
                        workflow[composite_node]["inputs"]["y"],
                    ],
                    component["target"],
                )
            final_node = next(
                node
                for node in workflow.values()
                if node["class_type"] == "ReferenceRegionComposite"
            )
            self.assertEqual(
                final_node["inputs"]["region"],
                ",".join(str(value) for value in layout["final_edit_region"]),
            )

    def test_contact_sheet_and_individual_native_outputs_are_retained(self):
        self.assertTrue((RUN / "comparison-contact-sheet.png").is_file())
        self.assertTrue((RUN / "outputs/donor-1-component-assembly.png").is_file())
        self.assertTrue((RUN / "outputs/donor-2-component-assembly.png").is_file())
        self.assertEqual(len(list((RUN / "controls").glob("*.png"))), 4)


if __name__ == "__main__":
    unittest.main()
