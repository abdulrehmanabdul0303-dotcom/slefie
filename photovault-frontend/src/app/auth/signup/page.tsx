"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { Button, Input } from "@/components/ui";
import { authService } from "@/lib/auth/auth-service";
import type { AuthError } from "@/lib/types/auth";

/**
 * Signup Page - Registration form with validation
 */
export default function SignupPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<AuthError | null>(null);
  const [success, setSuccess] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Basic validation
    if (!name.trim()) {
      setError({ message: "Please enter your name" });
      setLoading(false);
      return;
    }

    if (!email.includes("@")) {
      setError({ message: "Please enter a valid email" });
      setLoading(false);
      return;
    }

    if (password.length < 8) {
      setError({ message: "Password must be at least 8 characters" });
      setLoading(false);
      return;
    }

    if (!/[A-Z]/.test(password) || !/[a-z]/.test(password) || !/[0-9]/.test(password)) {
      setError({ message: "Password must contain at least one uppercase letter, one lowercase letter, and one number" });
      setLoading(false);
      return;
    }

    try {
      await authService.signup({ name, email, password });
      setSuccess(true);

      // Don't redirect to dashboard - user needs to verify email first
      // Show success message instead
      setTimeout(() => {
        router.push("/auth/login?message=Please check your email to verify your account");
      }, 2000);
    } catch (err: any) {
      setError({
        message: err.message || "Signup failed. Please try again.",
        code: err.code,
      });
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden bg-black">
      {/* Animated background */}
      <div
        className="absolute inset-0"
        style={{
          background: "radial-gradient(circle at 50% 50%, rgba(255, 215, 0, 0.1) 0%, transparent 70%)",
        }}
      />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: "spring", stiffness: 200, damping: 25 }}
        className="w-full max-w-md relative z-10"
      >
        <div className="glass rounded-2xl p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full glass mb-4">
              <Sparkles className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-semibold text-white mb-2">Join PhotoVault</h1>
            <p className="text-white/60">Start your photo journey</p>
          </div>

          {/* Success Message */}
          {success && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mb-4 p-4 rounded-lg bg-green-500/20 border border-green-500/50 text-green-200"
            >
              ✓ Account created successfully! Please check your email to verify your account before logging in.
            </motion.div>
          )}

          {/* Error Message */}
          {error && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mb-4 p-4 rounded-lg bg-red-500/20 border border-red-500/50 text-red-200 text-sm"
            >
              {error.message}
            </motion.div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Full Name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="John Doe"
              disabled={loading || success}
            />

            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              disabled={loading || success}
            />

            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 8 characters"
              helpText="Use a strong password with mix of letters, numbers"
              disabled={loading || success}
            />

            <Button
              type="submit"
              variant="primary"
              fullWidth
              loading={loading}
              disabled={success}
            >
              {success ? "Account Created!" : "Create Account"}
            </Button>
          </form>

          {/* Footer */}
          <div className="mt-6 text-center">
            <p className="text-white/60 text-sm">
              Already have an account?{" "}
              <a
                href="/auth/login"
                className="text-white hover:text-white/80 underline font-medium"
              >
                Sign in
              </a>
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
