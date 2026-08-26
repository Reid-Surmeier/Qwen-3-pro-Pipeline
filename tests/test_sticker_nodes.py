import importlib.util
import unittest
from pathlib import Path


NODES_PATH = (
    Path(__file__).parents[1]
    / "comfyui_custom_nodes"
    / "qwen_sticker_tooling"
    / "nodes.py"
)


def load_nodes_module():
    spec = importlib.util.spec_from_file_location("qwen_sticker_tooling_nodes", NODES_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {NODES_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StickerNodeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes = load_nodes_module()

    def test_custom_pack_exposes_additive_sticker_nodes(self):
        self.assertEqual(
            set(self.nodes.NODE_CLASS_MAPPINGS),
            {
                "StickerMaskBands",
                "StickerPerspectiveWarp",
                "MaskedReferenceFidelityGate",
                "ArtworkFidelityGate",
            },
        )

    def test_mask_bands_have_explicit_pixel_ownership_outputs(self):
        node = self.nodes.StickerMaskBands
        inputs = node.INPUT_TYPES()["required"]

        self.assertEqual(
            set(inputs),
            {"sticker_masks", "threshold", "artwork_inset", "cutline_width", "contact_width"},
        )
        self.assertEqual(
            node.RETURN_NAMES,
            (
                "artwork_interior",
                "white_cutline",
                "contact_band",
                "editable_union",
                "immutable_outside",
            ),
        )

    def test_perspective_warp_keeps_image_and_mask_synchronized(self):
        node = self.nodes.StickerPerspectiveWarp
        inputs = node.INPUT_TYPES()["required"]

        self.assertEqual(
            set(inputs),
            {"artwork_images", "sticker_masks", "canvas_width", "canvas_height", "target_quad"},
        )
        self.assertEqual(node.RETURN_TYPES, ("IMAGE", "MASK"))

    def test_fidelity_gates_return_reports_and_fail_closed(self):
        self.assertEqual(
            self.nodes.MaskedReferenceFidelityGate.RETURN_NAMES,
            ("images", "fidelity_report"),
        )
        self.assertEqual(
            self.nodes.ArtworkFidelityGate.RETURN_NAMES,
            ("images", "artwork_report"),
        )


if __name__ == "__main__":
    unittest.main()
