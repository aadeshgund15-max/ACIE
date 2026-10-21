"""
Adaptive Context Intelligence Engine (ACIE)

Memory Pipeline

Changes vs. the original:
- Ranking blends relevance to the CURRENT query with stored importance
  (the original ranked by stored importance only).
- Expensive "maintenance" stages (consolidation, reflection, graph build)
  are cached and only re-run when the memory store changed or every N calls,
  instead of on every query.
- Compression/summary run on the memories actually selected for this query
  (configurable back to "all").
- Components are injectable (testable); defaults still build the real ones.
- Optional stages are isolated: a failure is recorded, not fatal.
- Returns `ranked_memories` (what ResponseGenerator expects) and `metrics`.
- Rows are converted to dicts once instead of indexing tuples all over.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("acie.memory_pipeline")


# --------------------------------------------------
# Configuration
# --------------------------------------------------

@dataclass
class PipelineConfig:
    token_budget: int = 100          # was hardcoded inside process()
    top_k: int = 5
    relevance_weight: float = 0.6    # ranking = w*relevance + (1-w)*importance
    importance_scale: float = 100.0  # importance values above 1 are divided by this
    compress_scope: str = "retrieved"  # "retrieved" or "all"
    maintenance_every: int = 20      # force a maintenance refresh every N calls
    chars_per_token: int = 4


MEMORY_FIELDS = (
    "id", "query", "importance", "confidence", "decision",
    "created_at", "last_accessed", "access_count", "state",
)

STOPWORDS = frozenset(
    "a an the is are was were be to of in on at for and or but with this "
    "that it as by from what how why when where do does did can you i we "
    "explain please".split()
)

COMPONENT_NAMES = (
    "collector", "importance_scorer", "confidence_calculator",
    "decision_engine", "memory_manager", "compressor", "summarizer",
    "context_builder", "reflection_engine", "graph_builder",
    "graph_retriever", "episodic_memory", "working_memory",
    "memory_consolidation",
)


def default_components() -> Dict[str, Any]:
    """Build the real components lazily so tests can inject fakes."""
    from Backend.collector.context_collector import ContextCollector
    from Backend.scorer.importance_scorer import ImportanceScorer
    from Backend.scorer.confidence_calculator import ConfidenceCalculator
    from Backend.decision_engine.decision_engine import DecisionEngine
    from Backend.memory.memory_manager import MemoryManager
    from Backend.compressor.context_compressor import ContextCompressor
    from Backend.summarizer.memory_summarizer import MemorySummarizer
    from Backend.context_builder.context_window_builder import ContextWindowBuilder
    from Backend.reflection.reflection_engine import ReflectionEngine
    from Backend.knowledge.graph_builder import GraphBuilder
    from Backend.graph_retriever.graph_retriever import GraphRetriever
    from Backend.episodic.episodic_memory import EpisodicMemory
    from Backend.working_memory.working_memory import WorkingMemory
    from Backend.consolidation.memory_consolidation import MemoryConsolidation

    return {
        "collector": ContextCollector(),
        "importance_scorer": ImportanceScorer(),
        "confidence_calculator": ConfidenceCalculator(),
        "decision_engine": DecisionEngine(),
        "memory_manager": MemoryManager(),
        "compressor": ContextCompressor(),
        "summarizer": MemorySummarizer(),
        "context_builder": ContextWindowBuilder(),
        "reflection_engine": ReflectionEngine(),
        "graph_builder": GraphBuilder(),
        "graph_retriever": GraphRetriever(),
        "episodic_memory": EpisodicMemory(),
        "working_memory": WorkingMemory(),
        "memory_consolidation": MemoryConsolidation(),
    }


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def _row_to_memory(row: Any) -> dict:
    """Accept dicts, sqlite3.Row, or plain tuples in MEMORY_FIELDS order."""
    if isinstance(row, dict):
        return dict(row)
    if hasattr(row, "keys"):
        return {k: row[k] for k in row.keys()}
    return dict(zip(MEMORY_FIELDS, row))


def _terms(text: str) -> set:
    tokens = re.findall(r"[a-zA-Z0-9']+", str(text).lower())
    return {t for t in tokens if t not in STOPWORDS and len(t) > 2}


def _lexical_relevance(query: str, text: str) -> float:
    q = _terms(query)
    if not q:
        return 0.0
    return len(q & _terms(text)) / len(q)


# --------------------------------------------------
# Pipeline
# --------------------------------------------------

class MemoryPipeline:

    collector: Any
    importance_scorer: Any
    confidence_calculator: Any
    decision_engine: Any
    memory_manager: Any
    compressor: Any
    summarizer: Any
    context_builder: Any
    reflection_engine: Any
    graph_builder: Any
    graph_retriever: Any
    episodic_memory: Any
    working_memory: Any
    memory_consolidation: Any

    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        components: Optional[Dict[str, Any]] = None,
        **overrides: Any,
    ):
        self.config = config or PipelineConfig()

        parts = dict(components) if components else {}
        parts.update(overrides)
        missing = [n for n in COMPONENT_NAMES if n not in parts]
        if missing:
            parts = {**default_components(), **parts}

        for name in COMPONENT_NAMES:
            setattr(self, name, parts[name])

        self._calls = 0
        self._maintenance: Optional[dict] = None
        self._maintenance_sig: Any = None
        self._maintenance_age = 0

    # ----------------------------------------------
    # Stage runner
    # ----------------------------------------------

    def _run(self, name: str, fn: Callable[[], Any], timings: dict,
             errors: dict, default: Any = None, critical: bool = False):
        start = time.perf_counter()
        try:
            return fn()
        except Exception as exc:
            logger.exception("Stage '%s' failed", name)
            if critical:
                raise
            errors[name] = f"{type(exc).__name__}: {exc}"
            return default
        finally:
            timings[name] = round((time.perf_counter() - start) * 1000, 2)

    # ----------------------------------------------
    # Maintenance (cached)
    # ----------------------------------------------

    def _get_maintenance(self, memories: List[dict], timings: dict, errors: dict):
        """Consolidation + reflection + graph. Refreshed only when needed."""
        signature = (len(memories), memories[-1].get("id") if memories else None)
        self._maintenance_age += 1

        stale = (
            self._maintenance is None
            or signature != self._maintenance_sig
            or self._maintenance_age >= self.config.maintenance_every
        )
        if not stale:
            timings["maintenance"] = 0.0
            return self._maintenance, True

        start = time.perf_counter()
        consolidated = self._run(
            "consolidation",
            lambda: self.memory_consolidation.consolidate(memories),
            timings, errors, default=memories,
        )
        reflection = self._run(
            "reflection",
            lambda: self.reflection_engine.generate_report(consolidated),
            timings, errors, default={},
        )

        def build_graph():
            self.graph_builder.build(consolidated)
            return self.graph_builder.statistics()

        stats = self._run("graph", build_graph, timings, errors,
                          default={"nodes": 0, "relationships": 0})
        timings["maintenance"] = round((time.perf_counter() - start) * 1000, 2)

        self._maintenance = {
            "consolidated": consolidated,
            "reflection": reflection,
            "graph_statistics": stats,
        }
        self._maintenance_sig = signature
        self._maintenance_age = 0
        return self._maintenance, False

    # ----------------------------------------------
    # Ranking
    # ----------------------------------------------

    def _importance_norm(self, value: Any) -> float:
        try:
            v = float(value)
        except (TypeError, ValueError):
            return 0.0
        if v > 1.0:
            v = v / self.config.importance_scale
        return max(0.0, min(1.0, v))

    def _rank(self, query: str, memories: List[dict]) -> List[dict]:
        w = self.config.relevance_weight
        ranked = []
        for m in memories:
            text = m.get("query", "")
            provided = next(
                (m[k] for k in ("relevance", "similarity", "score", "graph_score")
                 if isinstance(m.get(k), (int, float))),
                None,
            )
            relevance = (
                max(0.0, min(1.0, float(provided)))
                if provided is not None
                else _lexical_relevance(query, text)
            )
            importance = self._importance_norm(m.get("importance"))
            ranked.append({
                "id": m.get("id"),
                "text": text,
                "relevance": round(relevance, 3),
                "importance": round(importance, 3),
                "ranking_score": round(w * relevance + (1 - w) * importance, 3),
            })
        ranked.sort(key=lambda r: r["ranking_score"], reverse=True)
        return ranked

    # ----------------------------------------------
    # Process
    # ----------------------------------------------

    def process(self, query, conversation, documents) -> dict:
        self._calls += 1
        timings: Dict[str, float] = {}
        errors: Dict[str, str] = {}
        cfg = self.config

        # ---- core stages (failures propagate) ----
        context = self._run(
            "collect",
            lambda: self.collector.collect(
                query=query, conversation=conversation, documents=documents),
            timings, errors, critical=True)

        importance = self._run(
            "importance",
            lambda: self.importance_scorer.calculate_score(context),
            timings, errors, critical=True)

        confidence = self._run(
            "confidence",
            lambda: self.confidence_calculator.calculate_confidence(context),
            timings, errors, critical=True)

        decision = self._run(
            "decision",
            lambda: self.decision_engine.decide(importance, confidence),
            timings, errors, critical=True)

        # working memory now receives the real importance (was always 0)
        self._run(
            "working_memory",
            lambda: self.working_memory.add_context(
                query=query, importance=importance, source="user"),
            timings, errors)

        memory_id = None
        if decision == "STORE":
            memory_id = self._run(
                "store",
                lambda: self.memory_manager.store(
                    context, importance, confidence, decision),
                timings, errors, critical=True)

        # ---- load + cached maintenance ----
        rows = self._run(
            "load_memories", self.memory_manager.get_all_memories,
            timings, errors, default=[], critical=True)
        memories = [_row_to_memory(r) for r in rows]

        maintenance, cache_hit = self._get_maintenance(memories, timings, errors)
        maintenance = maintenance or {}
        consolidated = maintenance.get("consolidated") or memories

        # ---- retrieval + relevance-aware ranking ----
        graph_results = self._run(
            "retrieval",
            lambda: self.graph_retriever.retrieve(
                query, consolidated, top_k=cfg.top_k),
            timings, errors, default={"expanded_memories": []})

        candidates = (graph_results or {}).get("expanded_memories") or []
        ranked = self._rank(query, candidates)[: cfg.top_k]

        context_window = self._run(
            "context_window",
            lambda: self.context_builder.build(
                [{"text": r["text"], "ranking_score": r["ranking_score"]}
                 for r in ranked],
                token_budget=cfg.token_budget),
            timings, errors, default={})

        # ---- compression + summary on what was actually selected ----
        if cfg.compress_scope == "all":
            compress_texts = [m.get("query", "") for m in consolidated]
        else:
            compress_texts = [r["text"] for r in ranked]

        compression = self._run(
            "compression",
            lambda: self.compressor.compress(compress_texts),
            timings, errors, default={"compressed_memories": compress_texts})

        summary = self._run(
            "summary",
            lambda: self.summarizer.summarize(
                (compression or {}).get("compressed_memories", compress_texts)),
            timings, errors, default="")

        episode = self._run(
            "episode",
            lambda: self.episodic_memory.create_episode(
                query=query, conversation=conversation, documents=documents,
                importance=importance, confidence=confidence,
                decision=decision,
                outcome=("Memory Stored" if memory_id is not None
                         else "Memory Not Stored")),
            timings, errors)

        working = self._run(
            "working_context", self.working_memory.get_recent_context,
            timings, errors, default=[])

        raw_tokens = sum(len(t) for t in compress_texts) // cfg.chars_per_token
        stats = maintenance.get("graph_statistics") or {}

        return {
            "memory_id": memory_id,
            "importance": importance,
            "confidence": confidence,
            "decision": decision,
            "working_memory": working,
            "episode": episode,
            "consolidated_memories": consolidated,
            "compression": compression,
            "summary": summary,
            "reflection": maintenance.get("reflection", {}),
            "knowledge_graph": {
                "nodes": stats.get("nodes", 0),
                "relationships": stats.get("relationships", 0),
            },
            "graph_retrieval": graph_results,
            "ranked_memories": ranked,       # consumed by ResponseGenerator
            "context_window": context_window,
            "metrics": {
                "stage_ms": timings,
                "stage_errors": errors,
                "maintenance_cache_hit": cache_hit,
                "memories_in_store": len(memories),
                "memories_selected": len(ranked),
                "raw_token_estimate": raw_tokens,
                "context_window_tokens": (
                    context_window.get("tokens")
                    if isinstance(context_window, dict) else None),
            },
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    pipeline = MemoryPipeline()
    result = pipeline.process(
        query="Explain adaptive context compression.",
        conversation=["What is semantic search?", "Explain embeddings."],
        documents=["Research Paper A", "Research Paper B"],
    )
    print(result["ranked_memories"])
    print(result["metrics"])