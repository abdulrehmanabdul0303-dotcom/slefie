"use client";

import { useState, useEffect, useRef } from "react";
import { api } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import { toast } from "sonner";
import { X, Trash2, Copy, RefreshCw } from "lucide-react";
import { PageErrorBoundary } from "@/components/common/PageErrorBoundary";

interface Share {
  share_id: string;
  expires_at: string | null;
  max_views: number | null;
  view_count: number;
  revoked: boolean;
  created_at: string | null;
  is_active: boolean;
}

function ShareModalContent({
  open,
  onClose,
  albumId,
}: {
  open: boolean;
  onClose: () => void;
  albumId: string;
}) {
  const [hours, setHours] = useState(72);
  const [maxViews, setMaxViews] = useState<number | "">("");
  const [shareType, setShareType] = useState<"PUBLIC" | "FACE_CLAIM">("PUBLIC");

  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [shareId, setShareId] = useState<string | null>(null);
  const [activeShares, setActiveShares] = useState<Share[]>([]);
  const [loadingShares, setLoadingShares] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      // Cancel any in-flight requests on unmount
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  useEffect(() => {
    if (open && albumId) {
      loadShares();
    }
    
    return () => {
      // Cancel request if modal closes or albumId changes
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [open, albumId]);

  async function loadShares() {
    // Cancel any previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();
    
    if (!mountedRef.current) return;
    setLoadingShares(true);
    
    try {
      const r = await api.get(endpoints.shareList(albumId), {
        signal: abortControllerRef.current.signal,
      });
      
      if (!mountedRef.current) return;
      setActiveShares(r.data?.shares ?? []);
    } catch (e: any) {
      if (e.name === 'AbortError' || e.name === 'CanceledError') {
        return; // Request was cancelled, ignore
      }
      console.error("Failed to load shares:", e);
      // Don't show error toast, just silently fail
    } finally {
      if (mountedRef.current) {
        setLoadingShares(false);
      }
    }
  }

  if (!open) return null;

  async function create() {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    try {
      // Backend expects: album_id (required), hours (optional, default 60), max_views (optional), share_type (optional)
      const body: any = { 
        album_id: albumId, 
        hours: hours || 72,
        share_type: shareType
      };
      if (maxViews !== "" && maxViews !== null && maxViews !== undefined) {
        body.max_views = Number(maxViews);
      }

      const r = await api.post(endpoints.shareCreate, body, {
        signal: abortControllerRef.current.signal,
      });
      const url = r.data?.share_url ?? r.data?.url ?? null;
      const newShareId = r.data?.share_id ?? null;
      
      if (!mountedRef.current) return;
      
      if (!url) {
        toast.error("Share URL not received from server");
        return;
      }
      
      // Construct full URL if backend returns relative path
      const fullUrl = url.startsWith("http") 
        ? url 
        : `${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8999"}${url.startsWith("/") ? url : `/${url}`}`;
      
      setShareUrl(fullUrl);
      setShareId(newShareId);
      toast.success("Share created");
      
      // Reload shares list
      await loadShares();
    } catch (e: any) {
      if (e.name === 'AbortError' || e.name === 'CanceledError') {
        return; // Request was cancelled, ignore
      }
      if (mountedRef.current) {
        const errorDetail = e?.response?.data?.detail ?? e?.response?.data?.message ?? e?.message;
        console.error("Share creation error:", e);
        toast.error(errorDetail ?? "Share creation failed. Please try again.");
      }
    }
  }

  async function revokeShare(shareIdToRevoke: string) {
    if (!confirm("Are you sure you want to revoke this share link? It will stop working immediately.")) {
      return;
    }

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    try {
      await api.post(endpoints.shareRevoke(shareIdToRevoke), {}, {
        signal: abortControllerRef.current.signal,
      });
      
      if (!mountedRef.current) return;
      toast.success("Share link revoked");
      
      // Reload shares list
      await loadShares();
      
      // Clear current share if it was revoked
      if (shareIdToRevoke === shareId) {
        setShareUrl(null);
        setShareId(null);
      }
    } catch (e: any) {
      if (e.name === 'AbortError' || e.name === 'CanceledError') {
        return; // Request was cancelled, ignore
      }
      if (mountedRef.current) {
        const errorMsg = e?.response?.data?.detail ?? e?.message ?? "Failed to revoke share";
        toast.error(errorMsg);
      }
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50" onClick={onClose}>
      <div className="w-full max-w-2xl bg-white rounded-xl border p-4 sm:p-6 space-y-4 max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <div className="font-semibold text-sm sm:text-base">Share Album</div>
          <button 
            className="p-1 hover:bg-gray-100 rounded" 
            onClick={onClose}
            aria-label="Close"
          >
            <X size={20} />
          </button>
        </div>

        {/* Active Shares List */}
        <div className="border rounded-md p-3 bg-gray-50">
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs sm:text-sm font-medium">Active Share Links</div>
            <button
              onClick={loadShares}
              disabled={loadingShares}
              className="p-1 hover:bg-gray-200 rounded disabled:opacity-50"
              title="Refresh"
            >
              <RefreshCw size={14} className={loadingShares ? "animate-spin" : ""} />
            </button>
          </div>
          
          {loadingShares ? (
            <div className="text-xs text-gray-500 py-2">Loading...</div>
          ) : activeShares.length === 0 ? (
            <div className="text-xs text-gray-500 py-2">No active share links</div>
          ) : (
            <div className="space-y-2">
              {activeShares.map((share) => (
                <div
                  key={share.share_id}
                  className={`border rounded-md p-2 text-xs ${
                    share.revoked ? "bg-red-50 border-red-200" : share.is_active ? "bg-white" : "bg-gray-100"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">
                        {share.revoked ? "Revoked" : share.is_active ? "Active" : "Expired"}
                      </div>
                      <div className="text-gray-500 mt-1">
                        Views: {share.view_count}
                        {share.max_views ? ` / ${share.max_views}` : ""}
                      </div>
                      {share.expires_at && (
                        <div className="text-gray-500">
                          Expires: {new Date(share.expires_at).toLocaleString()}
                        </div>
                      )}
                    </div>
                    {!share.revoked && share.is_active && (
                      <button
                        onClick={() => revokeShare(share.share_id)}
                        className="p-1.5 text-red-600 hover:bg-red-50 rounded min-h-[32px] min-w-[32px] flex items-center justify-center"
                        title="Revoke immediately"
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Create New Share */}
        <div className="border-t pt-4">
          <div className="text-xs sm:text-sm font-medium mb-3">Create New Share Link</div>
          
          {/* Share Type Selection */}
          <div className="mb-3">
            <label className="text-xs text-gray-500 block mb-2">Share Type</label>
            <div className="flex gap-2">
              <button
                onClick={() => setShareType("PUBLIC")}
                className={`flex-1 py-2 px-3 rounded-md text-xs sm:text-sm font-medium transition-colors ${
                  shareType === "PUBLIC"
                    ? "bg-black text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                Public Link
              </button>
              <button
                onClick={() => setShareType("FACE_CLAIM")}
                className={`flex-1 py-2 px-3 rounded-md text-xs sm:text-sm font-medium transition-colors ${
                  shareType === "FACE_CLAIM"
                    ? "bg-black text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                🔒 Face Claim
              </button>
            </div>
            {shareType === "FACE_CLAIM" && (
              <p className="text-xs text-gray-500 mt-2">
                Recipients must verify their face to see only their images
              </p>
            )}
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-500 block mb-1">Expiration hours</label>
              <input
                type="number"
                className="w-full border rounded-md px-3 py-2 text-sm min-h-[44px]"
                value={hours}
                onChange={(e) => setHours(Number(e.target.value))}
                min={1}
                max={720}
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Max views (optional)</label>
              <input
                type="number"
                className="w-full border rounded-md px-3 py-2 text-sm min-h-[44px]"
                value={maxViews}
                onChange={(e) => setMaxViews(e.target.value === "" ? "" : Number(e.target.value))}
                min={1}
              />
            </div>
          </div>

          <button 
            onClick={create} 
            className="w-full bg-black text-white rounded-md py-2.5 text-sm min-h-[44px] mt-3"
          >
            {shareType === "FACE_CLAIM" ? "Create Face Claim Link" : "Create Share Link"}
          </button>

          {shareUrl && (
            <div className="border rounded-md p-3 mt-3 bg-blue-50">
              <div className="text-xs text-gray-500 mb-1">New Share URL</div>
              <div className="text-xs sm:text-sm break-all font-mono bg-white p-2 rounded border mb-2">{shareUrl}</div>
              <button
                className="w-full sm:w-auto border rounded-md px-3 py-2 text-sm min-h-[44px] flex items-center justify-center gap-2 bg-white hover:bg-gray-50"
                onClick={() => {
                  navigator.clipboard.writeText(shareUrl);
                  toast.success("Copied to clipboard");
                }}
              >
                <Copy size={14} />
                Copy URL
              </button>
              {shareId && (
                <button
                  className="w-full sm:w-auto ml-0 sm:ml-2 mt-2 sm:mt-0 border border-red-300 text-red-600 rounded-md px-3 py-2 text-sm min-h-[44px] flex items-center justify-center gap-2 hover:bg-red-50"
                  onClick={() => revokeShare(shareId)}
                >
                  <Trash2 size={14} />
                  Revoke Immediately
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ShareModal({
  open,
  onClose,
  albumId,
}: {
  open: boolean;
  onClose: () => void;
  albumId: string;
}) {
  if (!open) return null;
  
  return (
    <PageErrorBoundary pageName="Share Modal" fallback={
      <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50" onClick={onClose}>
        <div className="w-full max-w-2xl bg-white rounded-xl border p-4 sm:p-6">
          <p className="text-red-600">Share modal error. Please close and try again.</p>
          <button onClick={onClose} className="mt-4 px-4 py-2 bg-black text-white rounded-md text-sm">
            Close
          </button>
        </div>
      </div>
    }>
      <ShareModalContent open={open} onClose={onClose} albumId={albumId} />
    </PageErrorBoundary>
  );
}
