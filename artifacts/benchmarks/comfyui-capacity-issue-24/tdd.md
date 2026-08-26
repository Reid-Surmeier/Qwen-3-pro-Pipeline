# TDD evidence

Issue: #24

The implementation followed red-green-refactor. No provider job, paid request,
service restart, or worker-count change was made during these cycles.

| Cycle | Red evidence | Green evidence |
| --- | --- | --- |
| Bound a 12-job burst | `ImportError`: `CapacityPolicy` did not exist | Five jobs run simultaneously and seven remain queued |
| Enforce memory limits | `AttributeError`: the recommendation had no memory-limited worker count | A 45 GiB ceiling, 8 GiB host reserve, and 2 GiB-per-worker reserve at 1.25 safety factor clamp 12 requested workers to five |
| Fail closed | Stale evidence had no typed failure; zero reserve and zero safety factor raised `ZeroDivisionError`; contradictory snapshots and negative job counts were accepted | Each unsafe input raises `CapacityPlanningError`; missing CLI fields and unsafe inputs produce structured JSON with status 2 |
| Require active-peak evidence | A request for eight workers recommended eight despite no active-job peak measurement | Unvalidated peak evidence clamps the result to the current five workers |
| Separate provider limits | The policy did not accept provider concurrency independently of memory capacity | Local worker capacity remains distinct from a provider cap or an explicitly unknown provider limit |
| Add reproducible sensitivity output | `ImportError`: scenario planner and CLI did not exist; later, `--output` was rejected by the parser | CLI writes a 5-by-3 worker/burst matrix to a deterministic JSON artifact |
| Bound overload | A 100-job burst had no characterized acceptance boundary | Five run, 64 queue, and 31 are rejected instead of creating unbounded local pressure |
| Name simultaneous capacity precisely | With only two submitted jobs, `maximum_simultaneous_jobs` incorrectly returned two | The field reports the safe capacity of five while accepted jobs remain two and queued jobs remain zero |

After the green cycles, evidence validation was extracted into one helper and
the focused suite remained green.
