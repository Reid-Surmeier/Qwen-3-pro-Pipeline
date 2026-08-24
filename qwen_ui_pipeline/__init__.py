"""Public interface for the reference-preserving Qwen UI pipeline."""

from .comfyui_workflow import build_comfyui_api_workflow, build_comfyui_assembly_workflow
from .providers.alibaba import AlibabaImageClient, build_alibaba_request
from .providers.router import ProviderResult, generate_with_provider
from .prompt_manifest import (
    CompiledEditBrief,
    PromptBudgetExceeded,
    PromptMetrics,
    compile_edit_brief,
)
from .providers.openrouter import (
    OpenRouterImageClient,
    build_openrouter_request,
    write_run_artifacts,
)
from .workflow_contract import (
    WORKFLOW_PROFILE,
    WorkflowContractError,
    validate_assembly_gate,
    validate_workflow_contract,
    verify_approved_output_hash,
    verify_reference_hash,
)

__all__ = [
    "CompiledEditBrief",
    "PromptBudgetExceeded",
    "PromptMetrics",
    "OpenRouterImageClient",
    "build_openrouter_request",
    "build_alibaba_request",
    "AlibabaImageClient",
    "ProviderResult",
    "build_comfyui_api_workflow",
    "build_comfyui_assembly_workflow",
    "compile_edit_brief",
    "write_run_artifacts",
    "generate_with_provider",
    "WORKFLOW_PROFILE",
    "WorkflowContractError",
    "validate_assembly_gate",
    "validate_workflow_contract",
    "verify_approved_output_hash",
    "verify_reference_hash",
]
