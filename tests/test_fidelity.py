import json
import tempfile
import unittest
from pathlib import Path

from qwen_ui_pipeline.fidelity import (
    FidelityContractError,
    FidelityEvidenceError,
    FidelityResult,
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
    def test_result_cannot_claim_a_pass_with_invariant_violations(self):
        with self.assertRaisesRegex(FidelityEvidenceError, "contradicts"):
            FidelityResult(
                passed=True,
                region_changes=(),
                invariant_violations=((9, 0),),
            )

    def test_result_rejects_malformed_invariant_violation_evidence(self):
        for malformed in (17, "bad", ((False, 2),), ((1,),), ([1, 2],)):
            with self.subTest(malformed=malformed):
                with self.assertRaisesRegex(FidelityEvidenceError, "integer.*coordinates"):
                    FidelityResult(
                        passed=False,
                        region_changes=(),
                        invariant_violations=malformed,
                    )

    def test_passes_when_only_licensed_regions_changed(self):
        contract = parse_fidelity_contract(CONTRACT)
        baseline = canvas()
        candidate = with_pixel(with_pixel(baseline, 2, 1, BLUE), 6, 7, BLUE)

        result = verify_against_baseline(contract, candidate, baseline)

        self.assertTrue(result.passed)
        self.assertEqual(result.invariant_violations, ())
        self.assertEqual(result.change("title").changed_pixels, 1)
        self.assertEqual(result.change("footer").changed_pixels, 1)
        self.assertEqual(result.change("title").total_pixels, 6)

    def test_passes_an_untouched_candidate_with_no_region_changes(self):
        contract = parse_fidelity_contract(CONTRACT)
        baseline = canvas()

        result = verify_against_baseline(contract, baseline, baseline)

        self.assertTrue(result.passed)
        self.assertFalse(any(change.changed for change in result.region_changes))

    def test_reports_every_pixel_changed_outside_every_region(self):
        contract = parse_fidelity_contract(CONTRACT)
        baseline = canvas()
        candidate = with_pixel(with_pixel(baseline, 9, 0, BLUE), 0, 9, BLUE)

        result = verify_against_baseline(contract, candidate, baseline)

        self.assertFalse(result.passed)
        self.assertEqual(result.invariant_violations, ((9, 0), (0, 9)))
        self.assertEqual(result.invariant_violation_count, 2)
        self.assertEqual(result.first_violation, (9, 0))
        self.assertIn("first at (9, 0)", describe_result(result))

    def test_fails_closed_when_explicit_pixel_evidence_is_incomplete(self):
        contract = parse_fidelity_contract(CONTRACT)
        complete = canvas()
        incomplete = (10, 10, [RED] * 99)

        with self.assertRaisesRegex(FidelityEvidenceError, "declares 100 pixels"):
            verify_against_baseline(contract, incomplete, complete)

    def test_fails_closed_when_explicit_dimensions_are_not_exact_integers(self):
        contract = parse_fidelity_contract(CONTRACT)

        with self.assertRaisesRegex(FidelityEvidenceError, "positive integers"):
            verify_against_baseline(contract, (10.5, 10, [RED] * 100), canvas())

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

    def test_rejects_a_prompt_missing_required_evidence(self):
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
                                "promotion_rule": "z",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(FidelityContractError, "required_evidence"):
                load_correction_prompts(path)

    def test_rejects_a_non_object_corpus_root(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "corpus.json"
            path.write_text(json.dumps([]), encoding="utf-8")

            with self.assertRaisesRegex(FidelityContractError, "JSON object"):
                load_correction_prompts(path)

    def test_rejects_non_string_correction_list_items(self):
        prompt = {
            "id": "malformed-list",
            "source_correction": "x",
            "review_prompt": "y",
            "applies_to": ["*"],
            "required_evidence": ["screenshot"],
            "promotion_rule": "z",
        }
        for field, value in (("applies_to", None), ("required_evidence", {})):
            with self.subTest(field=field):
                malformed = json.loads(json.dumps(prompt))
                malformed[field] = [value]
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "corpus.json"
                    path.write_text(
                        json.dumps({"prompts": [malformed]}), encoding="utf-8"
                    )

                    with self.assertRaisesRegex(FidelityContractError, "non-empty strings"):
                        load_correction_prompts(path)


if __name__ == "__main__":
    unittest.main()
