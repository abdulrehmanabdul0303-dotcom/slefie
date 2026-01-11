"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, MicOff, Sparkles } from "lucide-react";
import { GlassCard } from "./GlassCard";

interface VoiceLoginProps {
  onIntent: (intent: string) => void;
  onLogin?: (voiceText: string) => void;
}

/**
 * Voice Login - Web Speech API
 * User speaks "Login" or natural language commands
 */
export default function VoiceLogin({ onIntent, onLogin }: VoiceLoginProps) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [error, setError] = useState("");
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    // Check browser support
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setError("Voice recognition not supported in this browser");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onstart = () => {
      setIsListening(true);
      setError("");
    };

    recognition.onresult = (event: any) => {
      const current = event.resultIndex;
      const transcriptText = event.results[current][0].transcript;
      setTranscript(transcriptText);

      // If final result
      if (event.results[current].isFinal) {
        const text = transcriptText.toLowerCase().trim();
        
        // Check for login intent
        if (text.includes("login") || text.includes("sign in") || text.includes("enter")) {
          onLogin?.(text);
        } else {
          // Pass to intent parser
          onIntent(text);
        }
        
        setIsListening(false);
        setTranscript("");
      }
    };

    recognition.onerror = (event: any) => {
      console.error("Speech recognition error:", event.error);
      setError(`Error: ${event.error}`);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [onIntent, onLogin]);

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      try {
        recognitionRef.current.start();
      } catch (err) {
        console.error("Failed to start recognition:", err);
        setError("Failed to start voice recognition");
      }
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
    }
  };

  return (
    <div className="flex flex-col items-center gap-4">
      <GlassCard className="p-6">
        <div className="flex flex-col items-center gap-4">
          <motion.div
            animate={{
              scale: isListening ? [1, 1.2, 1] : 1,
            }}
            transition={{
              duration: 1,
              repeat: isListening ? Infinity : 0,
            }}
            className="relative"
          >
            <motion.button
              onClick={isListening ? stopListening : startListening}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              className={`w-20 h-20 rounded-full glass flex items-center justify-center ${
                isListening ? "bg-red-500/20" : "bg-white/10"
              }`}
            >
              {isListening ? (
                <MicOff className="w-8 h-8 text-red-400" />
              ) : (
                <Mic className="w-8 h-8 text-white" />
              )}
            </motion.button>

            {/* Pulsing ring when listening */}
            {isListening && (
              <motion.div
                className="absolute inset-0 rounded-full border-2 border-red-400"
                animate={{
                  scale: [1, 1.5, 1],
                  opacity: [1, 0, 1],
                }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                }}
              />
            )}
          </motion.div>

          <div className="text-center">
            <p className="text-white/80 text-sm mb-2">
              {isListening ? "Listening..." : "Tap to speak"}
            </p>
            {transcript && (
              <motion.p
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-white text-lg font-medium"
              >
                "{transcript}"
              </motion.p>
            )}
            {error && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-red-400 text-sm mt-2"
              >
                {error}
              </motion.p>
            )}
          </div>
        </div>
      </GlassCard>

      <p className="text-white/60 text-xs text-center max-w-xs">
        Say "Login" or describe what you want to see
      </p>
    </div>
  );
}

