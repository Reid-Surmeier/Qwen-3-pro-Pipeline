# `.sandcastle/` — how agents run in this repository

This folder is this repository's rules for the hourly issue sweep (`Reid-Surmeier/issue-sweep`) and for anyone running [sandcastle](https://github.com/mattpocock/sandcastle) against it by hand.

| File | Owns |
| --- | --- |
| `Dockerfile` | The toolchain the agents get. The sweep builds it (tag = hash of the file). |
| `implement-prompt.md` | How the implementer behaves here: what to read, what to run, what never to touch, when to say `<promise>COMPLETE</promise>`. |
| `review-prompt.md` | How the reviewer behaves: spec, standards, correctness, safety; fixes on the branch. |
| `CODING_STANDARDS.md` | What the reviewer enforces. |
| `sweep.json` | Orchestration rules: `verify` commands, `maxIterations` (Ralph loop), `maxAttempts`, model `rotation`, `setup`, `paused`. |
| `.env.example` | Names of the credentials the sandbox receives. Values never live here. |

Placeholders the sweep fills in the prompts: `{{ISSUE_NUMBER}}`, `{{ISSUE_TITLE}}`, `{{BRANCH}}`, `{{BASE_BRANCH}}`, `{{VERIFY_COMMANDS}}`, `{{VERIFY_OUTPUT}}` (review only), `{{ATTEMPT}}`, `{{MAX_ATTEMPTS}}`, `{{SKILLS_NOTE}}`. Lines like `` !`gh issue view …` `` run inside the sandbox when the prompt is expanded.

`logs/`, `worktrees/`, `locks/`, `patches/` are sandcastle's working directories and are ignored.
