import { useState } from "react";
import axios from "axios";
import { Upload, ShieldCheck, AlertOctagon, Loader } from "lucide-react";
import { SessionManager } from "../config/api"; // Import SessionManager

const ModuleC = () => {
    const [selectedFile, setSelectedFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            setSelectedFile(file);
            setPreview(URL.createObjectURL(file));
            setResult(null);
        }
    };

    const handleCheck = async () => {
        if (!selectedFile) return;
        setLoading(true);
        try {
            const formData = new FormData();
            formData.append("file", selectedFile);
            const response = await axios.post("http://localhost:8086/api/detect-deepfake", formData, {
                timeout: 30000  // 30 seconds for API call  
            });
            setResult(response.data);

            // Log Interaction
            SessionManager.logInteraction('detect', `Deepfake Analysis: ${selectedFile.name}`, {
                is_deepfake: !response.data.is_real,
                authenticity: response.data.is_real ? "Real" : "Fake",
                confidence: response.data.confidence
            });

        } catch (error) {
            console.error("Full error:", error);
            const errorMsg = error.response?.data?.detail || error.message || "Unknown error";
            alert(`Error checking authenticity: ${errorMsg}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <header className="text-center">
                <h2 className="text-3xl font-bold text-white mb-2">Deepfake Authenticity Checker</h2>
                <p className="text-slate-400">Standalone tool to analyze image metadata and artifacts.</p>
            </header>

            <div className="bg-slate-800/50 p-8 rounded-xl border border-slate-700 shadow-2xl">
                <div className="flex flex-col items-center gap-6">
                    {/* Upload Area */}
                    <div className="w-full max-w-md aspect-video bg-slate-900 rounded-lg border-2 border-dashed border-slate-600 flex items-center justify-center relative overflow-hidden group hover:border-rose-500 transition-colors">
                        <input type="file" onChange={handleFileChange} className="absolute inset-0 opacity-0 cursor-pointer z-10" />
                        {preview ? (
                            <img src={preview} alt="Analyze" className="w-full h-full object-contain" />
                        ) : (
                            <div className="text-center text-slate-500">
                                <Upload className="w-12 h-12 mx-auto mb-2" />
                                <p>Upload Image</p>
                            </div>
                        )}
                    </div>

                    <button
                        onClick={handleCheck}
                        disabled={!selectedFile || loading}
                        className="px-8 py-3 bg-rose-600 hover:bg-rose-700 text-white rounded-full font-bold shadow-lg shadow-rose-900/20 disabled:opacity-50 transition-all flex items-center gap-2"
                    >
                        {loading ? <Loader className="animate-spin" /> : <ShieldCheck />}
                        {loading ? "Scanning..." : "Run Diagnostics"}
                    </button>

                    {/* Result Reveal */}
                    {result && (
                        <div className="w-full animate-in fade-in slide-in-from-bottom-4 duration-700">
                            <div className={`p-6 rounded-xl border-l-4 ${result.is_real ? 'bg-green-900/20 border-green-500' : 'bg-red-900/20 border-red-500'} flex items-start gap-4`}>
                                <div className={`p-3 rounded-full ${result.is_real ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
                                    {result.is_real ? <ShieldCheck className="w-8 h-8 text-green-400" /> : <AlertOctagon className="w-8 h-8 text-red-500" />}
                                </div>
                                <div>
                                    <h3 className="text-2xl font-bold text-white mb-1">
                                        {result.is_real ? "Authentic Source" : "AI Manipulation Detected"}
                                    </h3>
                                    <div className="flex gap-4 text-sm text-slate-300">
                                        <p>Confidence: <span className="text-white font-mono">{(result.confidence * 100).toFixed(2)}%</span></p>
                                        <p>Class: <span className="text-white font-mono">{result.class}</span></p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ModuleC;
