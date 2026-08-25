"""Public interface for the reference-preserving Qwen UI pipeline."""

from .comfyui_workflow import (
    build_comfyui_api_workflow,
    build_comfyui_assembly_workflow,
    build_sticker_mask_assembly_workflow,
)
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
    "build_sticker_mask_assembly_workflow",
    "compile_edit_brief",
    "write_run_artifacts",
    "generate_with_provider",
]
