"""Command-line entry point for compiling and executing Render Passes."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import mimetypes
from pathlib import Path
from typing import Sequence

from .comfyui_workflow import build_comfyui_api_workflow, build_comfyui_assembly_workflow
from .prompt_manifest import compile_edit_brief
from .providers.openrouter import write_run_artifacts
from .providers.alibaba import build_alibaba_request
from .workflow_contract import (
    WorkflowContractError,
    validate_assembly_gate,
    validate_workflow_contract,
    verify_approved_output_hash,
    verify_reference_hash,
)


def image_data_url(path: Path) -> str:
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


def _load_brief(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Edit Brief must be a JSON object")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="qwen-ui-pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    compile_parser = subparsers.add_parser("compile", help="compile an Edit Brief")
    compile_parser.add_argument("brief", type=Path)
    compile_parser.add_argument("--json", action="store_true", dest="as_json")

    preflight_parser = subparsers.add_parser(
        "preflight", help="validate the full Qwen + ComfyUI workflow contract"
    )
    preflight_parser.add_argument("brief", type=Path)
    preflight_parser.add_argument("--reference", required=True, type=Path)

    generate_parser = subparsers.add_parser(
        "generate", help="reject direct generation; strict runs must go through ComfyUI"
    )
    generate_parser.add_argument("brief", type=Path)
    generate_parser.add_argument("--reference", action="append", default=[], type=Path)
    generate_parser.add_argument("--output-dir", type=Path, default=None)

    workflow_parser = subparsers.add_parser("workflow", help="write a ComfyUI API workflow")
    workflow_parser.add_argument("brief", type=Path)
    workflow_parser.add_argument("--reference-filename", required=True)
    workflow_parser.add_argument("--filename-prefix", required=True)
    workflow_parser.add_argument("--output", required=True, type=Path)

    assembly_parser = subparsers.add_parser(
        "assembly-workflow",
        help="write a deterministic ComfyUI region-assembly workflow",
    )
    assembly_parser.add_argument("brief", type=Path)
    assembly_parser.add_argument("--reference", required=True, type=Path)
    assembly_parser.add_argument("--generated", required=True, type=Path)
    assembly_parser.add_argument("--reference-filename", required=True)
    assembly_parser.add_argument("--generated-filename", required=True)
    assembly_parser.add_argument("--region", required=True)
    assembly_parser.add_argument("--filename-prefix", required=True)
    assembly_parser.add_argument("--output", required=True, type=Path)

    record_parser = subparsers.add_parser(
        "record-comfy", help="record completed ComfyUI outputs as a reproducible run"
    )
    record_parser.add_argument("brief", type=Path)
    record_parser.add_argument("--provider", choices=["alibaba"], required=True)
    record_parser.add_argument("--reference", action="append", default=[], type=Path)
    record_parser.add_argument("--image", action="append", required=True, type=Path)
    record_parser.add_argument("--output-dir", required=True, type=Path)
    record_parser.add_argument("--prompt-id", required=True)
    record_parser.add_argument("--source-url")
    record_parser.add_argument("--figma-file-key")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "assembly-workflow":
        brief = _load_brief(args.brief)
        validate_assembly_gate(brief)
        verify_reference_hash(brief, args.reference)
        verify_approved_output_hash(brief, args.generated)
        workflow = build_comfyui_assembly_workflow(
            brief,
            reference_filename=args.reference_filename,
            generated_filename=args.generated_filename,
            region=args.region,
            filename_prefix=args.filename_prefix,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(workflow, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(args.output)
        return 0

    brief = _load_brief(args.brief)
    validate_workflow_contract(brief)
    if args.command == "preflight":
        reference_sha256 = verify_reference_hash(brief, args.reference)
        compiled = compile_edit_brief(brief)
        print(
            json.dumps(
                {
                    "workflow_profile": brief["workflow_profile"],
                    "runtime": brief["runtime"],
                    "provider": brief["provider"],
                    "model": brief["model"],
                    "reference_sha256": reference_sha256,
                    "decision_count": len(brief["regions"]),
                    "candidate_count": brief["output"]["count"],
                    "seed": brief["output"]["seed"],
                    "prompt_metrics": vars(compiled.metrics),
                    "status": "ready_for_comfyui",
                },
                indent=2,
            )
        )
        return 0

    if args.command == "compile":
        compiled = compile_edit_brief(brief)
        if args.as_json:
            print(
                json.dumps(
                    {"prompt": compiled.prompt, "metrics": vars(compiled.metrics)},
                    indent=2,
                )
            )
        else:
            print(compiled.prompt)
        return 0

    if args.command == "workflow":
        verify_reference_hash(brief, Path(brief["reference"]["path"]))
        workflow = build_comfyui_api_workflow(
            brief,
            reference_filename=args.reference_filename,
            filename_prefix=args.filename_prefix,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(workflow, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(args.output)
        return 0

    if args.command == "generate":
        raise WorkflowContractError(
            "direct provider generation is disabled by "
            f"{brief['workflow_profile']}; create and queue a ComfyUI workflow instead"
        )

    reference_urls = [image_data_url(path) for path in args.reference]

    if args.command == "record-comfy":
        if not args.reference:
            raise WorkflowContractError("record-comfy requires the immutable reference")
        if len(args.image) != brief["output"]["count"]:
            raise WorkflowContractError(
                "record-comfy must receive exactly "
                f"{brief['output']['count']} fixed-seed candidate images"
            )
        verify_reference_hash(brief, args.reference[0])
        request_body = build_alibaba_request(brief, reference_urls=reference_urls)
        response_body = {
            "data": [
                {
                    "b64_json": base64.b64encode(path.read_bytes()).decode("ascii"),
                    "media_type": mimetypes.guess_type(path.name)[0] or "image/png",
                }
                for path in args.image
            ]
        }
        provenance = {
            "provider": args.provider,
            "prompt_id": args.prompt_id,
            "source_url": args.source_url,
            "figma_file_key": args.figma_file_key,
            "reference_sha256": (
                hashlib.sha256(args.reference[0].read_bytes()).hexdigest()
                if args.reference
                else None
            ),
        }
        record = write_run_artifacts(
            args.output_dir,
            brief,
            request_body,
            response_body,
            provenance=provenance,
        )
        print(json.dumps({"output_directory": str(args.output_dir), **record}, indent=2))
        return 0

    raise AssertionError(f"unhandled command: {args.command}")
