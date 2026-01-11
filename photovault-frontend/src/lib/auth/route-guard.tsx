"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/auth-provider";
import { api } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import { toast } from "sonner";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading) return <div className="p-6">Loading...</div>;
  if (!user) return null;
  
  // Check if email is verified (if verification is enabled)
  // Note: email_verified might be undefined for existing users, so we check explicitly
  if (user.email_verified === false) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6 bg-gray-50">
        <div className="w-full max-w-md bg-white border rounded-xl p-6">
          <h1 className="text-xl font-semibold mb-2">Email Verification Required</h1>
          <p className="text-sm text-gray-600 mb-4">
            Please verify your email address before accessing your account.
          </p>
          <p className="text-sm text-gray-500 mb-4">
            We've sent a verification link to <strong>{user.email}</strong>. Please check your inbox and click the link to verify your email.
          </p>
          <div className="space-y-2">
            <button
              onClick={async () => {
                try {
                  // Fetch CSRF token
                  try {
                    const csrfRes = await api.get(endpoints.csrf);
                    const csrfToken = csrfRes.data?.csrfToken ?? csrfRes.data;
                    if (csrfToken) {
                      // CSRF will be handled by interceptor
                    }
                  } catch (csrfError) {
                    console.warn("Failed to fetch CSRF token:", csrfError);
                  }

                  await api.post(endpoints.emailResend, { email: user.email });
                  toast.success("Verification email resent! Check your inbox.");
                } catch (e: any) {
                  toast.error("Failed to resend email. Please try again later.");
                }
              }}
              className="w-full rounded-md bg-black text-white py-2 text-sm hover:bg-gray-800"
            >
              Resend Verification Email
            </button>
            <button
              onClick={() => {
                router.push("/login");
              }}
              className="w-full rounded-md bg-gray-100 text-gray-700 py-2 text-sm hover:bg-gray-200"
            >
              Back to Login
            </button>
          </div>
        </div>
      </div>
    );
  }
  
  return <>{children}</>;
}

export function RedirectIfAuthed({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && user && (pathname === "/login" || pathname === "/signup")) {
      router.replace("/dashboard");
    }
  }, [loading, user, router, pathname]);

  if (loading) return <div className="p-6">Loading...</div>;
  if (user) return null;
  return <>{children}</>;
}

export function RequireAdmin({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && (!user || !user.is_admin)) router.replace("/dashboard");
  }, [loading, user, router]);

  if (loading) return <div className="p-6">Loading...</div>;
  if (!user?.is_admin) return null;
  return <>{children}</>;
}
