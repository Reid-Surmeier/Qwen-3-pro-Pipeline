import json
from pathlib import Path

import pytest
from PIL import Image

from seedance_icons.strategy import (
    anchor_is_crisp,
    check_strategy,
    gate_record,
    submit_allowed,
)

MATTE = (0, 255, 0)


def make_crisp_anchor(path: Path, colors: int = 16, block: int = 4) -> None:
    """A hard-pixel anchor: small palette on a matte, exact integer blocks."""
    small = Image.new("RGB", (40, 40), MATTE)
    palette = [(i * 15 % 256, i * 40 % 256, i * 90 % 256) for i in range(1, colors + 1)]
    for y in range(10, 30):
        for x in range(10, 30):
            small.putpixel((x, y), palette[(x + y) % colors])
    small.resize((40 * block, 40 * block), Image.NEAREST).save(path)


def make_soft_anchor(path: Path) -> None:
    """Screenshot-texture pixels: thousands of unique colors."""
    image = Image.new("RGB", (160, 160), MATTE)
    for y in range(40, 120):
        for x in range(40, 120):
            image.putpixel((x, y), (x % 256, y % 256, (x * y) % 256))
    image.save(path)


GOOD_BRIEF = {
    "era_idiom_basis": (
        "Pokemon TCG duel coin toss: 8 flat poses each held 4 ticks, "
        "per pret/poketcg anims3.asm AnimData167"
    ),
    "real_reference": "references/ref-coin-spin.gif",
}
LONG_PROMPT = "beat " * 400
VIDEO_REFERENCE = ["https://example.test/references/ref-coin-spin.mp4"]


def write_reference(tmp_path: Path) -> Path:
    brief_dir = tmp_path / "evidence" / "briefs-v3"
    brief_dir.mkdir(parents=True)
    refs = tmp_path / "evidence" / "references"
    refs.mkdir()
    (refs / "ref-coin-spin.gif").write_bytes(b"GIF89a")
    return brief_dir / "gloria.json"


def write_motion_registry(tmp_path: Path) -> None:
    registry = (
        tmp_path
        / "docs"
        / "evidence"
        / "board-icons-test"
        / "references"
        / "provenance.json"
    )
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(
        json.dumps(
            {
                "assets": {
                    "ref-coin-spin.gif": {"motion_kind": "rotate"},
                    "ref-textbox-arrow-bob.gif": {"motion_kind": "translate"},
                }
            }
        )
    )


def test_good_plan_passes(tmp_path):
    brief_path = write_reference(tmp_path)
    anchor = tmp_path / "anchor.png"
    make_crisp_anchor(anchor)
    violations = check_strategy(
        GOOD_BRIEF,
        brief_path,
        LONG_PROMPT,
        str(anchor),
        str(anchor),
        video_references=VIDEO_REFERENCE,
    )
    assert violations == []


def test_malformed_reference_registry_stops_strategy_check(tmp_path):
    brief_path = write_reference(tmp_path)
    registry = (
        tmp_path
        / "docs"
        / "evidence"
        / "board-icons-test"
        / "references"
        / "provenance.json"
    )
    registry.parent.mkdir(parents=True)
    registry.write_text("not json")
    anchor = tmp_path / "anchor.png"
    make_crisp_anchor(anchor)

    with pytest.raises(json.JSONDecodeError):
        check_strategy(
            GOOD_BRIEF,
            brief_path,
            LONG_PROMPT,
            str(anchor),
            str(anchor),
            video_references=VIDEO_REFERENCE,
        )


def test_actual_video_reference_is_required(tmp_path):
    brief_path = write_reference(tmp_path)
    anchor = tmp_path / "anchor.png"
    make_crisp_anchor(anchor)

    violations = check_strategy(
        GOOD_BRIEF,
        brief_path,
        LONG_PROMPT,
        str(anchor),
        str(anchor),
        video_references=[],
    )

    assert any("video_reference is required" in violation for violation in violations)


