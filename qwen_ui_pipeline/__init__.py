"""Public interface for the reference-preserving Qwen UI pipeline."""

from .capacity import (
    CapacityPlanningError,
    CapacityPolicy,
    CapacityRecommendation,
    CapacityScenario,
    MemorySnapshot,
    plan_capacity_scenarios,
    plan_worker_capacity,
)
from .comfyui_workflow import (
    build_comfyui_api_workflow,
    build_comfyui_assembly_workflow,
    build_comfyui_component_assembly_workflow,
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
    "CapacityPlanningError",
    "CapacityPolicy",
    "CapacityRecommendation",
    "CapacityScenario",
    "CompiledEditBrief",
    "MemorySnapshot",
    "PromptBudgetExceeded",
    "PromptMetrics",
    "OpenRouterImageClient",
    "build_openrouter_request",
    "build_alibaba_request",
    "AlibabaImageClient",
    "ProviderResult",
    "build_comfyui_api_workflow",
    "build_comfyui_assembly_workflow",
    "build_comfyui_component_assembly_workflow",
    "compile_edit_brief",
    "write_run_artifacts",
    "generate_with_provider",
    "plan_capacity_scenarios",
    "plan_worker_capacity",
]
