"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { authStore } from "@/lib/auth/auth-store";
import { GlassCard } from "@/components/GlassCard";

/**
 * Landing Page - Redirects to dashboard if logged in, otherwise shows welcome
 */
export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    const token = authStore.getToken();
    if (token) {
      router.push("/dashboard");
    }
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
      {/* Animated background */}
      <motion.div
        className="absolute inset-0"
        style={{
          background: "radial-gradient(circle at 50% 50%, rgba(135, 206, 235, 0.1) 0%, transparent 70%)",
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

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: "spring", stiffness: 200, damping: 25 }}
        className="w-full max-w-2xl relative z-10 text-center"
      >
        <GlassCard>
          <motion.div
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2 }}
            className="inline-flex items-center justify-center w-20 h-20 rounded-full glass mb-6"
          >
            <Sparkles className="w-10 h-10 text-white" />
          </motion.div>

          <h1 className="text-5xl font-bold text-white mb-4">
            PhotoVault
          </h1>
          <p className="text-xl text-white/80 mb-2">
            AI-First Photo Management
          </p>
          <p className="text-white/60 mb-8">
            No buttons. Just speak your intent.
          </p>

          <div className="flex gap-4 justify-center">
            <motion.a
              href="/auth/login"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-6 py-3 rounded-xl glass text-white font-medium hover:bg-white/10 transition-colors"
            >
              Sign In
            </motion.a>
            <motion.a
              href="/auth/signup"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-6 py-3 rounded-xl glass text-white font-medium hover:bg-white/10 transition-colors"
            >
              Get Started
            </motion.a>
          </div>
        </GlassCard>
      </motion.div>
    </div>
  );
}
