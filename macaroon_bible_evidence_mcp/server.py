"""Faith-only MCP tools backed by Macaroon's public, read-only Faith API."""
from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Any

import requests


_API_BASE = os.environ.get(
    "MACAROON_FAITH_API_URL", "https://api.macaroonnetwork.com"
).rstrip("/")
_EVIDENCE_API_BASE = os.environ.get(
    "MACAROON_FAITH_BACKEND_URL", "https://api.macaroonnetwork.com"
).rstrip("/")
_MAX_RESPONSE_BYTES = 1024 * 1024
_CHRISTIAN_SERVICE_ID = re.compile(r"^christian-[a-z0-9-]+-v[0-9]+$")
_TOOL_TITLES = {
    "faith_scripture_lookup": "Scripture Lookup",
    "faith_passage_context_preview": "Passage Context Preview",
    "faith_passage_compare_preview": "Translation Comparison Preview",
    "faith_cross_references_preview": "Cross-Reference Preview",
    "faith_scripture_search_preview": "Scripture Search Preview",
    "faith_topic_guide_preview": "Topic Evidence Preview",
    "faith_services_list": "List Faith Services",
    "faith_services_search": "Search Faith Services",
    "faith_service_detail": "Faith Service Details",
    "faith_service_evidence": "Faith Service Evidence",
    "faith_service_page": "Faith Service Page",
}
_READ_ONLY_ANNOTATIONS = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}
_OBJECT_OUTPUT_SCHEMA = {
    "type": "object",
    "description": "Structured Macaroon Faith evidence or catalogue result.",
    "additionalProperties": True,
}


class FaithAPIError(RuntimeError):
    """Safe, non-reflective upstream failure."""


class FaithAPIClient:
    def __init__(self, base_url: str = _API_BASE, session: requests.Session | None = None):
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()

    async def post(self, path: str, payload: dict[str, Any] | None) -> dict[str, Any]:
        return await asyncio.to_thread(self._post_sync, path, payload)

    def _post_sync(self, path: str, payload: dict[str, Any] | None) -> dict[str, Any]:
        try:
            response = self.session.post(
                f"{self.base_url}{path}",
                json=payload,
                timeout=(3.0, 12.0),
                allow_redirects=False,
                stream=True,
                headers={"Accept": "application/json", "User-Agent": "MacaroonFaithPlugin/0.3"},
            )
        except requests.RequestException as exc:
            raise FaithAPIError("faith service temporarily unavailable") from exc
        try:
            if response.is_redirect:
                raise FaithAPIError("faith service temporarily unavailable")
            if response.status_code == 404:
                raise FaithAPIError("Christian service unavailable")
            if response.status_code == 422:
                raise FaithAPIError("invalid faith request")
            if response.status_code >= 400:
                raise FaithAPIError("faith service temporarily unavailable")

            content_type = response.headers.get("content-type", "").lower()
            if "application/json" not in content_type:
                raise FaithAPIError("faith service returned an invalid response")
            chunks = []
            size = 0
            for chunk in response.iter_content(chunk_size=65536):
                size += len(chunk)
                if size > _MAX_RESPONSE_BYTES:
                    raise FaithAPIError("faith service response exceeded the safety limit")
                chunks.append(chunk)
            try:
                data = json.loads(b"".join(chunks))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise FaithAPIError("faith service returned an invalid response") from exc
            if not isinstance(data, dict):
                raise FaithAPIError("faith service returned an invalid response")
            return data
        finally:
            response.close()


_client = FaithAPIClient()
_evidence_client = FaithAPIClient(_EVIDENCE_API_BASE)


def _closed_schema(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": required,
    }


