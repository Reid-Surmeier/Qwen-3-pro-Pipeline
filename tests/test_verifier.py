import unittest

from qwen_ui_pipeline.fidelity import (
    FidelityContract,
    FidelityResult,
    RegionChange,
    parse_fidelity_contract,
    verify_against_baseline,
)
from qwen_ui_pipeline.verifier import (
    DEFECT,
    MATCH,
    UNREADABLE,
    VerificationError,
    VisionClient,
    build_region_reviews,
    describe_verification,
    parse_region_verdict,
    route_findings,
    run_verification,
)

CONTRACT = parse_fidelity_contract(
    {
        "width": 10,
        "height": 10,
        "approvedBaseline": "baseline.png",
        "mutableRegions": [
            {"name": "title", "x": 1, "y": 1, "width": 3, "height": 2},
            {"name": "footer", "x": 5, "y": 6, "width": 4, "height": 3},
        ],
    }
)

RED = (255, 0, 0, 255)
BLUE = (0, 0, 255, 255)

CORPUS = [
    {
        "id": "no-reference-underlay",
        "source_correction": "Do not put an interactive overlay on top of the original screenshot.",
        "review_prompt": "Is any part of the original reference still acting as the background?",
        "applies_to": ["*"],
        "required_evidence": ["hidden-layer screenshots"],
        "promotion_rule": "Promote to a hide-layer test.",
    },
    {
        "id": "checkbox-label-overlap",
        "source_correction": "The on label is overlapped by the checkbox.",
        "review_prompt": "Does any control overlap its own label?",
        "applies_to": ["options-window"],
        "required_evidence": ["control inventory"],
        "promotion_rule": "Promote to a layout test.",
    },
]


def canvas(colour=RED, width=10, height=10):
    return (width, height, [colour] * (width * height))


def passing_fidelity():
    return FidelityResult(
        passed=True,
        region_changes=(
            RegionChange("title", 4, 6),
            RegionChange("footer", 2, 12),
        ),
        invariant_violations=(),
    )


class StubVisionClient(VisionClient):
    def __init__(self, responses, model="stub-vision"):
        super().__init__(model=model)
        self._responses = responses

    def review(self, review):
        self.calls.append(review)
        response = self._responses[review.region]
        if isinstance(response, Exception):
            raise response
        return response


class GateOrderingTests(unittest.TestCase):
    def test_refuses_to_consult_the_vision_layer_when_the_gate_failed(self):
        failed = FidelityResult(
            passed=False,
            region_changes=(),
            invariant_violations=tuple((index, 0) for index in range(17)),
        )
        client = StubVisionClient({})

        result = run_verification(
            CONTRACT, failed, canvas(), canvas(), client=client, correction_prompts=CORPUS
        )

        self.assertFalse(result.verified)
        self.assertEqual(result.status, "revision-required")
        self.assertEqual(client.calls, [])
        self.assertIn("17 invariant violation", result.reason)

    def test_verifies_only_when_both_layers_pass(self):
        client = StubVisionClient(
            {"title": {"verdict": MATCH, "confidence": 0.9}, "footer": {"verdict": MATCH}}
        )

        result = run_verification(
            CONTRACT, passing_fidelity(), canvas(), canvas(), client=client
        )

        self.assertTrue(result.verified)
        self.assertEqual(result.status, "verified")
        self.assertEqual(len(client.calls), 2)
        self.assertEqual(result.findings, ())

    def test_raises_when_the_contract_licenses_no_region(self):
        empty = FidelityContract(
            width=10, height=10, approved_baseline="baseline.png", mutable_regions=()
        )

        with self.assertRaises(VerificationError):
            run_verification(
                empty, passing_fidelity(), canvas(), canvas(), client=StubVisionClient({})
            )


class VerdictParsingTests(unittest.TestCase):
    def test_parses_a_localised_defect(self):
        verdict = parse_region_verdict(
            "title",
            {"verdict": DEFECT, "defect_class": "geometry", "coordinates": [4, 9], "confidence": 0.8},
        )

        self.assertEqual(verdict.verdict, DEFECT)
        self.assertEqual(verdict.coordinates, (4, 9))
        self.assertEqual(verdict.owning_stage, "assembly")

    def test_treats_unparsable_prose_as_unreadable(self):
        verdict = parse_region_verdict("title", "looks good to me!")

        self.assertEqual(verdict.verdict, UNREADABLE)
        self.assertTrue(verdict.is_failure)

    def test_treats_an_unrecognised_verdict_as_unreadable(self):
        verdict = parse_region_verdict("title", {"verdict": "probably fine"})

        self.assertEqual(verdict.verdict, UNREADABLE)

    def test_rejects_a_defect_the_reviewer_cannot_localise(self):
        verdict = parse_region_verdict("title", {"verdict": DEFECT, "defect_class": "geometry"})

        self.assertEqual(verdict.verdict, UNREADABLE)
        self.assertIn("localise", verdict.note)

    def test_discards_an_out_of_range_confidence(self):
        verdict = parse_region_verdict("title", {"verdict": MATCH, "confidence": 4.2})

        self.assertIsNone(verdict.confidence)

    def test_accepts_a_json_encoded_response(self):
        verdict = parse_region_verdict(
            "footer", '{"verdict": "defect", "defect_class": "interaction", "coordinates": [1, 2]}'
        )

        self.assertEqual(verdict.verdict, DEFECT)
        self.assertEqual(verdict.owning_stage, "interactive-build")


