"""
Adaptive Context Intelligence Engine (ACIE)

Reasoning Engine

Responsible for:
- Query analysis (type, complexity, entities)
- Dynamic reasoning plans
- Evidence-based confidence scoring
- Answer verification (grounding, degeneration checks)
- Reflection that points at concrete problems

Everything tunable lives in ReasoningConfig. Classification is rule-based
but weighted and word-boundary safe; pass `classifier=` to plug in an LLM or
ML model that overrides the rules when it returns a type.
"""

from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

# --------------------------------------------------
# Configuration
# --------------------------------------------------

# type -> list of (regex, weight). Word boundaries avoid "how" matching "show".
DEFAULT_TYPE_PATTERNS: Dict[str, List[tuple]] = {
    "explanation": [
        (r"\bwhy\b", 2), (r"\bexplain\b", 3), (r"\breason(s)?\b", 2),
        (r"\bwhat is\b", 1), (r"\bmeaning of\b", 2),
    ],
    "problem_solving": [
        (r"\bhow (do|can|to|should)\b", 3), (r"\bcreate\b", 2),
        (r"\bbuild\b", 2), (r"\bfix\b", 2), (r"\bsolve\b", 2),
    ],
    "comparison": [
        (r"\bcompare\b", 3), (r"\bdifference(s)?\b", 3),
        (r"\bversus\b|\bvs\.?\b", 3), (r"\bbetter than\b", 2),
    ],
    "incident_report": [
        (r"\b(fire|flood|collapse|explosion|accident|crash|earthquake)\b", 3),
        (r"\b(injured|trapped|unconscious|bleeding|casualt(y|ies))\b", 3),
        (r"\b(reported|spotted|happening)\b", 1),
    ],
    "resource_request": [
        (r"\b(send|dispatch|deploy)\b", 3), (r"\brecommend\b", 2),
        (r"\b(ambulance|fire ?truck|police|rescue|unit(s)?)\b", 2),
        (r"\bneed(s|ed)?\b", 1),
    ],
    "status_query": [
        (r"\bstatus\b", 3), (r"\bupdate\b", 2), (r"\bwhere is\b", 3),
        (r"\bhow many\b", 2), (r"\bany news\b", 2),
    ],
}

STOPWORDS = frozenset(
    "a an the is are was were be been to of in on at for and or but with "
    "this that these those it its as by from into about what which who "
    "how why when where do does did can could should would will you i we "
    "me my our your please tell give explain describe compare show list summarize define".split()
)

CONJUNCTIONS = re.compile(r"\b(and|but|also|then|while|however|after)\b")


@dataclass
class ReasoningConfig:
    type_patterns: Dict[str, List[tuple]] = field(
        default_factory=lambda: dict(DEFAULT_TYPE_PATTERNS)
    )
    # complexity points: >= medium_at -> medium, >= high_at -> high
    medium_at: int = 2
    high_at: int = 4
    long_query_words: int = 15
    mid_query_words: int = 6
    # confidence = weighted sum of three evidence signals
    w_coverage: float = 0.5   # how many query terms the context covers
    w_retrieval: float = 0.3  # strength of the retrieved memories
    w_clarity: float = 0.2    # how clearly the query was classified
    min_confidence: float = 0.05
    # verification
    min_answer_chars: int = 20
    min_grounding: float = 0.15   # share of answer terms found in context
    max_repetition: float = 0.30  # min unique-token ratio (below = degenerate)
    history_size: int = 200


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def _content_terms(text: str) -> List[str]:
    tokens = re.findall(r"[a-zA-Z0-9']+", text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 2]


def _context_texts(context: Any) -> List[str]:
    """Pull plain text out of whatever shape the retrieval layer returns."""
    if not context:
        return []
    if isinstance(context, str):
        return [context]
    if isinstance(context, dict):
        for key in ("ranked_memories", "memories", "items"):
            if key in context and context[key]:
                return _context_texts(context[key])
        return [" ".join(str(v) for v in context.values() if isinstance(v, str))]
    if isinstance(context, (list, tuple)):
        out = []
        for item in context:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict):
                for key in ("content", "text", "summary", "memory"):
                    if isinstance(item.get(key), str):
                        out.append(item[key])
                        break
        return out
    return [str(context)]


def _context_scores(context: Any) -> List[float]:
    """Relevance scores (0..1) if the retrieval layer provided any."""
    items = []
    if isinstance(context, dict):
        items = context.get("ranked_memories") or context.get("memories") or []
    elif isinstance(context, (list, tuple)):
        items = context
    scores = []
    for item in items:
        if isinstance(item, dict):
            for key in ("score", "similarity", "relevance"):
                value = item.get(key)
                if isinstance(value, (int, float)):
                    scores.append(max(0.0, min(1.0, float(value))))
                    break
    return scores


