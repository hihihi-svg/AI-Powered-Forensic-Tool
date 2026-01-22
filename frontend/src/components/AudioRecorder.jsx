import { useState, useRef } from "react";
import { Mic, Square, Loader } from "lucide-react";

const AudioRecorder = ({ onRecordingComplete }) => {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      chunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/wav" });
        onRecordingComplete(blob);
        chunksRef.current = [];
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Error accessing microphone:", err);
      alert("Microphone access denied");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      // Stop all tracks
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop());
    }
  };

  return (
    <div className="flex flex-col items-center gap-4 p-6 bg-gray-800 rounded-xl border border-gray-700 shadow-lg">
      <div className={`p-4 rounded-full transition-all duration-300 ${isRecording ? 'bg-red-500/20 animate-pulse' : 'bg-blue-500/10'}`}>
        {isRecording ? (
          <Mic className="w-8 h-8 text-red-500" />
        ) : (
          <Mic className="w-8 h-8 text-blue-400" />
        )}
      </div>
      
      <div className="text-center">
        <h3 className="text-white font-medium mb-1">
          {isRecording ? "Listening..." : "Describe the Suspect"}
        </h3>
        <p className="text-sm text-gray-400">
          {isRecording ? "Speak clearly about facial features" : "Click to start recording"}
        </p>
      </div>

      <button
        onClick={isRecording ? stopRecording : startRecording}
        className={`px-6 py-2 rounded-lg font-medium transition-all ${
          isRecording 
            ? "bg-red-500 hover:bg-red-600 text-white"
            : "bg-blue-600 hover:bg-blue-700 text-white"
        }`}
      >
        {isRecording ? "Stop Recording" : "Start Recording"}
      </button>
    </div>
  );
};

export default AudioRecorder;
