# Memory 2.0: MemPalace/Ladybug Memory Retrieval Test Report

## Summary

A deterministic pytest benchmark was added to compare two memory retrieval paths for an agent:

1. **MemPalace-only** — answer memory questions directly from the MemPalace SQLite knowledge graph.
2. **Ladybug/MemPalace** — answer the same questions from the Ladybug-compatible graph projection built from MemPalace.

The test verifies both **accuracy** and **speed**.

Current result: both paths are **100% accurate**, while the Ladybug/MemPalace indexed path is materially faster for repeated agent memory lookups.

## Files

| Item | Path |
|---|---|
| Test added | `tests/plugins/memory/test_mempalace_ladybug_speed_accuracy.py` |
| Existing projection tests | `tests/plugins/memory/test_mempalace_ladybug_projection.py` |
| Commit | `a6663eae2 test: compare MemPalace-only and Ladybug retrieval speed` |
| Branch | `work/mempalace-ladybug-projection` |
| Fork remote | `renleding/hermes-agent` |

## Verification Command

```bash
pytest -q tests/plugins/memory/test_mempalace_ladybug_speed_accuracy.py tests/plugins/memory/test_mempalace_ladybug_projection.py
```

## Verification Result

```text
8 passed, 1 warning in 0.36s
```

The warning is the existing pytest event-loop warning from `tests/conftest.py`:

```text
DeprecationWarning: There is no current event loop
```

## Test Method

The test creates a synthetic MemPalace SQLite KG with:

| Metric | Value |
|---|---:|
| Source triples | `1,011` |
| Core memory facts | `11` |
| Noise facts | `1,000` |
| Benchmark questions | `1,000` |
| Ladybug nodes/entities | `2,011` |
| Ladybug edges | `2,022` |

The benchmark asks the same 5 memory questions repeatedly:

| Question pattern | Expected answer |
|---|---|
| `person:warren-l` `works_on` | `project:edgegde` |
| `project:edgegde` `uses_tool` | `tool:hermes` |
| `tool:hermes` inverse `prefers` | `person:warren-l` |
| `project:mempalace` `has` | `drawer:core` |
| `project:hermes-agent` `depends_on` | `project:edgegde` |

Each path must return the exact expected entity ID.

## Retrieval Paths Compared

### MemPalace-only

The MemPalace-only agent answers from the source SQLite KG:

```sql
SELECT subject, object
FROM triples
WHERE predicate = ? AND (subject = ? OR object = ?)
ORDER BY id
```

This represents a direct source-of-truth lookup path without the Ladybug projection cache.

### Ladybug/MemPalace

The Ladybug/MemPalace agent answers from the Ladybug projection graph. The test builds an in-memory adjacency index over Ladybug edges, including inverse edges, then answers each question from that index.

This represents the intended low-latency retrieval path:

```text
MemPalace source KG → Ladybug projection → indexed graph lookup
```

## Results

```json
{
  "triple_count": 1011,
  "question_count": 1000,
  "memPalace_only": {
    "accuracy": 1.0,
    "mean_ms": 0.062256,
    "p95_ms": 0.093291
  },
  "ladybug_memPalace": {
    "accuracy": 1.0,
    "mean_ms": 0.000199,
    "p95_ms": 0.000209
  },
  "speedup": {
    "mean": 312.844221,
    "p95": 446.368421
  }
}
```

## Comparison Table

| Metric | MemPalace-only | Ladybug/MemPalace | Result |
|---|---:|---:|---|
| Accuracy | `1.0` | `1.0` | Equal |
| Mean latency | `0.062256 ms` | `0.000199 ms` | Ladybug faster |
| p95 latency | `0.093291 ms` | `0.000209 ms` | Ladybug faster |
| Mean speedup | baseline | `312.84x` | Ladybug faster |
| p95 speedup | baseline | `446.37x` | Ladybug faster |

## Interpretation

The test shows:

- The Ladybug projection preserves the answer accuracy of the MemPalace source graph.
- The Ladybug/MemPalace indexed retrieval path is faster for repeated agent memory lookups.
- The projection is deterministic: the test asserts the expected manifest counts:

```json
{
  "fact_count": 1011,
  "edge_count": 2022,
  "entity_count": 2011
}
```

## Important Caveat

This benchmark measures deterministic retrieval latency. It does **not** measure:

- LLM token generation time
- model selection cost
- full Hermes turn latency
- Telegram/gateway overhead
- tool serialization overhead

The test isolates the memory retrieval layer so the result is attributable to the MemPalace vs Ladybug/MemPalace retrieval path.

## Conclusion

The memory test demonstrates that the Ladybug/MemPalace solution is both:

- **Accurate**: returns the same answers as MemPalace-only retrieval.
- **Faster**: reduces repeated lookup latency by more than 300x on mean latency in the synthetic benchmark.

This supports using the Ladybug-compatible projection as the low-latency read path while keeping MemPalace as the source of truth.
