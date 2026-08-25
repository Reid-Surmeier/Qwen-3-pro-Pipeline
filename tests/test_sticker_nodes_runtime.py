import importlib.util
import json
import unittest
from pathlib import Path

try:
    import torch
except ModuleNotFoundError:  # The repository's lightweight test env omits Torch.
    torch = None


NODES_PATH = (
    Path(__file__).parents[1]
    / "comfyui_custom_nodes"
    / "qwen_sticker_tooling"
    / "nodes.py"
)


def load_nodes_module():
    spec = importlib.util.spec_from_file_location(
        "qwen_sticker_tooling_runtime_nodes", NODES_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {NODES_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(torch is not None, "Torch is exercised in the ComfyUI venv")
class StickerNodeRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes = load_nodes_module()

    def test_mask_bands_are_disjoint_and_cover_only_the_editable_union(self):
        mask = torch.zeros((1, 9, 9), dtype=torch.float32)
        mask[:, 3:6, 3:6] = 1.0

        artwork, cutline, contact, editable, immutable = (
            self.nodes.StickerMaskBands().build(mask, 0.5, 0, 1, 1)
        )

        self.assertEqual(int(artwork.sum().item()), 9)
        self.assertEqual(int(cutline.sum().item()), 16)
        self.assertEqual(int(contact.sum().item()), 24)
        self.assertEqual(int(editable.sum().item()), 49)
        self.assertTrue(torch.equal(editable + immutable, torch.ones_like(editable)))
        self.assertEqual(int((artwork * cutline).sum().item()), 0)
        self.assertEqual(int((cutline * contact).sum().item()), 0)

    def test_identity_quad_preserves_the_artwork_and_mask(self):
        image = torch.zeros((1, 4, 5, 3), dtype=torch.float32)
        image[:, 1:3, 1:4, 0] = 1.0
        mask = torch.zeros((1, 4, 5), dtype=torch.float32)
        mask[:, 1:3, 1:4] = 1.0

        warped_image, warped_mask = self.nodes.StickerPerspectiveWarp().warp(
            image,
            mask,
            5,
            4,
            "0,0,4,0,4,3,0,3",
        )

        self.assertTrue(torch.allclose(warped_mask, mask, atol=1e-5))
        self.assertTrue(torch.allclose(warped_image, image, atol=1e-5))

    def test_masked_reference_gate_rejects_one_changed_pixel_outside_mask(self):
        reference = torch.zeros((1, 4, 4, 3), dtype=torch.float32)
        candidate = reference.clone()
        candidate[:, 0, 0, :] = 1.0
        allowed = torch.zeros((1, 4, 4), dtype=torch.float32)
        allowed[:, 2, 2] = 1.0

        with self.assertRaisesRegex(RuntimeError, "exact_outside_mask"):
            self.nodes.MaskedReferenceFidelityGate().check(
                reference, candidate, allowed, 0.5, True, 1.0, 0
            )

    def test_artwork_gate_accepts_exact_owned_pixels_and_reports_metrics(self):
        approved = torch.zeros((1, 4, 4, 3), dtype=torch.float32)
        approved[:, 1:3, 1:3, :] = 0.75
        candidate = approved.clone()
        mask = torch.zeros((1, 4, 4), dtype=torch.float32)
        mask[:, 1:3, 1:3] = 1.0

        images, report = self.nodes.ArtworkFidelityGate().check(
            approved,
            candidate,
            mask,
            mask,
            0.5,
            True,
            0.0,
            0.999,
            0.99,
            0.999,
            0.5,
            0.001,
        )

        self.assertIs(images, candidate)
        parsed = json.loads(report)
        self.assertTrue(parsed["candidates"][0]["passed"])
        self.assertEqual(parsed["candidates"][0]["changed_artwork_pixels"], 0)

    def test_artwork_gate_rejects_changed_owned_pixel(self):
        approved = torch.zeros((1, 4, 4, 3), dtype=torch.float32)
        candidate = approved.clone()
        candidate[:, 2, 2, 0] = 1.0
        mask = torch.ones((1, 4, 4), dtype=torch.float32)

        with self.assertRaisesRegex(RuntimeError, "exact_artwork"):
            self.nodes.ArtworkFidelityGate().check(
                approved,
                candidate,
                mask,
                mask,
                0.5,
                True,
                1.0,
                -1.0,
                0.0,
                0.0,
                999.0,
                1.0,
            )


if __name__ == "__main__":
    unittest.main()
