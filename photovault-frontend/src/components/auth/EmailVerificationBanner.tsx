"use client";

import { useAuth } from "@/lib/auth/auth-provider";
import { api } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import { toast } from "sonner";
import { useState, useRef, useEffect } from "react";
import { X } from "lucide-react";

export function EmailVerificationBanner() {
  const { user, refreshMe } = useAuth();
  const [dismissed, setDismissed] = useState(false);
  const [resending, setResending] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      // Cancel any in-flight requests on unmount
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Don't show if email is verified or user is not logged in
  if (!user || user.email_verified !== false || dismissed) {
    return null;
  }

  async function handleResend() {
    // Cancel any previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();
    
    if (!mountedRef.current) return;
    setResending(true);
    
    try {
      // Fetch CSRF token
      try {
        const csrfRes = await api.get(endpoints.csrf, {
          signal: abortControllerRef.current.signal,
        });
        const csrfToken = csrfRes.data?.csrfToken ?? csrfRes.data;
        if (csrfToken) {
          // CSRF will be handled by interceptor
        }
      } catch (csrfError: any) {
        if (csrfError.name === 'AbortError' || csrfError.name === 'CanceledError') {
          return; // Request was cancelled
        }
        console.warn("Failed to fetch CSRF token:", csrfError);
      }

      if (!user) return;
      
      await api.post(endpoints.emailResend, { email: user.email }, {
        signal: abortControllerRef.current.signal,
      });
      
      if (!mountedRef.current) return;
      toast.success("Verification email sent! Check your inbox.");
    } catch (e: any) {
      if (e.name === 'AbortError' || e.name === 'CanceledError') {
        return; // Request was cancelled, ignore
      }
      if (mountedRef.current) {
        toast.error("Failed to resend email. Please try again later.");
      }
    } finally {
      if (mountedRef.current) {
        setResending(false);
      }
    }
  }

  return (
    <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
      <div className="flex items-start">
        <div className="flex-1">
          <h3 className="text-sm font-medium text-yellow-800">
            Email Verification Required
          </h3>
          <p className="text-sm text-yellow-700 mt-1">
            Please verify your email address ({user.email}) to access all features.
          </p>
          <div className="mt-2 flex gap-2">
            <button
              onClick={handleResend}
              disabled={resending}
              className="text-sm underline text-yellow-800 hover:text-yellow-900 disabled:opacity-50"
            >
              {resending ? "Sending..." : "Resend verification email"}
            </button>
          </div>
        </div>
        <button
          onClick={() => setDismissed(true)}
          className="ml-4 text-yellow-600 hover:text-yellow-800"
          aria-label="Dismiss"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

