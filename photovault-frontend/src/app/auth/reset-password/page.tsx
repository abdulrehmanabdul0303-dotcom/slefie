"use client";

import { RedirectIfAuthed } from "@/lib/auth/route-guard";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import { toast } from "sonner";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { PageErrorBoundary } from "@/components/common/PageErrorBoundary";

const schema = z.object({
  password: z
    .string()
    .min(8, "Password must be at least 8 characters")
    .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
    .regex(/[a-z]/, "Password must contain at least one lowercase letter")
    .regex(/[0-9]/, "Password must contain at least one number"),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

type Form = z.infer<typeof schema>;

function ResetPasswordContent({
  searchParams,
}: {
  searchParams: Promise<{ token?: string }> | { token?: string };
}) {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<Form>({
    resolver: zodResolver(schema),
  });
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [tokenValid, setTokenValid] = useState<boolean | null>(null);
  const [resetSuccess, setResetSuccess] = useState(false);

  useEffect(() => {
    // Handle async searchParams in Next.js 14
    (async () => {
      const params = await Promise.resolve(searchParams);
      const tokenParam = params?.token;
      if (tokenParam) {
        setToken(tokenParam);
        // Optionally verify token is valid format
        if (tokenParam.length > 20) {
          setTokenValid(true);
        } else {
          setTokenValid(false);
        }
      } else {
        setTokenValid(false);
      }
    })();
  }, [searchParams]);

  async function onSubmit(values: Form) {
    if (!token) {
      toast.error("Invalid reset token");
      return;
    }

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

      // Reset password
      await api.post(endpoints.passwordReset, {
        token,
        new_password: values.password,
      });

      setResetSuccess(true);
      toast.success("Password reset successfully!");
      
      // Redirect to login after 2 seconds
      setTimeout(() => {
        router.push("/login");
      }, 2000);
    } catch (e: any) {
      const errorMsg = e?.response?.data?.detail ?? e?.message ?? "Failed to reset password";
      toast.error(errorMsg);
      
      // If token is invalid/expired, redirect to forgot password
      if (e?.response?.status === 400 || e?.response?.status === 401) {
        setTimeout(() => {
          router.push("/forgot-password");
        }, 3000);
      }
    }
  }

  if (resetSuccess) {
    return (
      <RedirectIfAuthed>
        <div className="min-h-screen flex items-center justify-center p-4 sm:p-6 bg-gray-50">
        <div className="w-full max-w-md bg-white border rounded-xl p-4 sm:p-6">
            <h1 className="text-xl font-semibold mb-2 text-green-600">Password Reset Successful!</h1>
            <p className="text-sm text-gray-600 mb-4">
              Your password has been reset successfully. You can now login with your new password.
            </p>
            <Link href="/login" className="block text-center w-full rounded-md bg-black text-white py-2 text-sm">
              Go to Login
            </Link>
          </div>
        </div>
      </RedirectIfAuthed>
    );
  }

  if (tokenValid === false) {
    return (
      <RedirectIfAuthed>
        <div className="min-h-screen flex items-center justify-center p-4 sm:p-6 bg-gray-50">
        <div className="w-full max-w-md bg-white border rounded-xl p-4 sm:p-6">
            <h1 className="text-xl font-semibold mb-2 text-red-600">Invalid Reset Link</h1>
            <p className="text-sm text-gray-600 mb-4">
              This password reset link is invalid or has expired. Please request a new one.
            </p>
            <Link href="/forgot-password" className="block text-center w-full rounded-md bg-black text-white py-2 text-sm">
              Request New Reset Link
            </Link>
          </div>
        </div>
      </RedirectIfAuthed>
    );
  }

  if (tokenValid === null) {
    return (
      <RedirectIfAuthed>
        <div className="min-h-screen flex items-center justify-center p-4 sm:p-6 bg-gray-50">
        <div className="w-full max-w-md bg-white border rounded-xl p-4 sm:p-6">
            <p className="text-sm text-gray-600">Loading...</p>
          </div>
        </div>
      </RedirectIfAuthed>
    );
  }

  return (
    <RedirectIfAuthed>
        <div className="min-h-screen flex items-center justify-center p-4 sm:p-6 bg-gray-50">
        <div className="w-full max-w-md bg-white border rounded-xl p-4 sm:p-6">
            <h1 className="text-lg sm:text-xl font-semibold mb-2">Reset Password</h1>
          <p className="text-xs sm:text-sm text-gray-500 mb-4">
            Enter your new password below.
          </p>

          <form className="space-y-3 sm:space-y-4" onSubmit={handleSubmit(onSubmit)}>
            <div>
              <label className="text-sm block mb-1">New Password</label>
              <input
                type="password"
                className="w-full border rounded-md px-3 py-2.5 text-base sm:text-sm min-h-[44px]"
                placeholder="Enter new password"
                {...register("password")}
                autoComplete="new-password"
              />
              {errors.password && (
                <p className="text-xs text-red-600 mt-1">{errors.password.message}</p>
              )}
              <p className="text-xs text-gray-500 mt-1">
                Must be at least 8 characters with uppercase, lowercase, and number
              </p>
            </div>

            <div>
              <label className="text-sm block mb-1">Confirm Password</label>
              <input
                type="password"
                className="w-full border rounded-md px-3 py-2.5 text-base sm:text-sm min-h-[44px]"
                placeholder="Confirm new password"
                {...register("confirmPassword")}
                autoComplete="new-password"
              />
              {errors.confirmPassword && (
                <p className="text-xs text-red-600 mt-1">{errors.confirmPassword.message}</p>
              )}
            </div>

            <button
              disabled={isSubmitting}
              className="w-full rounded-md bg-black text-white py-3 text-sm disabled:opacity-50 min-h-[44px]"
            >
              {isSubmitting ? "Resetting..." : "Reset Password"}
            </button>

            <Link href="/login" className="block text-center text-sm underline text-gray-600">
              Back to Login
            </Link>
          </form>
        </div>
      </div>
    </RedirectIfAuthed>
  );
}

export default function ResetPasswordPage({
  searchParams,
}: {
  searchParams: Promise<{ token?: string }> | { token?: string };
}) {
  return (
    <PageErrorBoundary pageName="Reset Password">
      <ResetPasswordContent searchParams={searchParams} />
    </PageErrorBoundary>
  );
}