class ReviewConstructionTests(unittest.TestCase):
    def test_builds_one_review_per_region_with_applicable_questions(self):
        reviews = build_region_reviews(
            CONTRACT, canvas(), canvas(), correction_prompts=CORPUS, target="options-window"
        )

        self.assertEqual([review.region for review in reviews], ["title", "footer"])
        self.assertEqual(len(reviews[0].questions), 2)
        self.assertIn("hidden-layer screenshots", reviews[0].required_evidence)

    def test_selects_only_universal_prompts_for_an_unrelated_target(self):
        reviews = build_region_reviews(
            CONTRACT, canvas(), canvas(), correction_prompts=CORPUS, target="map-window"
        )

        self.assertEqual(len(reviews[0].questions), 1)


class FindingRoutingTests(unittest.TestCase):
    def test_routes_each_finding_to_its_owning_stage(self):
        client = StubVisionClient(
            {
                "title": {"verdict": DEFECT, "defect_class": "visual-state", "coordinates": [2, 2]},
                "footer": {"verdict": DEFECT, "defect_class": "interaction", "coordinates": [6, 7]},
            }
        )

        result = run_verification(
            CONTRACT, passing_fidelity(), canvas(), canvas(), client=client
        )
        routed = route_findings(result)

        self.assertFalse(result.verified)
        self.assertEqual(result.status, "revision-required")
        self.assertEqual(routed["render-pass"][0].region, "title")
        self.assertEqual(routed["interactive-build"][0].region, "footer")

    def test_routes_an_unknown_defect_class_to_triage(self):
        client = StubVisionClient(
            {
                "title": {"verdict": DEFECT, "defect_class": "mystery", "coordinates": [2, 2]},
                "footer": {"verdict": MATCH},
            }
        )

        result = run_verification(CONTRACT, passing_fidelity(), canvas(), canvas(), client=client)

        self.assertEqual(route_findings(result)["triage"][0].region, "title")

    def test_a_failed_reviewer_call_fails_closed(self):
        client = StubVisionClient(
            {"title": RuntimeError("model timeout"), "footer": {"verdict": MATCH}}
        )

        result = run_verification(CONTRACT, passing_fidelity(), canvas(), canvas(), client=client)

        self.assertFalse(result.verified)
        self.assertEqual(result.verdict_for("title").verdict, UNREADABLE)
        self.assertIn("model timeout", result.verdict_for("title").note)

    def test_describes_the_verdict_for_a_reviewer(self):
        client = StubVisionClient(
            {
                "title": {"verdict": DEFECT, "defect_class": "geometry", "coordinates": [2, 2]},
                "footer": {"verdict": MATCH},
            }
        )

        text = describe_verification(
            run_verification(CONTRACT, passing_fidelity(), canvas(), canvas(), client=client)
        )

        self.assertIn("status: revision-required", text)
        self.assertIn("region title: defect (geometry) at (2, 2) -> assembly", text)
        self.assertIn("region footer: match", text)


class EndToEndGateTests(unittest.TestCase):
    def test_a_real_invariant_violation_stops_the_run_before_any_spend(self):
        baseline = canvas()
        width, height, pixels = baseline
        pixels = list(pixels)
        pixels[0 * width + 9] = BLUE  # outside every licensed region
        candidate = (width, height, pixels)

        fidelity = verify_against_baseline(CONTRACT, candidate, baseline)
        client = StubVisionClient({})

        result = run_verification(CONTRACT, fidelity, candidate, baseline, client=client)

        self.assertFalse(fidelity.passed)
        self.assertFalse(result.verified)
        self.assertEqual(client.calls, [])

class IntentTests(unittest.TestCase):
    def test_supplies_the_licensed_change_to_the_reviewer(self):
        reviews = build_region_reviews(
            CONTRACT,
            canvas(),
            canvas(),
            intents={"title": "replace the numeral 11 with 24"},
        )

        self.assertEqual(reviews[0].intent, "replace the numeral 11 with 24")
        self.assertEqual(reviews[1].intent, "")

    def test_a_region_without_a_declared_intent_carries_none(self):
        reviews = build_region_reviews(CONTRACT, canvas(), canvas())

        self.assertTrue(all(review.intent == "" for review in reviews))

    def test_run_verification_threads_intent_through_to_the_client(self):
        client = StubVisionClient({"title": {"verdict": MATCH}, "footer": {"verdict": MATCH}})

        run_verification(
            CONTRACT,
            passing_fidelity(),
            canvas(),
            canvas(),
            client=client,
            intents={"footer": "swap the tab labels"},
        )

        intents = {call.region: call.intent for call in client.calls}
        self.assertEqual(intents["footer"], "swap the tab labels")


if __name__ == "__main__":
    unittest.main()
