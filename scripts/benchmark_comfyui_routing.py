#!/usr/bin/env python3
"""Benchmark archived ComfyUI routing topologies without running image models.

The candidate router is loaded directly from its pinned Git commit.  A small
in-memory ComfyUI simulation provides serial queues and deterministic opaque
outputs so the benchmark exercises routing, not providers or image semantics.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence


BASELINE_BRANCH = "archive/source-main-2026-08-25"
BASELINE_COMMIT = "e8079a3d311f0402afa179080905b2e431c6c972"
CANDIDATE_BRANCH = "archive/concurrent-image-routing"
CANDIDATE_COMMIT = "b8e226cb12f7cea8a201da73a852542938fdad9f"
ROUTER_PATH = "qwen_ui_pipeline/comfyui_router.py"
BASELINE_DEPLOY_PATH = "deploy/run-comfyui.sh"
CANDIDATE_DEPLOY_PATH = "deploy/run-comfyui-pool.sh"
WORKFLOW_IDENTITY = "synthetic-opaque-comfyui-workflow-v1"
WORKER_COUNT = 5
DEFAULT_DURATIONS = (0.12, 0.14, 0.16, 0.18, 0.20, 0.22)


@dataclass(frozen=True)
class SyntheticJob:
    job_id: str
    input_identity: str
    duration_seconds: float
    payload: bytes


@dataclass
class JobObservation:
    submitted_ns: int | None = None
    started_ns: int | None = None
    completed_ns: int | None = None
    worker_id: str | None = None
    status: str = "pending"
    error: str | None = None
    enqueue_attempts: int = 0
    payload_sha256: str | None = None
    output_sha256: str | None = None
    history_verified: bool = False


@dataclass
class WorkerState:
    backend: str
    queue: deque[SyntheticJob] = field(default_factory=deque)
    running: SyntheticJob | None = None
    history: dict[str, dict[str, Any]] = field(default_factory=dict)
    stopping: bool = False
    condition: threading.Condition = field(default_factory=threading.Condition)
    thread: threading.Thread | None = None


@dataclass(frozen=True)
class SimulatedResponse:
    status: int
    headers: tuple[tuple[str, str], ...]
    body: bytes


def _json_response(value: Mapping[str, Any], status: int = 200) -> SimulatedResponse:
    return SimulatedResponse(
        status=status,
        headers=(("Content-Type", "application/json"),),
        body=json.dumps(value, separators=(",", ":")).encode("utf-8"),
    )


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _iso_timestamp(timestamp_ns: int) -> str:
    return datetime.fromtimestamp(timestamp_ns / 1_000_000_000, UTC).isoformat(
        timespec="microseconds"
    )


def _git(repository: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _git_text(repository: Path, *arguments: str) -> str:
    return _git(repository, *arguments).decode("utf-8").strip()


def _git_show(repository: Path, commit: str, path: str) -> bytes:
    return _git(repository, "show", f"{commit}:{path}")


def _verify_pins(repository: Path) -> dict[str, Any]:
    expected = {
        BASELINE_BRANCH: BASELINE_COMMIT,
        CANDIDATE_BRANCH: CANDIDATE_COMMIT,
    }
    resolved: dict[str, str] = {}
    for branch, commit in expected.items():
        commit_object = _git_text(repository, "rev-parse", f"{commit}^{{commit}}")
        if commit_object != commit:
            raise RuntimeError(f"pinned commit did not resolve exactly: {commit}")
        remote_ref = f"refs/remotes/origin/{branch}"
        branch_commit = _git_text(repository, "rev-parse", remote_ref)
        if branch_commit != commit:
            raise RuntimeError(f"{remote_ref} resolved to {branch_commit}, expected {commit}")
        resolved[branch] = branch_commit

    baseline_deploy = _git_show(repository, BASELINE_COMMIT, BASELINE_DEPLOY_PATH)
    candidate_deploy = _git_show(repository, CANDIDATE_COMMIT, CANDIDATE_DEPLOY_PATH)
    router_source = _git_show(repository, CANDIDATE_COMMIT, ROUTER_PATH)
    if baseline_deploy.count(b'"$COMFYUI_ROOT/main.py"') != 1:
        raise RuntimeError("baseline topology is not exactly one ComfyUI process")
    if b"QWEN_COMFYUI_WORKERS:-5" not in candidate_deploy:
        raise RuntimeError("candidate deployment no longer defaults to five workers")

    return {
        "resolved_branches": resolved,
        "source_files": {
            BASELINE_DEPLOY_PATH: {
                "commit_sha": BASELINE_COMMIT,
                "sha256": _sha256(baseline_deploy),
            },
            CANDIDATE_DEPLOY_PATH: {
                "commit_sha": CANDIDATE_COMMIT,
                "sha256": _sha256(candidate_deploy),
            },
            ROUTER_PATH: {
                "commit_sha": CANDIDATE_COMMIT,
                "sha256": _sha256(router_source),
            },
        },
        "router_source": router_source,
    }


def _load_router_module(router_source: bytes):
    with tempfile.TemporaryDirectory(prefix="qwen-router-benchmark-") as directory:
        module_path = Path(directory) / "pinned_comfyui_router.py"
        module_path.write_bytes(router_source)
        module_name = "_pinned_comfyui_router"
        specification = importlib.util.spec_from_file_location(module_name, module_path)
        if specification is None or specification.loader is None:
            raise RuntimeError("could not load pinned candidate router")
        module = importlib.util.module_from_spec(specification)
        sys.modules[module_name] = module
        try:
            specification.loader.exec_module(module)
        finally:
            sys.modules.pop(module_name, None)
        return module


class SimulatedComfyUITransport:
    """Thread-safe serial ComfyUI workers with instrumented synthetic jobs."""

    def __init__(self, backends: Sequence[str], jobs: Sequence[SyntheticJob]):
        self.workers = {backend: WorkerState(backend) for backend in backends}
        self.jobs = {job.job_id: job for job in jobs}
        self.observations = {job.job_id: JobObservation() for job in jobs}
        self._closed = False
        for state in self.workers.values():
            state.thread = threading.Thread(
                target=self._worker_loop,
                args=(state,),
                name=f"simulated-{state.backend.rsplit('/', 1)[-1]}",
                daemon=True,
            )
            state.thread.start()

    def mark_submitted(self, job_id: str) -> None:
        observation = self.observations[job_id]
        observation.submitted_ns = time.time_ns()
        observation.status = "submitted"

    def mark_submit_error(self, job_id: str, error: Exception) -> None:
        observation = self.observations[job_id]
        observation.completed_ns = time.time_ns()
        observation.status = "error"
        observation.error = f"{type(error).__name__}: {error}"

    def request(
        self,
        backend: str,
        method: str,
        target: str,
        headers: Mapping[str, str] | None = None,
        body: bytes | None = None,
    ) -> SimulatedResponse:
        del headers
        state = self.workers[backend]
        if method == "GET" and target == "/queue":
            with state.condition:
                running = [[0, state.running.job_id]] if state.running is not None else []
                pending = [[0, job.job_id] for job in state.queue]
            return _json_response({"queue_running": running, "queue_pending": pending})

        if method == "POST" and target == "/prompt":
            payload = json.loads((body or b"{}").decode("utf-8"))
            job_id = payload.get("job_id")
            if not isinstance(job_id, str) or job_id not in self.jobs:
                return _json_response({"error": "unknown synthetic job"}, status=400)
            observation = self.observations[job_id]
            observation.enqueue_attempts += 1
            observation.payload_sha256 = _sha256(body or b"")
            observation.worker_id = backend
            observation.status = "queued"
            with state.condition:
                state.queue.append(self.jobs[job_id])
                state.condition.notify_all()
            return _json_response({"prompt_id": job_id, "number": 1})

        if method == "GET" and target.startswith("/history/"):
            job_id = target.removeprefix("/history/")
            with state.condition:
                history = state.history.get(job_id)
            return _json_response({job_id: history} if history is not None else {})

        if method == "GET" and target == "/history":
            with state.condition:
                history = dict(state.history)
            return _json_response(history)

        return _json_response({"backend": backend, "target": target})

    def _worker_loop(self, state: WorkerState) -> None:
        while True:
            with state.condition:
                while not state.queue and not state.stopping:
                    state.condition.wait()
                if state.stopping and not state.queue:
                    return
                job = state.queue.popleft()
                state.running = job
                observation = self.observations[job.job_id]
                observation.started_ns = time.time_ns()
                observation.status = "running"

            time.sleep(job.duration_seconds)
            output = _canonical_json(
                {
                    "job_id": job.job_id,
                    "input_identity": job.input_identity,
                    "workflow_identity": WORKFLOW_IDENTITY,
                    "synthetic_result": "completed",
                }
            )
            completed_ns = time.time_ns()

            with state.condition:
                observation.output_sha256 = _sha256(output)
                observation.completed_ns = completed_ns
                observation.status = "completed"
                state.history[job.job_id] = {
                    "outputs": {"synthetic": {"sha256": observation.output_sha256}},
                    "status": {"completed": True},
                }
                state.running = None
                state.condition.notify_all()

    def wait_for_completion(self, timeout_seconds: float) -> None:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if all(
                observation.status in {"completed", "error"}
                for observation in self.observations.values()
            ):
                return
            time.sleep(0.005)
        incomplete = [
            job_id
            for job_id, observation in self.observations.items()
            if observation.status not in {"completed", "error"}
        ]
        raise TimeoutError(f"synthetic jobs did not complete: {incomplete}")

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for state in self.workers.values():
            with state.condition:
                state.stopping = True
                state.condition.notify_all()
        for state in self.workers.values():
            if state.thread is not None:
                state.thread.join(timeout=5)


def _build_jobs(duration_scale: float) -> list[SyntheticJob]:
    jobs = []
    for index, base_duration in enumerate(DEFAULT_DURATIONS, start=1):
        job_id = f"job-{index:02d}"
        input_identity = f"synthetic-input-{index:02d}-v1"
        payload = _canonical_json(
            {
                "job_id": job_id,
                "prompt": {
                    "1": {
                        "class_type": "SyntheticNoProviderNode",
                        "inputs": {
                            "input_identity": input_identity,
                            "workflow_identity": WORKFLOW_IDENTITY,
                        },
                    }
                },
            }
        )
        jobs.append(
            SyntheticJob(
                job_id=job_id,
                input_identity=input_identity,
                duration_seconds=base_duration * duration_scale,
                payload=payload,
            )
        )
    return jobs


def _observation_record(
    job: SyntheticJob,
    observation: JobObservation,
    configuration: str,
    commit_sha: str,
) -> dict[str, Any]:
    if observation.submitted_ns is None:
        raise RuntimeError(f"missing submission timestamp for {job.job_id}")
    completed_ns = observation.completed_ns or observation.submitted_ns
    started_ns = observation.started_ns
    return {
        "job_id": job.job_id,
        "submitted_at": _iso_timestamp(observation.submitted_ns),
        "started_at": _iso_timestamp(started_ns) if started_ns is not None else None,
        "completed_at": _iso_timestamp(completed_ns),
        "worker_id": observation.worker_id,
        "status": observation.status,
        "error": observation.error,
        "baseline_or_candidate": configuration,
        "commit_sha": commit_sha,
        "workflow_identity": WORKFLOW_IDENTITY,
        "input_identity": job.input_identity,
        "queue_wait_seconds": (
            round((started_ns - observation.submitted_ns) / 1_000_000_000, 6)
            if started_ns is not None
            else None
        ),
        "execution_time_seconds": (
            round((completed_ns - started_ns) / 1_000_000_000, 6)
            if started_ns is not None
            else None
        ),
        "enqueue_attempts": observation.enqueue_attempts,
        "payload_sha256": observation.payload_sha256,
        "expected_payload_sha256": _sha256(job.payload),
        "output_sha256": observation.output_sha256,
        "history_verified": observation.history_verified,
    }


def _run_once(
    configuration: str,
    repeat: int,
    jobs: Sequence[SyntheticJob],
    router_module: Any,
) -> dict[str, Any]:
    if configuration == "baseline":
        commit_sha = BASELINE_COMMIT
        backends = ["http://worker-1"]
    else:
        commit_sha = CANDIDATE_COMMIT
        backends = [f"http://worker-{index}" for index in range(1, WORKER_COUNT + 1)]

    transport = SimulatedComfyUITransport(backends, jobs)
    router = (
        router_module.ComfyUIRouter(
            backends,
            transport=transport,
            probe_transport=transport,
        )
        if configuration == "candidate"
        else None
    )
    barrier = threading.Barrier(len(jobs))

    def submit(job: SyntheticJob) -> None:
        try:
            barrier.wait(timeout=5)
            transport.mark_submitted(job.job_id)
            if router is None:
                response = transport.request(backends[0], "POST", "/prompt", body=job.payload)
            else:
                response = router.route("POST", "/prompt", body=job.payload)
            if not 200 <= response.status < 300:
                raise RuntimeError(f"enqueue returned HTTP {response.status}")
        except Exception as error:  # Capture every submit failure in evidence.
            transport.mark_submit_error(job.job_id, error)

    try:
        with ThreadPoolExecutor(max_workers=len(jobs)) as executor:
            list(executor.map(submit, jobs))
        transport.wait_for_completion(timeout_seconds=30)

        for job in jobs:
            observation = transport.observations[job.job_id]
            if observation.status != "completed":
                continue
            if router is None:
                history = transport.request(backends[0], "GET", f"/history/{job.job_id}")
            else:
                history = router.route("GET", f"/history/{job.job_id}")
            history_payload = json.loads(history.body)
            observation.history_verified = job.job_id in history_payload

        records = [
            _observation_record(job, transport.observations[job.job_id], configuration, commit_sha)
            for job in sorted(jobs, key=lambda item: item.job_id)
        ]
    finally:
        transport.close()

    submitted = [transport.observations[job.job_id].submitted_ns for job in jobs]
    completed = [transport.observations[job.job_id].completed_ns for job in jobs]
    if any(value is None for value in submitted + completed):
        raise RuntimeError("benchmark run has incomplete timestamps")
    queue_waits = [
        record["queue_wait_seconds"]
        for record in records
        if record["queue_wait_seconds"] is not None
    ]
    execution_times = [
        record["execution_time_seconds"]
        for record in records
        if record["execution_time_seconds"] is not None
    ]
    return {
        "configuration": configuration,
        "repeat": repeat,
        "commit_sha": commit_sha,
        "worker_count": len(backends),
        "jobs": records,
        "batch_makespan_seconds": round((max(completed) - min(submitted)) / 1_000_000_000, 6),
        "mean_queue_wait_seconds": round(statistics.mean(queue_waits), 6),
        "max_queue_wait_seconds": round(max(queue_waits), 6),
        "mean_execution_time_seconds": round(statistics.mean(execution_times), 6),
        "routing_failures": sum(record["status"] != "completed" for record in records),
        "retry_count": sum(max(record["enqueue_attempts"] - 1, 0) for record in records),
        "history_failures": sum(not record["history_verified"] for record in records),
        "payload_mismatches": sum(
            record["payload_sha256"] != record["expected_payload_sha256"] for record in records
        ),
    }


def _variation(values: Sequence[float]) -> dict[str, float]:
    return {
        "minimum": round(min(values), 6),
        "maximum": round(max(values), 6),
        "mean": round(statistics.mean(values), 6),
        "median": round(statistics.median(values), 6),
        "sample_standard_deviation": round(statistics.stdev(values), 6) if len(values) > 1 else 0.0,
    }


def _summarize(runs: Sequence[dict[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for configuration in ("baseline", "candidate"):
        selected = [run for run in runs if run["configuration"] == configuration]
        output[configuration] = {
            "batch_makespan_seconds": _variation(
                [run["batch_makespan_seconds"] for run in selected]
            ),
            "mean_queue_wait_seconds": _variation(
                [run["mean_queue_wait_seconds"] for run in selected]
            ),
            "max_queue_wait_seconds": _variation(
                [run["max_queue_wait_seconds"] for run in selected]
            ),
            "mean_execution_time_seconds": _variation(
                [run["mean_execution_time_seconds"] for run in selected]
            ),
            "routing_failures": sum(run["routing_failures"] for run in selected),
            "retry_count": sum(run["retry_count"] for run in selected),
            "history_failures": sum(run["history_failures"] for run in selected),
            "payload_mismatches": sum(run["payload_mismatches"] for run in selected),
            "completed_jobs": sum(
                job["status"] == "completed" for run in selected for job in run["jobs"]
            ),
            "dropped_jobs": sum(
                job["status"] not in {"completed", "error"}
                for run in selected
                for job in run["jobs"]
            ),
            "timeout_count": sum(
                bool(job["error"] and "Timeout" in job["error"])
                for run in selected
                for job in run["jobs"]
            ),
            "missing_observations": sum(
                any(
                    job[field] is None
                    for field in (
                        "submitted_at",
                        "started_at",
                        "completed_at",
                        "worker_id",
                    )
                )
                for run in selected
                for job in run["jobs"]
            ),
            "workers_observed": sorted(
                {
                    job["worker_id"]
                    for run in selected
                    for job in run["jobs"]
                    if job["worker_id"] is not None
                }
            ),
        }

    baseline_outputs = {
        (run["repeat"], job["job_id"]): job["output_sha256"]
        for run in runs
        if run["configuration"] == "baseline"
        for job in run["jobs"]
    }
    candidate_outputs = {
        (run["repeat"], job["job_id"]): job["output_sha256"]
        for run in runs
        if run["configuration"] == "candidate"
        for job in run["jobs"]
    }
    output["output_digest_parity"] = baseline_outputs == candidate_outputs
    baseline_makespan = output["baseline"]["batch_makespan_seconds"]["mean"]
    candidate_makespan = output["candidate"]["batch_makespan_seconds"]["mean"]
    baseline_wait = output["baseline"]["mean_queue_wait_seconds"]["mean"]
    candidate_wait = output["candidate"]["mean_queue_wait_seconds"]["mean"]
    output["mean_makespan_reduction_percent"] = round(
        (baseline_makespan - candidate_makespan) / baseline_makespan * 100, 2
    )
    output["mean_queue_wait_reduction_percent"] = round(
        (baseline_wait - candidate_wait) / baseline_wait * 100, 2
    )
    has_integrity_failure = (
        any(
            output[configuration][key]
            for configuration in ("baseline", "candidate")
            for key in (
                "routing_failures",
                "retry_count",
                "history_failures",
                "payload_mismatches",
            )
        )
        or not output["output_digest_parity"]
    )
    if has_integrity_failure:
        output["conclusion"] = "unsafe/unreliable"
    elif candidate_makespan < baseline_makespan and candidate_wait < baseline_wait:
        output["conclusion"] = "promising"
    else:
        output["conclusion"] = "not beneficial"
    return output


def _render_report(manifest: Mapping[str, Any]) -> str:
    summary = manifest["summary"]
    baseline = summary["baseline"]
    candidate = summary["candidate"]
    lines = [
        "# Issue #1: concurrent ComfyUI routing benchmark",
        "",
        f"**Conclusion:** `{summary['conclusion']}` for the simulated routing layer.",
        "",
        "## Exact comparison",
        "",
        f"- Baseline: `{BASELINE_BRANCH}` at `{BASELINE_COMMIT}` (one worker).",
        f"- Candidate: `{CANDIDATE_BRANCH}` at `{CANDIDATE_COMMIT}` (five workers).",
        f"- Repetitions: {manifest['benchmark']['repeat_count']} per configuration.",
        "- Workload: six simultaneous opaque synthetic ComfyUI jobs with fixed identities and durations.",
        "- No provider, model, image generation, credential, production endpoint, or paid operation was used.",
        "",
        "## Results",
        "",
        "| Measure | Baseline mean | Candidate mean | Change |",
        "| --- | ---: | ---: | ---: |",
        (
            "| Six-job makespan | "
            f"{baseline['batch_makespan_seconds']['mean']:.6f}s | "
            f"{candidate['batch_makespan_seconds']['mean']:.6f}s | "
            f"{summary['mean_makespan_reduction_percent']:.2f}% reduction |"
        ),
        (
            "| Per-run mean queue wait | "
            f"{baseline['mean_queue_wait_seconds']['mean']:.6f}s | "
            f"{candidate['mean_queue_wait_seconds']['mean']:.6f}s | "
            f"{summary['mean_queue_wait_reduction_percent']:.2f}% reduction |"
        ),
        (
            "| Mean synthetic execution time | "
            f"{baseline['mean_execution_time_seconds']['mean']:.6f}s | "
            f"{candidate['mean_execution_time_seconds']['mean']:.6f}s | n/a |"
        ),
        "",
        "Run-to-run variation is retained in `results.json`; ranges are:",
        "",
        (
            f"- Baseline makespan {baseline['batch_makespan_seconds']['minimum']:.6f}s–"
            f"{baseline['batch_makespan_seconds']['maximum']:.6f}s; candidate "
            f"{candidate['batch_makespan_seconds']['minimum']:.6f}s–"
            f"{candidate['batch_makespan_seconds']['maximum']:.6f}s."
        ),
        (
            f"- Baseline mean queue wait {baseline['mean_queue_wait_seconds']['minimum']:.6f}s–"
            f"{baseline['mean_queue_wait_seconds']['maximum']:.6f}s; candidate "
            f"{candidate['mean_queue_wait_seconds']['minimum']:.6f}s–"
            f"{candidate['mean_queue_wait_seconds']['maximum']:.6f}s."
        ),
        "",
        "## Integrity and routing evidence",
        "",
        f"- Candidate workers observed: {', '.join(candidate['workers_observed'])}.",
        f"- Routing failures: {candidate['routing_failures']}.",
        f"- Enqueue retries: {candidate['retry_count']}.",
        f"- Dropped jobs: {candidate['dropped_jobs']}.",
        f"- Timeouts: {candidate['timeout_count']}.",
        f"- Missing observations: {candidate['missing_observations']}.",
        f"- History-affinity failures: {candidate['history_failures']}.",
        f"- Opaque payload mismatches: {candidate['payload_mismatches']}.",
        f"- Synthetic output digest parity: {summary['output_digest_parity']}.",
        "",
        "## Interpretation and limits",
        "",
        "The candidate is promising for removing local FIFO wait in the isolated simulation. "
        "The result does not establish production throughput, provider concurrency limits, "
        "GPU/CPU/memory safety, or image fidelity. The benchmark deliberately used no images, "
        "so any possible visual-output difference remains unmeasured and requires human review "
        "before a later adoption decision.",
        "",
        "The benchmark does not adopt the router, merge either archive branch, or change provider, "
        "workflow, prompt, seed, output naming, Assembly, or Fidelity Check behavior.",
        "",
        "## Reproduce",
        "",
        "```bash",
        "python3.12 scripts/benchmark_comfyui_routing.py \\",
        "  --output-dir artifacts/benchmarks/comfyui-routing-issue-1",
        "```",
        "",
    ]
    return "\n".join(lines)


def run_benchmark(
    repository: Path,
    output_directory: Path,
    *,
    repeat_count: int = 5,
    duration_scale: float = 1.0,
) -> dict[str, Any]:
    if repeat_count < 2:
        raise ValueError("repeat count must be at least two to expose variation")
    if duration_scale <= 0:
        raise ValueError("duration scale must be positive")
    pins = _verify_pins(repository)
    router_module = _load_router_module(pins.pop("router_source"))
    jobs = _build_jobs(duration_scale)
    runs = []
    for repeat in range(1, repeat_count + 1):
        runs.append(_run_once("baseline", repeat, jobs, router_module))
        runs.append(_run_once("candidate", repeat, jobs, router_module))

    workflow_manifest = [
        {
            "job_id": job.job_id,
            "input_identity": job.input_identity,
            "duration_seconds": job.duration_seconds,
            "payload_sha256": _sha256(job.payload),
        }
        for job in jobs
    ]
    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "benchmark": {
            "issue": "https://github.com/Reid-Surmeier/Qwen-3-pro-Pipeline/issues/1",
            "kind": "non-production simulated routing; no image generation",
            "repeat_count": repeat_count,
            "statistics": "minimum, maximum, mean, median, and sample standard deviation",
            "repeat_rationale": (
                "Five paired runs expose scheduler variation while keeping the "
                "non-production simulation bounded."
            ),
            "submission_pattern": "six threads released through one barrier",
            "artifact_classification": "comparison evidence",
            "baseline": {
                "branch": BASELINE_BRANCH,
                "commit_sha": BASELINE_COMMIT,
                "worker_count": 1,
            },
            "candidate": {
                "branch": CANDIDATE_BRANCH,
                "commit_sha": CANDIDATE_COMMIT,
                "worker_count": WORKER_COUNT,
            },
            "workflow_identity": WORKFLOW_IDENTITY,
            "workload_sha256": _sha256(_canonical_json(workflow_manifest)),
            "jobs": workflow_manifest,
        },
        "source_verification": pins,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "repository_head": _git_text(repository, "rev-parse", "HEAD"),
        },
        "runs": runs,
        "summary": _summarize(runs),
        "limitations": [
            "Synthetic serial workers model ComfyUI queue behavior but not runtime resource use.",
            "No provider concurrency, throttling, timeout, or billing behavior was exercised.",
            "No images were produced, so visual or fidelity differences were not evaluated.",
            "A later adoption decision requires production-safe resource and human visual review.",
        ],
    }
    output_directory.mkdir(parents=True, exist_ok=True)
    (output_directory / "results.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_directory / "report.md").write_text(_render_report(manifest), encoding="utf-8")
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Benchmark exact archived ComfyUI routing commits without image generation."
    )
    parser.add_argument(
        "--repository",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/benchmarks/comfyui-routing-issue-1"),
    )
    parser.add_argument("--repeat-count", type=int, default=5)
    parser.add_argument("--duration-scale", type=float, default=1.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    manifest = run_benchmark(
        arguments.repository.resolve(),
        arguments.output_dir,
        repeat_count=arguments.repeat_count,
        duration_scale=arguments.duration_scale,
    )
    print(
        json.dumps(
            {
                "output_directory": str(arguments.output_dir),
                "conclusion": manifest["summary"]["conclusion"],
                "mean_makespan_reduction_percent": manifest["summary"][
                    "mean_makespan_reduction_percent"
                ],
                "mean_queue_wait_reduction_percent": manifest["summary"][
                    "mean_queue_wait_reduction_percent"
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
