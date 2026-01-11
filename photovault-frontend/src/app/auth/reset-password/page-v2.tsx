"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { Lock } from "lucide-react";
import { Button, Input } from "@/components/ui";
import { authService } from "@/lib/auth/auth-service";
import type { AuthError } from "@/lib/types/auth";

/**
 * Password Reset Page
 * User completes password reset with token from email
 */
export default function ResetPasswordPage() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const router = useRouter();

  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<AuthError | null>(null);
  const [success, setSuccess] = useState(false);

  // Validation
  const validateForm = (): boolean => {
    if (password.length < 8) {
      setError({ message: "Password must be at least 8 characters" });
      return false;
    }

    if (password !== passwordConfirm) {
      setError({ message: "Passwords do not match" });
      return false;
    }

    if (!/[A-Z]/.test(password)) {
      setError({ message: "Password must contain at least one uppercase letter" });
      return false;
    }

    if (!/[0-9]/.test(password)) {
      setError({ message: "Password must contain at least one number" });
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!token) {
      setError({ message: "Invalid reset link. Please request a new one." });
      return;
    }

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      await authService.resetPassword({
        token,
        password,
        password_confirm: passwordConfirm,
      });

      setSuccess(true);

      // Redirect to login after 2 seconds
      setTimeout(() => {
        router.push("/auth/login");
      }, 2000);
    } catch (err) {
      const error = err as { message?: string; code?: string };
      setError({
        message: error.message || "Password reset failed. Please try again.",
        code: error.code,
      });
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-black">
        <div className="glass rounded-2xl p-8 max-w-md w-full text-center">
          <h1 className="text-2xl font-semibold text-white mb-4">Invalid Reset Link</h1>
          <p className="text-white/60 mb-6">
            This password reset link is invalid or has expired.
          </p>
          <Button variant="primary" fullWidth onClick={() => router.push("/auth/forgot-password")}>
            Request New Link
          </Button>
        </div>
      </div>
    );
  }

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
              <Lock className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-semibold text-white mb-2">Reset Password</h1>
            <p className="text-white/60">Create a new secure password</p>
          </div>

          {/* Success Message */}
          {success && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mb-4 p-4 rounded-lg bg-green-500/20 border border-green-500/50 text-green-200"
            >
              ✓ Password reset successfully! Redirecting to login...
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
              label="New Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 8 characters"
              helpText="Include uppercase, lowercase, and numbers"
              disabled={loading || success}
            />

            <Input
              label="Confirm Password"
              type="password"
              value={passwordConfirm}
              onChange={(e) => setPasswordConfirm(e.target.value)}
              placeholder="Re-enter password"
              disabled={loading || success}
            />

            {/* Password strength indicator */}
            {password.length > 0 && (
              <div className="mt-4">
                <div className="flex gap-1">
                  <div
                    className={`flex-1 h-2 rounded-full ${
                      password.length >= 8 ? "bg-green-500" : "bg-white/20"
                    }`}
                  />
                  <div
                    className={`flex-1 h-2 rounded-full ${
                      /[A-Z]/.test(password) ? "bg-green-500" : "bg-white/20"
                    }`}
                  />
                  <div
                    className={`flex-1 h-2 rounded-full ${
                      /[0-9]/.test(password) ? "bg-green-500" : "bg-white/20"
                    }`}
                  />
                </div>
                <p className="text-white/50 text-xs mt-2">
                  {password.length >= 8 && /[A-Z]/.test(password) && /[0-9]/.test(password)
                    ? "✓ Strong password"
                    : "Weak password"}
                </p>
              </div>
            )}

            <Button
              type="submit"
              variant="primary"
              fullWidth
              loading={loading}
              disabled={success}
            >
              {success ? "Password Reset!" : "Reset Password"}
            </Button>
          </form>

          {/* Footer */}
          <div className="mt-6 text-center">
            <p className="text-white/60 text-sm">
              Remember your password?{" "}
              <a href="/auth/login" className="text-white hover:text-white/80 underline">
                Sign in
              </a>
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
