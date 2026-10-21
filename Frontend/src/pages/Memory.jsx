import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Database, Brain, Activity, Search, Layers } from "lucide-react";
import MemoryPanel from "../components/MemoryPanel";
import MetricsCard from "../components/MetricsCard";
import { getDashboardMetrics } from "../api/client";

function Memory() {
    const [usage, setUsage] = useState(null);
    const [loadingUsage, setLoadingUsage] = useState(true);

    useEffect(() => {
        let mounted = true;
        const loadUsage = async () => {
            const result = await getDashboardMetrics();
            if (mounted) {
                setUsage(result);
                setLoadingUsage(false);
            }
        };
        loadUsage();
        const timer = window.setInterval(loadUsage, 30000);
        return () => {
            mounted = false;
            window.clearInterval(timer);
        };
    }, []);

    const available = usage?.available === true;
    const totalMemories = usage?.total_memories ?? 0;
    const activeMemories = usage?.active_memories ?? 0;
    const retrievalSamples = usage?.retrieval_sample_count ?? 0;
    const memoryMetrics = [
        {
            title: "Total Memories",
            value: loadingUsage ? "…" : available ? String(totalMemories) : "—",
            description: available ? `${activeMemories} active memories in your database` : "Backend unavailable",
            type: "memory",
        },
        {
            title: "Retrieval Coverage",
            value: loadingUsage ? "…" : available && usage?.retrieval_coverage != null
                ? `${Math.round(usage.retrieval_coverage)}%` : "—",
            description: retrievalSamples
                ? `Chats that retrieved memories (${retrievalSamples} samples)`
                : available ? "Chat activity needed to measure" : "Backend unavailable",
            type: "confidence",
        },
        {
            title: "Memory Activity",
            value: loadingUsage ? "…" : available ? (activeMemories ? "ACTIVE" : "IDLE") : "—",
            description: available ? `${activeMemories} active memories` : "Backend unavailable",
            type: "activity",
        },
    ];

    const memoryFeatures = [
        { title: "Semantic Memory", description: "Stores meaningful long-term knowledge", icon: Brain },
        { title: "Context Memory", description: "Maintains current conversation state", icon: Layers },
        { title: "Memory Retrieval", description: "Finds relevant information using embeddings", icon: Search },
        { title: "Memory Optimization", description: "Compresses redundant information", icon: Activity },
    ];

    return (
        <motion.div className="memory-page" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <div className="page-header">
                <h1>ACIE Memory System</h1>
                <p>Manage and analyze memories stored by your chats</p>
            </div>

            <div className="metrics-grid">
                {memoryMetrics.map((metric) => <MetricsCard key={metric.title} {...metric} />)}
            </div>

            <div className="memory-layout">
                <div><MemoryPanel /></div>
                <motion.div className="memory-features" initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }}>
                    <h2>Memory Intelligence</h2>
                    {memoryFeatures.map((feature) => {
                        const Icon = feature.icon;
                        return (
                            <motion.div key={feature.title} className="feature-card" whileHover={{ scale: 1.03 }} transition={{ duration: 0.2 }}>
                                <div className="feature-icon"><Icon size={22} /></div>
                                <div><h3>{feature.title}</h3><p>{feature.description}</p></div>
                            </motion.div>
                        );
                    })}
                </motion.div>
            </div>

            <motion.div className="knowledge-section" whileHover={{ scale: 1.01 }}>
                <Database size={24} />
                <div>
                    <h2>Knowledge Graph</h2>
                    <p>Graph based memory visualization will be integrated here.</p>
                </div>
            </motion.div>
        </motion.div>
    );
}

export default Memory;
