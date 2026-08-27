# The blind reviewer's entire observable world.
#
# This image contains display and screenshot tooling plus the Godot runtime —
# and nothing about this repository. The candidate arrives only as a read-only
# /workspace mount assembled by build_workspace.py from the packet at the
# candidate SHA. That mount is where the review objective lives: the packet
# carries the Issue's approved acceptance contract, quoted in full in the
# reviewer's prompt — the reviewer always knows what the artifact is supposed
# to be, never how it was made. The container runs with --network none: model
# calls happen on the host, so no credential ever needs to exist in here.
#
# Build:
#   docker build -f scripts/blind_review/sandbox.Dockerfile \
#     -t qwen-pipeline/blind-review-sandbox scripts/blind_review

FROM debian:13-slim

ARG GODOT_VERSION=4.7.2
ARG GODOT_RELEASE_BASE=https://github.com/godotengine/godot/releases/download

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        unzip \
        xvfb \
        xauth \
        x11-utils \
        xdotool \
        imagemagick \
        libfontconfig1 \
        libgl1 \
        libegl1 \
        libgles2 \
        mesa-utils \
        libasound2 \
        libpulse0 \
        libudev1 \
        libxcursor1 \
        libxinerama1 \
        libxrandr2 \
        libxi6 \
        libxkbcommon0 \
        fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# Godot, verified against the checksums published with the same release.
RUN set -eu; \
    cd /tmp; \
    zip="Godot_v${GODOT_VERSION}-stable_linux.x86_64.zip"; \
    curl -fsSL --retry 3 -o "$zip" \
        "${GODOT_RELEASE_BASE}/${GODOT_VERSION}-stable/${zip}"; \
    curl -fsSL --retry 3 -o SHA512-SUMS.txt \
        "${GODOT_RELEASE_BASE}/${GODOT_VERSION}-stable/SHA512-SUMS.txt"; \
    grep " ${zip}\$" SHA512-SUMS.txt | sha512sum -c -; \
    unzip -q "$zip"; \
    mv "Godot_v${GODOT_VERSION}-stable_linux.x86_64" /usr/local/bin/godot; \
    chmod +x /usr/local/bin/godot; \
    rm -f "$zip" SHA512-SUMS.txt

ENV DISPLAY=:99
WORKDIR /workspace
