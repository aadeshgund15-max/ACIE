/*
=====================================================

Adaptive Context Intelligence Engine (ACIE)

Dashboard Page

Responsible for:
- Agent overview
- System metrics
- Intelligence monitoring

=====================================================
*/


import { useEffect, useState } from "react";

import {

    motion

} from "framer-motion";


import AgentStatus from "../components/AgentStatus";

import MetricsCard from "../components/MetricsCard";

import { getDashboardMetrics } from "../api/client";

import ReasoningTrace from "../components/ReasoningTrace";


import {


    Database,

    Zap,

    Brain


} from "lucide-react";








function Dashboard(){

    const [dashboardData, setDashboardData] = useState(null);
    const [loadingMetrics, setLoadingMetrics] = useState(true);

    useEffect(() => {
        let mounted = true;

        const loadMetrics = async () => {
            const result = await getDashboardMetrics();
            if (mounted) {
                setDashboardData(result);
                setLoadingMetrics(false);
            }
        };

        loadMetrics();
        const refreshTimer = window.setInterval(loadMetrics, 30000);

        return () => {
            mounted = false;
            window.clearInterval(refreshTimer);
        };
    }, []);

    const formatPercent = (value) =>
        value == null ? "—" : `${Math.round(value)}%`;

    const formatLatency = (value) => {
        if (value == null) return "—";
        return value >= 1000
            ? `${(value / 1000).toFixed(1)}s`
            : `${Math.round(value)}ms`;
    };

    const countChats = dashboardData?.chat_sample_count ?? 0;
    const countMemories = dashboardData?.stored_memories ?? 0;
    const compressionSamples = dashboardData?.compression_sample_count ?? 0;
    const confidenceSamples = dashboardData?.confidence_sample_count ?? 0;
    const metricsAvailable = dashboardData?.available === true;
    const backendUnavailable = !loadingMetrics && !metricsAvailable;
    const metrics = [
        {
            title: "Compression Ratio",
            value: loadingMetrics
                ? "…"
                : metricsAvailable
                    ? formatPercent(dashboardData?.average_compression_ratio)
                    : "—",
            description: backendUnavailable
                ? "Backend unavailable"
                : compressionSamples
                    ? `Average from ${compressionSamples} recent chats`
                    : "Chat activity needed to calculate",
            type: "compression"
        },
        {
            title: "Stored Memories",
            value: loadingMetrics ? "…" : metricsAvailable ? String(countMemories) : "—",
            description: backendUnavailable
                ? "Backend unavailable"
                : "Active memories in your database",
            type: "memory"
        },
        {
            title: "Response Latency",
            value: loadingMetrics
                ? "…"
                : metricsAvailable
                    ? formatLatency(dashboardData?.average_response_latency_ms)
                    : "—",
            description: backendUnavailable
                ? "Backend unavailable"
                : countChats
                    ? `Average across ${countChats} recent chats`
                    : "Chat activity needed to calculate",
            type: "latency"
        },
        {
            title: "Average Memory Confidence",
            value: loadingMetrics
                ? "…"
                : metricsAvailable
                    ? formatPercent(
                        dashboardData?.average_memory_confidence == null
                            ? null
                            : dashboardData.average_memory_confidence * 100
                    )
                    : "—",
            description: backendUnavailable
                ? "Backend unavailable"
                : confidenceSamples
                    ? `Based on ${confidenceSamples} active memories`
                    : "No scored memories yet",
            type: "confidence"
        }
    ];









    const systemOverview=[






        {


            title:"Context Intelligence",


            icon:Brain,


            status:"ACTIVE"



        },






        {


            title:"Memory System",


            icon:Database,


            status:"ONLINE"



        },






        {


            title:"Execution Engine",


            icon:Zap,


            status:"READY"



        }







    ];









    return (








        <motion.div






            className="dashboard"






            initial={{


                opacity:0,


                y:20



            }}



            animate={{


                opacity:1,


                y:0



            }}



            transition={{


                duration:0.5


            }}





        >







            {/* Header */}





            <div className="page-header">





                <h1>


                    ACIE Dashboard



                </h1>








                <p>


                    Personal metrics from your stored memories and recent chats



                </p>






            </div>















            {/* Metrics */}





            <motion.div





                className="metrics-grid"





                initial="hidden"

                animate="visible"

                variants={{


                    visible:{


                        transition:{


                            staggerChildren:0.1


                        }

                    }



                }}







            >






                {


                metrics.map((metric,index)=>(






                    <MetricsCard





                        key={index}





                        {...metric}





                    />






                ))





                }







            </motion.div>














            {/* Main Dashboard Grid */}





            <div className="dashboard-grid">







                <AgentStatus/>













                <motion.div





                    className="system-overview"





                    whileHover={{


                        scale:1.01



                    }}



                >








                    <h2>


                        System Overview



                    </h2>









                    {


                    systemOverview.map((item,index)=>{






                        const Icon=item.icon;







                        return (






                            <div





                            key={index}





                            className="overview-item"





                            >







                                <div className="overview-icon">





                                    <Icon size={22}/>





                                </div>









                                <div>







                                    <h3>

                                        {item.title}



                                    </h3>







                                    <span>



                                        ● {item.status}



                                    </span>







                                </div>







                            </div>








                        );






                    })






                    }







                </motion.div>








            </div>












            {/* Reasoning Preview */}





            <div className="reasoning-preview">





                <ReasoningTrace/>





            </div>







        </motion.div>







    );


}





export default Dashboard;
