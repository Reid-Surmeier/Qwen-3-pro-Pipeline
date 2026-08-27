"""Command-line entry point for compiling and executing Render Passes."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import mimetypes
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from .comfyui_workflow import (
    build_comfyui_api_workflow,
    build_comfyui_assembly_workflow,
    build_comfyui_component_assembly_workflow,
)
from .prompt_manifest import compile_edit_brief
from .providers.openrouter import (
    OpenRouterImageClient,
    build_openrouter_request,
    write_run_artifacts,
)
from .providers.alibaba import AlibabaImageClient, build_alibaba_request
from .providers.router import generate_with_provider


def image_data_url(path: Path) -> str:
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


def _load_brief(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Edit Brief must be a JSON object")
    return value


def _default_run_directory() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path("artifacts/runs") / timestamp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="qwen-ui-pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    compile_parser = subparsers.add_parser("compile", help="compile an Edit Brief")
    compile_parser.add_argument("brief", type=Path)
    compile_parser.add_argument("--json", action="store_true", dest="as_json")

    generate_parser = subparsers.add_parser("generate", help="run a provider-routed Render Pass")
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
    assembly_parser.add_argument("--reference-filename", required=True)
    assembly_parser.add_argument("--generated-filename", required=True)
    assembly_parser.add_argument("--region", required=True)
    assembly_parser.add_argument("--filename-prefix", required=True)
    assembly_parser.add_argument(
        "--preserve-reference-alpha",
        action="store_true",
        help="reconstruct the exact reference alpha channel",
    )
    assembly_parser.add_argument("--output", required=True, type=Path)

    component_parser = subparsers.add_parser(
        "component-assembly-workflow",
        help="write an opt-in source-component repair workflow",
    )
    component_parser.add_argument("layout", type=Path)
    component_parser.add_argument("--reference-filename", required=True)
    component_parser.add_argument("--generated-filename", required=True)
    component_parser.add_argument("--filename-prefix", required=True)
    component_parser.add_argument(
        "--preserve-reference-alpha",
        action="store_true",
        help="reconstruct the exact reference alpha channel",
    )
    component_parser.add_argument("--output", required=True, type=Path)

    record_parser = subparsers.add_parser(
        "record-comfy", help="record completed ComfyUI outputs as a reproducible run"
    )
    record_parser.add_argument("brief", type=Path)
    record_parser.add_argument("--provider", choices=["openrouter", "alibaba"], required=True)
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
        workflow = build_comfyui_assembly_workflow(
            reference_filename=args.reference_filename,
            generated_filename=args.generated_filename,
            region=args.region,
            filename_prefix=args.filename_prefix,
            preserve_reference_alpha=args.preserve_reference_alpha,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(workflow, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(args.output)
        return 0

    if args.command == "component-assembly-workflow":
        layout = _load_brief(args.layout)
        workflow = build_comfyui_component_assembly_workflow(
            reference_filename=args.reference_filename,
            generated_filename=args.generated_filename,
            layout=layout,
            filename_prefix=args.filename_prefix,
            preserve_reference_alpha=args.preserve_reference_alpha,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(workflow, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(args.output)
        return 0

    brief = _load_brief(args.brief)
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

    reference_urls = [image_data_url(path) for path in args.reference]

    if args.command == "record-comfy":
        if args.provider == "alibaba":
            request_body = build_alibaba_request(brief, reference_urls=reference_urls)
        else:
            request_body = build_openrouter_request(brief, reference_urls=reference_urls)
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

    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
    alibaba_key = os.environ.get("DASHSCOPE_API_KEY", "")
    result = generate_with_provider(
        brief,
        reference_urls=reference_urls,
        openrouter_client=(OpenRouterImageClient(openrouter_key) if openrouter_key else None),
        alibaba_client=(AlibabaImageClient(alibaba_key) if alibaba_key else None),
    )
    output_directory = args.output_dir or _default_run_directory()
    record = write_run_artifacts(
        output_directory,
        brief,
        result.request,
        result.response,
        provenance={
            "provider": result.provider,
            "prompt_id": result.response.get("request_id"),
        },
    )
    print(json.dumps({"output_directory": str(output_directory), **record}, indent=2))
    return 0
