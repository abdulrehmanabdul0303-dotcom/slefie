"use client";

import { RedirectIfAuthed } from "@/lib/auth/route-guard";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import { toast } from "sonner";
import { useState } from "react";
import Link from "next/link";
import { PageErrorBoundary } from "@/components/common/PageErrorBoundary";

const schema = z.object({
  email: z.string().email("Please enter a valid email address"),
});

type Form = z.infer<typeof schema>;

function ForgotPasswordContent() {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<Form>({
    resolver: zodResolver(schema),
  });
  const [emailSent, setEmailSent] = useState(false);
  const [submittedEmail, setSubmittedEmail] = useState<string>("");

  async function onSubmit(values: Form) {
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

      // Request password reset
      await api.post(endpoints.passwordResetRequest, { email: values.email });
      
      setEmailSent(true);
      setSubmittedEmail(values.email);
      toast.success("Password reset email sent! Check your inbox.");
    } catch (e: any) {
      // Don't reveal if email exists or not (security best practice)
      // But still show success message to user
      setEmailSent(true);
      setSubmittedEmail(values.email);
      toast.success("If an account exists with this email, a password reset link has been sent.");
    }
  }

  if (emailSent) {
    return (
      <RedirectIfAuthed>
        <div className="min-h-screen flex items-center justify-center p-6 bg-gray-50">
          <div className="w-full max-w-md bg-white border rounded-xl p-6">
            <h1 className="text-xl font-semibold mb-2">Check Your Email</h1>
            <p className="text-sm text-gray-600 mb-4">
              We've sent a password reset link to <strong>{submittedEmail}</strong>
            </p>
            <p className="text-sm text-gray-500 mb-4">
              Please check your inbox and click the link to reset your password. The link will expire in 1 hour.
            </p>
            <div className="space-y-2">
              <Link href="/login" className="block text-center text-sm underline text-gray-600">
                Back to Login
              </Link>
              <button
                onClick={() => {
                  setEmailSent(false);
                  setSubmittedEmail("");
                }}
                className="w-full rounded-md bg-gray-100 text-gray-700 py-2 text-sm hover:bg-gray-200"
              >
                Send Another Email
              </button>
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
            <h1 className="text-lg sm:text-xl font-semibold mb-2">Forgot Password</h1>
          <p className="text-xs sm:text-sm text-gray-500 mb-4">
            Enter your email address and we'll send you a link to reset your password.
          </p>

          <form className="space-y-3 sm:space-y-4" onSubmit={handleSubmit(onSubmit)}>
            <div>
              <label className="text-sm block mb-1">Email</label>
              <input
                type="email"
                className="w-full border rounded-md px-3 py-2.5 text-base sm:text-sm min-h-[44px]"
                placeholder="your@email.com"
                {...register("email")}
                autoComplete="email"
              />
              {errors.email && <p className="text-xs text-red-600 mt-1">{errors.email.message}</p>}
            </div>

            <button
              disabled={isSubmitting}
              className="w-full rounded-md bg-black text-white py-3 text-sm disabled:opacity-50 min-h-[44px]"
            >
              {isSubmitting ? "Sending..." : "Send Reset Link"}
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

export default function ForgotPasswordPage() {
  return (
    <PageErrorBoundary pageName="Forgot Password">
      <ForgotPasswordContent />
    </PageErrorBoundary>
  );
}

