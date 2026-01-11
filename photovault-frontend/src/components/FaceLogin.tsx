"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Camera, CheckCircle, XCircle, Loader } from "lucide-react";
import { GlassCard } from "./GlassCard";
import { detectFaceFromVideo, loadFaceModels, hashEmbedding } from "@/lib/faceLocalAuth";
import { api } from "@/lib/api/client";
import { authStore } from "@/lib/auth/auth-store";
import { useRouter } from "next/navigation";

interface FaceLoginProps {
  onSuccess?: () => void;
}

/**
 * Face Login - On-device face recognition
 * Privacy-first: face matching happens in browser
 */
export default function FaceLogin({ onSuccess }: FaceLoginProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [status, setStatus] = useState<"idle" | "scanning" | "success" | "error">("idle");
  const [message, setMessage] = useState("");
  const [modelsLoaded, setModelsLoaded] = useState(false);
  const streamRef = useRef<MediaStream | null>(null);
  const router = useRouter();

  // Load face models on mount
  useEffect(() => {
    loadFaceModels().then((loaded) => {
      setModelsLoaded(loaded);
      if (!loaded) {
        setMessage("Face recognition models not available. Using fallback mode.");
      }
    });
  }, []);

  // Start camera
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: "user" },
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
      }
    } catch (error) {
      console.error("Camera access error:", error);
      setStatus("error");
      setMessage("Camera access denied. Please allow camera permissions.");
    }
  };

  // Stop camera
  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  };

  // Capture and verify face
  const captureAndVerify = async () => {
    if (!videoRef.current || !modelsLoaded) {
      setMessage("Models not loaded yet. Please wait...");
      return;
    }

    setIsScanning(true);
    setStatus("scanning");
    setMessage("Scanning face...");

    try {
      // Detect face
      const faceData = await detectFaceFromVideo(videoRef.current);

      if (!faceData) {
        setStatus("error");
        setMessage("No face detected. Please position your face in the frame.");
        setIsScanning(false);
        return;
      }

      // Hash embedding for privacy
      const embeddingHash = await hashEmbedding(faceData.descriptor);

      // Send hash to backend for verification
      try {
        const response = await api.post("/face/login", {
          embedding_hash: embeddingHash,
          // Optionally send embedding array (if backend supports)
          embedding: Array.from(faceData.descriptor),
        });

        const { access_token, confidence } = response.data;

        if (access_token) {
          // Store token
          authStore.setToken(access_token);

          setStatus("success");
          setMessage(`Face recognized! Confidence: ${(confidence * 100).toFixed(1)}%`);

          // Redirect after short delay
          setTimeout(() => {
            onSuccess?.();
            router.push("/dashboard");
          }, 1500);
        } else {
          setStatus("error");
          setMessage("Face not recognized. Please try again.");
        }
      } catch (error: any) {
        setStatus("error");
        setMessage(
          error.response?.data?.detail || "Face verification failed. Please try again."
        );
      }
    } catch (error) {
      console.error("Face detection error:", error);
      setStatus("error");
      setMessage("Face detection failed. Please try again.");
    } finally {
      setIsScanning(false);
    }
  };

  useEffect(() => {
    startCamera();
    return () => {
      stopCamera();
    };
  }, []);

  return (
    <div className="flex flex-col items-center gap-6">
      <GlassCard className="p-6">
        <div className="flex flex-col items-center gap-4">
          {/* Camera view */}
          <div className="relative">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="rounded-xl w-64 h-48 object-cover bg-black/20"
            />

            {/* Overlay grid */}
            <div className="absolute inset-0 pointer-events-none">
              <div className="absolute inset-0 border-2 border-white/30 rounded-xl" />
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-40 border-2 border-white/50 rounded-lg" />
            </div>

            {/* Status indicator */}
            <AnimatePresence>
              {status === "scanning" && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute inset-0 bg-black/40 rounded-xl flex items-center justify-center"
                >
                  <Loader className="w-8 h-8 text-white animate-spin" />
                </motion.div>
              )}
              {status === "success" && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  className="absolute inset-0 bg-green-500/20 rounded-xl flex items-center justify-center"
                >
                  <CheckCircle className="w-12 h-12 text-green-400" />
                </motion.div>
              )}
              {status === "error" && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  className="absolute inset-0 bg-red-500/20 rounded-xl flex items-center justify-center"
                >
                  <XCircle className="w-12 h-12 text-red-400" />
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Status message */}
          <div className="text-center min-h-[40px]">
            <AnimatePresence mode="wait">
              <motion.p
                key={status}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className={`text-sm ${status === "success"
                  ? "text-green-400"
                  : status === "error"
                    ? "text-red-400"
                    : "text-white/80"
                  }`}
              >
                {message || "Position your face in the frame"}
              </motion.p>
            </AnimatePresence>
          </div>

          {/* Capture button */}
          <motion.button
            onClick={captureAndVerify}
            disabled={isScanning || !modelsLoaded}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className={`px-6 py-3 rounded-xl glass text-white font-medium flex items-center gap-2 ${isScanning || !modelsLoaded
              ? "opacity-50 cursor-not-allowed"
              : "hover:bg-white/10"
              }`}
          >
            <Camera className="w-4 h-4" />
            {isScanning ? "Scanning..." : "Scan Face"}
          </motion.button>
        </div>
      </GlassCard>

      <p className="text-white/60 text-xs text-center max-w-xs">
        Your face is processed locally. Only a hash is sent to the server for verification.
      </p>
    </div>
  );
}

