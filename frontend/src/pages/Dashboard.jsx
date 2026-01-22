import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Mic, Image as ImageIcon, ShieldCheck, Database, ArrowRight, Activity, Clock, History } from "lucide-react";
import { SessionManager } from "../config/api";

const Dashboard = () => {
    const [history, setHistory] = useState([]);
    const [sessionStats, setSessionStats] = useState({ count: 0, duration: '0m' });

    useEffect(() => {
        const fetchHistory = async () => {
            const data = await SessionManager.getHistory(5);
            setHistory(data);
            setSessionStats(prev => ({ ...prev, count: data.length }));
        };
        fetchHistory();

        // Refresh every 30 seconds
        const interval = setInterval(fetchHistory, 30000);
        return () => clearInterval(interval);
    }, []);

    const modules = [
        {
            title: "Speech to Sketch",
            desc: "Generate forensic sketches from witness descriptions using AI.",
            path: "/module-a",
            icon: <Mic className="w-8 h-8 text-blue-400" />,
            color: "hover:border-blue-500/50 hover:bg-blue-500/5"
        },
        {
            title: "Image Verification",
            desc: "Verify authenticity of evidence and search criminal database.",
            path: "/module-b",
            icon: <ImageIcon className="w-8 h-8 text-purple-400" />,
            color: "hover:border-purple-500/50 hover:bg-purple-500/5"
        },
        {
            title: "Deepfake Detective",
            desc: "Standalone tool to detect AI-generated manipulations.",
            path: "/module-c",
            icon: <ShieldCheck className="w-8 h-8 text-rose-400" />,
            color: "hover:border-rose-500/50 hover:bg-rose-500/5"
        },
        {
            title: "Database Management",
            desc: "Manage suspect records, view statistics, and perform CRUD operations.",
            path: "/module-d",
            icon: <Database className="w-8 h-8 text-green-400" />,
            color: "hover:border-green-500/50 hover:bg-green-500/5"
        }
    ];

    const formatTime = (isoString) => {
        const date = new Date(isoString);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    const getActionColor = (type) => {
        switch (type) {
            case 'search': return 'text-blue-400';
            case 'generate': return 'text-purple-400';
            case 'detect': return 'text-rose-400';
            case 'view': return 'text-green-400';
            default: return 'text-slate-400';
        }
    };

    return (
        <div className="space-y-10">
            <div className="text-center space-y-4 py-10">
                <h1 className="text-5xl font-extrabold bg-gradient-to-r from-blue-400 via-purple-400 to-rose-400 bg-clip-text text-transparent">
                    Forensic Analysis Dashboard
                </h1>
                <p className="text-xl text-slate-400 max-w-2xl mx-auto">
                    Advanced AI-powered toolkit for suspect identification, evidence verification, and deepfake detection.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {modules.map((m) => (
                    <Link
                        key={m.path}
                        to={m.path}
                        className={`bg-slate-800/40 p-8 rounded-2xl border border-slate-700 transition-all duration-300 group ${m.color}`}
                    >
                        <div className="mb-6 p-4 bg-slate-900 rounded-full w-fit group-hover:scale-110 transition-transform">
                            {m.icon}
                        </div>
                        <h3 className="text-2xl font-bold text-white mb-2">{m.title}</h3>
                        <p className="text-slate-400 mb-6">{m.desc}</p>
                        <div className="flex items-center gap-2 text-sm font-medium text-slate-300 group-hover:text-white transition-colors">
                            Access Module <ArrowRight size={16} />
                        </div>
                    </Link>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-12">
                <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800">
                    <h4 className="text-lg font-bold text-slate-300 mb-4 flex items-center gap-2">
                        <Activity className="w-5 h-5 text-green-400" /> System Status
                    </h4>
                    <div className="space-y-4">
                        <div className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg">
                            <div className="flex items-center gap-3">
                                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                                <span className="text-sm text-slate-300">Backend API</span>
                            </div>
                            <span className="text-xs text-green-400 px-2 py-1 bg-green-400/10 rounded">Operational</span>
                        </div>
                        <div className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg">
                            <div className="flex items-center gap-3">
                                <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
                                <span className="text-sm text-slate-300">Vector Database (Qdrant)</span>
                            </div>
                            <span className="text-xs text-blue-400 px-2 py-1 bg-blue-400/10 rounded">Connected</span>
                        </div>
                        <div className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg">
                            <div className="flex items-center gap-3">
                                <span className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></span>
                                <span className="text-sm text-slate-300">AI Models</span>
                            </div>
                            <span className="text-xs text-purple-400 px-2 py-1 bg-purple-400/10 rounded">Ready</span>
                        </div>
                    </div>
                </div>

                <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800">
                    <h4 className="text-lg font-bold text-slate-300 mb-4 flex items-center gap-2">
                        <History className="w-5 h-5 text-blue-400" />
                        Session Memory
                        <span className="ml-auto text-xs font-normal text-slate-500 flex items-center gap-1">
                            <Clock size={12} /> Auto-tracking active
                        </span>
                    </h4>
                    <div className="space-y-2">
                        {history.length > 0 ? (
                            history.map((h, i) => (
                                <div key={i} className="flex items-start gap-3 p-3 bg-slate-800/30 rounded-lg hover:bg-slate-800/50 transition-colors">
                                    <div className="min-w-[60px] text-xs text-slate-500 mt-0.5">
                                        {formatTime(h.timestamp)}
                                    </div>
                                    <div>
                                        <div className={`text-sm font-medium uppercase tracking-wider ${getActionColor(h.type)}`}>
                                            {h.type}
                                        </div>
                                        <div className="text-sm text-slate-300">
                                            {h.query || "Viewed suspect details"}
                                        </div>
                                        {h.results?.matches && (
                                            <div className="text-xs text-slate-500 mt-1">
                                                {h.results.matches} matches found
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="text-sm text-slate-500 py-8 text-center italic">
                                No recent activity logged in this session.
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
