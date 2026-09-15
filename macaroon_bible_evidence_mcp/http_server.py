"""Hosted Streamable HTTP transport for the Faith-only MCP server."""
from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from .server import _build_mcp_server


def _build_app() -> Starlette:
    from mcp.server.streamable_http_manager import (
        StreamableHTTPASGIApp,
        StreamableHTTPSessionManager,
    )

    server, _stdio_server = _build_mcp_server()
    manager = StreamableHTTPSessionManager(app=server, json_response=True)
    http_app = StreamableHTTPASGIApp(manager)

    async def health(_request):
        return JSONResponse({
            "status": "ok",
            "server": "macaroon-bible-evidence",
            "version": "0.3.0",
            "scope": "read-only-faith",
        })

    @contextlib.asynccontextmanager
    async def lifespan(_app: Starlette) -> AsyncIterator[None]:
        async with manager.run():
            yield

    return Starlette(
        routes=[Route("/health", health), Mount("/mcp", app=http_app)],
        lifespan=lifespan,
    )


app = _build_app()
