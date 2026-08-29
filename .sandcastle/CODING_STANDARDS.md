# Coding standards the reviewer enforces

<!-- The sweep's reviewer reads this file. Keep it short and specific to this repository. -->

- Follow `AGENTS.md`; where this file and `AGENTS.md` disagree, `AGENTS.md` wins.
- Errors are values, not exceptions, wherever the codebase already does that.
- Tests assert behaviour through an existing seam; no new seams invented for a test.
- No secret values, no `.env` files, no credentials in logs or commit messages.
- Commit messages: conventional, prefixed `SWEEP:` by the sweep's agents.
