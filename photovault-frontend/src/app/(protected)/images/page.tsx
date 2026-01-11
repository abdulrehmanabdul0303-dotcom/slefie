"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { api } from "@/lib/api/client";
import type { ImageItem } from "@/lib/types/models";
import { toast } from "sonner";
import UploadDropzone from "@/components/images/UploadDropzone";
import { BulkOperationsBar } from "@/components/images/BulkOperationsBar";
import { endpoints } from "@/lib/api/endpoints";
import { CheckSquare, Square } from "lucide-react";
import { PageErrorBoundary } from "@/components/common/PageErrorBoundary";
import { DEFAULT_IMAGE_PAGE_SIZE } from "@/lib/config/constants";

function ImagesContent() {
  const [items, setItems] = useState<ImageItem[]>([]);
  const [skip, setSkip] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const abortControllerRef = useRef<AbortController | null>(null);
  const actionAbortRef = useRef<AbortController | null>(null);
  const loadedPagesRef = useRef<Set<number>>(new Set());
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

  const load = useCallback(async (reset = false) => {
    // Cancel any in-flight request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const nextSkip = reset ? 0 : skip;
    const page = Math.floor(nextSkip / DEFAULT_IMAGE_PAGE_SIZE);

    // Prevent duplicate page loads
    if (!reset && loadedPagesRef.current.has(page)) {
      return;
    }

    if (reset) {
      setLoading(true);
      loadedPagesRef.current.clear();
    } else {
      setLoadingMore(true);
    }

    abortControllerRef.current = new AbortController();

    try {
      const res = await api.get<{results: ImageItem[], count: number, next: string | null, previous: string | null}>(`${endpoints.images}?skip=${nextSkip}&limit=${DEFAULT_IMAGE_PAGE_SIZE}`, {
        signal: abortControllerRef.current.signal,
      });
      const data = res.data?.results ?? [];
      
      if (data.length < DEFAULT_IMAGE_PAGE_SIZE) {
        setHasMore(false);
      }

      setItems((prev) => {
        if (reset) {
          return data;
        }
        // Prevent duplicates
        const existingIds = new Set(prev.map(i => i.id));
        const newItems = data.filter(i => !existingIds.has(i.id));
        return [...prev, ...newItems];
      });
      
      loadedPagesRef.current.add(page);
      setSkip(nextSkip + DEFAULT_IMAGE_PAGE_SIZE);
    } catch (e: any) {
      if (e.name === 'AbortError' || e.name === 'CanceledError') {
        return; // Request was cancelled, ignore
      }
      toast.error(e?.response?.data?.detail ?? "Failed to load images");
    } finally {
      setLoading(false);
      setLoadingMore(false);
      abortControllerRef.current = null;
    }
  }, [skip]);

  useEffect(() => {
    load(true);
    
    return () => {
      // Cleanup: cancel any in-flight requests
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  async function remove(id: string) {
    if (!confirm("Delete this image?")) return;

    if (actionAbortRef.current) {
      actionAbortRef.current.abort();
    }
    actionAbortRef.current = new AbortController();
    
    // Optimistic update
    const previousItems = items;
    if (mountedRef.current) {
      setItems((p) => p.filter((x) => x.id !== id));
      setSelectedIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
    
    try {
      await api.delete(endpoints.imageDelete(id), {
        signal: actionAbortRef.current.signal,
      });
      
      if (!mountedRef.current) return;
      toast.success("Deleted");
    } catch (e: any) {
      if (e.name === 'AbortError' || e.name === 'CanceledError') {
        return; // Request was cancelled, ignore
      }
      // Rollback on error
      if (mountedRef.current) {
        setItems(previousItems);
        toast.error(e?.response?.data?.detail ?? "Delete failed");
      }
    }
  }

  function toggleSelect(id: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  function handleBulkDeleteComplete() {
    // Reload images after bulk delete
    load(true);
    setSelectedIds(new Set());
  }

  if (loading) return <div className="p-6">Loading...</div>;
  
  if (items.length === 0) {
    return (
      <div className="space-y-4">
        <UploadDropzone onDone={() => load(true)} />
        <div className="bg-white border rounded-xl p-12 text-center">
          <p className="text-gray-500">No images yet. Upload your first photo!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <UploadDropzone onDone={() => load(true)} />

      <BulkOperationsBar
        selectedIds={selectedIds}
        onSelectionChange={setSelectedIds}
        onDeleteComplete={handleBulkDeleteComplete}
        totalCount={items.length}
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2 sm:gap-3">
        {items.map((img) => {
          const isSelected = selectedIds.has(img.id);
          return (
            <div
              key={img.id}
              className={`bg-white border rounded-xl overflow-hidden relative ${
                isSelected ? "ring-2 ring-blue-500 border-blue-500" : ""
              }`}
            >
              {/* Selection checkbox */}
              <button
                onClick={() => toggleSelect(img.id)}
                className="absolute top-2 left-2 z-10 p-1.5 bg-white/90 rounded shadow-sm hover:bg-white transition-colors"
                title={isSelected ? "Deselect" : "Select"}
                aria-label={isSelected ? `Deselect ${img.original_filename ?? "image"}` : `Select ${img.original_filename ?? "image"}`}
              >
                {isSelected ? (
                  <CheckSquare className="h-5 w-5 text-blue-600" />
                ) : (
                  <Square className="h-5 w-5 text-gray-400" />
                )}
              </button>

              <img
                src={`${process.env.NEXT_PUBLIC_API_BASE_URL}${endpoints.imageThumb(img.id)}`}
                alt={img.original_filename ?? "image"}
                className="w-full h-40 sm:h-48 object-cover"
                loading="lazy"
              />
              <div className="p-2 sm:p-3 text-sm">
                <div className="font-medium truncate text-xs sm:text-sm">{img.original_filename ?? "Untitled"}</div>
                <div className="text-xs text-gray-500 truncate">{img.location_text ?? ""}</div>
                <div className="mt-2 flex gap-2">
                  <a
                    className="text-xs underline min-h-[44px] flex items-center"
                    href={`${process.env.NEXT_PUBLIC_API_BASE_URL}${endpoints.imageView(img.id)}`}
                    target="_blank"
                  >
                    View
                  </a>
                  <button
                    className="text-xs underline text-red-600 min-h-[44px] flex items-center"
                    onClick={() => remove(img.id)}
                    aria-label={`Delete ${img.original_filename ?? "image"}`}
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {hasMore && (
        <button 
          className="border rounded-md px-3 py-2 text-sm disabled:opacity-50" 
          onClick={() => load(false)}
          disabled={loadingMore}
        >
          {loadingMore ? "Loading..." : "Load more"}
        </button>
      )}
    </div>
  );
}

export default function ImagesPage() {
  return (
    <PageErrorBoundary pageName="Images">
      <ImagesContent />
    </PageErrorBoundary>
  );
}
