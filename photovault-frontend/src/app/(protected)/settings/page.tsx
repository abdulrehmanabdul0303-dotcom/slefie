"use client";

import { useState, useRef, useEffect } from "react";
import { api } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import CameraCapture from "@/components/facial/CameraCapture";
import { AccountDeletion } from "@/components/settings/AccountDeletion";
import { toast } from "sonner";
import { PageErrorBoundary } from "@/components/common/PageErrorBoundary";

function SettingsContent() {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<any>(null);
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

  async function registerFace(file: File) {
    // Cancel any previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();
    
    if (!mountedRef.current) return;
    setBusy(true);
    setResult(null);
    
    try {
      const fd = new FormData();
      fd.append("image", file);
      const r = await api.post(endpoints.faceRegister, fd, { 
        headers: { "Content-Type": "multipart/form-data" },
        signal: abortControllerRef.current.signal,
      });
      
      if (!mountedRef.current) return;
      toast.success("Face registered");
      setResult(r.data);
    } catch (e: any) {
      if (e.name === 'AbortError' || e.name === 'CanceledError') {
        return; // Request was cancelled, ignore
      }
      if (mountedRef.current) {
        toast.error(e?.response?.data?.detail ?? "Register failed");
      }
    } finally {
      if (mountedRef.current) {
        setBusy(false);
      }
    }
  }

  async function verifyFace(file: File) {
    // Cancel any previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();
    
    if (!mountedRef.current) return;
    setBusy(true);
    setResult(null);
    
    try {
      const fd = new FormData();
      fd.append("image", file);
      const r = await api.post(endpoints.faceVerify, fd, { 
        headers: { "Content-Type": "multipart/form-data" },
        signal: abortControllerRef.current.signal,
      });
      
      if (!mountedRef.current) return;
      toast.success("Verification done");
      setResult(r.data);
    } catch (e: any) {
      if (e.name === 'AbortError' || e.name === 'CanceledError') {
        return; // Request was cancelled, ignore
      }
      if (mountedRef.current) {
        toast.error(e?.response?.data?.detail ?? "Verify failed");
      }
    } finally {
      if (mountedRef.current) {
        setBusy(false);
      }
    }
  }

  return (
    <div className="space-y-4">
      <div className="bg-white border rounded-xl p-4">
        <div className="font-semibold">Settings</div>
        <div className="text-xs text-gray-500">Facial security</div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4">
        <div className="space-y-2">
          <div className="bg-white border rounded-xl p-3 sm:p-4">
            <div className="font-medium text-sm sm:text-base">Register Face</div>
            <div className="text-xs text-gray-500">Register your face for secure actions</div>
          </div>
          <CameraCapture onCapture={registerFace} />
        </div>

        <div className="space-y-2">
          <div className="bg-white border rounded-xl p-3 sm:p-4">
            <div className="font-medium text-sm sm:text-base">Verify Face</div>
            <div className="text-xs text-gray-500">Verify for sensitive operations</div>
          </div>
          <CameraCapture onCapture={verifyFace} />
        </div>
      </div>

      <div className="bg-white border rounded-xl p-4">
        <div className="font-medium">Result</div>
        <pre className="text-xs bg-gray-50 border rounded-md p-3 overflow-auto mt-2">
          {busy ? "Working..." : JSON.stringify(result, null, 2)}
        </pre>
      </div>

      <div className="mt-6">
        <AccountDeletion />
      </div>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <PageErrorBoundary pageName="Settings">
      <SettingsContent />
    </PageErrorBoundary>
  );
}
