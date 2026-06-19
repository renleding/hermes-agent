import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

from plugins.memory.mempalace_ladybug_projection.mcp import MCPReadAPI
from plugins.memory.mempalace_ladybug_projection.mempalace_adapter import MemPalaceKGAdapter
from plugins.memory.mempalace_ladybug_projection.projection import DroidProjectionWorker, LadybugSQLiteStore


@dataclass(frozen=True)
class RetrievalQuestion:
    entity_id: str
    predicate: str
    expected_object_id: str


class MemPalaceSQLiteAgent:
    """Deterministic agent path that answers from MemPalace's SQLite KG only."""

    def __init__(self, source_db: Path):
        self.con = sqlite3.connect(source_db)

    def answer(self, question: RetrievalQuestion) -> str:
        rows = self.con.execute(
            """
            SELECT subject, object
            FROM triples
            WHERE predicate = ? AND (subject = ? OR object = ?)
            ORDER BY id
            """,
            (question.predicate, question.entity_id, question.entity_id),
        ).fetchall()
        if not rows:
            return ""
        subject, object_id = rows[0]
        return object_id if subject == question.entity_id else subject


class LadybugIndexedAgent:
    """Deterministic agent path that answers from the Ladybug graph cache."""

    def __init__(self, graph: dict):
        self.index: dict[tuple[str, str], list[dict]] = {}
        for edge in graph["edges"]:
            predicate = edge["predicate"]
            if predicate.startswith("inverse:"):
                self.index.setdefault((edge["subject"], predicate.removeprefix("inverse:")), []).append(edge)
            else:
                self.index.setdefault((edge["subject"], predicate), []).append(edge)
                self.index.setdefault((edge["object"], predicate), []).append(edge)

    def answer(self, question: RetrievalQuestion) -> str:
        for edge in self.index.get((question.entity_id, question.predicate), []):
            return edge["object"] if edge["subject"] == question.entity_id else edge["subject"]
        return ""


def _round_ms(value: float) -> float:
    return round(value, 6)


def _p95_ms(latencies_ms: list[float]) -> float:
    ordered = sorted(latencies_ms)
    return _round_ms(ordered[int(len(ordered) * 0.95) - 1])


