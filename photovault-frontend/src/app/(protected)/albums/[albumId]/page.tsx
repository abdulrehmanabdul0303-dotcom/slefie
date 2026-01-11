"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import type { Album, ImageItem } from "@/lib/types/models";
import { toast } from "sonner";
import ShareModal from "@/components/albums/ShareModal";
import { PageErrorBoundary } from "@/components/common/PageErrorBoundary";
import { IMAGE_PICKER_PAGE_SIZE } from "@/lib/config/constants";

function AlbumDetailContent({ params }: { params: Promise<{ albumId: string }> | { albumId: string } }) {
  const [albumId, setAlbumId] = useState<string>("");
  const router = useRouter();
  
  useEffect(() => {
    (async () => {
      const resolvedParams = await Promise.resolve(params);
      setAlbumId(resolvedParams.albumId);
    })();
  }, [params]);
  const [album, setAlbum] = useState<Album | null>(null);
  const [images, setImages] = useState<ImageItem[]>([]);
  const [selectMode, setSelectMode] = useState(false);
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [shareOpen, setShareOpen] = useState(false);
  const [pickerOpen, setPickerOpen] = useState(false);

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
      const [a, imgs] = await Promise.all([
        api.get(endpoints.album(albumId), { signal: abortControllerRef.current.signal }),
        api.get(endpoints.albumImages(albumId), { signal: abortControllerRef.current.signal }),
      ]);
      setAlbum(a.data?.id ? a.data : a.data?.album ?? a.data);
      setImages(Array.isArray(imgs.data) ? imgs.data : (imgs.data?.images ?? []));
    } catch (e: any) {
      if (e.name === 'AbortError' || e.name === 'CanceledError') {
        return; // Request was cancelled, ignore
      }
      throw e;
    }
  }

  useEffect(() => {
    if (!albumId) return;
    (async () => {
      try { await load(); }
      catch (e: any) { toast.error(e?.response?.data?.detail ?? "Failed to load album"); }
    })();

    return () => {
      // Cleanup: cancel any in-flight requests
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [albumId]);

  function toggle(id: string) {
    setSelected((p) => ({ ...p, [id]: !p[id] }));
  }

  async function removeSelected() {
    const ids = Object.keys(selected).filter((k) => selected[k]);
    if (!ids.length) return toast.error("Select images first");

    if (actionAbortRef.current) {
      actionAbortRef.current.abort();
    }
    actionAbortRef.current = new AbortController();

    // Optimistic update
    const previousImages = images;
    if (mountedRef.current) {
      setImages((prev) => prev.filter((img) => !ids.includes(img.id)));
      setSelected({});
      setSelectMode(false);
    }

    try {
      await api.post(endpoints.albumRemoveImages(albumId), ids, {
        signal: actionAbortRef.current.signal,
      });
      
      if (!mountedRef.current) return;
      toast.success("Removed");
      await load();
    } catch (e: any) {
      if (e.name === 'AbortError' || e.name === 'CanceledError') {
        return; // Request was cancelled, ignore
      }
      // Rollback on error
      if (mountedRef.current) {
        setImages(previousImages);
        toast.error(e?.response?.data?.detail ?? "Remove failed");
      }
    }
  }

  async function addImages(ids: string[]) {
    if (actionAbortRef.current) {
      actionAbortRef.current.abort();
    }
    actionAbortRef.current = new AbortController();

    try {
      await api.post(endpoints.albumAddImages(albumId), ids, {
        signal: actionAbortRef.current.signal,
      });
      
      if (!mountedRef.current) return;
      toast.success("Added");
      await load();
    } catch (e: any) {
      if (e.name === 'AbortError' || e.name === 'CanceledError') {
        return; // Request was cancelled, ignore
      }
      if (mountedRef.current) {
        toast.error(e?.response?.data?.detail ?? "Add failed");
      }
    }
  }

  async function deleteAlbum() {
    if (!confirm("Delete this album? (Manual only)")) return;
    try {
      await api.delete(endpoints.albumDelete(albumId));
      toast.success("Album deleted");
      router.push("/albums");
    } catch (e: any) {
      toast.error(e?.response?.data?.detail ?? "Delete failed");
    }
  }

  if (!albumId || !album) return <div className="p-6">Loading...</div>;

  return (
    <div className="space-y-4">
      <ShareModal open={shareOpen} onClose={() => setShareOpen(false)} albumId={albumId} />

      {pickerOpen && (
        <ImagePicker
          onClose={() => setPickerOpen(false)}
          onConfirm={(ids) => {
            setPickerOpen(false);
            addImages(ids);
          }}
        />
      )}

      <div className="bg-white border rounded-xl p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-xl font-semibold">{album.name}</h1>
            <p className="text-sm text-gray-500">{album.description ?? ""}</p>
            <div className="mt-2 text-xs text-gray-500">
              {album.image_count ?? images.length} images • {album.album_type ?? (album.is_auto_generated ? "Auto" : "Manual")}
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <button 
              className="border rounded-md px-3 py-2.5 text-sm min-h-[44px] flex-1 sm:flex-none" 
              onClick={() => setPickerOpen(true)}
            >
              Add Images
            </button>
            <button
              className="border rounded-md px-3 py-2.5 text-sm min-h-[44px] flex-1 sm:flex-none"
              onClick={() => setSelectMode((v) => !v)}
            >
              {selectMode ? "Cancel" : "Remove"}
            </button>
            <button 
              className="border rounded-md px-3 py-2.5 text-sm min-h-[44px] flex-1 sm:flex-none" 
              onClick={() => setShareOpen(true)}
            >
              Share
            </button>

            <a
              className="border rounded-md px-3 py-2.5 text-sm min-h-[44px] flex-1 sm:flex-none text-center"
              href={`${process.env.NEXT_PUBLIC_API_BASE_URL}${endpoints.albumQR(albumId)}`}
              target="_blank"
            >
              QR Code
            </a>

            {!album.is_auto_generated && (
              <button 
                className="border rounded-md px-3 py-2.5 text-sm text-red-600 min-h-[44px] flex-1 sm:flex-none" 
                onClick={deleteAlbum}
              >
                Delete
              </button>
            )}
          </div>
        </div>

        {selectMode && (
          <div className="mt-3 flex flex-col sm:flex-row gap-2 items-start sm:items-center">
            <button 
              className="bg-black text-white rounded-md px-3 py-2.5 text-sm min-h-[44px] w-full sm:w-auto" 
              onClick={removeSelected}
            >
              Remove Selected ({Object.values(selected).filter(Boolean).length})
            </button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2 sm:gap-3">
        {images.map((img) => (
          <div 
            key={img.id} 
            className={`bg-white border rounded-xl overflow-hidden ${selectMode && selected[img.id] ? "ring-2 ring-black" : ""}`}
          >
            <img
              src={`${process.env.NEXT_PUBLIC_API_BASE_URL}${endpoints.imageThumb(img.id)}`}
              className="w-full h-40 sm:h-48 object-cover"
              alt={img.original_filename ?? "image"}
              onClick={() => selectMode && toggle(img.id)}
            />
            <div className="p-2 sm:p-3 text-xs sm:text-sm flex items-center justify-between">
              <div className="truncate flex-1">{img.original_filename ?? "Untitled"}</div>
              {selectMode && (
                <input 
                  type="checkbox" 
                  checked={!!selected[img.id]} 
                  onChange={() => toggle(img.id)}
                  className="ml-2 w-5 h-5"
                />
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function AlbumDetail({ params }: { params: Promise<{ albumId: string }> | { albumId: string } }) {
  return (
    <PageErrorBoundary pageName="Album Detail">
      <AlbumDetailContent params={params} />
    </PageErrorBoundary>
  );
}

function ImagePicker({
  onClose,
  onConfirm,
}: {
  onClose: () => void;
  onConfirm: (ids: string[]) => void;
}) {
  const [all, setAll] = useState<ImageItem[]>([]);
  const [sel, setSel] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    abortControllerRef.current = new AbortController();

    (async () => {
      try {
        const r = await api.get(endpoints.images + `?skip=0&limit=${IMAGE_PICKER_PAGE_SIZE}`, {
          signal: abortControllerRef.current!.signal,
        });
        const data = Array.isArray(r.data) ? r.data : (r.data?.images ?? []);
        setAll(data);
      } catch (e: any) {
        if (e.name === 'AbortError' || e.name === 'CanceledError') {
          return;
        }
        console.error("Failed to load images for picker:", e);
      } finally {
        setLoading(false);
      }
    })();

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  function toggle(id: string) {
    setSel((p) => ({ ...p, [id]: !p[id] }));
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
      <div className="w-full max-w-4xl bg-white rounded-xl border p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="font-semibold">Pick images to add</div>
          <button className="text-sm underline" onClick={onClose}>Close</button>
        </div>

        {loading ? (
          <div className="text-center py-8 text-gray-500">Loading images...</div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 max-h-[70vh] overflow-auto">
            {all.map((img) => (
            <div key={img.id} className={`border rounded-xl overflow-hidden ${sel[img.id] ? "ring-2 ring-black" : ""}`}>
              <img
                src={`${process.env.NEXT_PUBLIC_API_BASE_URL}${endpoints.imageThumb(img.id)}`}
                className="w-full h-40 object-cover"
                alt="pick"
                onClick={() => toggle(img.id)}
              />
              <div className="p-2 text-xs flex items-center justify-between">
                <span className="truncate">{img.original_filename ?? "Untitled"}</span>
                <input type="checkbox" checked={!!sel[img.id]} onChange={() => toggle(img.id)} />
              </div>
            </div>
          ))}
          </div>
        )}

        <button
          className="w-full bg-black text-white rounded-md py-2 text-sm"
          onClick={() => onConfirm(Object.keys(sel).filter((k) => sel[k]))}
        >
          Add Selected
        </button>
      </div>
    </div>
  );
}
