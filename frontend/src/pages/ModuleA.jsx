import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Loader, ArrowRight, Mic, StopCircle } from "lucide-react";
import { SessionManager } from "../config/api"; // Import SessionManager

const ModuleA = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [description, setDescription] = useState("");
    const [sketch, setSketch] = useState(null);
    const [matches, setMatches] = useState([]);
    const [verificationResult, setVerificationResult] = useState(null);
    const [recording, setRecording] = useState(false);
    const [progress, setProgress] = useState(0);
    const [audioBlob, setAudioBlob] = useState(null);
    const mediaRecorderRef = useRef(null);
    const chunksRef = useRef([]);

    const [isListening, setIsListening] = useState(false);
    const recognitionRef = useRef(null);
    const shouldStopRef = useRef(false);

    // Initialize Speech Recognition
    const toggleListening = () => {
        if (isListening) {
            shouldStopRef.current = true; // User intentionally stopped
            if (recognitionRef.current) {
                recognitionRef.current.stop();
            }
            setIsListening(false);
            return;
        }

        if (!('webkitSpeechRecognition' in window)) {
            alert("Your browser does not support speech recognition. Please use Chrome/Edge.");
            return;
        }

        shouldStopRef.current = false; // Reset stop flag
        const recognition = new window.webkitSpeechRecognition();
        recognitionRef.current = recognition;

        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
            setIsListening(true);
        };

        recognition.onresult = (event) => {
            let finalTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript + ' ';
                }
            }
            if (finalTranscript) {
                setDescription(prev => (prev + " " + finalTranscript).trim());
            }
        };

        recognition.onerror = (event) => {
            console.error("Speech recognition error", event.error);
            // Don't auto-restart on error to avoid infinite loops, but update state
            if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
                setIsListening(false);
            }
        };

        recognition.onend = () => {
            // Auto-restart if not intentionally stopped
            if (!shouldStopRef.current) {
                try {
                    recognition.start();
                } catch (e) {
                    console.error("Failed to restart recognition:", e);
                    setIsListening(false);
                }
            } else {
                setIsListening(false);
            }
        };

        recognition.start();
    };



    const handleGenerate = async () => {
        if (!description.trim()) {
            alert("Please enter a description or record audio first");
            return;
        }

        setLoading(true);
        setProgress(0);

        try {
            // 1. Start generation job
            console.log("Starting generation job...");
            const startResponse = await axios.post("http://localhost:8086/api/start-generation", {
                prompt: description
            });

            const jobId = startResponse.data.job_id;
            console.log("Job started with ID:", jobId);

            // 2. Poll for status
            let attempts = 0;
            const maxAttempts = 360; // 30 mins (5s interval)

            const pollInterval = setInterval(async () => {
                attempts++;

                try {
                    const statusResponse = await axios.get(`http://localhost:8086/api/check-status/${jobId}`);
                    const status = statusResponse.data.status;
                    const currentProgress = statusResponse.data.progress || 0;

                    setProgress(currentProgress);
                    console.log(`Poll ${attempts}: ${status} (${currentProgress}%)`);

                    if (status === "completed") {
                        clearInterval(pollInterval);
                        console.log("Generation completed!");

                        setSketch(statusResponse.data.sketch);
                        setMatches(statusResponse.data.matches || []);
                        setLoading(false);
                        setProgress(100);

                        // Log interaction
                        SessionManager.logInteraction('generate', description, {
                            sketch_generated: true,
                            matches_found: statusResponse.data.matches?.length || 0
                        });
                    } else if (status === "failed") {
                        clearInterval(pollInterval);
                        console.error("Job failed:", statusResponse.data.error);
                        alert(`Generation failed: ${statusResponse.data.error}`);
                        setLoading(false);
                    } else if (attempts >= maxAttempts) {
                        clearInterval(pollInterval);
                        alert("Generation timed out. Please check backend logs.");
                        setLoading(false);
                    }
                } catch (err) {
                    console.error("Polling error:", err);
                    // Don't stop polling on transient network errors
                }
            }, 5000); // Poll every 5 seconds

        } catch (error) {
            console.error("Error starting sketch generation:", error);
            alert(`Error: ${error.response?.data?.detail || error.message}`);
            setLoading(false);
        }
    };

    return (
        <div className="space-y-8">
            <header>
                <h2 className="text-3xl font-bold text-white mb-2">Speech/Text to Sketch</h2>
                <p className="text-slate-400">Describe the suspect by typing or speaking.</p>
            </header>

            {/* Input Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="space-y-6">
                    <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700">
                        <h3 className="text-xl font-semibold mb-4 text-blue-400">1. Suspect Description</h3>

                        <div className="space-y-4">
                            {/* Audio Recording */}
                            <div className="flex gap-2">
                                <button
                                    onClick={toggleListening}
                                    className={`flex-1 font-semibold py-3 px-6 rounded-lg transition-all flex items-center justify-center gap-2 ${isListening
                                        ? "bg-red-600 hover:bg-red-700 animate-pulse text-white"
                                        : "bg-blue-600 hover:bg-blue-700 text-white"
                                        }`}
                                >
                                    {isListening ? (
                                        <>
                                            <StopCircle className="w-5 h-5" />
                                            Stop Listening
                                        </>
                                    ) : (
                                        <>
                                            <Mic className="w-5 h-5" />
                                            Start Dictation
                                        </>
                                    )}
                                </button>
                            </div>

                            {/* Text Input */}
                            <textarea
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                placeholder="Describe the suspect (e.g., Male, 30 years old, short black hair, oval face, thick eyebrows, medium eyes, straight nose, thin lips, light beard...)"
                                className="w-full h-40 px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 resize-none"
                            />

                            <button
                                onClick={handleGenerate}
                                disabled={loading || !description.trim()}
                                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 rounded-lg transition-all"
                            >
                                {loading ? `Generating... ${progress}%` : "Generate Sketch"}
                            </button>
                        </div>
                    </div>
                </div>

                {/* Output Section */}
                <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700 min-h-[400px]">
                    <h3 className="text-xl font-semibold mb-4 text-rose-400">2. Generated Sketch</h3>

                    {loading ? (
                        <div className="flex flex-col items-center justify-center h-64 text-slate-500 gap-3">
                            <Loader className="animate-spin w-10 h-10 text-blue-500" />
                            <p>Generating AI-powered forensic sketch...</p>
                            <p className="text-xs text-slate-500 max-w-xs text-center">
                                This may take 5-10 minutes on CPU. Please be patient and don't close the tab.
                            </p>
                            <p className="text-xs text-blue-400">
                                First-time use may take longer while downloading models.
                            </p>
                        </div>
                    ) : sketch ? (
                        <div className="space-y-4">
                            <div className="rounded-lg overflow-hidden border border-slate-700">
                                <img src={sketch} alt="Generated Sketch" className="w-full h-auto object-cover" />
                            </div>

                            {/* Action Buttons */}
                            <div className="space-y-3">
                                <button
                                    onClick={async () => {
                                        if (!sketch) return;
                                        setLoading(true);
                                        try {
                                            // Convert base64 to blob
                                            const res = await fetch(sketch);
                                            const blob = await res.blob();
                                            const file = new File([blob], "generated_sketch.png", { type: "image/png" });

                                            const formData = new FormData();
                                            formData.append("file", file);

                                            const response = await axios.post("http://localhost:8086/api/verify-and-search", formData);
                                            const { verification, matches } = response.data;

                                            setVerificationResult(verification);
                                            setMatches(matches); // This updates the new Matches section

                                            // Scroll to matches if any
                                            setTimeout(() => {
                                                const matchesElement = document.getElementById('matches-section');
                                                if (matchesElement) matchesElement.scrollIntoView({ behavior: 'smooth' });
                                            }, 100);

                                        } catch (error) {
                                            console.error("Verification error:", error);
                                            alert("Error verifying sketch");
                                        } finally {
                                            setLoading(false);
                                        }
                                    }}
                                    className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg transition-all flex items-center justify-center gap-2"
                                >
                                    <span>Verify & Search This Sketch</span>
                                </button>

                                {verificationResult && (
                                    <div className={`p-4 rounded-lg border flex flex-col items-center justify-center gap-2 ${verificationResult.label === 'Real' ? 'bg-green-900/30 border-green-500' : 'bg-red-900/30 border-red-500'}`}>
                                        <div className="flex items-center gap-2">
                                            <div className={`w-3 h-3 rounded-full ${verificationResult.label === 'Real' ? 'bg-green-500' : 'bg-red-500'}`}></div>
                                            <p className={`font-bold text-lg ${verificationResult.label === 'Real' ? 'text-green-400' : 'text-red-400'}`}>
                                                Authenticity: {verificationResult.label}
                                            </p>
                                        </div>
                                        <p className="text-sm text-slate-300">Confidence: {(verificationResult.confidence * 100).toFixed(1)}%</p>
                                        {verificationResult.label === 'Fake' && (
                                            <p className="text-xs text-slate-400 mt-1">(Expected for generated sketches)</p>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="flex items-center justify-center h-64 text-slate-600 border-2 border-dashed border-slate-700 rounded-lg">
                            <p>No sketch generated yet</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Matches Section Display (Integrated) */}
            {matches.length > 0 && (
                <div id="matches-section" className="bg-slate-800/50 p-6 rounded-xl border border-slate-700 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <h3 className="text-xl font-semibold mb-4 text-green-400 flex items-center gap-2">
                        <span className="bg-green-500/20 text-green-400 p-1.5 rounded-lg">✓</span>
                        Database Matches Found
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {matches.map((match) => (
                            <div key={match.id} className="bg-slate-900 rounded-lg overflow-hidden border border-slate-700 hover:border-green-500 transition-all group">
                                <div className="relative aspect-square">
                                    <img src={match.image} alt={match.payload.filename} className="w-full h-full object-cover" />
                                    <div className="absolute top-2 right-2 bg-black/70 px-2 py-1 rounded text-xs text-green-400 border border-green-500/30">
                                        {(match.score * 100).toFixed(0)}% Similarity
                                    </div>
                                </div>
                                <div className="p-4 space-y-2">
                                    <h4 className="font-medium text-white text-lg truncate" title={match.payload.filename}>
                                        {match.payload.filename}
                                    </h4>
                                    <p className="text-sm text-orange-400">{match.payload.crime_type}</p>
                                    <p className="text-xs text-slate-500">{match.payload.timestamp?.split('T')[0]}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default ModuleA;
