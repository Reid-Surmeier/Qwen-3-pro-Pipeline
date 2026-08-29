# The sandbox the hourly issue sweep runs this repo's agents in.
#
# Built by the sweep from this file (image tag = hash of this file), so a change
# here takes effect on the next cycle. Keep: a non-root user, git, gh, and the
# agent CLIs on PATH. Add this repo's own runtime below the marker.
#
# Base and layout follow sandcastle's claude-code template: the worktree is
# bind-mounted at /home/agent/workspace and the container idles until an agent
# is exec'd into it.

FROM node:22-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
  git curl jq ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# GitHub CLI — prompts inside the sandbox read the issue with `gh`.
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
  | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
  && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
  | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
  && apt-get update && apt-get install -y gh \
  && rm -rf /var/lib/apt/lists/*

# Agent CLIs that install as root (global npm).
RUN npm install -g @openai/codex opencode-ai@latest

# Python for this repo: AGENTS.md's baseline runs `python3.12`; Debian bookworm ships 3.11,
# so the agent user gets a uv-managed CPython 3.12 (installed below, after the USER switch).
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv \
  && rm -rf /var/lib/apt/lists/*

# UID/GID alignment with the host user, so files the agent writes are the owner's.
ARG AGENT_UID=1000
ARG AGENT_GID=1000
RUN groupmod -o -g $AGENT_GID node && usermod -o -u $AGENT_UID -g $AGENT_GID -d /home/agent -m -l agent node
USER ${AGENT_UID}:${AGENT_GID}

# Claude Code installs per user.
RUN curl -fsSL https://claude.ai/install.sh | bash
ENV PATH="/home/agent/.local/bin:$PATH"

# uv and a CPython 3.12 for the agent user; `python3.12` on PATH is what the verify commands call.
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
  && uv python install 3.12 \
  && ln -sf "$(uv python find 3.12)" /home/agent/.local/bin/python3.12 \
  && python3.12 --version

WORKDIR /home/agent
ENTRYPOINT ["sleep", "infinity"]
