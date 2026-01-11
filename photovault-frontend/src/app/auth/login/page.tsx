"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Button, Input } from "@/components/ui";
import { authService } from "@/lib/auth/auth-service";
import { Sparkles, Eye, EyeOff } from "lucide-react";
import type { AuthError } from "@/lib/types/auth";

/**
 * Login Page - Email/Password with multi-modal auth support
 */
export default function LoginPage() {
  const [mode, setMode] = useState<"email" | "voice" | "face">("email");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<AuthError | null>(null);
  const [emailNotVerified, setEmailNotVerified] = useState(false);
  const [success, setSuccess] = useState(false);
  const [resendingVerification, setResendingVerification] = useState(false);
  const router = useRouter();

  /**
   * Resend email verification
   */
  const handleResendVerification = async () => {
    if (!email) return;
    
    setResendingVerification(true);
    try {
      // Call resend verification endpoint
      await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/api/auth/verify/resend/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });
      
      setError({
        message: "Verification email sent! Please check your inbox.",
        code: "200"
      });
    } catch (err) {
      setError({
        message: "Failed to send verification email. Please try again.",
        code: "500"
      });
    } finally {
      setResendingVerification(false);
    }
  };

  /**
   * Handle traditional email/password login
   */
  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Validation
    if (!email.includes("@")) {
      setError({ message: "Please enter a valid email" });
      setLoading(false);
      return;
    }

    if (password.length < 1) {
      setError({ message: "Please enter your password" });
      setLoading(false);
      return;
    }

    try {
      await authService.login({ email, password });
      setSuccess(true);

      // Redirect to dashboard
      setTimeout(() => {
        router.push("/dashboard");
      }, 500);
    } catch (err: any) {
      // Check if it's an email verification error
      if (err.message && err.message.includes("Email not verified")) {
        setEmailNotVerified(true);
        setError({
          message: "Please verify your email address before signing in.",
          code: err.code,
        });
      } else {
        setError({
          message: err.message || "Login failed. Please try again.",
          code: err.code,
        });
      }
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden bg-black">
      {/* Animated background */}
      {/* eslint-disable-next-line */}
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
            <div className="inline-flex items-center justify-center w-24 h-24 mb-6">
              <motion.svg
                width="80"
                height="80"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                initial="hidden"
                animate="visible"
              >
                <motion.path
                  d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z"
                  stroke="white"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  variants={{
                    hidden: { pathLength: 0, opacity: 0 },
                    visible: {
                      pathLength: 1,
                      opacity: 1,
                      transition: {
                        pathLength: { duration: 1.5, ease: "easeInOut" },
                        opacity: { duration: 0.5 }
                      }
                    }
                  }}
                />
                <motion.path
                  d="M12 8V11"
                  stroke="white"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  variants={{
                    hidden: { pathLength: 0, opacity: 0 },
                    visible: {
                      pathLength: 1,
                      opacity: 1,
                      transition: {
                        pathLength: { delay: 1, duration: 0.5, ease: "easeInOut" },
                        opacity: { delay: 1, duration: 0.2 }
                      }
                    }
                  }}
                />
                <motion.rect
                  x="9"
                  y="11"
                  width="6"
                  height="5"
                  rx="1"
                  stroke="white"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  variants={{
                    hidden: { pathLength: 0, opacity: 0 },
                    visible: {
                      pathLength: 1,
                      opacity: 1,
                      transition: {
                        pathLength: { delay: 1.2, duration: 0.5, ease: "easeInOut" },
                        opacity: { delay: 1.2, duration: 0.2 }
                      }
                    }
                  }}
                />
              </motion.svg>
            </div>
            <h1 className="text-3xl font-semibold text-white mb-2">Welcome Back</h1>
            <p className="text-white/60">Sign in to your PhotoVault account</p>
          </div>

          {/* Success Message */}
          {success && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mb-4 p-4 rounded-lg bg-green-500/20 border border-green-500/50 text-green-200"
            >
              ✓ Logged in successfully! Redirecting...
            </motion.div>
          )}

          {/* Error Message */}
          {error && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className={`mb-4 p-4 rounded-lg border text-sm ${
                error.code === "200" 
                  ? "bg-green-500/20 border-green-500/50 text-green-200"
                  : "bg-red-500/20 border-red-500/50 text-red-200"
              }`}
            >
              {error.message}
              {emailNotVerified && (
                <div className="mt-3 pt-3 border-t border-red-500/30">
                  <p className="text-xs text-red-300 mb-2">
                    Haven't received the verification email?
                  </p>
                  <button
                    type="button"
                    onClick={handleResendVerification}
                    disabled={resendingVerification || !email}
                    className="text-xs bg-red-500/20 hover:bg-red-500/30 px-3 py-1 rounded border border-red-500/50 disabled:opacity-50"
                  >
                    {resendingVerification ? "Sending..." : "Resend Verification Email"}
                  </button>
                </div>
              )}
            </motion.div>
          )}

          {/* Login Form */}
          <form onSubmit={handleEmailLogin} className="space-y-4">
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              disabled={loading || success}
            />

            <div className="relative">
              <Input
                label="Password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Your password"
                disabled={loading || success}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 top-10 text-white/60 hover:text-white"
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>

            <Button
              type="submit"
              variant="primary"
              fullWidth
              loading={loading}
              disabled={success}
            >
              {success ? "Logged In!" : "Sign In"}
            </Button>
          </form>

          {/* Links */}
          <div className="mt-6 space-y-3 text-center text-sm">
            <p className="text-white/60">
              <a href="/auth/forgot-password" className="text-white hover:text-white/80 underline">
                Forgot password?
              </a>
            </p>
            <p className="text-white/60">
              Don&apos;t have an account?{" "}
              <a href="/auth/signup" className="text-white hover:text-white/80 underline font-medium">
                Sign up
              </a>
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
