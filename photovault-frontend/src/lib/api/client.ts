import axios, { AxiosError, AxiosRequestConfig } from "axios";
import { authStore } from "@/lib/auth/auth-store";
import {
  API_TIMEOUT_MS,
  TOKEN_REFRESH_TIMEOUT_MS,
  REQUEST_CACHE_TTL_MS,
  MAX_RETRY_ATTEMPTS,
  RETRY_DELAY_MS,
} from "@/lib/config/constants";

const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8999";

export const api = axios.create({
  baseURL,
  withCredentials: true, // supports httpOnly cookie mode too
  timeout: API_TIMEOUT_MS,
});

// Request deduplication cache
const requestCache = new Map<string, Promise<any>>();
const CACHE_TTL = REQUEST_CACHE_TTL_MS;

function getCacheKey(config: AxiosRequestConfig): string {
  return `${config.method?.toUpperCase()}_${config.url}_${JSON.stringify(config.params || {})}`;
}

// Attach auth token
api.interceptors.request.use(async (config) => {
  const token = authStore.getToken();
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Refresh on 401 once - improved multi-tab safety
let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;
let queue: Array<(token: string | null) => void> = [];

function flushQueue(token: string | null) {
  queue.forEach((fn) => fn(token));
  queue = [];
}

async function retryRequest(
  requestFn: () => Promise<any>,
  retries = MAX_RETRY_ATTEMPTS,
  delay = RETRY_DELAY_MS
): Promise<any> {
  try {
    return await requestFn();
  } catch (error: any) {
    // Don't retry on 4xx errors (client errors)
    if (error.response?.status >= 400 && error.response?.status < 500) {
      throw error;
    }

    // Don't retry if no retries left
    if (retries === 0) {
      throw error;
    }

    // Exponential backoff
    await new Promise(resolve => setTimeout(resolve, delay));
    return retryRequest(requestFn, retries - 1, delay * 2);
  }
}

api.interceptors.response.use(
  (r) => r,
  async (err: AxiosError) => {
    const status = err.response?.status;
    const original = err.config as any;

    if (status === 401 && !original?._retry) {
      original._retry = true;

      // If already refreshing, wait for that promise
      if (isRefreshing && refreshPromise) {
        return refreshPromise.then((newToken) => {
          if (!newToken) return Promise.reject(err);
          original.headers.Authorization = `Bearer ${newToken}`;
          return api(original);
        }).catch(() => {
          return Promise.reject(err);
        });
      }

      // If not refreshing, start refresh
      if (!isRefreshing) {
        isRefreshing = true;
        refreshPromise = (async () => {
          try {
            const token = authStore.getToken();
            const refreshRes = await axios.post(
              `${baseURL}/api/auth/refresh/`,
              {},
              {
                withCredentials: true,
                headers: token ? { Authorization: `Bearer ${token}` } : {},
                timeout: TOKEN_REFRESH_TIMEOUT_MS,
              }
            );

            // backend returns access_token as primary field
            const newToken = (refreshRes.data?.access_token ?? refreshRes.data?.token ?? null) as string | null;
            if (newToken) {
              authStore.setToken(newToken);
              // Broadcast token update to other tabs
              if (typeof window !== "undefined") {
                window.localStorage.setItem("photovault_token_updated", Date.now().toString());
              }
            }

            flushQueue(newToken);
            return newToken;
          } catch (e) {
            authStore.clear();
            flushQueue(null);
            if (typeof window !== "undefined") window.location.href = "/login";
            return null;
          } finally {
            isRefreshing = false;
            // Clear promise after a short delay to allow reuse
            setTimeout(() => {
              refreshPromise = null;
            }, 1000);
          }
        })();
      }

      // Wait for refresh and retry original request
      try {
        const newToken = await refreshPromise;
        if (!newToken) return Promise.reject(err);
        original.headers.Authorization = `Bearer ${newToken}`;
        return api(original);
      } catch (e) {
        return Promise.reject(err);
      }
    }

    // Retry on network errors or 5xx errors (but not on 500 if it's a share/create endpoint - likely backend issue)
    const isShareCreate = original?.url?.includes('/api/link/create');

    if (!err.response || (err.response.status >= 500 && err.response.status < 600)) {
      // Don't retry share creation on 500 - likely a backend data issue, not transient
      if (isShareCreate && err.response?.status === 500) {
        return Promise.reject(err);
      }

      if (original && !original._retryCount) {
        original._retryCount = 1;
        return retryRequest(() => api(original));
      }
    }

    return Promise.reject(err);
  }
);
