"use client";

import { useRef, useState, useEffect } from "react";
import { api } from "@/lib/api/client";
import { toast } from "sonner";
import { PageErrorBoundary } from "@/components/common/PageErrorBoundary";

type Props = { onDone: () => void };

function UploadDropzoneContent({ onDone }: Props) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadingFile, setUploadingFile] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      // Cancel any in-flight uploads on unmount
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  async function uploadSingle(file: File) {
    // Cancel any previous upload
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();
    const fd = new FormData();
    fd.append("file", file);
    
    if (!mountedRef.current) return;
    setUploadingFile(file.name);
    setProgress(0);
    
    try {
      await api.post("/images/upload", fd, {
        headers: { "Content-Type": "multipart/form-data" },
        signal: abortControllerRef.current.signal,
        onUploadProgress: (p) => {
          if (!mountedRef.current) return;
          const pct = p.total ? Math.round((p.loaded / p.total) * 100) : 0;
          setProgress(pct);
        },
      });
      
      if (!mountedRef.current) return;
      setUploadingFile(null);
      setProgress(0);
    } catch (e: any) {
      if (e.name === 'AbortError' || e.name === 'CanceledError') {
        return; // Request was cancelled, ignore
      }
      if (mountedRef.current) {
        toast.error(e?.response?.data?.detail ?? "Upload failed");
      }
      if (mountedRef.current) {
        setUploadingFile(null);
        setProgress(0);
      }
    }
  }

  async function uploadBulk(files: FileList) {
    // Cancel any previous upload
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();
    const fd = new FormData();
    const fileArray = Array.from(files);
    fileArray.forEach((f) => fd.append("files", f));
    
    if (!mountedRef.current) return;
    setUploadingFile(`${fileArray.length} files`);
    setProgress(0);
    
    try {
      await api.post("/images/bulk/upload", fd, { 
        headers: { "Content-Type": "multipart/form-data" },
        signal: abortControllerRef.current.signal,
        onUploadProgress: (p) => {
          if (!mountedRef.current) return;
          const pct = p.total ? Math.round((p.loaded / p.total) * 100) : 0;
          setProgress(pct);
        },
      });
      
      if (!mountedRef.current) return;
      setUploadingFile(null);
      setProgress(0);
    } catch (e: any) {
      if (e.name === 'AbortError' || e.name === 'CanceledError') {
        return; // Request was cancelled, ignore
      }
      if (mountedRef.current) {
        toast.error(e?.response?.data?.detail ?? "Upload failed");
      }
      if (mountedRef.current) {
        setUploadingFile(null);
        setProgress(0);
      }
    }
  }

  return (
    <div className="bg-white border rounded-xl p-3 sm:p-4">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 sm:gap-0">
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-sm sm:text-base">Upload photos</div>
          <div className="text-xs text-gray-500">JPEG / PNG / WebP, max 50MB</div>
        </div>
        <button
          className="w-full sm:w-auto border rounded-md px-3 py-2.5 text-sm disabled:opacity-50 min-h-[44px]"
          onClick={() => inputRef.current?.click()}
          disabled={busy}
        >
          {busy ? "Uploading..." : "Choose files"}
        </button>
      </div>

      {busy && uploadingFile && (
        <div className="mt-3 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-600 truncate">{uploadingFile}</span>
            <span className="text-gray-500">{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      <input
        ref={inputRef}
        type="file"
        multiple
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
        onChange={async (e) => {
          if (!e.target.files?.length) return;
          if (!mountedRef.current) return;
          
          setBusy(true);
          try {
            const files = e.target.files;
            if (files.length === 1) await uploadSingle(files[0]);
            else await uploadBulk(files);
            
            if (!mountedRef.current) return;
            toast.success("Upload complete");
            onDone();
          } catch (err: any) {
            if (err.name === 'AbortError' || err.name === 'CanceledError') {
              return; // Request was cancelled, ignore
            }
            if (mountedRef.current) {
              toast.error(err?.response?.data?.detail ?? "Upload failed");
            }
          } finally {
            if (mountedRef.current) {
              setBusy(false);
              setProgress(0);
              setUploadingFile(null);
            }
            e.target.value = "";
          }
        }}
      />
    </div>
  );
}

export default function UploadDropzone({ onDone }: Props) {
  return (
    <PageErrorBoundary pageName="Upload">
      <UploadDropzoneContent onDone={onDone} />
    </PageErrorBoundary>
  );
}
