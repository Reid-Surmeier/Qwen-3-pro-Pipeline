# Repository workflow

This document explains how work moves through `Qwen-3-Pro-Pipeline`. It is written for humans and agents. The enforceable agent rules live in [`../../AGENTS.md`](../../AGENTS.md).

## Goal

Keep `main` understandable and known-good while making changes small, reviewable, reproducible, and recoverable.

The lifecycle is:

```text
not-ready
  -> needs-triage / needs-info
  -> agent triage brief
  -> needs-human-decision
  -> human approves, revises, splits, or rejects
  -> ready-for-agent
  -> in-progress branch or worktree
  -> locally verified
  -> pull request
  -> CI and review
  -> approved
  -> merged
  -> branch cleanup
```

## What each repository object owns

| Object | It answers |
| --- | --- |
| `README.md` | What is this project and how do I begin? |
| `CONTEXT.md` | What do project terms mean and how are they related? |
| `AGENTS.md` | How must an agent operate here? |
| ADR | Why was an important architectural decision made? |
| Issue | What problem or outcome should be addressed? |
| Branch/worktree | Where is one isolated line of work happening? |
| Commit | What coherent checkpoint can be recovered or reviewed? |
| Pull request | What change is proposed for `main`, and what evidence supports it? |
| GitHub Actions workflow | Which repeatable checks run automatically on an event? |
| Agent skill | Which reusable reasoning or execution procedure can an agent load? |

These objects should point to each other rather than duplicate one another.

## 1. Capture work in an Issue

GitHub Issues are the authoritative work tracker.

An Issue may describe a bug, feature, investigation, documentation task, CI task, or repository chore. It should focus on the problem and observable outcome.

A useful Issue contains:

- problem or desired outcome,
- evidence or current behavior,
- expected behavior,
- acceptance criteria,
- in-scope and out-of-scope boundaries,
- verification method,
- dependencies and approval requirements.

Do not require the Issue author to prescribe code structure unless that structure is already an accepted architectural decision.

## 2. Triage before assigning an agent

Use the canonical workflow labels in [`triage-labels.md`](triage-labels.md).

While an Issue has `needs-triage`, an agent may inspect repository context and post the five-part triage brief defined in [`issue-tracker.md`](issue-tracker.md). It must not create a branch, modify files, or begin implementation.

After commenting, the agent replaces `needs-triage` with `needs-human-decision` and stops. The human then chooses one outcome:

- approve the proposed work packet,
- request revisions,
- split the work into smaller Issues,
- request more investigation,
- reject or close the work.

Only the human may authorize the transition to `ready-for-agent`. Before that transition, update the Issue body with the approved outcome, scope, acceptance criteria, verification, dependencies, and approval boundaries. The body is the canonical work packet; comments remain the decision history.

`ready-for-agent` is a gate, not a general priority label. Apply it only when an agent can act without inventing product, architecture, security, cost, or acceptance decisions.

Move an Issue to `needs-info` when a missing answer could materially change the solution. Use `ready-for-human` when the work requires direct human judgment or execution rather than approval of an agent proposal.

## 3. Create one isolated branch or worktree

Start from the current known-good `main`:

```bash
git switch main
git pull --ff-only origin main
git switch -c docs/example-change
```

Use a worktree when another branch already contains uncommitted work or when two lines of work must remain visible at the same time:

```bash
git worktree add ../worktrees/example-change -b docs/example-change main
```

Recommended branch prefixes:

```text
docs/       documentation
feat/       new behavior
fix/        defect correction
refactor/   behavior-preserving restructuring
test/       verification coverage
ci/         GitHub Actions or automation
```

A branch should correspond to one Issue or one coherent migration gate.

## 4. Run preflight

Before editing:

```bash
git status --short --branch
git diff --check
```

Read the active Issue, `AGENTS.md`, `CONTEXT.md`, and relevant ADRs. Inspect the closest implementation and tests before proposing a structure.

Stop if:

- the worktree contains unrelated changes,
- an ADR conflicts with the request,
- credentials are present,
- acceptance criteria are missing,
- paid or external execution lacks approval.

## 5. Implement the smallest coherent change

Prefer a vertical slice with an observable result over a broad reorganization.

For behavior changes:

1. Demonstrate the current failure or write a failing test.
2. Implement the smallest change that addresses it.
3. Run the focused test.
4. Refactor only after the behavior is protected.
5. Run the full baseline checks.

For documentation or repository-management changes:

1. Identify the stale or missing rule.
2. Change the smallest authoritative document.
3. Check that linked files exist and terminology matches `CONTEXT.md`.
4. Avoid claiming automation or policy that has not been implemented.

## 6. Verify before committing

Current baseline:

```bash
python3.12 -m unittest discover -s tests -v
node --test tests/figma-mcp-client.test.mjs tests/figma-oauth-bootstrap.test.mjs
python3.12 -m compileall -q qwen_ui_pipeline tests scripts
git diff --check
```

