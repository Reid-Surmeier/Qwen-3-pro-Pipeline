import json
import tempfile
import unittest
from pathlib import Path

from qwen_ui_pipeline.fidelity import (
    FidelityContractError,
    compare_palettes,
    describe_palettes,
    FidelityEvidenceError,
    corrections_for,
    describe_result,
    load_correction_prompts,
    load_fidelity_contract,
    parse_fidelity_contract,
    verify_against_baseline,
)

CONTRACT = {
    "width": 10,
    "height": 10,
    "approvedBaseline": "baseline.png",
    "mutableRegions": [
        {"name": "title", "x": 1, "y": 1, "width": 3, "height": 2},
        {"name": "footer", "x": 5, "y": 6, "width": 4, "height": 3},
    ],
}

RED = (255, 0, 0, 255)
BLUE = (0, 0, 255, 255)


def canvas(width=10, height=10, colour=RED):
    return (width, height, [colour] * (width * height))


def with_pixel(image, x, y, colour):
    width, height, pixels = image
    pixels = list(pixels)
    pixels[y * width + x] = colour
    return (width, height, pixels)


class FidelityContractTests(unittest.TestCase):
    def test_parses_a_valid_contract(self):
        contract = parse_fidelity_contract(CONTRACT)

        self.assertEqual(contract.width, 10)
        self.assertEqual(contract.approved_baseline, "baseline.png")
        self.assertEqual([r.name for r in contract.mutable_regions], ["title", "footer"])
        self.assertEqual(contract.region("footer").right, 9)

    def test_rejects_a_region_extending_past_the_canvas(self):
        document = json.loads(json.dumps(CONTRACT))
        document["mutableRegions"][0]["width"] = 40

        with self.assertRaises(FidelityContractError):
            parse_fidelity_contract(document)

    def test_rejects_overlapping_regions_because_change_is_unattributable(self):
        document = json.loads(json.dumps(CONTRACT))
        document["mutableRegions"][1] = {"name": "overlap", "x": 2, "y": 1, "width": 4, "height": 3}

        with self.assertRaises(FidelityContractError):
            parse_fidelity_contract(document)

    def test_rejects_zero_area_and_missing_regions(self):
        zero_area = json.loads(json.dumps(CONTRACT))
        zero_area["mutableRegions"][0]["height"] = 0
        with self.assertRaises(FidelityContractError):
            parse_fidelity_contract(zero_area)

        empty = json.loads(json.dumps(CONTRACT))
        empty["mutableRegions"] = []
        with self.assertRaises(FidelityContractError):
            parse_fidelity_contract(empty)

    def test_loads_a_contract_from_disk(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fidelity-contract.json"
            path.write_text(json.dumps(CONTRACT), encoding="utf-8")

            self.assertEqual(load_fidelity_contract(path).height, 10)


class VerifyAgainstBaselineTests(unittest.TestCase):
    def test_passes_when_only_licensed_regions_changed(self):
        contract = parse_fidelity_contract(CONTRACT)
        baseline = canvas()
        candidate = with_pixel(with_pixel(baseline, 2, 1, BLUE), 6, 7, BLUE)

        result = verify_against_baseline(contract, candidate, baseline)

        self.assertTrue(result.passed)
        self.assertEqual(result.invariant_violations, 0)
        self.assertEqual(result.change("title").changed_pixels, 1)
        self.assertEqual(result.change("footer").changed_pixels, 1)
        self.assertEqual(result.change("title").total_pixels, 6)

    def test_passes_an_untouched_candidate_with_no_region_changes(self):
        contract = parse_fidelity_contract(CONTRACT)
        baseline = canvas()

        result = verify_against_baseline(contract, baseline, baseline)

        self.assertTrue(result.passed)
        self.assertFalse(any(change.changed for change in result.region_changes))

    def test_fails_on_a_single_pixel_changed_outside_every_region(self):
        contract = parse_fidelity_contract(CONTRACT)
        baseline = canvas()
        candidate = with_pixel(baseline, 9, 0, BLUE)

        result = verify_against_baseline(contract, candidate, baseline)

        self.assertFalse(result.passed)
        self.assertEqual(result.invariant_violations, 1)
        self.assertEqual(result.first_violation, (9, 0))
        self.assertIn("first at (9, 0)", describe_result(result))

    def test_fails_closed_when_the_images_disagree_on_size(self):
        contract = parse_fidelity_contract(CONTRACT)

        with self.assertRaises(FidelityEvidenceError):
            verify_against_baseline(contract, canvas(10, 10), canvas(10, 9))

    def test_fails_closed_when_images_do_not_match_the_contract_canvas(self):
        contract = parse_fidelity_contract(CONTRACT)

        with self.assertRaises(FidelityEvidenceError):
            verify_against_baseline(contract, canvas(12, 12), canvas(12, 12))


class CorrectionCorpusTests(unittest.TestCase):
    def setUp(self):
        self.corpus = Path(__file__).resolve().parents[1] / "qa" / "correction-replay.json"

    def test_repository_corpus_is_valid_and_complete(self):
        prompts = load_correction_prompts(self.corpus)

        self.assertGreaterEqual(len(prompts), 19)
        identifiers = {prompt["id"] for prompt in prompts}
        self.assertIn("no-reference-underlay", identifiers)
        self.assertIn("independent-elements", identifiers)

    def test_universal_prompts_apply_to_every_target(self):
        prompts = load_correction_prompts(self.corpus)

        selected = corrections_for(prompts, "some-new-window")

        self.assertIn("no-reference-underlay", selected)

    def test_rejects_a_prompt_missing_its_promotion_rule(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "corpus.json"
            path.write_text(
                json.dumps(
                    {
                        "prompts": [
                            {
                                "id": "incomplete",
                                "source_correction": "x",
                                "review_prompt": "y",
                                "applies_to": ["*"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(FidelityContractError):
                load_correction_prompts(path)

class PaletteComparisonTests(unittest.TestCase):
    def setUp(self):
        self.contract = parse_fidelity_contract(CONTRACT)

    def test_an_unchanged_candidate_reports_no_growth(self):
        baseline = canvas()

        comparisons = compare_palettes(self.contract, baseline, baseline)

        self.assertEqual(len(comparisons), 2)
        self.assertTrue(all(c.growth == 1.0 for c in comparisons))
        self.assertTrue(all(c.within_tolerance for c in comparisons))

    def test_flags_a_flat_region_redrawn_in_continuous_tone(self):
        baseline = canvas()
        width, height, pixels = baseline
        pixels = list(pixels)
        # Repaint the licensed title region with a distinct colour per pixel,
        # the signature of a continuous-tone redraw of a flat control.
        region = self.contract.region("title")
        shade = 0
        for y in range(region.y, region.bottom):
            for x in range(region.x, region.right):
                pixels[y * width + x] = (shade, 10, 20, 255)
                shade += 1
        candidate = (width, height, pixels)

        comparisons = compare_palettes(self.contract, candidate, baseline)
        title = next(c for c in comparisons if c.region == "title")

        self.assertFalse(title.within_tolerance)
        self.assertEqual(title.baseline_colours, 1)
        self.assertEqual(title.candidate_colours, 6)
        self.assertIn("lost bitmap character", describe_palettes(comparisons))

    def test_accepts_a_small_legitimate_palette_change(self):
        baseline = canvas()
        candidate = with_pixel(with_pixel(baseline, 2, 1, BLUE), 3, 2, (0, 128, 0, 255))

        title = next(
            c
            for c in compare_palettes(self.contract, candidate, baseline)
            if c.region == "title"
        )

        self.assertEqual(title.candidate_colours, 3)
        self.assertTrue(title.within_tolerance)

    def test_tolerance_is_configurable(self):
        baseline = canvas()
        candidate = with_pixel(with_pixel(baseline, 2, 1, BLUE), 3, 2, (0, 128, 0, 255))

        strict = next(
            c
            for c in compare_palettes(self.contract, candidate, baseline, max_growth=2.0)
            if c.region == "title"
        )

        self.assertFalse(strict.within_tolerance)

    def test_rejects_a_tolerance_that_would_fail_an_identical_palette(self):
        with self.assertRaises(FidelityContractError):
            compare_palettes(self.contract, canvas(), canvas(), max_growth=0.5)

    def test_fails_closed_on_a_size_mismatch(self):
        with self.assertRaises(FidelityEvidenceError):
            compare_palettes(self.contract, canvas(10, 10), canvas(10, 9))


if __name__ == "__main__":
    unittest.main()
