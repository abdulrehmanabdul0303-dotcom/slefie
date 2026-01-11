"use client";
import { useEffect, useRef } from "react";
import { toast } from "sonner";
import {
  SSE_INITIAL_RETRY_DELAY_MS,
  SSE_MAX_RETRY_DELAY_MS,
  SSE_MAX_ATTEMPTS,
} from "@/lib/config/constants";

export function useMetadataEvents() {
  const esRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const retryDelayRef = useRef(SSE_INITIAL_RETRY_DELAY_MS);
  const maxRetryDelay = SSE_MAX_RETRY_DELAY_MS;
  const attemptCountRef = useRef(0);
  const maxAttempts = SSE_MAX_ATTEMPTS;

  useEffect(() => {
    let mounted = true;

    function connect() {
      if (!mounted) return;
      
      // Stop if we've tried too many times (likely endpoint doesn't exist)
      if (attemptCountRef.current >= maxAttempts) {
        console.warn("SSE endpoint /metadata/events not available - feature disabled");
        return;
      }

      attemptCountRef.current++;
      const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8999";
      const es = new EventSource(`${base}/metadata/events`, { withCredentials: true } as any);
      esRef.current = es;

      es.onopen = () => {
        // Reset retry delay and attempt count on successful connection
        retryDelayRef.current = SSE_INITIAL_RETRY_DELAY_MS;
        attemptCountRef.current = 0; // Reset on successful connection
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      es.onmessage = (ev) => {
        if (!mounted) return;
        try {
          const data = JSON.parse(ev.data);
          toast.success(data.message ?? "Metadata updated");
        } catch {
          toast.success("Metadata updated");
        }
      };

      es.onerror = (error) => {
        if (!mounted) return;
        
        // If we've tried maxAttempts times, stop trying (likely 404)
        if (attemptCountRef.current >= maxAttempts) {
          es.close();
          esRef.current = null;
          console.warn("SSE endpoint /metadata/events not available - feature disabled");
          return;
        }
        
        es.close();
        esRef.current = null;

        // Reconnect with exponential backoff
        reconnectTimeoutRef.current = setTimeout(() => {
          if (mounted && attemptCountRef.current < maxAttempts) {
            retryDelayRef.current = Math.min(retryDelayRef.current * 2, maxRetryDelay);
            connect();
          }
        }, retryDelayRef.current);
      };
    }

    connect();

    return () => {
      mounted = false;
      if (esRef.current) {
        esRef.current.close();
        esRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
  }, []);
}
