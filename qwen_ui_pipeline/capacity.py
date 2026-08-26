"""Pure memory-capacity planning for a bounded ComfyUI worker pool."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from math import ceil, isfinite
from pathlib import Path
from typing import Sequence, TextIO


class CapacityPlanningError(ValueError):
    """Raised when memory evidence cannot support a safe recommendation."""


@dataclass(frozen=True)
class MemorySnapshot:
    total_bytes: int
    available_bytes: int
    service_current_bytes: int
    configured_workers: int
    measurement_age_seconds: float


@dataclass(frozen=True)
class CapacityPolicy:
    memory_ceiling_bytes: int
    host_reserve_bytes: int
    worker_reserved_bytes: int
    worker_safety_factor: float
    queue_limit: int
    max_measurement_age_seconds: float
    worker_peak_validated: bool
    provider_concurrency_limit: int | None = None


@dataclass(frozen=True)
class CapacityRecommendation:
    memory_limited_worker_count: int
    recommended_workers: int
    maximum_simultaneous_jobs: int
    accepted_jobs: int
    queued_jobs: int
    rejected_jobs: int
    projected_total_used_bytes: int
    remaining_host_headroom_bytes: int
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class CapacityScenario:
    requested_workers: int
    submitted_jobs: int
    recommendation: CapacityRecommendation


def _validate_evidence(snapshot: MemorySnapshot, policy: CapacityPolicy) -> None:
    numeric_evidence = (
        ("total memory", snapshot.total_bytes),
        ("available memory", snapshot.available_bytes),
        ("service memory", snapshot.service_current_bytes),
        ("configured workers", snapshot.configured_workers),
        ("memory measurement age", snapshot.measurement_age_seconds),
        ("memory ceiling", policy.memory_ceiling_bytes),
        ("host reserve", policy.host_reserve_bytes),
        ("worker reserve", policy.worker_reserved_bytes),
        ("worker safety factor", policy.worker_safety_factor),
        ("queue limit", policy.queue_limit),
        ("maximum measurement age", policy.max_measurement_age_seconds),
    )
    if policy.provider_concurrency_limit is not None:
        numeric_evidence += (
            ("provider concurrency limit", policy.provider_concurrency_limit),
        )
    for name, value in numeric_evidence:
        try:
            finite = isfinite(value)
        except TypeError as error:
            raise CapacityPlanningError(f"{name} must be numeric") from error
        if not finite:
            raise CapacityPlanningError(f"{name} must be finite")
    if snapshot.total_bytes <= 0:
        raise CapacityPlanningError("total memory must be positive")
    if snapshot.configured_workers <= 0:
        raise CapacityPlanningError("configured workers must be positive")
    if snapshot.measurement_age_seconds < 0:
        raise CapacityPlanningError("memory measurement age must not be negative")
    if snapshot.measurement_age_seconds > policy.max_measurement_age_seconds:
        raise CapacityPlanningError("memory measurement is stale")
    if policy.memory_ceiling_bytes <= 0:
        raise CapacityPlanningError("memory ceiling must be positive")
    if policy.host_reserve_bytes < 0:
        raise CapacityPlanningError("host reserve must not be negative")
    if policy.worker_reserved_bytes <= 0:
        raise CapacityPlanningError("worker reserve must be positive")
    if policy.worker_safety_factor <= 0:
        raise CapacityPlanningError("worker safety factor must be positive")
    if policy.queue_limit < 0:
        raise CapacityPlanningError("queue limit must not be negative")
    if policy.max_measurement_age_seconds < 0:
        raise CapacityPlanningError("maximum measurement age must not be negative")
    if (
        policy.provider_concurrency_limit is not None
        and policy.provider_concurrency_limit < 0
    ):
        raise CapacityPlanningError("provider concurrency limit must not be negative")
    if not 0 <= snapshot.available_bytes <= snapshot.total_bytes:
        raise CapacityPlanningError("available memory must be within total memory")
    current_used_bytes = snapshot.total_bytes - snapshot.available_bytes
    if not 0 <= snapshot.service_current_bytes <= current_used_bytes:
        raise CapacityPlanningError("service memory must be within host used memory")


def plan_worker_capacity(
    snapshot: MemorySnapshot,
    policy: CapacityPolicy,
    *,
    requested_workers: int,
    submitted_jobs: int,
) -> CapacityRecommendation:
    """Plan bounded simultaneous execution while retaining excess jobs in queue."""
    _validate_evidence(snapshot, policy)
    if requested_workers < 0:
        raise CapacityPlanningError("requested workers must not be negative")
    if submitted_jobs < 0:
        raise CapacityPlanningError("submitted jobs must not be negative")
    current_used_bytes = snapshot.total_bytes - snapshot.available_bytes
    non_service_used_bytes = current_used_bytes - snapshot.service_current_bytes
    fixed_service_bytes = max(
        snapshot.service_current_bytes
        - snapshot.configured_workers * policy.worker_reserved_bytes,
        0,
    )
    reserved_worker_bytes = ceil(
        policy.worker_reserved_bytes * policy.worker_safety_factor
    )
    effective_ceiling_bytes = min(
        snapshot.total_bytes, policy.memory_ceiling_bytes
    )
    worker_budget_bytes = (
        effective_ceiling_bytes
        - policy.host_reserve_bytes
        - non_service_used_bytes
        - fixed_service_bytes
    )
    memory_limited_workers = max(worker_budget_bytes // reserved_worker_bytes, 0)
    recommended_workers = min(requested_workers, memory_limited_workers)
    reasons: list[str] = []
    if requested_workers > memory_limited_workers:
        reasons.append("memory_limit")
    if (
        not policy.worker_peak_validated
        and requested_workers > snapshot.configured_workers
    ):
        recommended_workers = min(recommended_workers, snapshot.configured_workers)
        reasons.append("active_worker_peak_unvalidated")
    simultaneous_capacity = recommended_workers
    if policy.provider_concurrency_limit is None:
        reasons.append("provider_concurrency_unverified")
    elif policy.provider_concurrency_limit < simultaneous_capacity:
        simultaneous_capacity = policy.provider_concurrency_limit
        reasons.append("provider_concurrency_limit")
    accepted_jobs = min(submitted_jobs, simultaneous_capacity + policy.queue_limit)
    projected_total_used_bytes = (
        non_service_used_bytes
        + fixed_service_bytes
        + recommended_workers * reserved_worker_bytes
    )
    if not reasons:
        reasons.append("within_memory_budget")
    return CapacityRecommendation(
        memory_limited_worker_count=memory_limited_workers,
        recommended_workers=recommended_workers,
        maximum_simultaneous_jobs=simultaneous_capacity,
        accepted_jobs=accepted_jobs,
        queued_jobs=max(accepted_jobs - simultaneous_capacity, 0),
        rejected_jobs=submitted_jobs - accepted_jobs,
        projected_total_used_bytes=projected_total_used_bytes,
        remaining_host_headroom_bytes=(
            effective_ceiling_bytes - projected_total_used_bytes
        ),
        reasons=tuple(reasons),
    )


def plan_capacity_scenarios(
    snapshot: MemorySnapshot,
    policy: CapacityPolicy,
    *,
    requested_worker_counts: Sequence[int],
    submitted_job_counts: Sequence[int],
) -> tuple[CapacityScenario, ...]:
    """Return a deterministic cross-product of worker and burst scenarios."""
    return tuple(
        CapacityScenario(
            requested_workers=requested_workers,
            submitted_jobs=submitted_jobs,
            recommendation=plan_worker_capacity(
                snapshot,
                policy,
                requested_workers=requested_workers,
                submitted_jobs=submitted_jobs,
            ),
        )
        for requested_workers in requested_worker_counts
        for submitted_jobs in submitted_job_counts
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="qwen-worker-capacity")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    return parser


def _emit_json(
    value: dict[str, object],
    *,
    output_path: Path | None,
    stdout: TextIO,
) -> None:
    rendered = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if output_path is None:
        stdout.write(rendered)
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
) -> int:
    """Read one sanitized JSON request and emit a capacity plan as JSON."""
    arguments = build_parser().parse_args(argv)
    output = stdout or sys.stdout
    try:
        request = json.loads(arguments.input.read_text(encoding="utf-8"))
        snapshot = MemorySnapshot(**request["snapshot"])
        policy = CapacityPolicy(**request["policy"])
        plan = plan_worker_capacity(
            snapshot,
            policy,
            requested_workers=request["requested_workers"],
            submitted_jobs=request["submitted_jobs"],
        )
        sensitivity = request["sensitivity"]
        scenarios = plan_capacity_scenarios(
            snapshot,
            policy,
            requested_worker_counts=tuple(sensitivity["requested_worker_counts"]),
            submitted_job_counts=tuple(sensitivity["submitted_job_counts"]),
        )
    except (CapacityPlanningError, KeyError, TypeError, json.JSONDecodeError, OSError) as error:
        _emit_json(
            {"status": "error", "error": str(error)},
            output_path=arguments.output,
            stdout=output,
        )
        return 2
    if plan.recommended_workers > snapshot.configured_workers:
        decision = "increase-workers"
    elif plan.recommended_workers < snapshot.configured_workers:
        decision = "reduce-workers"
    else:
        decision = "keep-current-workers"
    _emit_json(
        {
            "status": "ok",
            "decision": decision,
            "plan": asdict(plan),
            "scenarios": [asdict(item) for item in scenarios],
        },
        output_path=arguments.output,
        stdout=output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