def get_tool_definitions() -> list[dict[str, Any]]:
    service_id = {
        "type": "string",
        "pattern": r"^christian-[a-z0-9-]+-v[0-9]+$",
        "description": "Exact public Christian Faith service ID.",
    }
    source_id = {"type": "string", "enum": ["bsb", "web"]}
    book_id = {"type": "string", "minLength": 2, "maxLength": 24}
    chapter = {"type": "integer", "minimum": 1, "maximum": 150}
    verse = {"type": "integer", "minimum": 1, "maximum": 176}
    tools = [
        {
            "name": "faith_scripture_lookup",
            "description": "Retrieve one to five exact, same-chapter verses from pinned BSB or WEB evidence.",
            "inputSchema": _closed_schema(
                {
                    "source_id": source_id,
                    "book_id": book_id,
                    "chapter": chapter,
                    "verse_start": {"type": "integer", "minimum": 1, "maximum": 176},
                    "verse_end": {"type": "integer", "minimum": 1, "maximum": 176},
                },
                ["source_id", "book_id", "chapter", "verse_start", "verse_end"],
            ),
        },
        {
            "name": "faith_passage_context_preview",
            "description": "Return the requested verse with one same-chapter verse before and after; no generated interpretation.",
            "inputSchema": _closed_schema(
                {"source_id": source_id, "book_id": book_id, "chapter": chapter, "verse": verse},
                ["source_id", "book_id", "chapter", "verse"],
            ),
        },
        {
            "name": "faith_passage_compare_preview",
            "description": "Compare one exact verse in BSB and WEB without blending or interpreting the source texts.",
            "inputSchema": _closed_schema(
                {"book_id": book_id, "chapter": chapter, "verse": verse},
                ["book_id", "chapter", "verse"],
            ),
        },
        {
            "name": "faith_cross_references_preview",
            "description": "Return one sourced cross-reference for an exact verse, with relationship attribution.",
            "inputSchema": _closed_schema(
                {"source_id": source_id, "book_id": book_id, "chapter": chapter, "verse": verse},
                ["source_id", "book_id", "chapter", "verse"],
            ),
        },
        {
            "name": "faith_scripture_search_preview",
            "description": "Return up to three literal corpus matches for a short keyword or phrase; not a doctrinal ranking.",
            "inputSchema": _closed_schema(
                {
                    "source_id": source_id,
                    "query": {"type": "string", "minLength": 2, "maxLength": 40},
                },
                ["source_id", "query"],
            ),
        },
        {
            "name": "faith_topic_guide_preview",
            "description": "Return a deterministic source-labelled evidence guide for one supported topic.",
            "inputSchema": _closed_schema(
                {
                    "source_id": source_id,
                    "topic": {
                        "type": "string",
                        "enum": ["anxiety", "hope", "forgiveness", "wisdom", "grief", "justice"],
                    },
                },
                ["source_id", "topic"],
            ),
        },
        {
            "name": "faith_services_list",
            "description": "List public, sale-ready Christian Faith and Theology services.",
            "inputSchema": _closed_schema({}, []),
        },
        {
            "name": "faith_services_search",
            "description": "Search public Christian services with a short, non-personal capability query.",
            "inputSchema": _closed_schema(
                {
                    "query": {"type": "string", "minLength": 1, "maxLength": 200},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 10},
                },
                ["query"],
            ),
        },
        {
            "name": "faith_service_detail",
            "description": "Get current details for one public Christian Faith service.",
            "inputSchema": _closed_schema({"service_id": service_id}, ["service_id"]),
        },
        {
            "name": "faith_service_evidence",
            "description": "Get validation evidence and limitations for one public Christian Faith service.",
            "inputSchema": _closed_schema({"service_id": service_id}, ["service_id"]),
        },
        {
            "name": "faith_service_page",
            "description": "Get an external Macaroon page without executing or paying for a service.",
            "inputSchema": _closed_schema({"service_id": service_id}, ["service_id"]),
        },
    ]
    for tool in tools:
        tool["title"] = _TOOL_TITLES[tool["name"]]
        tool["annotations"] = dict(_READ_ONLY_ANNOTATIONS)
        tool["outputSchema"] = dict(_OBJECT_OUTPUT_SCHEMA)
    return tools


_PATHS = {
    "faith_scripture_lookup": "/api/public/gpt/faith/scripture-lookup",
    "faith_passage_context_preview": "/scripture/context",
    "faith_passage_compare_preview": "/scripture/compare",
    "faith_cross_references_preview": "/scripture/cross-references",
    "faith_scripture_search_preview": "/scripture/search",
    "faith_topic_guide_preview": "/devotional/topic-guide",
    "faith_services_list": "/api/public/gpt/faith/services/list",
    "faith_services_search": "/api/public/gpt/faith/services/search",
    "faith_service_detail": "/api/public/gpt/faith/services/detail",
    "faith_service_evidence": "/api/public/gpt/faith/services/evidence",
    "faith_service_page": "/api/public/gpt/faith/services/page",
}
_SERVICE_TOOLS = {
    "faith_service_detail", "faith_service_evidence", "faith_service_page"
}
_PREVIEW_SERVICES = {
    "faith_passage_context_preview": "christian-scripture-passage-context-v1",
    "faith_passage_compare_preview": "christian-passage-compare-v1",
    "faith_cross_references_preview": "christian-cross-references-v1",
    "faith_scripture_search_preview": "christian-scripture-keyword-search-v1",
    "faith_topic_guide_preview": "christian-topic-scripture-guide-v1",
}