Add focused checks for the area changed. Examples include provider-routing tests, workflow-contract tests, JavaScript tests, schema validation, artifact-manifest validation, or pixel-preservation comparisons.

Record real output. A planned command is not verification.

## 7. Commit a recoverable checkpoint

Stage only intended paths:

```bash
git add README.md docs/agents/repository-workflow.md
git diff --cached --check
git diff --cached --stat
```

Use a concise Conventional Commit-style subject:

```text
docs: define repository workflow
ci: verify Python changes on pull requests
fix: reject unapproved region assembly
```

If Git author identity is not configured, stop. The agent must not invent a name/email or attribute work to the user without their configuration.

## 8. Open a pull request

A pull request should use [the repository template](../../.github/pull_request_template.md)
and answer four questions in plain language:

1. What changed?
2. Why was it needed?
3. What should the human check?
4. Which checks actually ran, and what happened?

Keep the scope, risks, and outstanding human decisions explicit. Use draft
status while acceptance criteria or evidence are incomplete.

### Visual or generation proof

When a pull request changes or generates visual output, put the result before
the technical provenance so a human can inspect it quickly:

- embed the important Reference Screen, candidate, selected donor, or final
  output previews in the PR when practical;
- otherwise explain why embedding is impractical and link a durable contact
  sheet or output artifact;
- identify what each preview represents: a probabilistic Render Pass, selected
  donor, deterministic Assembly, or final output;
- link the source identity, run or validated manifest, output path, provider
  and model, exact commits, hashes, and objective Fidelity Check from one
  traceable record when they apply;
- state which donor, final visual, FigJam placement/readback, cost, credential,
  or production decisions are approved and which remain open.

For strict preservation, include dimensions, the declared edit region, the
outside-region changed-pixel count, Exact Copy results, and remaining
limitations. A preview helps a human judge the result; it does not make the
output authoritative or replace a Fidelity Check.

Use existing reviewed outputs when they already answer the verification
question. When fresh paid verification is necessary, the authoritative,
human-approved Issue must name the question, model, initial batch, stopping
condition, and any authorization for further output. Use OpenRouter explicitly,
submit the smallest useful batch, and stop when the named question is answered.
The absence of a repository-wide numeric cap does not authorize a broader
batch. Do not use provider auto-selection or direct Alibaba under this
allowance.

Count requested and completed images in the run record. Treat an ambiguous
possibly billed request as spent until reconciled, and never retry it blindly.
Record the provider/model, request or task ID, estimated and actual cost when
exposed, output paths, hashes, provenance, and limitations. This allowance does
not enable paid/model-backed generation in ordinary PR CI.

Keep credentials, tokens, unsafe raw provider responses, and unrelated large
artifacts out of the PR.

For a non-visual change, write one line: `Not applicable — this PR does not
change or generate visual output.`

## 9. Review in two passes

### Specification review

Ask:

- Does the change solve the linked Issue?
- Are all acceptance criteria demonstrated?
- Did scope expand without approval?
- Are required artifacts or comparisons present?

### Engineering review

Ask:

- Is the change minimal and understandable?
- Does it preserve architectural boundaries?
- Are failures handled safely?
- Are secrets and external side effects controlled?
- Are tests meaningful rather than merely passing?
- Can the change be reverted cleanly?

A fluent agent explanation is not evidence. Read the diff and the verification output.

## 10. Merge and clean up

Merge only after required checks and approvals pass. Prefer squash merging for a small single-purpose branch unless preserving its internal commit history is important.

After merge:

```bash
git switch main
git pull --ff-only origin main
git branch -d <merged-branch>
git worktree remove <completed-worktree-path>
```

Close the Issue through the pull request and record follow-up work as new Issues rather than hidden TODOs.

## GitHub Actions boundaries

### Default pull-request verification

The first workflow should run cheap deterministic checks:

- Python unit tests,
- Python compilation,
- repository hygiene checks,
- schema or manifest validation as those gates are added.

It should use read-only repository permissions unless a job has a documented need for more.

### Visual evaluation workflow

A later visual workflow should compare exact baseline and candidate commit SHAs and preserve:

- source hashes,
- workflow/profile identity,
- provider/model identity,
- seeds and candidate count,
- baseline image,
- candidate image,
- diff and objective metrics,
- run manifest.

Paid generation and model-based evaluation must be separate from ordinary PR CI and require explicit approval. Automated metrics support review; they do not replace human subjective acceptance.

## Migration rule

The old repository is evidence, not a cleanup target.

During migration:

- preserve exact committed refs,
- archive current WIP separately,
- classify artifacts before moving or deleting them,
- change organization through small branches,
- avoid behavior rewrites unless a later Issue explicitly requests them.
