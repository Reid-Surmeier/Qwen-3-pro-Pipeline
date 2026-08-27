import json
from pathlib import Path

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


def write_reference(tmp_path: Path) -> Path:
    brief_dir = tmp_path / "evidence" / "briefs-v3"
    brief_dir.mkdir(parents=True)
    refs = tmp_path / "evidence" / "references"
    refs.mkdir()
    (refs / "ref-coin-spin.gif").write_bytes(b"GIF89a")
    return brief_dir / "gloria.json"


def test_good_plan_passes(tmp_path):
    brief_path = write_reference(tmp_path)
    anchor = tmp_path / "anchor.png"
    make_crisp_anchor(anchor)
    violations = check_strategy(GOOD_BRIEF, brief_path, LONG_PROMPT, str(anchor), str(anchor))
    assert violations == []


def test_missing_idiom_and_reference_fail(tmp_path):
    brief_path = write_reference(tmp_path)
    anchor = tmp_path / "anchor.png"
    make_crisp_anchor(anchor)
    violations = check_strategy({}, brief_path, LONG_PROMPT, str(anchor), str(anchor))
    assert any("era_idiom_basis" in v for v in violations)
    assert any("real_reference" in v for v in violations)


def test_unresolvable_reference_fails(tmp_path):
    brief_path = write_reference(tmp_path)
    anchor = tmp_path / "anchor.png"
    make_crisp_anchor(anchor)
    brief = dict(GOOD_BRIEF, real_reference="references/does-not-exist.gif")
    violations = check_strategy(brief, brief_path, LONG_PROMPT, str(anchor), str(anchor))
    assert any("does not resolve" in v for v in violations)


def test_corpus_citation_resolves(tmp_path):
    brief_path = write_reference(tmp_path)
    docs = tmp_path / "evidence" / "docs"
    docs.mkdir()
    (docs / "corpus.md").write_text("# corpus")
    anchor = tmp_path / "anchor.png"
    make_crisp_anchor(anchor)
    brief = dict(GOOD_BRIEF, real_reference="era corpus Tier B (docs/corpus.md B.4a)")
    violations = check_strategy(brief, brief_path, LONG_PROMPT, str(anchor), str(anchor))
    assert violations == []


def test_short_prompt_fails(tmp_path):
    brief_path = write_reference(tmp_path)
    anchor = tmp_path / "anchor.png"
    make_crisp_anchor(anchor)
    violations = check_strategy(GOOD_BRIEF, brief_path, "too short", str(anchor), str(anchor))
    assert any("compiled prompt" in v for v in violations)


def test_soft_anchor_fails(tmp_path):
    brief_path = write_reference(tmp_path)
    soft = tmp_path / "soft.png"
    make_soft_anchor(soft)
    violations = check_strategy(GOOD_BRIEF, brief_path, LONG_PROMPT, str(soft), str(soft))
    assert any("non-matte colors" in v for v in violations)


def test_missing_and_url_anchors_fail(tmp_path):
    brief_path = write_reference(tmp_path)
    violations = check_strategy(
        GOOD_BRIEF, brief_path, LONG_PROMPT, None, "https://example.com/a.png"
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
    record = gate_record(["a"], "reason")
    assert json.loads(json.dumps(record)) == record
