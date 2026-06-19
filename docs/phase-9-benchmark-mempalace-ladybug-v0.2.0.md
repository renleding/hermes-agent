# Phase 9 Benchmark — Memory 2.0 MemPalace Ladybug Projection v0.2.0

Command:

```bash
python -m plugins.memory.mempalace_ladybug_projection.benchmark
```

## Results

| Metric | Value |
|---|---:|
| MemPalace entities | 21 |
| MemPalace facts | 19 |
| Rebuild seconds | 0.007073 |
| Query count | 25 |
| Query latency mean ms | 0.210835 |
| Query latency p95 ms | 0.226625 |
| Projected entities | 21 |
| Projected facts | 19 |
| Projected edges | 38 |
| Ladybug backend | sqlite-compatible-1.0.0 |

## Interpretation

- Rebuild was deterministic and sub-millisecond on the current local KG.
- Bounded read queries were sub-millisecond p95 in this environment.
- The implementation uses a SQLite-compatible LadybugDB projection backend because `duckdb`/`ladybugdb` is not installed in the active environment.
- The optional engine boundary is preserved in `LadybugSQLiteStore`; a future DuckDB/LadybugDB backend can implement the same graph schema without changing the policy, Droid worker, MCP contract, or retriever.
