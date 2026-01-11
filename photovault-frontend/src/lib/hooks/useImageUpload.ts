import { useState, useCallback } from 'react';
import axios, { AxiosProgressEvent } from 'axios';
import { useToast } from './useToast';

export interface UploadProgress {
  fileName: string;
  progress: number;
  total: number;
  speed: number; // bytes per second
  eta: number; // seconds remaining
}

export interface UploadFile {
  id: string;
  file: File;
  preview: string;
  progress: number;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  error?: string;
}

interface UseImageUploadReturn {
  files: UploadFile[];
  isUploading: boolean;
  addFiles: (files: File[]) => Promise<void>;
  removeFile: (id: string) => void;
  clearAll: () => void;
  uploadAll: () => Promise<void>;
}

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const MAX_FILES = 100;

/**
 * Hook for managing image uploads with progress tracking
 * 
 * @returns Upload state and control methods
 * 
 * @example
 * ```tsx
 * const { files, isUploading, addFiles, uploadAll } = useImageUpload();
 * 
 * const handleDrop = (e: DragEvent) => {
 *   const files = Array.from(e.dataTransfer.files);
 *   addFiles(files);
 * };
 * 
 * const handleUpload = async () => {
 *   await uploadAll();
 * };
 * ```
 */
export function useImageUpload(): UseImageUploadReturn {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const { success, error: showError, info } = useToast();

  /**
   * Validate a single file
   */
  const validateFile = useCallback((file: File): string | null => {
    // Check file type
    if (!ALLOWED_TYPES.includes(file.type)) {
      return `Invalid file type: ${file.name}. Only JPEG, PNG, WebP, and GIF are allowed.`;
    }

    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return `File too large: ${file.name}. Maximum size is 50MB.`;
    }

    // Check file size > 0
    if (file.size === 0) {
      return `Empty file: ${file.name}. Please select a valid image.`;
    }

    return null;
  }, []);

  /**
   * Add files to upload queue
   */
  const addFiles = useCallback(async (newFiles: File[]) => {
    // Check total file count
    if (files.length + newFiles.length > MAX_FILES) {
      showError(`Too many files. Maximum is ${MAX_FILES} files.`);
      return;
    }

    // Filter and validate files
    const validFiles: UploadFile[] = [];
    const errors: string[] = [];

    for (const file of newFiles) {
      const validationError = validateFile(file);
      if (validationError) {
        errors.push(validationError);
      } else {
        // Create preview
        const preview = URL.createObjectURL(file);
        validFiles.push({
          id: `${Date.now()}-${Math.random()}`,
          file,
          preview,
          progress: 0,
          status: 'pending',
        });
      }
    }

    // Show validation errors
    if (errors.length > 0) {
      errors.forEach(showError);
    }

    // Add valid files
    if (validFiles.length > 0) {
      setFiles(prev => [...prev, ...validFiles]);
      info(`Added ${validFiles.length} file(s) to upload queue`);
    }
  }, [files.length, validateFile, showError, info]);

  /**
   * Remove a file from queue
   */
  const removeFile = useCallback((id: string) => {
    setFiles(prev => {
      const file = prev.find(f => f.id === id);
      if (file?.preview) {
        URL.revokeObjectURL(file.preview);
      }
      return prev.filter(f => f.id !== id);
    });
  }, []);

  /**
   * Clear all files
   */
  const clearAll = useCallback(() => {
    files.forEach(file => {
      if (file.preview) {
        URL.revokeObjectURL(file.preview);
      }
    });
    setFiles([]);
  }, [files]);

  /**
   * Upload a single file
   */
  const uploadSingleFile = useCallback(
    async (uploadFile: UploadFile) => {
      try {
        setFiles(prev =>
          prev.map(f =>
            f.id === uploadFile.id ? { ...f, status: 'uploading' as const } : f
          )
        );

        const { api } = await import('@/lib/api/client');
        const formData = new FormData();
        formData.append('file', uploadFile.file);

        await api.post('/images/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent: AxiosProgressEvent) => {
            const progress = progressEvent.loaded / (progressEvent.total || 1);

            setFiles(prev =>
              prev.map(f =>
                f.id === uploadFile.id
                  ? {
                    ...f,
                    progress: Math.round(progress * 100),
                  }
                  : f
              )
            );
          },
        });

        // Mark as completed
        setFiles(prev =>
          prev.map(f =>
            f.id === uploadFile.id ? { ...f, status: 'completed' } : f
          )
        );
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : 'Upload failed';
        setFiles(prev =>
          prev.map(f =>
            f.id === uploadFile.id
              ? { ...f, status: 'error', error: errorMessage }
              : f
          )
        );
        showError(`Failed to upload ${uploadFile.file.name}`);
      }
    },
    [showError]
  );

  /**
   * Upload all pending files
   */
  const uploadAll = useCallback(async () => {
    const pendingFiles = files.filter(f => f.status === 'pending');
    if (pendingFiles.length === 0) {
      showError('No files to upload');
      return;
    }

    setIsUploading(true);

    try {
      // Upload each file sequentially
      for (const uploadFile of pendingFiles) {
        await uploadSingleFile(uploadFile);
      }

      // Count successful uploads
      const successCount = files.filter(f => f.status === 'completed').length;
      const errorCount = files.filter(f => f.status === 'error').length;

      if (errorCount === 0) {
        success(`Successfully uploaded ${successCount} image(s)`);
      } else if (successCount > 0) {
        info(`Uploaded ${successCount} image(s), ${errorCount} failed`);
      }
    } finally {
      setIsUploading(false);
    }
  }, [files, success, showError, info, uploadSingleFile]);

  return {
    files,
    isUploading,
    addFiles,
    removeFile,
    clearAll,
    uploadAll,
  };
}
