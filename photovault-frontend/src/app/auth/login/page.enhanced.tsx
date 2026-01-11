'use client';

import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';
import { ToastContainer } from '@/components/ui/ToastContainer';
import { AuthForm, type LoginData } from '@/components/auth/AuthForm';
import { authService } from '@/lib/auth/auth-service';

/**
 * Enhanced Login Page with PHASE 3 UI Foundation
 * Features:
 * - Toast notifications
 * - Form validation
 * - Loading states
 * - Error handling
 */
export default function LoginPage() {
  const router = useRouter();

  const handleSubmit = async (data: LoginData) => {
    await authService.login({
      email: data.email,
      password: data.password,
    });

    // Redirect on success
    router.push('/dashboard');
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden bg-black">
      {/* Toast notifications */}
      <ToastContainer />

      {/* Animated background */}
      {/* eslint-disable-next-line */}
      <div
        className="absolute inset-0"
        style={{
          background:
            'radial-gradient(circle at 50% 50%, rgba(255, 215, 0, 0.1) 0%, transparent 70%)',
        }}
      />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: 'spring', stiffness: 200, damping: 25 }}
        className="w-full max-w-md relative z-10"
      >
        <div className="glass rounded-2xl p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full glass mb-4">
              <Sparkles className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-semibold text-white mb-2">
              Welcome Back
            </h1>
            <p className="text-white/60">
              Sign in to your PhotoVault account
            </p>
          </div>

          {/* Enhanced Auth Form with validation & toasts */}
          <AuthForm mode="login" onSubmit={handleSubmit} />

          {/* Links */}
          <div className="mt-6 space-y-3 text-center text-sm">
            <p className="text-white/60">
              <a
                href="/auth/forgot-password"
                className="text-white hover:text-white/80 underline"
              >
                Forgot password?
              </a>
            </p>
            <p className="text-white/60">
              Don&apos;t have an account?{' '}
              <a
                href="/auth/signup"
                className="text-white hover:text-white/80 underline font-medium"
              >
                Sign up
              </a>
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
