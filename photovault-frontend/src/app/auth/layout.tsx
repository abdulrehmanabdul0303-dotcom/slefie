"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { authStore } from "@/lib/auth/auth-store";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    try {
      // Check if user is already authenticated
      const token = authStore.getToken();
      if (token) {
        // User is already logged in, redirect to dashboard
        router.push("/dashboard");
      } else {
        setIsLoading(false);
      }
    } catch (error) {
      console.error("Auth check error:", error);
      setIsLoading(false);
    }
  }, [router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black">
        <div className="text-white text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-white mb-4"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-black">
      {children}
    </div>
  );
}
