# Memory 2.0: MemPalace + LadybugDB Projection v0.2.0

## Purpose

MemPalace remains the source of truth for Hermes memory. This plugin adds a mandatory read-only LadybugDB-compatible projection for bounded graph retrieval through Aegis-gated MCP-style read tools.

## Invariants

- MemPalace owns memory truth.
- LadybugDB-compatible projection is mandatory but read-only.
- Droid rebuilds projection from MemPalace facts.
- Aegis gates every query.
- Hermes approves schema and policy changes.
- Agents use read-only MCP/provider tools only.
- No API keys, tokens, passwords, secrets, credentials, or connection strings are stored in this feature.

## Phase coverage

| Phase | Artifact |
|---|---|
| 0 | Governance invariants in this document and plugin manifest |
| 1 | `ontology.py` entity/predicate policy |
| 2 | `mempalace_adapter.py` SQLite KG adapter |
| 3 | `projection.py` LadybugDB-compatible schema |
| 4 | `DroidProjectionWorker` deterministic rebuild |
| 5 | `aegis.py` policy gate |
| 6 | `mcp.py` read-only MCP API contract |
| 7 | `retriever.py` bounded graph context |
| 8 | `projection.py` manifest, staging, rollback pointer |
| 9 | benchmark plan/results documented separately |
| 10 | provider registration and rollout guardrails |

## Provider

- Name: `mempalace-ladybug-projection`
- Manifest: `plugins/memory/mempalace_ladybug_projection/plugin.yaml`
- Provider: `plugins/memory/mempalace_ladybug_projection/provider.py`
- Tools:
  - `mempalace_ladybug_entity`
  - `mempalace_ladybug_subgraph`
  - `mempalace_ladybug_manifest`

## Testing

Run:

```bash
pytest -q tests/plugins/memory/test_mempalace_ladybug_projection.py
```

## Rollout

This is a local controlled rollout implementation. No production deployment is performed unless separately requested.
