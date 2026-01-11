"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { getEmotionFromIntent, Intent } from "@/lib/intent";

type Emotion = "happy" | "calm" | "sad" | "neutral";

interface EmotionShellProps {
  intent: Intent | null;
  children: React.ReactNode;
}

/**
 * Emotion-Reactive Shell - Changes UI color and blur based on mood
 */
export function EmotionShell({ intent, children }: EmotionShellProps) {
  const [emotion, setEmotion] = useState<Emotion>("neutral");
  const [color, setColor] = useState("rgba(255, 255, 255, 0.05)");

  useEffect(() => {
    if (intent) {
      const newEmotion = getEmotionFromIntent(intent);
      setEmotion(newEmotion);
      
      // Set color based on emotion
      switch (newEmotion) {
        case "happy":
          setColor("rgba(255, 215, 0, 0.1)");
          break;
        case "calm":
          setColor("rgba(135, 206, 235, 0.1)");
          break;
        case "sad":
          setColor("rgba(147, 112, 219, 0.1)");
          break;
        default:
          setColor("rgba(255, 255, 255, 0.05)");
      }
    } else {
      setEmotion("neutral");
      setColor("rgba(255, 255, 255, 0.05)");
    }
  }, [intent]);

  return (
    <motion.div
      className="min-h-screen w-full relative overflow-hidden"
      style={{
        backgroundColor: color,
      }}
      animate={{
        filter: emotion === "happy" ? "brightness(1.1)" : 
                emotion === "calm" ? "brightness(0.95)" :
                emotion === "sad" ? "brightness(0.9)" : "brightness(1)",
      }}
      transition={{ duration: 0.5 }}
    >
      {/* Animated background gradient */}
      <motion.div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: emotion === "happy" 
            ? "radial-gradient(circle at 50% 50%, rgba(255, 215, 0, 0.1) 0%, transparent 70%)"
            : emotion === "calm"
            ? "radial-gradient(circle at 50% 50%, rgba(135, 206, 235, 0.1) 0%, transparent 70%)"
            : emotion === "sad"
            ? "radial-gradient(circle at 50% 50%, rgba(147, 112, 219, 0.1) 0%, transparent 70%)"
            : "transparent",
        }}
        animate={{
          opacity: [0.3, 0.5, 0.3],
        }}
        transition={{
          duration: 4,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      
      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>
    </motion.div>
  );
}

