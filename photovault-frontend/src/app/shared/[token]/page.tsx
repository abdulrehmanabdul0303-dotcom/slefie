"use client";

import { useEffect, useState, useRef } from "react";
import { motion } from "framer-motion";
import axios from "axios";
import { endpoints } from "@/lib/api/endpoints";
import { PageErrorBoundary } from "@/components/common/PageErrorBoundary";
import { PUBLIC_SHARE_CACHE_TTL_MS } from "@/lib/config/constants";

// Use unauthenticated axios instance for public shares
const publicApi = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8999",
  timeout: 10000,
});

// Request deduplication for public shares
const shareRequestCache = new Map<string, Promise<any>>();

function PublicShareContent({ params }: { params: Promise<{ token: string }> | { token: string } }) {
  const [data, setData] = useState<any>(null);
  const [token, setToken] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    (async () => {
      const resolvedParams = await Promise.resolve(params);
      setToken(resolvedParams.token);
    })();
  }, [params]);

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;

    // Cancel any in-flight request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();
    setLoading(true);
    setError(null);

    // Request deduplication
    const cacheKey = `share_${token}`;
    if (shareRequestCache.has(cacheKey)) {
      shareRequestCache.get(cacheKey)!
        .then(setData)
        .catch((e: any) => setError(e?.response?.data?.detail ?? "Failed to load share"))
        .finally(() => setLoading(false));
      return;
    }

    const requestPromise = (async () => {
      try {
        const r = await publicApi.get(endpoints.publicShare(token), {
          signal: abortControllerRef.current!.signal,
        });
        return r.data;
      } catch (e: any) {
        if (e.name === 'AbortError' || e.name === 'CanceledError') {
          return null;
        }
        throw e;
      } finally {
        setTimeout(() => shareRequestCache.delete(cacheKey), PUBLIC_SHARE_CACHE_TTL_MS);
      }
    })();

    shareRequestCache.set(cacheKey, requestPromise);
    requestPromise
      .then(setData)
      .catch((e: any) => setError(e?.response?.data?.detail ?? "Invalid or expired link"))
      .finally(() => setLoading(false));

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [token]);

  if (loading) return <div className="p-6">Loading...</div>;
  if (error) return (
    <div className="p-6 flex flex-col items-center justify-center min-h-[50vh] text-center">
      <h2 className="text-xl font-semibold text-red-600 mb-2">Unavailable</h2>
      <p className="text-gray-600">{error}</p>
    </div>
  );
  if (!data) return <div className="p-6">Link not found.</div>;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <motion.div
        className="max-w-5xl mx-auto space-y-4"
        initial="hidden"
        animate="show"
        variants={{
          hidden: { opacity: 0 },
          show: { opacity: 1, transition: { staggerChildren: 0.1 } }
        }}
      >
        <motion.div
          className="bg-white border rounded-xl p-3 sm:p-4"
          variants={{ hidden: { opacity: 0, y: -20 }, show: { opacity: 1, y: 0 } }}
        >
          <h1 className="text-lg sm:text-xl font-semibold">{data.album?.name ?? "Shared Album"}</h1>
          <p className="text-xs sm:text-sm text-gray-500">{data.album?.description ?? ""}</p>
        </motion.div>

        <motion.div
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2 sm:gap-3"
          variants={{
            hidden: { opacity: 0 },
            show: { opacity: 1, transition: { staggerChildren: 0.05 } }
          }}
        >
          {(data.images ?? []).map((img: any) => (
            <motion.a
              key={img.id}
              href={`${process.env.NEXT_PUBLIC_API_BASE_URL}${endpoints.publicShareImage(token, img.id)}`}
              target="_blank"
              className="block"
              variants={{ hidden: { opacity: 0, scale: 0.9 }, show: { opacity: 1, scale: 1 } }}
              whileHover={{ scale: 1.03 }}
              transition={{ type: "spring", stiffness: 300, damping: 20 }}
            >
              <img
                src={`${process.env.NEXT_PUBLIC_API_BASE_URL}${endpoints.publicShareImage(token, img.id)}`}
                className="w-full h-40 sm:h-48 object-cover rounded-xl border bg-white"
                alt="shared"
              />
            </motion.a>
          ))}
        </motion.div>
      </motion.div>
    </div>
  );
}

export default function PublicShare({ params }: { params: Promise<{ token: string }> | { token: string } }) {
  return (
    <PageErrorBoundary pageName="Shared Album">
      <PublicShareContent params={params} />
    </PageErrorBoundary>
  );
}
