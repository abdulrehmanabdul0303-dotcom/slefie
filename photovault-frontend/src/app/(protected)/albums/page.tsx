"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import type { Album } from "@/lib/types/models";
import { toast } from "sonner";
import { PageErrorBoundary } from "@/components/common/PageErrorBoundary";

function AlbumsContent() {
  const [albums, setAlbums] = useState<Album[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
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
      const r = await api.get(endpoints.albums, {
        signal: abortControllerRef.current.signal,
      });
      // supports either array or {albums:[]}
      const data = Array.isArray(r.data) ? r.data : (r.data?.albums ?? []);
      setAlbums(data);
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
      catch (e: any) { toast.error(e?.response?.data?.detail ?? "Failed to load albums"); }
      finally { setLoading(false); }
    })();

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  async function createAlbum() {
    // TODO: Replace prompt with proper modal/form for better UX and accessibility
    const name = prompt("Album name?");
    if (!name) return;
    const description = prompt("Description (optional)?") || null;

    if (actionAbortRef.current) {
      actionAbortRef.current.abort();
    }
    actionAbortRef.current = new AbortController();

    try {
      const r = await api.post(endpoints.albumCreateManual, { name, description, image_ids: [] }, {
        signal: actionAbortRef.current.signal,
      });
      
      if (!mountedRef.current) return;
      toast.success("Album created");
      const created = r.data?.id ? r.data : r.data?.album;
      if (created?.id) {
        router.push(`/albums/${created.id}`);
      } else {
        await load();
      }
    } catch (e: any) {
      if (e.name === 'AbortError' || e.name === 'CanceledError') {
        return; // Request was cancelled, ignore
      }
      if (mountedRef.current) {
        toast.error(e?.response?.data?.detail ?? "Create failed");
      }
    }
  }

  async function autoGenerate() {
    if (actionAbortRef.current) {
      actionAbortRef.current.abort();
    }
    actionAbortRef.current = new AbortController();

    try {
      await api.post(endpoints.albumAutoGenerate, {}, {
        signal: actionAbortRef.current.signal,
      });
      
      if (!mountedRef.current) return;
      toast.success("Auto-generate done");
      await load();
    } catch (e: any) {
      if (e.name === 'AbortError' || e.name === 'CanceledError') {
        return; // Request was cancelled, ignore
      }
      if (mountedRef.current) {
        toast.error(e?.response?.data?.detail ?? "Auto-generate failed");
      }
    }
  }

  async function autoCategorize() {
    if (actionAbortRef.current) {
      actionAbortRef.current.abort();
    }
    actionAbortRef.current = new AbortController();

    try {
      await api.post(endpoints.albumAutoCategorize, {}, {
        signal: actionAbortRef.current.signal,
      });
      
      if (!mountedRef.current) return;
      toast.success("Auto-categorize done");
      await load();
    } catch (e: any) {
      if (e.name === 'AbortError' || e.name === 'CanceledError') {
        return; // Request was cancelled, ignore
      }
      if (mountedRef.current) {
        toast.error(e?.response?.data?.detail ?? "Auto-categorize failed");
      }
    }
  }

  if (loading) return <div>Loading...</div>;

  return (
    <div className="space-y-4">
      <div className="bg-white border rounded-xl p-4 flex flex-wrap gap-2 items-center justify-between">
        <div>
          <div className="font-semibold">Albums</div>
          <div className="text-xs text-gray-500">Manual + AI albums</div>
        </div>

        <div className="flex flex-wrap gap-2">
          <button className="border rounded-md px-3 py-2.5 text-sm min-h-[44px] flex-1 sm:flex-none" onClick={createAlbum}>Create Album</button>
          <button className="border rounded-md px-3 py-2.5 text-sm min-h-[44px] flex-1 sm:flex-none" onClick={autoGenerate}>Auto-Generate</button>
          <button className="border rounded-md px-3 py-2.5 text-sm min-h-[44px] flex-1 sm:flex-none" onClick={autoCategorize}>AI Categorize</button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2 sm:gap-3">
        {albums.map((a) => (
          <a 
            key={a.id} 
            href={`/albums/${a.id}`} 
            className="bg-white border rounded-xl overflow-hidden hover:shadow-sm transition block"
          >
            <div className="h-36 sm:h-44 bg-gray-100">
              {a.cover_image_id ? (
                <img
                  src={`${process.env.NEXT_PUBLIC_API_BASE_URL}${endpoints.imageThumb(a.cover_image_id)}`}
                  className="w-full h-36 sm:h-44 object-cover"
                  alt={a.name}
                />
              ) : (
                <div className="w-full h-36 sm:h-44 flex items-center justify-center text-gray-400 text-xs sm:text-sm">No cover</div>
              )}
            </div>
            <div className="p-2 sm:p-3 text-xs sm:text-sm">
              <div className="font-medium truncate">{a.name}</div>
              <div className="text-xs text-gray-500 truncate">{a.description ?? ""}</div>
              <div className="mt-2 flex items-center justify-between text-xs">
                <span className="px-2 py-1 rounded-md bg-gray-100 truncate">{a.album_type ?? (a.is_auto_generated ? "Auto" : "Manual")}</span>
                <span className="text-gray-500 ml-2">{a.image_count ?? 0} imgs</span>
              </div>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}

export default function AlbumsPage() {
  return (
    <PageErrorBoundary pageName="Albums">
      <AlbumsContent />
    </PageErrorBoundary>
  );
}
