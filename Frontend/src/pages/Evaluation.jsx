import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { BarChart3, TrendingDown, Database, Gauge, Target } from "lucide-react";
import MetricsCard from "../components/MetricsCard";
import { getDashboardMetrics } from "../api/client";

const percent = (value) => value == null ? null : Math.round(value);
const latency = (value) => {
    if (value == null) return null;
    return value >= 1000 ? `${(value / 1000).toFixed(1)}s` : `${Math.round(value)}ms`;
};

function Evaluation() {
    const [usage, setUsage] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let mounted = true;
        const loadMetrics = async () => {
            const result = await getDashboardMetrics();
            if (mounted) {
                setUsage(result);
                setLoading(false);
            }
        };
        loadMetrics();
        const timer = window.setInterval(loadMetrics, 30000);
        return () => {
            mounted = false;
            window.clearInterval(timer);
        };
    }, []);

    const available = usage?.available === true;
    const compression = percent(usage?.average_compression_ratio);
    const retrieval = percent(usage?.retrieval_coverage);
    const confidence = percent(usage?.average_chat_confidence == null
        ? null : usage.average_chat_confidence * 100);
    const savedTokens = usage?.tokens_saved_total;
    const countDescription = (count, noun) => count
        ? `Measured across ${count} recent ${noun}`
        : "Chat activity needed to calculate";
    const evaluationMetrics = [
        {
            title: "Compression Ratio",
            value: loading ? "…" : available && compression != null ? `${compression}%` : "—",
            description: available ? countDescription(usage.compression_sample_count, "chats") : "Backend unavailable",
            type: "compression",
        },
        {
            title: "Tokens Saved",
            value: loading ? "…" : available && savedTokens != null ? Math.round(savedTokens).toLocaleString() : "—",
            description: available ? countDescription(usage.tokens_saved_sample_count, "chats") : "Backend unavailable",
            type: "token",
        },
        {
            title: "Retrieval Coverage",
            value: loading ? "…" : available && retrieval != null ? `${retrieval}%` : "—",
            description: available ? countDescription(usage.retrieval_sample_count, "chats") : "Backend unavailable",
            type: "memory",
        },
        {
            title: "Average Chat Confidence",
            value: loading ? "…" : available && confidence != null ? `${confidence}%` : "—",
            description: available ? countDescription(usage.chat_confidence_sample_count, "chats") : "Backend unavailable",
            type: "confidence",
        },
    ];

    const stages = [
        { name: "Context Compression", score: compression, icon: TrendingDown, samples: usage?.compression_sample_count },
        { name: "Memory Retrieval Coverage", score: retrieval, icon: Database, samples: usage?.retrieval_sample_count },
        { name: "Reasoning Confidence", score: confidence, icon: Target, samples: usage?.chat_confidence_sample_count },
        { name: "Average Response Latency", value: latency(usage?.average_response_latency_ms), icon: Gauge, samples: usage?.chat_sample_count },
    ];

    return (
        <motion.div className="evaluation-page" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <div className="page-header">
                <h1>ACIE Evaluation</h1>
                <p>Performance metrics measured from your recent chats and stored memories</p>
            </div>

            <div className="metrics-grid">
                {evaluationMetrics.map((metric) => <MetricsCard key={metric.title} {...metric} />)}
            </div>

            <div className="evaluation-panel">
                <div className="panel-title"><BarChart3 size={24} /><h2>Observed Chat Metrics</h2></div>
                <div className="evaluation-list">
                    {stages.map((stage, index) => {
                        const Icon = stage.icon;
                        const value = stage.value ?? (stage.score == null ? "—" : `${Math.round(stage.score)}%`);
                        return (
                            <motion.div key={stage.name} className="evaluation-item" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: index * 0.1 }}>
                                <div className="evaluation-icon"><Icon size={22} /></div>
                                <div className="evaluation-content">
                                    <h3>{stage.name}</h3>
                                    <div className="score-row">
                                        <span>{stage.samples ? `Based on ${stage.samples} chats` : "Waiting for chat data"}</span>
                                        <strong>{loading ? "…" : available ? value : "—"}</strong>
                                    </div>
                                    {stage.score != null && (
                                        <div className="progress-bar">
                                            <motion.div className="progress-fill" initial={{ width: 0 }} animate={{ width: `${loading || !available ? 0 : Math.max(0, Math.min(100, stage.score))}%` }} transition={{ duration: 0.8 }} />
                                        </div>
                                    )}
                                </div>
                            </motion.div>
                        );
                    })}
                </div>
            </div>

            <div className="chart-placeholder">
                <h2>Performance Visualization</h2>
                <p>Metrics update from the latest 50 chats handled by the running backend.</p>
            </div>
        </motion.div>
    );
}

export default Evaluation;
