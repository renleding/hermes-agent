# Memory 2.0: MemPalace Ladybug Projection Plugin

Version: `0.2.0`

This memory provider implements the EdgeGDE memory projection design:

- MemPalace is source of truth.
- LadybugDB-compatible projection is mandatory and read-only.
- Droid rebuilds the projection from MemPalace's SQLite KG.
- Aegis gates every query.
- MCP/provider tools are read-only.

## Files

- `__init__.py` — provider registration.
- `provider.py` — Hermes memory provider and read-only tools.
- `models.py` — graph dataclasses.
- `ontology.py` — entity/predicate policy and redaction.
- `aegis.py` — policy gate.
- `mempalace_adapter.py` — MemPalace SQLite KG adapter.
- `projection.py` — Droid worker and LadybugDB-compatible SQLite store.
- `mcp.py` — read-only MCP API surface.
- `retriever.py` — bounded graph retrieval for token efficiency.

## Local setup

Activate with Hermes memory provider config:

```yaml
memory:
  provider: mempalace-ladybug-projection
```

The provider uses:

- MemPalace home: `~/.mempalace` by default.
- Projection output: `$HERMES_HOME/mempalace-ladybug-projection`.

No external API key is required.
