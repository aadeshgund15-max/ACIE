/*
=====================================================

Adaptive Context Intelligence Engine (ACIE)

API Client

Responsible for:
- Backend communication
- Axios configuration
- API services
- Health monitoring
- Error handling

=====================================================
*/

import axios from "axios";

/* =====================================================
   BACKEND CONFIGURATION
===================================================== */

const API_BASE_URL =
    import.meta.env.VITE_API_URL ||
    "http://127.0.0.1:8000";

/* =====================================================
   AXIOS INSTANCE
===================================================== */

const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: 60000,
    headers: {
        "Content-Type": "application/json",
    },
});

/* =====================================================
   REQUEST LOGGER
===================================================== */

client.interceptors.request.use(
    (config) => {
        console.log(
            `🚀 ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`
        );
        return config;
    },
    (error) => Promise.reject(error)
);

/* =====================================================
   RESPONSE LOGGER
===================================================== */

client.interceptors.response.use(
    (response) => {
        console.log(
            `✅ ${response.status} ${response.config.url}`
        );
        return response;
    },
    (error) => {

        console.error("❌ API Error");

        if (error.response) {

            console.error(
                "Status:",
                error.response.status
            );

            console.error(
                error.response.data
            );

        } else {

            console.error(error.message);

        }

        return Promise.reject(error);
    }
);

/* =====================================================
   COMMON REQUEST WRAPPER
===================================================== */

const safeRequest = async (request, fallback) => {

    try {

        const response = await request();

        return response.data;

    } catch (error) {

        return fallback;

    }

};

/* =====================================================
   HEALTH CHECK
===================================================== */

export const healthCheck = () =>
    safeRequest(
        () => client.get("/health"),
        {
            status: "Offline",
            message: "Backend unavailable",
        }
    );

/* =====================================================
   PING
===================================================== */

export const pingBackend = () =>
    safeRequest(
        () => client.get("/ping"),
        {
            message: "Backend Offline",
        }
    );

/* =====================================================
   AGENT STATUS
===================================================== */

export const getAgentStatus = () =>
    safeRequest(
        () => client.get("/agent-status"),
        {
            agent: "ACIE",
            api: "OFFLINE",
            memory: "OFFLINE",
            retrieval: "OFFLINE",
            reasoning: "OFFLINE",
            llm: "OFFLINE",
        }
    );

/* =====================================================
   CHAT
===================================================== */

export const sendChatMessage = (
    query,
    conversation = []
) =>
    safeRequest(
        () =>
            client.post("/chat", {
                query,
                conversation,
            }),
        {
            response:
                "Unable to connect to backend.",
            status: "FAILED",
        }
    );

/* =====================================================
   MEMORIES
===================================================== */

export const getMemories = () =>
    safeRequest(
        () => client.get("/memories"),
        {
            count: 0,
            memories: [],
        }
    );

/* =====================================================
   STORE MEMORY
===================================================== */

export const storeMemory = (data) =>
    safeRequest(
        () => client.post("/store", data),
        {
            stored: false,
        }
    );

/* =====================================================
   RETRIEVE MEMORY
===================================================== */

export const retrieveMemory = (
    query,
    top_k = 5
) =>
    safeRequest(
        () =>
            client.post("/retrieve", {
                query,
                top_k,
            }),
        {
            results: [],
        }
    );

/* =====================================================
   HYBRID RETRIEVAL
===================================================== */

export const hybridRetrieve = (
    query,
    top_k = 5
) =>
    safeRequest(
        () =>
            client.post("/hybrid-retrieve", {
                query,
                top_k,
            }),
        {
            results: [],
        }
    );

/* =====================================================
   CONTEXT COMPRESSION
===================================================== */

export const compressContext = (
    memories
) =>
    safeRequest(
        () =>
            client.post("/compress", {
                memories,
            }),
        {
            compressed: [],
        }
    );

/* =====================================================
   BUILD CONTEXT
===================================================== */

export const buildContext = (
    query,
    token_budget = 1500,
    top_k = 5
) =>
    safeRequest(
        () =>
            client.post("/build-context", {
                query,
                token_budget,
                top_k,
            }),
        {
            result: {},
        }
    );

/* =====================================================
   REFLECTION REPORT
===================================================== */

export const getReflectionReport = () =>
    safeRequest(
        () => client.get("/reflect"),
        {}
    );

/* =====================================================
   PIPELINE
===================================================== */

export const executePipeline = (
    data
) =>
    safeRequest(
        () => client.post("/pipeline", data),
        {}
    );

/* =====================================================
   COMPLETE ENGINE
===================================================== */

export const executeEngine = (
    data
) =>
    safeRequest(
        () => client.post("/engine", data),
        {}
    );

/* =====================================================
   EVALUATION METRICS
===================================================== */

export const getEvaluationMetrics = () =>
    safeRequest(
        () => client.get("/evaluation"),
        {
            available: false,
            compression_sample_count: 0,
            retrieval_sample_count: 0,
            chat_confidence_sample_count: 0,
        }
    );

export const getDashboardMetrics = () =>
    safeRequest(
        () => client.get("/dashboard-metrics"),
        {
            available: false,
            stored_memories: 0,
            total_memories: 0,
            active_memories: 0,
            average_memory_confidence: null,
            confidence_sample_count: 0,
            average_chat_confidence: null,
            chat_confidence_sample_count: 0,
            average_compression_ratio: null,
            compression_sample_count: 0,
            tokens_saved_total: null,
            tokens_saved_sample_count: 0,
            retrieval_coverage: null,
            retrieval_sample_count: 0,
            average_response_latency_ms: null,
            chat_sample_count: 0,
        }
    );

/* =====================================================
   EXPORT
===================================================== */

export default client;
