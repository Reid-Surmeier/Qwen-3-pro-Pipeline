import hashlib
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "artifacts/references/ro-desktop-b/control-inventory.json"
ASSEMBLY = ROOT / "godot/data/image-79-assembly-manifest.json"
CONTROL_SPEC = ROOT / "godot/data/image-79-control-spec.json"


class Image79FinalAssemblyTests(unittest.TestCase):
    def test_all_239_source_controls_have_unique_stable_assembly_ids(self):
        inventory = json.loads(INVENTORY.read_text())
        assembly = json.loads(ASSEMBLY.read_text())

        self.assertEqual(inventory["total_controls"], 239)
        self.assertEqual(assembly["source_control_count"], 239)
        self.assertEqual(len(assembly["controls"]), 239)
        stable_ids = [entry["stable_id"] for entry in assembly["controls"]]
        self.assertEqual(len(stable_ids), len(set(stable_ids)))
        self.assertEqual(
            [entry["source_rect"] for entry in assembly["controls"]],
            [entry["rect"] for entry in inventory["controls"]],
        )

    def test_every_source_control_names_a_production_owner(self):
        assembly = json.loads(ASSEMBLY.read_text())
        control_spec = json.loads(CONTROL_SPEC.read_text())
        window_ids = {window["id"] for window in control_spec["windows"]}
        production_controls = {
            control["id"]
            for window in control_spec["windows"]
            for control in window["controls"]
        }

        self.assertEqual(set(assembly["window_ids"]), window_ids)
        for entry in assembly["controls"]:
            self.assertIn(entry["window_id"], window_ids)
            self.assertIn(
                entry["owner_kind"],
                {"control", "surface", "window_drag", "state_surface", "baked_visual"},
            )
            if entry["owner_kind"] in {"control", "surface"}:
                self.assertIn(entry["control_id"], production_controls)
            self.assertNotIn("prototype", entry["production_owner"])

    def test_final_assembly_manifest_is_bound_to_the_reference(self):
        inventory = json.loads(INVENTORY.read_text())
        assembly = json.loads(ASSEMBLY.read_text())

        self.assertEqual(assembly["schema_version"], 1)
        self.assertEqual(
            assembly["reference_sha256"],
            "f4844fa9030b31b233f43244290f729db105f7256e0c0a6e889f0889bb88366f",
        )
        self.assertEqual(assembly["viewport"], [1536, 1024])
        self.assertEqual(assembly["generation_requests"], 0)
        self.assertEqual(
            assembly["source_inventory_sha256"],
            hashlib.sha256(INVENTORY.read_bytes()).hexdigest(),
        )
        expected_counts = {}
        for entry in inventory["controls"]:
            window_id = entry["window"].replace("-", "_")
            expected_counts[window_id] = expected_counts.get(window_id, 0) + 1
        self.assertEqual(assembly["source_counts_by_window"], expected_counts)


if __name__ == "__main__":
    unittest.main()
