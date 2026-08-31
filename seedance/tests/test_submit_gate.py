from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from seedance_icons.cli import cmd_submit
from seedance_icons.openrouter import request_digest
from seedance_icons.strategy import gate_record


def test_submit_refuses_a_payload_changed_after_planning(tmp_path: Path) -> None:
    request = {
        "model": "bytedance/seedance-2.0-mini",
        "prompt": "planned prompt",
        "duration": 12,
        "size": "480x480",
        "input_references": [
            {
                "type": "video_url",
                "video_url": {
                    "url": "https://example.test/ref-textbox-arrow-bob.mp4"
                },
            }
        ],
    }
    plan = {
        "request_sha256": request_digest(request),
        "estimated_cost_usd": "0.1361",
        "canonical_slug": "bytedance/seedance-2.0-mini-20260811",
        "strategy_gate": gate_record([], None),
    }
    (tmp_path / "plan.json").write_text(json.dumps(plan))

    request["input_references"] = []
    (tmp_path / "request.payload.json").write_text(json.dumps(request))

    with pytest.raises(SystemExit, match="Request payload changed since planning"):
        cmd_submit(Namespace(run=str(tmp_path), acknowledge_cost="0.1361"))
