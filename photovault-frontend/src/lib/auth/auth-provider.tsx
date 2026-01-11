"use client";

import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api/client";
import { authStore } from "@/lib/auth/auth-store";
import type { User } from "@/lib/types/models";

type AuthCtx = {
  user: User | null;
  loading: boolean;
  setUser: (u: User | null) => void;
  logout: () => Promise<void>;
  refreshMe: () => Promise<void>;
};

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  async function refreshMe() {
    const token = authStore.getToken();
    if (!token) {
      setUser(null);
      return;
    }
    // verify token then load me
    await api.get("/auth/verify");
    const me = await api.get<User>("/auth/me");
    setUser(me.data);
  }

  async function logout() {
    try {
      await api.post("/auth/logout", {});
    } finally {
      authStore.clear();
      setUser(null);
      if (typeof window !== "undefined") {
        window.location.href = "/auth/login";
      }
    }
  }

  useEffect(() => {
    // Listen for token refresh from other tabs
    const handleTokenRefresh = () => {
      refreshMe();
    };
    window.addEventListener("token-refreshed", handleTokenRefresh);

    (async () => {
      try {
        // Only fetch CSRF if not already present
        if (!authStore.getCsrf()) {
          try {
            const csrfRes = await api.get("/api/auth/csrf/");
            authStore.setCsrf((csrfRes.data?.csrfToken ?? csrfRes.data) as string);
          } catch (e) {
            console.warn("Failed to fetch CSRF on mount:", e);
          }
        }

        await refreshMe();
      } catch {
        authStore.clear();
        setUser(null);
      } finally {
        setLoading(false);
      }
    })();

    return () => {
      window.removeEventListener("token-refreshed", handleTokenRefresh);
    };
  }, []);

  const value = useMemo(() => ({ user, loading, setUser, logout, refreshMe }), [user, loading]);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