def test_actual_video_reference_must_match_declared_motion(tmp_path):
    brief_path = write_reference(tmp_path)
    write_motion_registry(tmp_path)
    anchor = tmp_path / "anchor.png"
    make_crisp_anchor(anchor)
    brief = dict(GOOD_BRIEF, motion_kind="rotate")

    violations = check_strategy(
        brief,
        brief_path,
        LONG_PROMPT,
        str(anchor),
        str(anchor),
        video_references=[
            "https://example.test/references/ref-textbox-arrow-bob.mp4"
        ],
    )

    assert any("does not match real_reference" in violation for violation in violations)
    assert any("moves by 'translate'" in violation for violation in violations)


def test_matching_https_video_reference_passes_motion_gate(tmp_path):
    brief_path = write_reference(tmp_path)
    write_motion_registry(tmp_path)
    anchor = tmp_path / "anchor.png"
    make_crisp_anchor(anchor)
    brief = dict(GOOD_BRIEF, motion_kind="rotate")

    violations = check_strategy(
        brief,
        brief_path,
        LONG_PROMPT,
        str(anchor),
        str(anchor),
        video_references=VIDEO_REFERENCE,
    )

    assert violations == []


def test_missing_idiom_and_reference_fail(tmp_path):
    brief_path = write_reference(tmp_path)
    anchor = tmp_path / "anchor.png"
    make_crisp_anchor(anchor)
    violations = check_strategy(
        {},
        brief_path,
        LONG_PROMPT,
        str(anchor),
        str(anchor),
        video_references=VIDEO_REFERENCE,
    )
    assert any("era_idiom_basis" in v for v in violations)
    assert any("real_reference" in v for v in violations)


def test_unresolvable_reference_fails(tmp_path):
    brief_path = write_reference(tmp_path)
    anchor = tmp_path / "anchor.png"
    make_crisp_anchor(anchor)
    brief = dict(GOOD_BRIEF, real_reference="references/does-not-exist.gif")
    violations = check_strategy(
        brief,
        brief_path,
        LONG_PROMPT,
        str(anchor),
        str(anchor),
        video_references=VIDEO_REFERENCE,
    )
    assert any("does not resolve" in v for v in violations)


def test_corpus_citation_resolves(tmp_path):
    brief_path = write_reference(tmp_path)
    docs = tmp_path / "evidence" / "docs"
    docs.mkdir()
    (docs / "corpus.md").write_text("# corpus")
    anchor = tmp_path / "anchor.png"
    make_crisp_anchor(anchor)
    brief = dict(GOOD_BRIEF, real_reference="era corpus Tier B (docs/corpus.md B.4a)")
    violations = check_strategy(
        brief,
        brief_path,
        LONG_PROMPT,
        str(anchor),
        str(anchor),
        video_references=VIDEO_REFERENCE,
    )
    assert violations == []


def test_short_prompt_fails(tmp_path):
    brief_path = write_reference(tmp_path)
    anchor = tmp_path / "anchor.png"
    make_crisp_anchor(anchor)
    violations = check_strategy(
        GOOD_BRIEF,
        brief_path,
        "too short",
        str(anchor),
        str(anchor),
        video_references=VIDEO_REFERENCE,
    )
    assert any("compiled prompt" in v for v in violations)


def test_soft_anchor_fails(tmp_path):
    brief_path = write_reference(tmp_path)
    soft = tmp_path / "soft.png"
    make_soft_anchor(soft)
    violations = check_strategy(
        GOOD_BRIEF,
        brief_path,
        LONG_PROMPT,
        str(soft),
        str(soft),
        video_references=VIDEO_REFERENCE,
    )
    assert any("non-matte colors" in v for v in violations)


def test_missing_and_url_anchors_fail(tmp_path):
    brief_path = write_reference(tmp_path)
    violations = check_strategy(
        GOOD_BRIEF,
        brief_path,
        LONG_PROMPT,
        None,
        "https://example.com/a.png",
        video_references=VIDEO_REFERENCE,
    )
    assert any("first_frame anchor is required" in v for v in violations)
    assert any("last_frame must be a local crisp anchor" in v for v in violations)


def test_anchor_crisp_detects_blockiness(tmp_path):
    anchor = tmp_path / "crisp.png"
    make_crisp_anchor(anchor, block=2)
    ok, detail = anchor_is_crisp(anchor)
    assert ok, detail


