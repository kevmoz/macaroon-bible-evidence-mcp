# Macaroon Bible Evidence

Free, read-only MCP server for source-labelled Christian Scripture evidence — exact
Berean Standard Bible (BSB) / World English Bible (WEB) verse lookup, passage context,
translation comparison, cross-references, keyword search, and topic guides.

Every response carries a source label, corpus version, and deterministic content hash.
No wallet, purchase, or execution tool is exposed — this server is read-only by design.

- **Hosted remote server, no install required.**
- **Endpoint:** `https://api.macaroonnetwork.com/mcp-faith-evidence-v1/mcp/`
- **Transport:** Streamable HTTP
- **Official MCP Registry name:** `com.macaroonnetwork/bible-evidence`
- **Site:** [macaroonnetwork.com/bible-api](https://macaroonnetwork.com/bible-api)

## Tools

| Tool | Description |
|---|---|
| `faith_scripture_lookup` | Retrieve one to five exact, same-chapter verses from pinned BSB or WEB evidence. |
| `faith_passage_context_preview` | Return the requested verse with one same-chapter verse before and after; no generated interpretation. |
| `faith_passage_compare_preview` | Compare one exact verse in BSB and WEB without blending or interpreting the source texts. |
| `faith_cross_references_preview` | Return one sourced cross-reference for an exact verse, with relationship attribution. |
| `faith_scripture_search_preview` | Return up to three literal corpus matches for a short keyword or phrase. |
| `faith_topic_guide_preview` | Return a deterministic source-labelled evidence guide for one supported topic. |
| `faith_services_list` | List public, sale-ready Christian Faith and Theology services. |
| `faith_services_search` | Search public Christian services with a short, non-personal capability query. |
| `faith_service_detail` | Get current details for one public Christian Faith service. |
| `faith_service_evidence` | Get validation evidence and limitations for one public Christian Faith service. |
| `faith_service_page` | Get an external Macaroon page without executing or paying for a service. |

## Connect (hosted, no install)

Point any MCP-capable client (Claude, Cursor, Windsurf, etc.) at the Streamable HTTP
endpoint above. No API key or configuration is required.

```json
{
  "mcpServers": {
    "macaroon-bible-evidence": {
      "url": "https://api.macaroonnetwork.com/mcp-faith-evidence-v1/mcp/"
    }
  }
}
```

## Connect (local stdio)

The same server also runs locally over stdio. Not yet published to PyPI —
install straight from this repo:

```bash
pip install git+https://github.com/kevmoz/macaroon-bible-evidence-mcp.git
```

```json
{
  "mcpServers": {
    "macaroon-bible-evidence": {
      "command": "macaroon-bible-evidence-mcp"
    }
  }
}
```

## About

This repository is a source mirror of the Faith Evidence MCP server that is part of
[Macaroon Network](https://macaroonnetwork.com), a marketplace where AI agents discover
and pay for live data and scientific computing capabilities. The Bible Evidence server
itself is free and requires no payment — it exists to demonstrate the same
source-labelled, falsifiable-evidence discipline the rest of the marketplace runs on.

## License

MIT
