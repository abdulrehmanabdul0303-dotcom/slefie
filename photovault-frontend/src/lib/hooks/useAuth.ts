'use client';

import { useState, useEffect, useCallback } from 'react';
import { authStore } from '@/lib/auth/auth-store';
import type { AuthUser } from '@/lib/types/auth';

export interface UseAuthReturn {
  token: string | null;
  user: AuthUser | null;
  isLoading: boolean;
  logout: () => Promise<void>;
}

/**
 * useAuth Hook
 * Provides access to authentication state
 */
export const useAuth = (): UseAuthReturn => {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize auth state from storage
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const storedToken = authStore.getToken();
        setToken(storedToken);
        // TODO: Fetch user data if token exists
      } catch (error) {
        console.error('Failed to initialize auth:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();

    // Listen for token changes from other tabs
    const handleTokenRefresh = () => {
      const newToken = authStore.getToken();
      setToken(newToken);
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('token-refreshed', handleTokenRefresh);
      window.addEventListener('storage', handleTokenRefresh);
    }

    return () => {
      if (typeof window !== 'undefined') {
        window.removeEventListener('token-refreshed', handleTokenRefresh);
        window.removeEventListener('storage', handleTokenRefresh);
      }
    };
  }, []);

  const logout = useCallback(async () => {
    try {
      authStore.clear();
      setToken(null);
      setUser(null);
    } catch (error) {
      console.error('Logout failed:', error);
      throw error;
    }
  }, []);

  return {
    token,
    user,
    isLoading,
    logout,
  };
};
