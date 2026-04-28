import { useState, useRef, useCallback, useEffect } from "react";
import { aiAPI, formatApiError } from "../../../utils/api";

/**
 * VoiceRecorder – a mic button that records audio, sends it to the backend
 * speech-to-text endpoint, and calls onTranscript with the resulting text.
 *
 * Props:
 *   onTranscript(text: string)  – called with the transcribed English text
 *   disabled?: boolean          – disables the button
 */
export default function VoiceRecorder({ onTranscript, disabled = false }) {
  const [recording, setRecording] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [elapsed, setElapsed] = useState(0);

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);
  const timerRef = useRef(null);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, []);

  const startRecording = useCallback(async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        // Stop all tracks
        stream.getTracks().forEach((t) => t.stop());
        streamRef.current = null;

        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }

        const blob = new Blob(chunksRef.current, { type: mimeType });
        chunksRef.current = [];

        if (blob.size === 0) {
          setError("No audio captured.");
          return;
        }

        // Send to backend
        setProcessing(true);
        try {
          const res = await aiAPI.speechToText(blob);
          if (res.data.success && res.data.text) {
            onTranscript(res.data.text);
          } else {
            setError(res.data.error || "No speech detected.");
          }
        } catch (err) {
          setError(formatApiError(err.response?.data) || "Transcription failed.");
        } finally {
          setProcessing(false);
          setElapsed(0);
        }
      };

      mediaRecorder.start(250); // collect chunks every 250ms
      setRecording(true);
      setElapsed(0);

      // Elapsed timer
      timerRef.current = setInterval(() => {
        setElapsed((e) => e + 1);
      }, 1000);
    } catch (err) {
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        setError("Microphone access denied. Please allow microphone permission.");
      } else {
        setError("Could not access microphone.");
      }
    }
  }, [onTranscript]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    setRecording(false);
  }, []);

  const handleClick = () => {
    if (disabled || processing) return;
    if (recording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const formatTime = (secs) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="relative flex items-center">
      {/* Error tooltip */}
      {error && (
        <div className="absolute bottom-full mb-2 right-0 bg-red-500/90 text-white text-xs rounded-lg px-3 py-2 whitespace-nowrap shadow-lg animate-fade-in">
          {error}
          <button
            onClick={() => setError(null)}
            className="ml-2 text-white/70 hover:text-white"
          >
            ✕
          </button>
        </div>
      )}

      {/* Recording timer badge */}
      {recording && (
        <div className="mr-2 flex items-center gap-1.5 bg-red-500/20 border border-red-500/40 rounded-full px-3 py-1 animate-fade-in">
          <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
          <span className="text-xs text-red-400 font-mono tabular-nums">
            {formatTime(elapsed)}
          </span>
        </div>
      )}

      {/* Processing indicator */}
      {processing && (
        <div className="mr-2 flex items-center gap-1.5 bg-yellow-600/20 border border-yellow-600/40 rounded-full px-3 py-1 animate-fade-in">
          <svg className="w-3 h-3 text-yellow-500 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span className="text-xs text-yellow-400">Transcribing...</span>
        </div>
      )}

      {/* Mic button */}
      <button
        type="button"
        onClick={handleClick}
        disabled={disabled || processing}
        title={recording ? "Stop recording" : "Voice input"}
        className={`relative rounded-full p-3 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-black
          ${
            recording
              ? "bg-red-500 hover:bg-red-600 text-white focus:ring-red-500 scale-110"
              : processing
                ? "bg-gray-700 text-gray-400 cursor-not-allowed"
                : "bg-gray-800 hover:bg-gray-700 text-gray-300 hover:text-yellow-400 focus:ring-yellow-600"
          }
          ${disabled ? "opacity-50 cursor-not-allowed" : ""}
        `}
      >
        {/* Pulse rings when recording */}
        {recording && (
          <>
            <span className="absolute inset-0 rounded-full bg-red-500 animate-ping opacity-20" />
            <span className="absolute -inset-1 rounded-full border-2 border-red-400 opacity-40 animate-pulse" />
          </>
        )}

        {/* Mic icon */}
        {recording ? (
          // Stop icon
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 relative z-10">
            <path fillRule="evenodd" d="M4.5 7.5a3 3 0 013-3h9a3 3 0 013 3v9a3 3 0 01-3 3h-9a3 3 0 01-3-3v-9z" clipRule="evenodd" />
          </svg>
        ) : (
          // Microphone icon
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
            <path d="M8.25 4.5a3.75 3.75 0 117.5 0v8.25a3.75 3.75 0 11-7.5 0V4.5z" />
            <path d="M6 10.5a.75.75 0 01.75.75v1.5a5.25 5.25 0 1010.5 0v-1.5a.75.75 0 011.5 0v1.5a6.751 6.751 0 01-6 6.709v2.291h3a.75.75 0 010 1.5h-7.5a.75.75 0 010-1.5h3v-2.291a6.751 6.751 0 01-6-6.709v-1.5A.75.75 0 016 10.5z" />
          </svg>
        )}
      </button>
    </div>
  );
}
