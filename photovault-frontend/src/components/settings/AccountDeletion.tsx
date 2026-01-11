"use client";

import { useState, useRef, useEffect } from "react";
import { api } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import { useAuth } from "@/lib/auth/auth-provider";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { Trash2, AlertTriangle } from "lucide-react";

export function AccountDeletion() {
  const [showConfirm, setShowConfirm] = useState(false);
  const [password, setPassword] = useState("");
  const [confirmText, setConfirmText] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const { user, logout } = useAuth();
  const router = useRouter();
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

  const CONFIRM_TEXT = "DELETE MY ACCOUNT";

  async function handleDelete() {
    if (confirmText !== CONFIRM_TEXT) {
      toast.error(`Please type "${CONFIRM_TEXT}" to confirm`);
      return;
    }

    if (!password) {
      toast.error("Please enter your password");
      return;
    }

    // Cancel any previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();

    if (!mountedRef.current) return;
    setIsDeleting(true);

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

      // Delete account
      await api.post(
        endpoints.accountDelete,
        { password },
        {
          headers: {
            "Content-Type": "application/json",
          },
          signal: abortControllerRef.current.signal,
        }
      );

      if (!mountedRef.current) return;
      toast.success("Account deleted successfully");

      // Logout and redirect
      await logout();
      router.push("/login");
    } catch (e: any) {
      if (e.name === 'AbortError' || e.name === 'CanceledError') {
        return; // Request was cancelled, ignore
      }
      if (mountedRef.current) {
        const errorMsg = e?.response?.data?.detail ?? e?.message ?? "Failed to delete account";
        toast.error(errorMsg);
        setIsDeleting(false);
      }
    }
  }

  if (!showConfirm) {
    return (
      <div className="bg-white border border-red-200 rounded-xl p-6">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-red-50 rounded-lg">
            <Trash2 className="h-5 w-5 text-red-600" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-red-900 mb-1">Delete Account</h3>
            <p className="text-sm text-gray-600 mb-4">
              Once you delete your account, there is no going back. All your photos, albums, and data will be permanently deleted.
            </p>
            <button
              onClick={() => setShowConfirm(true)}
              className="px-4 py-2 bg-red-600 text-white rounded-md text-sm hover:bg-red-700 transition-colors"
            >
              Delete My Account
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border-2 border-red-300 rounded-xl p-6 space-y-4">
      <div className="flex items-start gap-3">
        <div className="p-2 bg-red-50 rounded-lg">
          <AlertTriangle className="h-5 w-5 text-red-600" />
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-red-900 mb-2">Are you absolutely sure?</h3>
          <div className="space-y-4">
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <p className="text-sm text-red-900 font-medium mb-2">This action cannot be undone.</p>
              <p className="text-xs text-red-700">
                This will permanently delete your account and remove all of your data from our servers. This includes:
              </p>
              <ul className="text-xs text-red-700 mt-2 ml-4 list-disc space-y-1">
                <li>All your photos and images</li>
                <li>All your albums</li>
                <li>All your face recognition data</li>
                <li>All your sharing links</li>
                <li>Your account settings and preferences</li>
              </ul>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">
                Enter your password to confirm
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Your password"
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
                disabled={isDeleting}
              />
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">
                Type <span className="font-mono font-bold">{CONFIRM_TEXT}</span> to confirm
              </label>
              <input
                type="text"
                value={confirmText}
                onChange={(e) => setConfirmText(e.target.value)}
                placeholder={CONFIRM_TEXT}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-red-500"
                disabled={isDeleting}
              />
            </div>

            <div className="flex gap-2 pt-2">
              <button
                onClick={() => {
                  setShowConfirm(false);
                  setPassword("");
                  setConfirmText("");
                }}
                disabled={isDeleting}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-sm text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={isDeleting || password === "" || confirmText !== CONFIRM_TEXT}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-md text-sm hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isDeleting ? "Deleting..." : "Yes, Delete My Account"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

