import { useState } from "react";
import axios from "axios";
import { Upload, CheckCircle, AlertTriangle, Search, Loader } from "lucide-react";

const ModuleB = () => {
    const [selectedFile, setSelectedFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [loading, setLoading] = useState(false);
    const [authResult, setAuthResult] = useState(null);
    const [searchResults, setSearchResults] = useState([]);
    const [topK, setTopK] = useState(3);

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            setSelectedFile(file);
            setPreview(URL.createObjectURL(file));
            setAuthResult(null);
            setSearchResults([]);
        }
    };

    const handleUploadAndAnalyze = async () => {
        console.log("Analyzing button clicked");
        if (!selectedFile) {
            console.log("No file selected");
            return;
        }
        setLoading(true);
        console.log("Starting analysis...", selectedFile.name);

        try {
            const formData = new FormData();
            formData.append("file", selectedFile);

            console.log("Sending request to http://127.0.0.1:8086/api/upload-image");
            // 1. Check Authenticity
            const authResponse = await axios.post("http://127.0.0.1:8086/api/upload-image", formData, {
                timeout: 60000 // 60s timeout for cold start
            });
            console.log("Auth Response:", authResponse.data);
            setAuthResult(authResponse.data);

            if (authResponse.data.is_real) {
                console.log("Image is real. Starting Search...");
                // 2. If Real, Search
                const searchFormData = new FormData();
                searchFormData.append("file", selectedFile);
                searchFormData.append("top_k", topK);

                console.log("Sending request to http://127.0.0.1:8086/api/search");
                const searchResponse = await axios.post("http://127.0.0.1:8086/api/search", searchFormData, {
                    headers: { "Content-Type": "multipart/form-data" },
                    timeout: 60000
                });
                console.log("Search Response:", searchResponse.data);
                setSearchResults(searchResponse.data.results);
            } else {
                console.log("Image is NOT real. Skipping search.");
            }
        } catch (error) {
            console.error("Analysis failed:", error);
            if (error.code === 'ECONNABORTED') {
                alert("Request timed out. Backend is not responding.");
            } else if (error.response) {
                console.error("Backend Error Data:", error.response.data);
                console.error("Backend Status:", error.response.status);
                alert(`Server Error: ${error.response.status}`);
            } else if (error.request) {
                console.error("No response received from backend (Network Error?)");
                alert("Network Error: Could not connect to Backend.");
            } else {
                console.error("Error setting up request:", error.message);
                alert("Error: " + error.message);
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-8">
            <header>
                <h2 className="text-3xl font-bold text-white mb-2">Image Verification & Search</h2>
                <p className="text-slate-400">Verify image authenticity and search for matches in the database.</p>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Upload Section */}
                <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="text-xl font-semibold text-blue-400">1. Upload Suspect Image</h3>
                        <button
                            onClick={async () => {
                                try {
                                    alert("Testing connection...");
                                    const res = await axios.get("http://127.0.0.1:8086/");
                                    alert("Connection Successful: " + JSON.stringify(res.data));
                                } catch (e) {
                                    alert("Connection Failed: " + e.message);
                                }
                            }}
                            className="text-xs bg-slate-700 hover:bg-slate-600 px-2 py-1 rounded text-slate-300"
                        >
                            Test Connection
                        </button>
                    </div>

                    <div className="border-2 border-dashed border-slate-600 rounded-xl p-8 text-center hover:border-blue-500 transition-colors relative">
                        <input
                            type="file"
                            onChange={handleFileChange}
                            accept="image/*"
                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        />
                        {preview ? (
                            <img src={preview} alt="Preview" className="max-h-64 mx-auto rounded-lg shadow-lg" />
                        ) : (
                            <div className="flex flex-col items-center gap-3 text-slate-400">
                                <Upload size={40} />
                                <p>Drag & drop or click to upload</p>
                            </div>
                        )}
                    </div>

                    <button
                        onClick={handleUploadAndAnalyze}
                        disabled={!selectedFile || loading}
                        className="w-full mt-6 bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                        {loading ? <Loader className="animate-spin" /> : <Search />}
                        {loading ? "Analyzing..." : "Analyze Image"}
                    </button>
                </div>

                {/* Results Section */}
                <div className="space-y-6">
                    {/* Authenticity Result - Only show if there's a match */}
                    {authResult && authResult.match && (
                        <div className="p-6 rounded-xl border bg-green-500/10 border-green-500/50">
                            <div className="flex items-center gap-3 mb-2">
                                <CheckCircle className="text-green-500" />
                                <h3 className="text-xl font-bold text-green-400">
                                    Present in Database
                                </h3>
                            </div>
                            <p className="text-slate-300">
                                Confidence Score: <span className="font-mono text-white">{(authResult.confidence * 100).toFixed(1)}%</span>
                            </p>

                            {/* MATCHED IMAGE DISPLAY */}
                            <div className="mt-4 p-4 bg-black/30 rounded-lg flex items-center gap-4">
                                <div className="relative">
                                    <img
                                        src={authResult.match.image}
                                        alt="Database Match"
                                        className="w-20 h-20 rounded-lg object-cover border-2 border-green-500/50"
                                    />
                                    <span className="absolute -bottom-2 -right-2 bg-green-600 text-[10px] px-1.5 py-0.5 rounded-full text-white font-bold">MATCH</span>
                                </div>
                                <div className="flex-1">
                                    <p className="text-sm text-slate-400">Match Found in Database</p>
                                    <p className="text-green-400 font-mono font-bold">{authResult.match.filename}</p>
                                    {authResult.match.crime_type && (
                                        <p className="text-xs text-orange-400 mt-1">Crime: {authResult.match.crime_type}</p>
                                    )}
                                    {authResult.match.arrest_timestamp && (
                                        <p className="text-xs text-slate-500">Arrested: {new Date(authResult.match.arrest_timestamp).toLocaleDateString()}</p>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Search Results */}
                    {authResult?.is_real && (
                        <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700">
                            <h3 className="text-xl font-semibold mb-4 text-white">Database Matches</h3>

                            {searchResults.length > 0 ? (
                                <>
                                    {/* Top K Slider */}
                                    <div className="mb-6 p-4 bg-slate-700/50 rounded-lg">
                                        <label className="block text-sm font-medium text-slate-300 mb-2">
                                            Number of Results: <span className="text-blue-400 font-bold">{topK}</span>
                                        </label>
                                        <input
                                            type="range"
                                            min="1"
                                            max="10"
                                            value={topK}
                                            onChange={(e) => setTopK(parseInt(e.target.value))}
                                            className="w-full h-2 bg-slate-600 rounded-lg appearance-none cursor-pointer"
                                        />
                                    </div>

                                    <div className="space-y-4">
                                        {searchResults.map((result) => (
                                            <div key={result.id} className="bg-slate-900 p-4 rounded-lg flex items-center justify-between border border-slate-700">
                                                <div className="flex items-center gap-4">
                                                    {/* Display Image */}
                                                    {result.image && (
                                                        <img
                                                            src={result.image}
                                                            alt={`Match ${result.id}`}
                                                            className="w-16 h-16 rounded-md object-cover border border-slate-600"
                                                        />
                                                    )}
                                                    <div>
                                                        <p className="font-bold text-blue-400">ID: {result.id}</p>
                                                        <p className="text-sm text-slate-400">Context: {result.payload.crime_type}</p>
                                                        <p className="text-xs text-slate-500">{new Date(result.payload.timestamp).toLocaleDateString()}</p>
                                                    </div>
                                                </div>
                                                <div className="text-right">
                                                    <div className="text-2xl font-bold text-green-400">{(result.score * 100).toFixed(0)}%</div>
                                                    <span className="text-xs text-slate-500">Similarity</span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </>
                            ) : (
                                <div className="p-8 text-center text-slate-500 border border-dashed border-slate-700 rounded-lg">
                                    <p>No matches found in database (Similarity &lt; 40%).</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ModuleB;