def _ok(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "isError": False,
        "content": [{"type": "text", "text": json.dumps(data, separators=(",", ":"))}],
        "structuredContent": data,
    }


def _error(message: str) -> dict[str, Any]:
    return {"isError": True, "content": [{"type": "text", "text": message}]}


def _valid_arguments(name: str, arguments: dict[str, Any]) -> bool:
    definition = next(
        (tool for tool in get_tool_definitions() if tool["name"] == name), None
    )
    if definition is None:
        return False
    schema = definition["inputSchema"]
    properties = schema["properties"]
    if set(arguments) - set(properties):
        return False
    if any(field not in arguments for field in schema["required"]):
        return False
    for field, value in arguments.items():
        rule = properties[field]
        expected = rule.get("type")
        if expected == "string":
            if not isinstance(value, str):
                return False
            if len(value) < rule.get("minLength", 0) or len(value) > rule.get("maxLength", 10_000):
                return False
            if "enum" in rule and value not in rule["enum"]:
                return False
            if "pattern" in rule and re.fullmatch(rule["pattern"], value) is None:
                return False
        elif expected == "integer":
            if isinstance(value, bool) or not isinstance(value, int):
                return False
            if value < rule.get("minimum", value) or value > rule.get("maximum", value):
                return False
    if name == "faith_scripture_lookup":
        start = arguments["verse_start"]
        end = arguments["verse_end"]
        if end < start or end - start + 1 > 5:
            return False
    return True


async def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    path = _PATHS.get(name)
    if path is None:
        return _error("tool unavailable")
    if not isinstance(arguments, dict):
        return _error("invalid faith request")
    if not _valid_arguments(name, arguments):
        return _error("invalid faith request")
    if name in _SERVICE_TOOLS:
        service_id = arguments.get("service_id")
        if not isinstance(service_id, str) or not _CHRISTIAN_SERVICE_ID.fullmatch(service_id):
            return _error("Christian service unavailable")

    payload = None if name == "faith_services_list" else dict(arguments)
    api_client = _client
    if name in _PREVIEW_SERVICES:
        api_client = _evidence_client
        if name == "faith_passage_context_preview":
            payload.update({"before": 1, "after": 1})
        elif name == "faith_passage_compare_preview":
            verse_number = payload.pop("verse", None)
            payload.update({"verse_start": verse_number, "verse_end": verse_number})
        elif name == "faith_cross_references_preview":
            payload["limit"] = 1
        elif name == "faith_scripture_search_preview":
            payload["limit"] = 3
    try:
        data = await api_client.post(path, payload)
        if name in _PREVIEW_SERVICES:
            data["preview"] = {
                "bounded": True,
                "full_service_id": _PREVIEW_SERVICES[name],
                "full_service_access": "Use faith_service_page for the external paid service.",
            }
        return _ok(data)
    except (FaithAPIError, KeyError, TypeError, ValueError) as exc:
        message = str(exc) if isinstance(exc, FaithAPIError) else "invalid faith request"
        return _error(message)


def _build_mcp_server():
    import mcp.types as types
    from mcp.server import Server
    from mcp.server.stdio import stdio_server

    async def on_list_tools(ctx, params):
        return types.ListToolsResult(tools=[
            types.Tool(
                name=tool["name"],
                title=tool["title"],
                description=tool["description"],
                input_schema=tool["inputSchema"],
                output_schema=tool["outputSchema"],
                annotations=types.ToolAnnotations(**tool["annotations"]),
            )
            for tool in get_tool_definitions()
        ])

    async def on_call_tool(ctx, params):
        result = await call_tool(params.name, params.arguments or {})
        content = [
            types.TextContent(type="text", text=item["text"])
            for item in result["content"]
        ]
        return types.CallToolResult(
            content=content,
            structured_content=result.get("structuredContent"),
            is_error=result["isError"],
        )

    return Server(
        "macaroon-bible-evidence",
        version="0.3.0",
        on_list_tools=on_list_tools,
        on_call_tool=on_call_tool,
    ), stdio_server


async def _main() -> None:
    mcp_server, stdio_server = _build_mcp_server()
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            mcp_server.create_initialization_options(),
        )


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
