"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { authStore } from "@/lib/auth/auth-store";
import { useAuth } from "@/lib/auth/auth-provider";
import { toast } from "sonner";
import { PageErrorBoundary } from "@/components/common/PageErrorBoundary";

function GoogleCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { refreshMe } = useAuth();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");

  useEffect(() => {
    async function handleCallback() {
      try {
        const token = searchParams.get("token");
        const csrf = searchParams.get("csrf");
        const error = searchParams.get("error");

        if (error) {
          setStatus("error");
          toast.error(`OAuth error: ${error}`);
          setTimeout(() => router.push("/login"), 2000);
          return;
        }

        if (!token) {
          setStatus("error");
          toast.error("No token received from OAuth provider");
          setTimeout(() => router.push("/login"), 2000);
          return;
        }

        // Store tokens
        authStore.setToken(token);
        if (csrf) {
          authStore.setCsrf(csrf);
        }

        // Refresh user data
        await refreshMe();

        setStatus("success");
        toast.success("Successfully signed in with Google!");
        router.push("/dashboard");
      } catch (e: any) {
        setStatus("error");
        toast.error("Failed to complete Google sign-in");
        setTimeout(() => router.push("/login"), 2000);
      }
    }

    handleCallback();
  }, [searchParams, router, refreshMe]);

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50">
      <div className="w-full max-w-md bg-white border rounded-xl p-6 text-center">
        {status === "loading" && (
          <>
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-black mx-auto mb-4"></div>
            <h2 className="text-xl font-semibold mb-2">Completing sign-in...</h2>
            <p className="text-sm text-gray-600">Please wait while we finish setting up your account.</p>
          </>
        )}
        {status === "success" && (
          <>
            <div className="text-green-500 text-4xl mb-4">✓</div>
            <h2 className="text-xl font-semibold mb-2">Success!</h2>
            <p className="text-sm text-gray-600">Redirecting to dashboard...</p>
          </>
        )}
        {status === "error" && (
          <>
            <div className="text-red-500 text-4xl mb-4">✗</div>
            <h2 className="text-xl font-semibold mb-2">Sign-in failed</h2>
            <p className="text-sm text-gray-600">Redirecting to login page...</p>
          </>
        )}
      </div>
    </div>
  );
}

export default function GoogleCallbackPage() {
  return (
    <PageErrorBoundary pageName="Google OAuth Callback">
      <Suspense fallback={
        <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50">
          <div className="w-full max-w-md bg-white border rounded-xl p-6 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-black mx-auto mb-4"></div>
            <h2 className="text-xl font-semibold mb-2">Loading...</h2>
          </div>
        </div>
      }>
        <GoogleCallbackContent />
      </Suspense>
    </PageErrorBoundary>
  );
}

