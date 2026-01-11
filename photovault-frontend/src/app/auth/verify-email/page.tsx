"use client";

import { RedirectIfAuthed } from "@/lib/auth/route-guard";
import { useState, useEffect } from "react";
import { api } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { PageErrorBoundary } from "@/components/common/PageErrorBoundary";

function VerifyEmailContent({
  searchParams,
}: {
  searchParams: Promise<{ token?: string }> | { token?: string };
}) {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [verified, setVerified] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Handle async searchParams in Next.js 14
    (async () => {
      const params = await Promise.resolve(searchParams);
      const tokenParam = params?.token;
      if (tokenParam) {
        setToken(tokenParam);
        // Auto-verify if token is present
        verifyEmail(tokenParam);
      } else {
        setError("No verification token provided");
      }
    })();
  }, [searchParams]);

  async function verifyEmail(tokenToVerify: string) {
    setVerifying(true);
    setError(null);

    try {
      // Fetch CSRF token before making the request
      try {
        const csrfRes = await api.get(endpoints.csrf);
        const csrfToken = csrfRes.data?.csrfToken ?? csrfRes.data;
        if (csrfToken) {
          // CSRF will be handled by interceptor
        }
      } catch (csrfError) {
        console.warn("Failed to fetch CSRF token:", csrfError);
      }

      // Verify email
      await api.post(endpoints.emailVerify, { token: tokenToVerify });

      setVerified(true);
      toast.success("Email verified successfully!");
      
      // Redirect to login after 2 seconds
      setTimeout(() => {
        router.push("/login");
      }, 2000);
    } catch (e: any) {
      const errorMsg = e?.response?.data?.detail ?? e?.message ?? "Failed to verify email";
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setVerifying(false);
    }
  }

  if (verified) {
    return (
      <RedirectIfAuthed>
        <div className="min-h-screen flex items-center justify-center p-4 sm:p-6 bg-gray-50">
        <div className="w-full max-w-md bg-white border rounded-xl p-4 sm:p-6">
            <h1 className="text-xl font-semibold mb-2 text-green-600">Email Verified!</h1>
            <p className="text-sm text-gray-600 mb-4">
              Your email has been verified successfully. You can now login to your account.
            </p>
            <Link href="/login" className="block text-center w-full rounded-md bg-black text-white py-2 text-sm">
              Go to Login
            </Link>
          </div>
        </div>
      </RedirectIfAuthed>
    );
  }

  if (error && !verifying) {
    return (
      <RedirectIfAuthed>
        <div className="min-h-screen flex items-center justify-center p-4 sm:p-6 bg-gray-50">
        <div className="w-full max-w-md bg-white border rounded-xl p-4 sm:p-6">
            <h1 className="text-xl font-semibold mb-2 text-red-600">Verification Failed</h1>
            <p className="text-sm text-gray-600 mb-4">{error}</p>
            <p className="text-sm text-gray-500 mb-4">
              The verification link may be invalid or expired. Please request a new verification email.
            </p>
            <div className="space-y-2">
              <Link href="/forgot-password" className="block text-center w-full rounded-md bg-black text-white py-2 text-sm">
                Request New Verification Email
              </Link>
              <Link href="/login" className="block text-center text-sm underline text-gray-600">
                Back to Login
              </Link>
            </div>
          </div>
        </div>
      </RedirectIfAuthed>
    );
  }

  return (
    <RedirectIfAuthed>
        <div className="min-h-screen flex items-center justify-center p-4 sm:p-6 bg-gray-50">
        <div className="w-full max-w-md bg-white border rounded-xl p-4 sm:p-6">
          <h1 className="text-xl font-semibold mb-2">Verifying Email</h1>
          <p className="text-sm text-gray-600 mb-4">
            Please wait while we verify your email address...
          </p>
          <div className="flex justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black"></div>
          </div>
        </div>
      </div>
    </RedirectIfAuthed>
  );
}

export default function VerifyEmailPage({
  searchParams,
}: {
  searchParams: Promise<{ token?: string }> | { token?: string };
}) {
  return (
    <PageErrorBoundary pageName="Verify Email">
      <VerifyEmailContent searchParams={searchParams} />
    </PageErrorBoundary>
  );
}