# --------------------------------------------------
# Engine
# --------------------------------------------------

class ReasoningEngine:

    def __init__(
        self,
        config: Optional[ReasoningConfig] = None,
        classifier: Optional[Callable[[str], Optional[str]]] = None,
    ):
        self.config = config or ReasoningConfig()
        self.classifier = classifier
        self.reasoning_history: deque = deque(maxlen=self.config.history_size)

    # ----------------------------------------------
    # Analyze
    # ----------------------------------------------

    def analyze(self, query: str) -> dict:
        query_type, margin = self._classify(query)
        return {
            "query": query,
            "type": query_type,
            "type_clarity": margin,
            "complexity": self.estimate_complexity(query),
            "key_terms": _content_terms(query),
            "timestamp": datetime.now().isoformat(),
        }

    def detect_type(self, query: str) -> str:
        return self._classify(query)[0]

    def _classify(self, query: str):
        """Returns (type, clarity 0..1)."""
        if self.classifier is not None:
            try:
                guess = self.classifier(query)
                if guess:
                    return guess, 1.0
            except Exception:
                pass  # fall back to rules

        q = query.lower()
        scores = {}
        for qtype, patterns in self.config.type_patterns.items():
            total = sum(w for rx, w in patterns if re.search(rx, q))
            if total:
                scores[qtype] = total
        if not scores:
            return "general", 0.0

        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        best_type, best = ranked[0]
        second = ranked[1][1] if len(ranked) > 1 else 0
        clarity = round((best - second) / best, 2)
        return best_type, clarity

    def estimate_complexity(self, query: str) -> str:
        cfg = self.config
        words = len(query.split())
        points = 0
        if words >= cfg.long_query_words:
            points += 2
        elif words >= cfg.mid_query_words:
            points += 1
        points += min(2, len(CONJUNCTIONS.findall(query.lower())))
        if query.count("?") > 1:
            points += 1
        if re.search(r"\d", query):
            points += 1  # concrete quantities/addresses add detail to handle
        if points >= cfg.high_at:
            return "high"
        if points >= cfg.medium_at:
            return "medium"
        return "low"

    # ----------------------------------------------
    # Plan (depends on type, complexity and context)
    # ----------------------------------------------

    def create_plan(self, analysis: dict, context: Any = None) -> dict:
        qtype = analysis["type"]
        steps = ["Understand user intent"]

        if _context_texts(context):
            steps.append("Review retrieved context for relevance")
        else:
            steps.append("Retrieve relevant memories (none supplied yet)")

        if analysis["complexity"] == "high":
            steps.append("Break the query into sub-questions")

        type_steps = {
            "explanation": ["Gather definitions and causes", "Order explanation simply to detailed"],
            "problem_solving": ["Identify constraints", "Draft step-by-step solution"],
            "comparison": ["List comparison criteria", "Compare each option per criterion"],
            "incident_report": [
                "Extract location, incident type and severity",
                "Check for duplicate or related incidents",
                "Recommend response units",
            ],
            "resource_request": [
                "Identify required capabilities",
                "Match available units to the request",
            ],
            "status_query": ["Find latest record for the subject", "Report status with timestamp"],
        }
        steps.extend(type_steps.get(qtype, ["Generate answer from context"]))
        steps.append("Verify output against context")

        return {"goal": analysis["query"], "steps": steps, "strategy": qtype}

    # ----------------------------------------------
    # Reason
    # ----------------------------------------------

    def reason(self, query: str, context: Any = None) -> dict:
        analysis = self.analyze(query)
        plan = self.create_plan(analysis, context)
        confidence, signals = self._score_confidence(analysis, context)

        result = {
            "analysis": analysis,
            "plan": plan,
            "confidence": confidence,
            "confidence_signals": signals,
            "context_used": bool(_context_texts(context)),
        }
        self.reasoning_history.append(result)
        return result

    # ----------------------------------------------
    # Confidence (evidence based)
    # ----------------------------------------------

    def calculate_confidence(self, analysis: dict, context: Any) -> float:
        return self._score_confidence(analysis, context)[0]

    def _score_confidence(self, analysis: dict, context: Any):
        cfg = self.config
        texts = _context_texts(context)
        context_terms = set(_content_terms(" ".join(texts)))
        key_terms = analysis.get("key_terms") or _content_terms(analysis["query"])

        if key_terms and context_terms:
            covered = [t for t in key_terms if t in context_terms]
            coverage = len(covered) / len(key_terms)
            missing = [t for t in key_terms if t not in context_terms]
        else:
            coverage, missing = 0.0, list(key_terms)

        scores = _context_scores(context)
        if scores:
            top = sorted(scores, reverse=True)[:3]
            retrieval = sum(top) / len(top)
        else:
            retrieval = 0.5 if texts else 0.0  # context exists but unscored

        clarity = float(analysis.get("type_clarity", 0.0))

        raw = (
            cfg.w_coverage * coverage
            + cfg.w_retrieval * retrieval
            + cfg.w_clarity * clarity
        )
        confidence = round(max(cfg.min_confidence, min(1.0, raw)), 2)
        return confidence, {
            "coverage": round(coverage, 2),
            "retrieval_strength": round(retrieval, 2),
            "type_clarity": round(clarity, 2),
            "missing_terms": missing,
        }

    # ----------------------------------------------
    # Verification
    # ----------------------------------------------

    def verify(self, answer: str, context: Any = None) -> dict:
        cfg = self.config
        answer = answer or ""
        tokens = re.findall(r"[a-zA-Z0-9']+", answer.lower())

        checks = {
            "non_empty": len(answer.strip()) > 0,
            "long_enough": len(answer.strip()) >= cfg.min_answer_chars,
            "not_repetitive": (
                len(tokens) < 20
                or len(set(tokens)) / len(tokens) >= cfg.max_repetition
            ),
            "grounded": None,  # only evaluated when context is available
        }

        texts = _context_texts(context)
        if texts:
            answer_terms = set(_content_terms(answer))
            context_terms = set(_content_terms(" ".join(texts)))
            if answer_terms:
                overlap = len(answer_terms & context_terms) / len(answer_terms)
                checks["grounded"] = overlap >= cfg.min_grounding
                checks["grounding_ratio"] = round(overlap, 2)
            else:
                checks["grounded"] = False

        issues = [
            name for name, ok in checks.items()
            if ok is False and name != "grounding_ratio"
        ]
        return {"passed": not issues, "issues": issues, "checks": checks}

    # ----------------------------------------------
    # Reflection (points at concrete problems)
    # ----------------------------------------------

    def reflect(self, result: dict, verification: Optional[dict] = None) -> dict:
        signals = result.get("confidence_signals", {})
        suggestions = []

        if signals.get("coverage", 1.0) < 0.5:
            missing = signals.get("missing_terms", [])[:5]
            suggestions.append(
                "Retrieved context misses key query terms: " + ", ".join(missing)
                if missing else "Retrieve more relevant context."
            )
        if 0 < signals.get("retrieval_strength", 1.0) < 0.5:
            suggestions.append("Retrieved memories have low relevance scores; widen or re-rank retrieval.")
        if not result.get("context_used", True):
            suggestions.append("No context was supplied; answer would be ungrounded.")
        if signals.get("type_clarity", 1.0) < 0.3:
            suggestions.append("Query type is ambiguous; consider asking a clarifying question.")
        if verification and not verification.get("passed", True):
            suggestions.append(
                "Answer failed verification: " + ", ".join(verification["issues"])
            )

        return {
            "confidence": result.get("confidence", 0),
            "needs_improvement": bool(suggestions),
            "suggestions": suggestions or ["No issues detected."],
        }

    # ----------------------------------------------
    # History / status
    # ----------------------------------------------

    def history(self) -> list:
        return list(self.reasoning_history)

    def status(self) -> dict:
        confidences = [r["confidence"] for r in self.reasoning_history]
        return {
            "reasoning_steps": len(self.reasoning_history),
            "average_confidence": (
                round(sum(confidences) / len(confidences), 2) if confidences else None
            ),
        }


# --------------------------------------------------
# Test
# --------------------------------------------------

if __name__ == "__main__":
    engine = ReasoningEngine()

    ctx = {"ranked_memories": [
        {"content": "Quantum computing uses qubits that can be in superposition.", "score": 0.82},
        {"content": "Quantum computers solve some problems faster than classical ones.", "score": 0.7},
    ]}

    good = engine.reason("Explain quantum computing", ctx)
    print(good["analysis"]["type"], good["confidence"], good["confidence_signals"])

    bad = engine.reason("Explain quantum computing", None)
    print(bad["confidence"], engine.reflect(bad)["suggestions"])

    inc = engine.reason("Building collapse on 5th street, 3 people trapped and fire spreading")
    print(inc["analysis"]["type"], inc["analysis"]["complexity"])
    print(inc["plan"]["steps"])

    v = engine.verify("Quantum computing uses qubits in superposition.", ctx)
    print(v["passed"], v["checks"])
    print(engine.status())