def test_submit_refuses_without_gate():
    allowed, reason = submit_allowed({"estimated_cost_usd": "0.0756"})
    assert not allowed
    assert "no strategy_gate" in reason


def test_submit_refuses_failed_gate_without_waiver():
    plan = {"strategy_gate": gate_record(["compiled prompt is 5 words"], None)}
    allowed, _reason = submit_allowed(plan)
    assert not allowed


def test_submit_allows_pass_and_waiver():
    assert submit_allowed({"strategy_gate": gate_record([], None)})[0]
    waived = {"strategy_gate": gate_record(["x"], "owner-approved overlay experiment")}
    allowed, reason = submit_allowed(waived)
    assert allowed and "waived" in reason


def test_gate_record_round_trips_through_json():
    record = gate_record(["a"], "reason", "smooth")
    assert json.loads(json.dumps(record)) == record
    assert record["grammar"] == "smooth"


SMOOTH_BRIEF = {
    "grammar": "smooth",
    "motion_basis": (
        "Material Design ripple acknowledgment: radial ink expands from the touch "
        "point and fades, per the published motion spec"
    ),
    "real_reference": "references/ref-coin-spin.gif",
}


def test_smooth_grammar_accepts_soft_anchor(tmp_path):
    brief_path = write_reference(tmp_path)
    soft = tmp_path / "soft.png"
    make_soft_anchor(soft)
    violations = check_strategy(
        SMOOTH_BRIEF,
        brief_path,
        LONG_PROMPT,
        str(soft),
        str(soft),
        video_references=VIDEO_REFERENCE,
    )
    assert violations == []


def test_smooth_grammar_still_requires_basis_reference_and_anchors(tmp_path):
    brief_path = write_reference(tmp_path)
    violations = check_strategy(
        {"grammar": "smooth"},
        brief_path,
        "short",
        None,
        None,
        video_references=VIDEO_REFERENCE,
    )
    assert any("motion_basis" in v for v in violations)
    assert any("real_reference" in v for v in violations)
    assert any("compiled prompt" in v for v in violations)
    assert any("first_frame anchor is required" in v for v in violations)


def test_smooth_grammar_rejects_missing_anchor_file(tmp_path):
    brief_path = write_reference(tmp_path)
    missing = tmp_path / "nope.png"
    violations = check_strategy(
        SMOOTH_BRIEF,
        brief_path,
        LONG_PROMPT,
        str(missing),
        str(missing),
        video_references=VIDEO_REFERENCE,
    )
    assert any("anchor not found" in v for v in violations)


def test_default_grammar_is_retro_sprite(tmp_path):
    brief_path = write_reference(tmp_path)
    soft = tmp_path / "soft.png"
    make_soft_anchor(soft)
    brief = dict(GOOD_BRIEF)  # no grammar declared
    violations = check_strategy(
        brief,
        brief_path,
        LONG_PROMPT,
        str(soft),
        str(soft),
        video_references=VIDEO_REFERENCE,
    )
    assert any("non-matte colors" in v for v in violations)


def test_unknown_grammar_fails(tmp_path):
    brief_path = write_reference(tmp_path)
    anchor = tmp_path / "anchor.png"
    make_crisp_anchor(anchor)
    brief = dict(GOOD_BRIEF, grammar="freeform")
    violations = check_strategy(
        brief,
        brief_path,
        LONG_PROMPT,
        str(anchor),
        str(anchor),
        video_references=VIDEO_REFERENCE,
    )
    assert any("not recognized" in v for v in violations)


def test_smooth_grammar_accepts_era_basis_as_fallback(tmp_path):
    brief_path = write_reference(tmp_path)
    soft = tmp_path / "soft.png"
    make_soft_anchor(soft)
    brief = dict(GOOD_BRIEF, grammar="smooth")  # has era_idiom_basis, no motion_basis
    violations = check_strategy(
        brief,
        brief_path,
        LONG_PROMPT,
        str(soft),
        str(soft),
        video_references=VIDEO_REFERENCE,
    )
    assert violations == []
