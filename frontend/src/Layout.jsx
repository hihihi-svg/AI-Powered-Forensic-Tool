import { Link, useLocation } from "react-router-dom";
import { LayoutDashboard, Mic, Image as ImageIcon, ShieldCheck, Database } from "lucide-react";

const Layout = ({ children }) => {
    const location = useLocation();

    const navItems = [
        { path: "/", label: "Dashboard", icon: <LayoutDashboard size={20} /> },
        { path: "/module-a", label: "Speech Sketch", icon: <Mic size={20} /> },
        { path: "/module-b", label: "Image Verify", icon: <ImageIcon size={20} /> },
        { path: "/module-c", label: "Deepfake Check", icon: <ShieldCheck size={20} /> },
        { path: "/module-d", label: "Database", icon: <Database size={20} /> },
    ];

    return (
        <div className="min-h-screen flex bg-background">
            {/* Sidebar */}
            <aside className="w-64 bg-slate-900 border-r border-slate-800 p-6 flex flex-col">
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-rose-400 bg-clip-text text-transparent mb-8">
                    Forensic AI
                </h1>

                <nav className="flex-1 space-y-2">
                    {navItems.map((item) => {
                        const isActive = location.pathname === item.path;
                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${isActive
                                    ? "bg-blue-600/20 text-blue-400 border border-blue-600/30"
                                    : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
                                    }`}
                            >
                                {item.icon}
                                <span className="font-medium">{item.label}</span>
                            </Link>
                        );
                    })}
                </nav>

                <div className="mt-auto pt-6 border-t border-slate-800 text-xs text-slate-500">
                    <p>System Online</p>
                    <p>v1.0.0 (Agentic)</p>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 p-8 overflow-y-auto">
                <div className="max-w-7xl mx-auto">
                    {children}
                </div>
            </main>
        </div>
    );
};

export default Layout;