def _seed_mempalace_kg(source_db: Path, noise_facts: int = 1_000) -> None:
    con = sqlite3.connect(source_db)
    try:
        con.execute("CREATE TABLE entities (id TEXT PRIMARY KEY, name TEXT NOT NULL, type TEXT DEFAULT 'unknown', properties TEXT DEFAULT '{}', created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        con.execute("CREATE TABLE triples (id TEXT PRIMARY KEY, subject TEXT NOT NULL, predicate TEXT NOT NULL, object TEXT NOT NULL, valid_from TEXT, valid_to TEXT, confidence REAL DEFAULT 1.0, source_closet TEXT, source_file TEXT, source_drawer_id TEXT, adapter_name TEXT, extracted_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        con.executemany(
            "INSERT INTO entities VALUES (?, ?, ?, ?, ?)",
            [
                ("person:warren-l", "Warren L", "person", "{}", "2026-06-19T00:00:00Z"),
                ("project:edgegde", "EdgeGDE", "project", "{}", "2026-06-19T00:00:00Z"),
                ("project:hermes-agent", "Hermes Agent", "project", "{}", "2026-06-19T00:00:00Z"),
                ("tool:hermes", "Hermes", "tool", "{}", "2026-06-19T00:00:00Z"),
                ("tool:deepseek", "DeepSeek", "tool", "{}", "2026-06-19T00:00:00Z"),
                ("tool:qwen3-vl", "Qwen3 VL", "tool", "{}", "2026-06-19T00:00:00Z"),
                ("tool:telegram", "Telegram", "tool", "{}", "2026-06-19T00:00:00Z"),
                ("project:canvas", "Canvas", "project", "{}", "2026-06-19T00:00:00Z"),
                ("project:ladybug", "Ladybug projection", "project", "{}", "2026-06-19T00:00:00Z"),
                ("project:mempalace", "MemPalace", "project", "{}", "2026-06-19T00:00:00Z"),
                ("drawer:core", "Core drawer", "drawer", "{}", "2026-06-19T00:00:00Z"),
            ],
        )
        con.executemany(
            "INSERT INTO triples VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("fact-001", "person:warren-l", "works_on", "project:edgegde", "2026-06-19", None, 1.0, "memory-reference", "core.md", "drawer:core", "mempalace", "2026-06-19T00:00:00Z"),
                ("fact-002", "person:warren-l", "prefers", "tool:hermes", "2026-06-19", None, 1.0, "memory-reference", "core.md", "drawer:core", "mempalace", "2026-06-19T00:00:00Z"),
                ("fact-003", "person:warren-l", "uses_model", "tool:qwen3-vl", "2026-06-19", None, 1.0, "memory-reference", "core.md", "drawer:core", "mempalace", "2026-06-19T00:00:00Z"),
                ("fact-004", "project:edgegde", "uses_tool", "tool:hermes", "2026-06-19", None, 1.0, "memory-reference", "core.md", "drawer:core", "mempalace", "2026-06-19T00:00:00Z"),
                ("fact-005", "project:edgegde", "depends_on", "project:mempalace", "2026-06-19", None, 1.0, "memory-reference", "core.md", "drawer:core", "mempalace", "2026-06-19T00:00:00Z"),
                ("fact-006", "project:mempalace", "has", "drawer:core", "2026-06-19", None, 1.0, "memory-reference", "core.md", "drawer:core", "mempalace", "2026-06-19T00:00:00Z"),
                ("fact-007", "project:edgegde", "has", "project:canvas", "2026-06-19", None, 1.0, "memory-reference", "core.md", "drawer:core", "mempalace", "2026-06-19T00:00:00Z"),
                ("fact-008", "project:canvas", "has", "project:ladybug", "2026-06-19", None, 1.0, "memory-reference", "core.md", "drawer:core", "mempalace", "2026-06-19T00:00:00Z"),
                ("fact-009", "project:hermes-agent", "depends_on", "project:edgegde", "2026-06-19", None, 1.0, "memory-reference", "core.md", "drawer:core", "mempalace", "2026-06-19T00:00:00Z"),
                ("fact-010", "project:edgegde", "uses_tool", "tool:telegram", "2026-06-19", None, 1.0, "memory-reference", "core.md", "drawer:core", "mempalace", "2026-06-19T00:00:00Z"),
                ("fact-011", "project:edgegde", "uses_model", "tool:deepseek", "2026-06-19", None, 1.0, "memory-reference", "core.md", "drawer:core", "mempalace", "2026-06-19T00:00:00Z"),
            ],
        )
        for index in range(noise_facts):
            project_id = f"project:noise-{index:04d}"
            drawer_id = f"drawer:noise-{index:04d}"
            con.execute("INSERT INTO entities VALUES (?, ?, ?, ?, ?)", (project_id, f"Noise Project {index}", "project", "{}", "2026-06-19T00:00:00Z"))
            con.execute("INSERT INTO entities VALUES (?, ?, ?, ?, ?)", (drawer_id, f"Noise Drawer {index}", "drawer", "{}", "2026-06-19T00:00:00Z"))
            con.execute("INSERT INTO triples VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (f"noise-{index:04d}", project_id, "has", drawer_id, "2026-06-19", None, 1.0, "memory-reference", "noise.md", drawer_id, "mempalace", "2026-06-19T00:00:00Z"))
        con.commit()
    finally:
        con.close()


def _benchmark_questions(repeats: int = 200) -> list[RetrievalQuestion]:
    questions = [
        RetrievalQuestion("person:warren-l", "works_on", "project:edgegde"),
        RetrievalQuestion("project:edgegde", "uses_tool", "tool:hermes"),
        RetrievalQuestion("tool:hermes", "prefers", "person:warren-l"),
        RetrievalQuestion("project:mempalace", "has", "drawer:core"),
        RetrievalQuestion("project:hermes-agent", "depends_on", "project:edgegde"),
    ]
    return questions * repeats


def _benchmark_agent(agent, questions: list[RetrievalQuestion]) -> dict:
    latencies_ms = []
    correct = 0
    for question in questions:
        start = time.perf_counter_ns()
        answer = agent.answer(question)
        latencies_ms.append((time.perf_counter_ns() - start) / 1_000_000)
        correct += int(answer == question.expected_object_id)

    return {
        "accuracy": correct / len(questions),
        "mean_ms": _round_ms(mean(latencies_ms)),
        "p95_ms": _p95_ms(latencies_ms),
    }


def run_speed_accuracy_comparison(tmp_path: Path) -> dict:
    source_db = tmp_path / "knowledge_graph.sqlite3"
    projection_dir = tmp_path / "projection"
    _seed_mempalace_kg(source_db)

    triples = MemPalaceKGAdapter(source_db).read_triples()
    manifest = DroidProjectionWorker(projection_dir).build(source_db)
    graph = MCPReadAPI(LadybugSQLiteStore(projection_dir / "active" / "ladybug.sqlite3"))._load_graph_from_store()
    questions = _benchmark_questions()

    mempalace_only = _benchmark_agent(MemPalaceSQLiteAgent(source_db), questions)
    ladybug_mempalace = _benchmark_agent(LadybugIndexedAgent(graph), questions)
    mean_speedup = mempalace_only["mean_ms"] / ladybug_mempalace["mean_ms"]
    p95_speedup = mempalace_only["p95_ms"] / ladybug_mempalace["p95_ms"]

    return {
        "triple_count": len(triples),
        "question_count": len(questions),
        "manifest": {
            "fact_count": manifest["fact_count"],
            "edge_count": manifest["edge_count"],
            "entity_count": manifest["entity_count"],
        },
        "memPalace_only": mempalace_only,
        "ladybug_memPalace": ladybug_mempalace,
        "speedup": {
            "mean": _round_ms(mean_speedup),
            "p95": _round_ms(p95_speedup),
        },
    }


def test_memPalace_only_vs_ladybug_memPalace_speed_accuracy_comparison(tmp_path):
    comparison = run_speed_accuracy_comparison(tmp_path)

    assert comparison["manifest"] == {
        "fact_count": 1_011,
        "edge_count": 2_022,
        "entity_count": 2_011,
    }
    assert comparison["memPalace_only"]["accuracy"] == 1.0
    assert comparison["ladybug_memPalace"]["accuracy"] == 1.0
    assert comparison["ladybug_memPalace"]["mean_ms"] < comparison["memPalace_only"]["mean_ms"]
    assert comparison["ladybug_memPalace"]["p95_ms"] < comparison["memPalace_only"]["p95_ms"]
