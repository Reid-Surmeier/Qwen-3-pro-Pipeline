# Bound paid visual experiments by the authoritative Issue

Status: accepted on 2026-08-26. Supersedes ADR 0003.

## Context

ADR 0003 limited paid visual verification to 10 cumulative output images per
linked Issue and pull request. That ceiling bounded cost, but it also stopped a
useful experiment after its first hypothesis failed. A single repository-wide
number cannot express the different cost and evidence needs of each visual
question.

## Decision

An authoritative, human-approved Issue defines the paid-output boundary for a
visual experiment. The Issue must name the question, provider, model, initial
batch, stopping condition, and any further authorization before a paid request
is submitted.

OpenRouter remains the only provider allowed by this policy, and Qwen Image 3
Pro remains the main generator. Use the smallest useful batch and stop when the
named question is answered. The absence of a repository-wide numeric cap is not
permission to broaden a batch: further outputs must answer a named unresolved
question within the Issue's approved scope.

Estimate cost before submission. Record requested and completed image counts,
provider and model, request identity, actual cost when exposed, paths, hashes,
and provenance. Treat an ambiguous possibly billed request as spent, reconcile
it before proceeding, and never retry it blindly. Paid model execution remains
excluded from ordinary pull-request CI, and human visual approval remains
authoritative.

## Consequences

- Cheap exploratory work is not stopped by an unrelated global image count.
- The Issue becomes the auditable cost and experiment boundary.
- Agents must stop when evidence is sufficient or the Issue's approved scope
  is exhausted, even if more generations are technically possible.
- Provider fallback, automatic paid CI, and untracked retries remain forbidden.
