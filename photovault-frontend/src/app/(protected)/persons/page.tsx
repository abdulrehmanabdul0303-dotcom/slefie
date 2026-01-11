"use client";

import { useEffect, useState, useRef } from "react";
import { api } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import type { PersonCluster } from "@/lib/types/models";
import { toast } from "sonner";
import { PageErrorBoundary } from "@/components/common/PageErrorBoundary";

function PersonsContent() {
  const [clusters, setClusters] = useState<PersonCluster[]>([]);
  const [loading, setLoading] = useState(true);
  const abortControllerRef = useRef<AbortController | null>(null);
  const actionAbortRef = useRef<AbortController | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      // Cancel any in-flight requests on unmount
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (actionAbortRef.current) {
        actionAbortRef.current.abort();
      }
    };
  }, []);

  async function load() {
    // Cancel any in-flight request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();

    try {
      const r = await api.get(endpoints.personClusters, {
        signal: abortControllerRef.current.signal,
      });
      const data = Array.isArray(r.data) ? r.data : (r.data?.clusters ?? r.data?.data ?? []);
      setClusters(data);
    } catch (e: any) {
      if (e.name === 'AbortError' || e.name === 'CanceledError') {
        return; // Request was cancelled, ignore
      }
      throw e;
    }
  }

  useEffect(() => {
    (async () => {
      try { await load(); }
      catch (e: any) { toast.error(e?.response?.data?.detail ?? "Failed to load people"); }
      finally { setLoading(false); }
    })();

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  async function rename(clusterId: string, current: string) {
    // TODO: Replace prompt with proper modal/form for better UX and accessibility
    const label = prompt("New name:", current);
    if (!label) return;

    if (actionAbortRef.current) {
      actionAbortRef.current.abort();
    }
    actionAbortRef.current = new AbortController();

    try {
      await api.post(`${endpoints.personRename(clusterId)}?label=${encodeURIComponent(label)}`, {}, {
        signal: actionAbortRef.current.signal,
      });
      
      if (!mountedRef.current) return;
      toast.success("Renamed");
      await load();
    } catch (e: any) {
      if (e.name === 'AbortError' || e.name === 'CanceledError') {
        return; // Request was cancelled, ignore
      }
      if (mountedRef.current) {
        toast.error(e?.response?.data?.detail ?? "Rename failed");
      }
    }
  }

  if (loading) return <div>Loading...</div>;

  return (
    <div className="space-y-4">
      <div className="bg-white border rounded-xl p-4">
        <div className="font-semibold">People</div>
        <div className="text-xs text-gray-500">Detected face clusters</div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2 sm:gap-3">
        {clusters.map((c) => (
          <div key={c.id} className="bg-white border rounded-xl p-3 sm:p-4">
            <div className="font-medium truncate text-sm sm:text-base">{c.label}</div>
            <div className="text-xs text-gray-500 mt-1">{c.faces} faces</div>
            <button 
              className="mt-3 w-full border rounded-md px-3 py-2.5 text-sm min-h-[44px]" 
              onClick={() => rename(c.id, c.label)}
            >
              Rename
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function PersonsPage() {
  return (
    <PageErrorBoundary pageName="Persons">
      <PersonsContent />
    </PageErrorBoundary>
  );
}
