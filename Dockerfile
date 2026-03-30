# Zion's Minecraft Mod Builder — UI Server
# Packages the Python web UI for containerized deployment.
# The actual Minecraft server runs on the host — this container
# just serves the UI and delegates to the Claude CLI.

FROM python:3.11-slim

WORKDIR /app

# Copy UI files
COPY ui/ ./ui/
COPY agents/ ./agents/
COPY CLAUDE.md .
COPY AGENTS.md .

# No pip installs needed — server.py uses stdlib only
# (anthropic is only needed for the optional .agent/agent.py)

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8765/status')"

CMD ["python3", "ui/server.py"]
