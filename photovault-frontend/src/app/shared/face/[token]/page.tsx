"use client";

import { useEffect, useState, useRef } from "react";
import axios from "axios";
import { endpoints } from "@/lib/api/endpoints";
import { PageErrorBoundary } from "@/components/common/PageErrorBoundary";
import { toast } from "sonner";
import CameraCapture from "@/components/facial/CameraCapture";

// Use unauthenticated axios instance for public face claim
const publicApi = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8999",
  timeout: 30000,
});

type Step = "intro" | "capture" | "processing" | "success" | "denied";

interface ShareInfo {
  valid: boolean;
  share_type: string;
  album_name: string;
  album_description?: string;
  expires_at: string;
  privacy_notice: string;
  attempts_remaining: number;
}

interface MatchedImage {
  id: string;
  thumbnail_url: string;
  view_url: string;
  width: number;
  height: number;
  filename: string;
}

interface VerifyResponse {
  verified: boolean;
  confidence?: number;
  matched_faces_count?: number;
  images?: MatchedImage[];
  access_token?: string;
  message?: string;
}

function FaceClaimContent({ params }: { params: Promise<{ token: string }> | { token: string } }) {
  const [token, setToken] = useState<string>("");
  const [step, setStep] = useState<Step>("intro");
  const [shareInfo, setShareInfo] = useState<ShareInfo | null>(null);
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [matchedImages, setMatchedImages] = useState<MatchedImage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    (async () => {
      const resolvedParams = await Promise.resolve(params);
      setToken(resolvedParams.token);
    })();
  }, [params]);

  useEffect(() => {
    if (!token) return;

    // Cancel any in-flight request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();
    setLoading(true);
    setError(null);

    (async () => {
      try {
        const r = await publicApi.get(endpoints.faceClaimInit(token), {
          signal: abortControllerRef.current!.signal,
        });
        setShareInfo(r.data);
      } catch (e: any) {
        if (e.name === 'AbortError' || e.name === 'CanceledError') {
          return;
        }
        console.error("Failed to load face claim:", e);
        const errorMsg = e?.response?.data?.detail || "Invalid or expired link";
        setError(errorMsg);
        toast.error(errorMsg);
      } finally {
        setLoading(false);
      }
    })();

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [token]);

  async function handleFaceCapture(file: File) {
    if (!token) return;

    setStep("processing");
    setError(null);

    try {
      // Step 1: Upload face for scanning
      const formData = new FormData();
      formData.append("file", file);
      formData.append("method", "upload");

      const scanRes = await publicApi.post(
        endpoints.faceClaimScan(token),
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
          signal: abortControllerRef.current?.signal,
        }
      );

      if (scanRes.data.session_token) {
        setSessionToken(scanRes.data.session_token);

        // Step 2: Verify face
        await new Promise((resolve) => setTimeout(resolve, 1000)); // Brief delay for UX

        const verifyRes = await publicApi.post<VerifyResponse>(
          endpoints.faceClaimVerify(token),
          { session_token: scanRes.data.session_token },
          {
            signal: abortControllerRef.current?.signal,
          }
        );

        if (verifyRes.data.verified && verifyRes.data.images && verifyRes.data.images.length > 0) {
          // Success - matched images found
          setAccessToken(verifyRes.data.access_token || null);
          setMatchedImages(verifyRes.data.images);
          setStep("success");
          toast.success(`Found ${verifyRes.data.images.length} images with your face!`);
        } else {
          // No match found
          setStep("denied");
          toast.error(verifyRes.data.message || "No matching images found");
        }
      }
    } catch (e: any) {
      if (e.name === 'AbortError' || e.name === 'CanceledError') {
        return;
      }
      console.error("Face claim error:", e);
      const errorMsg = e?.response?.data?.detail || "Face verification failed";
      setError(errorMsg);
      setStep("capture");
      toast.error(errorMsg);
    }
  }

  function handleContinue() {
    setStep("capture");
  }

  function handleTryAgain() {
    setStep("capture");
    setSessionToken(null);
    setError(null);
  }

  if (loading && !shareInfo) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-black mx-auto mb-4"></div>
          <p className="text-sm text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (error && !shareInfo) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="max-w-md w-full bg-white border rounded-xl p-6 text-center">
          <div className="text-red-500 text-4xl mb-4">✗</div>
          <h2 className="text-xl font-semibold mb-2">Access Denied</h2>
          <p className="text-sm text-gray-600 mb-4">{error}</p>
          <p className="text-xs text-gray-500">This link may be invalid, expired, or revoked.</p>
        </div>
      </div>
    );
  }

  if (!shareInfo) return null;

  // Intro Screen
  if (step === "intro") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="max-w-md w-full bg-white border rounded-xl p-6 space-y-4">
          <div className="text-center">
            <div className="text-4xl mb-4">🔒</div>
            <h1 className="text-2xl font-semibold mb-2">Face-Based Access</h1>
            <p className="text-sm text-gray-600 mb-4">{shareInfo.album_name}</p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-2">
            <p className="text-sm font-medium text-blue-900">Privacy Notice</p>
            <p className="text-xs text-blue-700">{shareInfo.privacy_notice}</p>
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex items-start gap-2">
              <span className="text-green-500">✓</span>
              <span className="text-gray-700">Only YOUR images will be shown</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-green-500">✓</span>
              <span className="text-gray-700">No access to others' photos</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-green-500">✓</span>
              <span className="text-gray-700">Your face data is temporary</span>
            </div>
          </div>

          {shareInfo.attempts_remaining > 0 && (
            <p className="text-xs text-gray-500 text-center">
              {shareInfo.attempts_remaining} attempts remaining
            </p>
          )}

          <button
            onClick={handleContinue}
            className="w-full rounded-md bg-black text-white py-3 text-sm min-h-[44px] hover:bg-gray-800 transition-colors"
          >
            Continue
          </button>
        </div>
      </div>
    );
  }

  // Capture Screen
  if (step === "capture") {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-2xl mx-auto space-y-4">
          <div className="bg-white border rounded-xl p-4 text-center">
            <h2 className="text-xl font-semibold mb-2">📸 Verify Your Identity</h2>
            <p className="text-sm text-gray-600 mb-4">
              Upload a photo or use your camera to verify your face
            </p>
          </div>

          <div className="bg-white border rounded-xl p-4">
            <div className="mb-4">
              <p className="text-sm font-medium mb-2">Requirements:</p>
              <ul className="text-xs text-gray-600 space-y-1">
                <li>• Face clearly visible</li>
                <li>• Good lighting</li>
                <li>• Single person only</li>
              </ul>
            </div>
            <CameraCapture onCapture={handleFaceCapture} />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Processing Screen
  if (step === "processing") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="max-w-md w-full bg-white border rounded-xl p-6 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-black mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold mb-2">🔍 Processing...</h2>
          <p className="text-sm text-gray-600">Detecting face...</p>
          <p className="text-sm text-gray-600">Extracting features...</p>
          <p className="text-sm text-gray-600">Matching with album...</p>
        </div>
      </div>
    );
  }

  // Success Screen - Gallery
  if (step === "success" && matchedImages.length > 0) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-5xl mx-auto space-y-4">
          <div className="bg-white border rounded-xl p-4 text-center">
            <div className="text-green-500 text-4xl mb-2">✅</div>
            <h1 className="text-xl font-semibold mb-2">Access Granted</h1>
            <p className="text-sm text-gray-600">
              Found {matchedImages.length} image{matchedImages.length !== 1 ? 's' : ''} with your face!
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {matchedImages.map((img) => (
              <a
                key={img.id}
                href={`${process.env.NEXT_PUBLIC_API_BASE_URL}${img.view_url}`}
                target="_blank"
                rel="noopener noreferrer"
                className="block group"
              >
                <div className="bg-white border rounded-xl overflow-hidden hover:shadow-lg transition-shadow">
                  <img
                    src={`${process.env.NEXT_PUBLIC_API_BASE_URL}${img.thumbnail_url}`}
                    alt={img.filename}
                    className="w-full h-48 object-cover"
                    onError={(e) => {
                      // Fallback if thumbnail fails
                      (e.target as HTMLImageElement).src = `${process.env.NEXT_PUBLIC_API_BASE_URL}${img.view_url}`;
                    }}
                  />
                  <div className="p-2">
                    <p className="text-xs text-gray-600 truncate">{img.filename}</p>
                    <p className="text-xs text-gray-400">{img.width} × {img.height}</p>
                  </div>
                </div>
              </a>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Denied Screen
  if (step === "denied") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="max-w-md w-full bg-white border rounded-xl p-6 text-center space-y-4">
          <div className="text-red-500 text-4xl mb-4">❌</div>
          <h2 className="text-xl font-semibold mb-2">Access Denied</h2>
          <p className="text-sm text-gray-600 mb-4">
            No matching images found. This album may not contain photos of you, or the link may have expired.
          </p>
          <div className="space-y-2">
            <button
              onClick={handleTryAgain}
              className="w-full rounded-md bg-black text-white py-3 text-sm min-h-[44px] hover:bg-gray-800 transition-colors"
            >
              Try Again
            </button>
            <p className="text-xs text-gray-500">
              If you believe this is an error, please contact the album owner.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return null;
}

export default function FaceClaimPage({ params }: { params: Promise<{ token: string }> | { token: string } }) {
  return (
    <PageErrorBoundary pageName="Face Claim">
      <FaceClaimContent params={params} />
    </PageErrorBoundary>
  );
}

