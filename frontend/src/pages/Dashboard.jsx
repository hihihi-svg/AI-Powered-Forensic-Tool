import { Link } from "react-router-dom";
import { Mic, Image as ImageIcon, ShieldCheck, Database, ArrowRight } from "lucide-react";

const Dashboard = () => {
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
                    <h4 className="text-lg font-bold text-slate-300 mb-4">System Status</h4>
                    <div className="flex items-center gap-3">
                        <span className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>
                        <span className="text-sm text-slate-400">All Systems Operational</span>
                    </div>
                </div>
                <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800">
                    <h4 className="text-lg font-bold text-slate-300 mb-4">Recent Activity</h4>
                    <div className="space-y-2">
                        <div className="text-sm text-slate-500">No recent cases log found.</div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
