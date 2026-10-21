"""
Adaptive Context Intelligence Engine (ACIE)
API Routes
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Literal
from collections import deque
from threading import Lock
from time import perf_counter

from Backend.collector.context_collector import ContextCollector
from Backend.scorer.importance_scorer import ImportanceScorer
from Backend.scorer.confidence_calculator import ConfidenceCalculator
from Backend.decision_engine.decision_engine import DecisionEngine
from Backend.memory.memory_manager import MemoryManager
from Backend.retriever.retriever import Retriever
from Backend.compressor.context_compressor import ContextCompressor
from Backend.hybrid.hybrid_retriever import HybridRetriever
from Backend.context_builder.context_window_builder import ContextWindowBuilder
from Backend.pipeline.memory_pipeline import MemoryPipeline
from Backend.reflection.reflection_engine import ReflectionEngine
from Backend.agent.agent_runtime import AgentRuntime
from Backend.core.pipeline_manager import PipelineManager

from Backend.models.request_models import (
    StoreRequest,
    RetrieveRequest,
    CompressRequest,
    ContextRequest
)


class ChatMessage(BaseModel):

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):

    query: str
    conversation: list[ChatMessage] = Field(default_factory=list, max_length=24)


class ChatResponse(BaseModel):

    response: str
    status: str

router = APIRouter()

collector = ContextCollector()
importance_scorer = ImportanceScorer()
confidence_calculator = ConfidenceCalculator()
decision_engine = DecisionEngine()
memory_manager = MemoryManager()
retriever = Retriever()
compressor = ContextCompressor()
hybrid_retriever = HybridRetriever()
context_builder = ContextWindowBuilder()

pipeline = MemoryPipeline()
manager = PipelineManager()
reflection_engine = ReflectionEngine()
agent_runtime = AgentRuntime()

_recent_chat_metrics = deque(maxlen=50)
_chat_metrics_lock = Lock()


@router.get("/")
def root():

    return {

        "project": "Adaptive Context Intelligence Engine",

        "version": "2.0.0",

        "status": "Running"

    }


@router.get("/health")
def health():

    return {

        "status": "Healthy",

        "message": "ACIE API is running successfully."

    }


@router.get("/version")
def version():

    return {

        "project": "Adaptive Context Intelligence Engine",

        "version": "2.0.0"

    }


@router.get("/memories")
def get_memories():

    raw_memories = memory_manager.get_all_memories()

    memories = []

    for m in raw_memories:

        memories.append({

            "id": m[0],
            "query": m[1],
            "importance": m[2],
            "confidence": m[3],
            "decision": m[4],
            "created_at": m[5],
            "last_accessed": m[6],
            "access_count": m[7],
            "state": m[8]

        })

    return {

        "count": len(memories),

        "memories": memories

    }


@router.post("/store")
def store_memory(request: StoreRequest):

    context = collector.collect(

        query=request.query,

        conversation=request.conversation,

        documents=request.documents

    )

    importance = importance_scorer.calculate_score(context)

    confidence = confidence_calculator.calculate_confidence(context)

    decision = decision_engine.decide(

        importance,

        confidence

    )

    if decision == "STORE":

        memory_id = memory_manager.store(

            context,

            importance,

            confidence,

            decision

        )

        return {

            "stored": True,

            "memory_id": memory_id,

            "importance": importance,

            "confidence": confidence,

            "decision": decision

        }

    return {

        "stored": False,

        "importance": importance,

        "confidence": confidence,

        "decision": decision

    }


@router.post("/retrieve")
def retrieve_memory(request: RetrieveRequest):

    results = retriever.retrieve(

        request.query,

        request.top_k

    )

    return {

        "query": request.query,

        "results": results

    }


@router.post("/hybrid-retrieve")
def hybrid_retrieve(request: RetrieveRequest):

    results = hybrid_retriever.retrieve(

        request.query,

        request.top_k

    )

    return {

        "query": request.query,

        "retrieval_type": "Hybrid",

        "results": results

    }


@router.post("/compress")
def compress_context(request: CompressRequest):

    return compressor.compress(

        request.memories

    )


@router.post("/build-context")
def build_context(request: ContextRequest):

    ranked = hybrid_retriever.retrieve(

        request.query,

        request.top_k

    )

    result = context_builder.build(

        ranked,

        request.token_budget

    )

    return {

        "query": request.query,

        "result": result

    }


# ==========================
# Reflection API
# ==========================

@router.get("/reflect")
def reflect():

    memories = memory_manager.get_all_memories()

    formatted = []

    for memory in memories:

        formatted.append({

            "id": memory[0],

            "query": memory[1],

            "importance": memory[2],

            "confidence": memory[3],

            "decision": memory[4],

            "created_at": memory[5],

            "last_accessed": memory[6],

            "access_count": memory[7],

            "state": memory[8]

        })

    return reflection_engine.generate_report(

        formatted

    )


# ==========================
# Complete Pipeline API
# ==========================

@router.post("/pipeline")
def execute_pipeline(request: StoreRequest):

    result = pipeline.process(

        query=request.query,

        conversation=request.conversation,

        documents=request.documents

    )

    return result

# =====================================
# AI CHAT ENDPOINT
# =====================================

@router.post("/chat")
def chat(request: ChatRequest):

    started_at = perf_counter()
    result = agent_runtime.run(
        request.query,
        conversation=[
            {"role": message.role, "content": message.content}
            for message in request.conversation
        ],
    )

    if result.get("status") == "SUCCESS":
        metrics = result.get("metrics", {}) or {}
        with _chat_metrics_lock:
            _recent_chat_metrics.append({
                "latency_ms": (perf_counter() - started_at) * 1000,
                "compression_ratio": metrics.get("compression_ratio"),
                "tokens_saved": metrics.get("tokens_saved"),
                "confidence": metrics.get("confidence"),
                "memories_selected": metrics.get("memories_selected", 0),
                "memories_available": metrics.get("memories_available", 0),
            })

    return result

# =====================================
# AGENT STATUS
# =====================================

@router.get("/agent-status")
def agent_status():

    return {

        "agent": "ACIE",

        "memory": "READY",

        "retrieval": "READY",

        "reasoning": "READY",

        "llm": "READY",

        "api": "ONLINE"

    }

# =====================================
# EVALUATION METRICS
# =====================================

@router.get("/evaluation")
def evaluation():
    return dashboard_metrics()


@router.get("/dashboard-metrics")
def dashboard_metrics():

    rows = memory_manager.get_all_memories()
    active_memories = [
        row for row in rows
        if len(row) > 8 and str(row[8]).upper() == "ACTIVE"
    ]
    confidence_values = []
    for row in active_memories:
        try:
            confidence_values.append(float(row[3]))
        except (TypeError, ValueError):
            continue

    with _chat_metrics_lock:
        chat_samples = list(_recent_chat_metrics)

    compression_values = []
    latency_values = []
    for sample in chat_samples:
        try:
            compression_values.append(float(sample["compression_ratio"]))
        except (TypeError, ValueError):
            pass
        try:
            latency_values.append(float(sample["latency_ms"]))
        except (TypeError, ValueError):
            pass

    chat_confidence_values = []
    tokens_saved_values = []
    retrieval_hits = 0
    retrieval_samples = 0
    for sample in chat_samples:
        try:
            chat_confidence_values.append(float(sample["confidence"]))
        except (KeyError, TypeError, ValueError):
            pass
        try:
            tokens_saved_values.append(float(sample["tokens_saved"]))
        except (KeyError, TypeError, ValueError):
            pass
        try:
            available = int(sample["memories_available"])
            if available > 0:
                retrieval_samples += 1
                if int(sample["memories_selected"]) > 0:
                    retrieval_hits += 1
        except (KeyError, TypeError, ValueError):
            pass

    def average(values):
        return round(sum(values) / len(values), 2) if values else None

    return {
        "available": True,
        "stored_memories": len(active_memories),
        "total_memories": len(rows),
        "active_memories": len(active_memories),
        "average_memory_confidence": average(confidence_values),
        "confidence_sample_count": len(confidence_values),
        "average_chat_confidence": average(chat_confidence_values),
        "chat_confidence_sample_count": len(chat_confidence_values),
        "average_compression_ratio": average(compression_values),
        "compression_sample_count": len(compression_values),
        "tokens_saved_total": round(sum(tokens_saved_values), 2) if tokens_saved_values else None,
        "tokens_saved_sample_count": len(tokens_saved_values),
        "retrieval_coverage": (
            round(retrieval_hits / retrieval_samples * 100, 2)
            if retrieval_samples else None
        ),
        "retrieval_sample_count": retrieval_samples,
        "average_response_latency_ms": average(latency_values),
        "chat_sample_count": len(latency_values),
    }

# =====================================
# PING
# =====================================

@router.get("/ping")
def ping():

    return {

        "message": "Pong"

    }
# =====================================
# COMPLETE ACIE ENGINE
# =====================================

@router.post("/engine")
def execute_engine(request: StoreRequest):

    request_data = {

        "query": request.query,

        "requires_retrieval": True,

        "task_type": "general"

    }

    result = manager.execute(

        request=request_data,

        conversation=request.conversation,

        documents=request.documents

    )

    return result

