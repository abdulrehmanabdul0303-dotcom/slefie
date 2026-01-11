"use client";

import { useEffect, useRef, useState } from "react";

interface CameraCaptureProps {
  onCapture: (file: File) => void;
  showUpload?: boolean;
  showCamera?: boolean;
}

export default function CameraCapture({ 
  onCapture, 
  showUpload = true, 
  showCamera = true 
}: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [ready, setReady] = useState(false);
  const [method, setMethod] = useState<"camera" | "upload">("camera");
  const mountedRef = useRef(true);

  useEffect(() => {
    let stream: MediaStream | null = null;
    mountedRef.current = true;

    (async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        
        // Check if component is still mounted and video ref exists
        if (!mountedRef.current || !videoRef.current) {
          stream?.getTracks().forEach((t) => t.stop());
          return;
        }

        const video = videoRef.current;
        video.srcObject = stream;
        
        // Handle play() promise with proper error handling
        try {
          await video.play();
          // Only set ready if component is still mounted
          if (mountedRef.current) {
            setReady(true);
          }
        } catch (playError: any) {
          // Ignore AbortError - it's expected if component unmounts during play
          if (playError.name !== 'AbortError' && playError.name !== 'NotAllowedError') {
            console.warn("Video play error:", playError);
          }
          // Clean up stream if play fails
          if (stream) {
            stream.getTracks().forEach((t) => t.stop());
          }
        }
      } catch (error: any) {
        console.error("Error accessing camera:", error);
        if (mountedRef.current) {
          setReady(false);
        }
      }
    })();

    return () => {
      mountedRef.current = false;
      if (stream) {
        stream.getTracks().forEach((t) => t.stop());
      }
      // Clear video source
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
    };
  }, []);

  function snap() {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0);
    canvas.toBlob((blob) => {
      if (!blob) return;
      const file = new File([blob], "capture.jpg", { type: "image/jpeg" });
      onCapture(file);
    }, "image/jpeg", 0.92);
  }

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      onCapture(file);
    }
  }

  function handleUploadClick() {
    fileInputRef.current?.click();
  }

  return (
    <div className="space-y-3">
      {/* Method Selection */}
      {(showUpload && showCamera) && (
        <div className="flex gap-2">
          <button
            onClick={() => setMethod("camera")}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              method === "camera"
                ? "bg-black text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            📷 Camera
          </button>
          <button
            onClick={() => setMethod("upload")}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              method === "upload"
                ? "bg-black text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            📁 Upload
          </button>
        </div>
      )}

      {/* Camera Method */}
      {method === "camera" && showCamera && (
        <div className="border rounded-xl p-3 bg-white">
          <div className="text-sm font-medium mb-2">Camera</div>
          <video 
            ref={videoRef} 
            className="w-full rounded-md bg-black aspect-video object-cover" 
            autoPlay 
            playsInline
            muted
          />
          <canvas ref={canvasRef} className="hidden" />
          <button 
            disabled={!ready} 
            className="mt-3 w-full bg-black text-white rounded-md py-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-800 transition-colors" 
            onClick={snap}
          >
            Capture
          </button>
          {!ready && (
            <p className="text-xs text-gray-500 mt-2">Requesting camera access...</p>
          )}
        </div>
      )}

      {/* Upload Method */}
      {method === "upload" && showUpload && (
        <div className="border rounded-xl p-3 bg-white">
          <div className="text-sm font-medium mb-2">Upload Photo</div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            className="hidden"
          />
          <button
            onClick={handleUploadClick}
            className="w-full bg-black text-white rounded-md py-2 text-sm hover:bg-gray-800 transition-colors"
          >
            Choose File
          </button>
          <p className="text-xs text-gray-500 mt-2 text-center">
            Select an image file from your device
          </p>
        </div>
      )}
    </div>
  );
}
