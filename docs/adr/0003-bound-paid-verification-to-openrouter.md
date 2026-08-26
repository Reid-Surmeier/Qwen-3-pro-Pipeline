# Bound paid verification to OpenRouter

Status: superseded by ADR 0004 on 2026-08-26.

Fresh paid generation may be used when an authoritative Issue requires visual
verification, but only through an explicitly selected OpenRouter provider. Use
the smallest useful batch and stop before exceeding 10 cumulative output images
for the linked Issue/PR; `provider: auto` and direct Alibaba are outside this
allowance. This provides enough candidates for human review while keeping cost,
fallback behavior, and duplicate-billing risk bounded.

An ambiguous possibly billed request counts against the allowance until it is
reconciled and must not be retried blindly. Every paid verification run records
requested and completed image counts, provider/model, request identity,
estimated and actual cost when exposed, output paths, hashes, and provenance.
Paid generation remains excluded from ordinary pull-request CI, and human
visual approval remains authoritative.
