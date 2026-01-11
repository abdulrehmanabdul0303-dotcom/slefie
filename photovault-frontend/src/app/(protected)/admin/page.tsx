"use client";

import { useEffect, useState, useRef } from "react";
import { RequireAdmin } from "@/lib/auth/route-guard";
import { api } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import { toast } from "sonner";
import { PageErrorBoundary } from "@/components/common/PageErrorBoundary";

export default function AdminPage() {
  return (
    <RequireAdmin>
      <PageErrorBoundary pageName="Admin">
        <AdminInner />
      </PageErrorBoundary>
    </RequireAdmin>
  );
}

function AdminInner() {
  const [personAlbums, setPersonAlbums] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [shareInfo, setShareInfo] = useState<any>(null);
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
      const r = await api.get(endpoints.adminPersonAlbums, {
        signal: abortControllerRef.current.signal,
      });
      setPersonAlbums(r.data?.albums ?? r.data ?? []);
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
      catch (e: any) { toast.error(e?.response?.data?.detail ?? "Admin load failed"); }
      finally { setLoading(false); }
    })();

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  async function createShare(albumId: string) {
    if (actionAbortRef.current) {
      actionAbortRef.current.abort();
    }
    actionAbortRef.current = new AbortController();

    try {
      const r = await api.post(`${endpoints.adminShareCreateForPersonAlbum(albumId)}?hours=72&max_views=100`, {}, {
        signal: actionAbortRef.current.signal,
      });
      
      if (!mountedRef.current) return;
      setShareInfo(r.data);
      toast.success("Share created");
    } catch (e: any) {
      if (e.name === 'AbortError' || e.name === 'CanceledError') {
        return; // Request was cancelled, ignore
      }
      if (mountedRef.current) {
        toast.error(e?.response?.data?.detail ?? "Share create failed");
      }
    }
  }

  async function revoke(shareId: string) {
    if (actionAbortRef.current) {
      actionAbortRef.current.abort();
    }
    actionAbortRef.current = new AbortController();

    try {
      await api.post(endpoints.adminRevokeShare(shareId), {}, {
        signal: actionAbortRef.current.signal,
      });
      
      if (!mountedRef.current) return;
      toast.success("Revoked");
    } catch (e: any) {
      if (e.name === 'AbortError' || e.name === 'CanceledError') {
        return; // Request was cancelled, ignore
      }
      if (mountedRef.current) {
        toast.error(e?.response?.data?.detail ?? "Revoke failed");
      }
    }
  }

  async function stats(shareId: string) {
    if (actionAbortRef.current) {
      actionAbortRef.current.abort();
    }
    actionAbortRef.current = new AbortController();

    try {
      const r = await api.get(endpoints.adminShareStats(shareId), {
        signal: actionAbortRef.current.signal,
      });
      
      if (!mountedRef.current) return;
      setShareInfo(r.data);
      toast.success("Stats loaded");
    } catch (e: any) {
      if (e.name === 'AbortError' || e.name === 'CanceledError') {
        return; // Request was cancelled, ignore
      }
      if (mountedRef.current) {
        toast.error(e?.response?.data?.detail ?? "Stats failed");
      }
    }
  }

  if (loading) return <div>Loading...</div>;

  return (
    <div className="space-y-4">
      <div className="bg-white border rounded-xl p-4">
        <div className="text-xl font-semibold">Admin</div>
        <div className="text-xs text-gray-500">Manage person albums & shares</div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4">
        <div className="bg-white border rounded-xl p-3 sm:p-4">
          <div className="font-semibold mb-2 text-sm sm:text-base">Person albums</div>
          <div className="space-y-2">
            {personAlbums.map((a) => (
              <div key={a.id} className="border rounded-md p-2 sm:p-3 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <div className="font-medium truncate text-xs sm:text-sm">{a.name ?? a.label ?? "Person Album"}</div>
                  <div className="text-xs text-gray-500 truncate">id: {a.id}</div>
                </div>
                <div className="flex gap-2 w-full sm:w-auto">
                  <button 
                    className="flex-1 sm:flex-none border rounded-md px-3 py-2 text-sm min-h-[44px]" 
                    onClick={() => createShare(a.id)}
                  >
                    Share
                  </button>
                  <a
                    className="flex-1 sm:flex-none border rounded-md px-3 py-2 text-sm text-center min-h-[44px] flex items-center justify-center"
                    href={`${process.env.NEXT_PUBLIC_API_BASE_URL}${endpoints.adminShareQrForPersonAlbum(a.id)}?hours=72`}
                    target="_blank"
                  >
                    QR
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white border rounded-xl p-4">
          <div className="font-semibold mb-2">Share actions</div>

          <div className="grid grid-cols-1 gap-2">
            <div className="text-xs text-gray-500">Paste a share_id below to revoke/stats</div>
            <ShareTools onRevoke={revoke} onStats={stats} />
          </div>

          <div className="mt-3">
            <div className="text-xs text-gray-500 mb-1">Response</div>
            <pre className="text-xs bg-gray-50 border rounded-md p-3 overflow-auto">
              {JSON.stringify(shareInfo, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}

function ShareTools({ onRevoke, onStats }: { onRevoke: (id: string) => void; onStats: (id: string) => void }) {
  const [id, setId] = useState("");
  return (
    <div className="flex gap-2">
      <input className="border rounded-md px-3 py-2 w-full" placeholder="share_id" value={id} onChange={(e) => setId(e.target.value)} />
      <button className="border rounded-md px-3 py-2 text-sm" onClick={() => onStats(id)}>Stats</button>
      <button className="border rounded-md px-3 py-2 text-sm text-red-600" onClick={() => onRevoke(id)}>Revoke</button>
    </div>
  );
}
