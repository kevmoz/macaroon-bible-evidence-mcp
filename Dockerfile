# Glama (https://glama.ai/mcp/servers) requires a Dockerfile that starts the
# server and responds to MCP introspection over stdio -- see the sibling
# macaroonnetwork-mcp repo's own Dockerfile note (awesome-mcp-servers PR
# #12148 bot comment) for the same requirement. This mirrors that pattern:
# a pip-installable package with a console-script stdio entrypoint (see
# pyproject.toml's [project.scripts]).
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY macaroon_bible_evidence_mcp ./macaroon_bible_evidence_mcp

RUN pip install --no-cache-dir .

# Talks MCP over stdio, same as every other client (Claude Desktop, uvx, etc.) --
# no network port, no server-held secrets, no required env vars to start.
# (The hosted streamable-HTTP transport in server.json's "remotes" is a
# separate, already-live deployment -- this Dockerfile is for local/stdio use.)
ENTRYPOINT ["macaroon-bible-evidence-mcp"]
