from seedance_icons.brief import compile_prompt


def test_prompt_has_stable_requirement_sections():
    prompt = compile_prompt(
        {
            "source_authority": "source",
            "style_lock": ["flat", "blue"],
            "motion": "rotate",
            "timing": "settle",
            "camera": "locked",
            "background": "green matte",
            "negative_constraints": ["no morph"],
        }
    )
    assert prompt.index("SOURCE AUTHORITY") < prompt.index("LOCKED STYLE") < prompt.index("MOTION")
    assert "- no morph" in prompt
