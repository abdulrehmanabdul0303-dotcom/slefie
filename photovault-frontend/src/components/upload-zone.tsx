'use client';

import { useState, useRef } from 'react';
import { Upload, X } from 'lucide-react';
import { Button, Spinner } from './ui';

interface FileWithPreview {
  file: File;
  preview: string;
  progress: number;
}

interface UploadZoneProps {
  onUpload?: (files: File[]) => Promise<void>;
  maxSize?: number; // in MB
  acceptedTypes?: string[];
}

export function UploadZone({
  onUpload,
  maxSize = 50,
  acceptedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
}: UploadZoneProps): React.ReactNode {
  const [files, setFiles] = useState<FileWithPreview[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFiles = Array.from(e.dataTransfer.files);
    addFiles(droppedFiles);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    addFiles(selectedFiles);
  };

  const addFiles = (newFiles: File[]) => {
    const validFiles = newFiles.filter((file) => {
      if (!acceptedTypes.includes(file.type)) {
        console.warn(`Invalid file type: ${file.name}`);
        return false;
      }
      if (file.size > maxSize * 1024 * 1024) {
        console.warn(`File too large: ${file.name}`);
        return false;
      }
      return true;
    });

    validFiles.forEach((file) => {
      const preview = URL.createObjectURL(file);
      setFiles((prev) => [...prev, { file, preview, progress: 0 }]);
    });
  };

  const removeFile = (index: number) => {
    setFiles((prev) => {
      const updated = prev.filter((_, i) => i !== index);
      URL.revokeObjectURL(prev[index].preview);
      return updated;
    });
  };

  const handleUpload = async () => {
    if (!onUpload || files.length === 0) return;

    setIsUploading(true);
    try {
      const filesToUpload = files.map((f) => f.file);
      await onUpload(filesToUpload);
      setFiles([]);
      if (inputRef.current) inputRef.current.value = '';
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="w-full space-y-4">
      {/* Drag-drop area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-200 ${
          isDragging
            ? 'border-blue-500/50 bg-blue-500/10'
            : 'border-white/20 bg-white/5 hover:bg-white/10'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          onChange={handleFileSelect}
          accept={acceptedTypes.join(',')}
          className="hidden"
        />

        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-500/20 to-cyan-500/20 flex items-center justify-center border border-blue-500/30">
            <Upload className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <p className="text-white font-medium">Drag photos here or click to select</p>
            <p className="text-white/50 text-sm mt-1">
              PNG, JPG, GIF, WebP • Up to {maxSize}MB each
            </p>
          </div>
        </div>
      </div>

      {/* File previews */}
      {files.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-white">
            {files.length} file{files.length !== 1 ? 's' : ''} selected
          </h3>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {files.map((file, index) => (
              <div key={index} className="relative group">
                {/* Image preview */}
                <img
                  src={file.preview}
                  alt={file.file.name}
                  className="w-full aspect-square object-cover rounded-lg border border-white/10"
                />

                {/* Progress overlay */}
                {isUploading && file.progress < 100 && (
                  <div className="absolute inset-0 bg-black/50 rounded-lg flex items-center justify-center">
                    <div className="text-center">
                      <Spinner size="sm" />
                      <p className="text-xs text-white mt-2">{file.progress}%</p>
                    </div>
                  </div>
                )}

                {/* Remove button */}
                {!isUploading && (
                  <button
                    onClick={() => removeFile(index)}
                    className="absolute top-2 right-2 p-1.5 rounded-lg bg-red-500/80 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600"
                  >
                    <X className="w-4 h-4 text-white" />
                  </button>
                )}

                {/* Success checkmark */}
                {isUploading && file.progress === 100 && (
                  <div className="absolute inset-0 bg-green-500/20 rounded-lg flex items-center justify-center">
                    <svg className="w-8 h-8 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                )}

                {/* File name tooltip */}
                <div className="absolute bottom-0 left-0 right-0 bg-black/80 rounded-b-lg px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <p className="text-xs text-white truncate">{file.file.name}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Upload button */}
          <Button
            variant="primary"
            fullWidth
            onClick={handleUpload}
            loading={isUploading}
            disabled={isUploading}
          >
            {isUploading ? 'Uploading...' : `Upload ${files.length} file${files.length !== 1 ? 's' : ''}`}
          </Button>
        </div>
      )}
    </div>
  );
}
