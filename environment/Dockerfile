FROM node:20-bookworm-slim@sha256:3d0f05455dea2c82e2f76e7e2543964c30f6b7d673fc1a83286736d44fe4c41c

WORKDIR /app

# Install system dependencies (no test-only packages like pytest here)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
        procps \
        python3 \
        python3-pip \
        python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment but DO NOT install pytest yet
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy API package.json and install
COPY api/package.json api/package-lock.json /app/api/
RUN cd /app/api && npm ci

# Copy CLI package.json and install
COPY cli/package.json cli/package-lock.json /app/cli/
RUN cd /app/cli && npm ci

# Copy source code
COPY api/ /app/api/
COPY cli/ /app/cli/

# Set executable permission for the CLI
RUN chmod +x /app/cli/index.js

# Ensure local CLI bin is in path
ENV PATH="/app/cli:$PATH"

# Make sure tests have a place to write
RUN mkdir -p /logs/verifier
