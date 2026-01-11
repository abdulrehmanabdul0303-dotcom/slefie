'use client';

import React, { useCallback, useRef, useState } from 'react';
import { Upload, X, CheckCircle, AlertCircle } from 'lucide-react';
import Image from 'next/image';
import { useImageUpload, UploadFile } from '@/lib/hooks/useImageUpload';

/**
 * Image Upload Widget with drag-drop, preview, and progress tracking
 *
 * @example
 * ```tsx
 * import { ImageUploadWidget } from '@/components/images/ImageUploadWidget';
 *
 * export default function UploadPage() {
 *   return <ImageUploadWidget />;
 * }
 * ```
 */
export function ImageUploadWidget() {
  const { files, isUploading, addFiles, removeFile, clearAll, uploadAll } =
    useImageUpload();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragOver(false);

      const droppedFiles = Array.from(e.dataTransfer.files);
      addFiles(droppedFiles);
    },
    [addFiles]
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) {
        const selectedFiles = Array.from(e.target.files);
        addFiles(selectedFiles);
        // Reset input
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }
    },
    [addFiles]
  );

  const handleBrowseClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleUpload = useCallback(async () => {
    await uploadAll();
  }, [uploadAll]);

  const totalSize = files.reduce((sum, f) => sum + f.file.size, 0);
  const uploadedSize = files
    .filter(f => f.status !== 'error')
    .reduce((sum, f) => sum + (f.file.size * f.progress) / 100, 0);
  const uploadProgress =
    totalSize > 0 ? Math.round((uploadedSize / totalSize) * 100) : 0;

  const completedCount = files.filter(f => f.status === 'completed').length;
  const errorCount = files.filter(f => f.status === 'error').length;
  const pendingCount = files.filter(f => f.status === 'pending').length;

  return (
    <div className='space-y-6'>
      {/* Main Upload Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          relative rounded-lg border-2 border-dashed transition-colors
          ${
            isDragOver
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 bg-gray-50 hover:border-gray-400'
          }
        `}
      >
        <div className='p-12 text-center'>
          <Upload className='mx-auto h-12 w-12 text-gray-400 mb-4' />
          <h3 className='text-lg font-medium text-gray-900 mb-2'>
            Drop images here
          </h3>
          <p className='text-sm text-gray-500 mb-4'>
            or{' '}
            <button
              onClick={handleBrowseClick}
              className='text-blue-600 hover:text-blue-700 font-medium'
              aria-label='Browse files from computer'
              title='Select images from your device'
            >
              browse from your computer
            </button>
          </p>
          <p className='text-xs text-gray-400'>
            Supported formats: JPEG, PNG, WebP, GIF • Max 50MB per file
          </p>
          <input
            ref={fileInputRef}
            type='file'
            multiple
            accept='image/*'
            onChange={handleFileInput}
            className='hidden'
            aria-label='Select images to upload'
          />
        </div>
      </div>

      {/* Upload Statistics */}
      {files.length > 0 && (
        <div className='grid grid-cols-4 gap-4'>
          <div className='bg-blue-50 rounded-lg p-4'>
            <div className='text-2xl font-bold text-blue-600'>
              {files.length}
            </div>
            <div className='text-sm text-gray-600'>Total Files</div>
          </div>
          <div className='bg-green-50 rounded-lg p-4'>
            <div className='text-2xl font-bold text-green-600'>
              {completedCount}
            </div>
            <div className='text-sm text-gray-600'>Uploaded</div>
          </div>
          <div className='bg-yellow-50 rounded-lg p-4'>
            <div className='text-2xl font-bold text-yellow-600'>
              {pendingCount}
            </div>
            <div className='text-sm text-gray-600'>Pending</div>
          </div>
          <div className='bg-red-50 rounded-lg p-4'>
            <div className='text-2xl font-bold text-red-600'>{errorCount}</div>
            <div className='text-sm text-gray-600'>Failed</div>
          </div>
        </div>
      )}

      {/* Overall Progress */}
      {files.length > 0 && isUploading && (
        <div className='space-y-2'>
          <div className='flex justify-between text-sm'>
            <span className='font-medium text-gray-700'>Overall Progress</span>
            <span className='text-gray-600'>{uploadProgress}%</span>
          </div>
          <div className='w-full bg-gray-200 rounded-full h-2'>
            {/* eslint-disable-next-line @next/next/no-style-jsx-in-document */}
            <div
              className='bg-blue-600 h-2 rounded-full transition-all duration-300'
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* File List */}
      {files.length > 0 && (
        <div className='space-y-3 max-h-96 overflow-y-auto'>
          {files.map(file => (
            <FileUploadItem
              key={file.id}
              file={file}
              onRemove={() => removeFile(file.id)}
            />
          ))}
        </div>
      )}

      {/* Action Buttons */}
      {files.length > 0 && (
        <div className='flex gap-3'>
          <button
            onClick={handleUpload}
            disabled={isUploading || files.every(f => f.status !== 'pending')}
            className={`
              flex-1 px-4 py-2 rounded-lg font-medium transition-colors
              ${
                isUploading || files.every(f => f.status !== 'pending')
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }
            `}
          >
            {isUploading ? `Uploading... ${uploadProgress}%` : 'Upload Files'}
          </button>
          <button
            onClick={clearAll}
            disabled={isUploading}
            className={`
              px-4 py-2 rounded-lg font-medium transition-colors
              ${
                isUploading
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }
            `}
          >
            Clear All
          </button>
        </div>
      )}
    </div>
  );
}

/**
 * Individual file upload item with preview and progress
 */
interface FileUploadItemProps {
  file: UploadFile;
  onRemove: () => void;
}

function FileUploadItem({ file, onRemove }: FileUploadItemProps) {
  const sizeInMB = (file.file.size / (1024 * 1024)).toFixed(2);

  return (
    <div className='flex gap-3 p-3 bg-gray-50 rounded-lg'>
      {/* Preview */}
      <div className='relative h-16 w-16 shrink-0 rounded-md bg-gray-200 overflow-hidden'>
        <Image
          src={file.preview}
          alt={file.file.name}
          fill
          className='object-cover'
        />
        {file.status === 'completed' && (
          <div className='absolute inset-0 bg-green-500/20 flex items-center justify-center'>
            <CheckCircle className='h-6 w-6 text-green-600' />
          </div>
        )}
        {file.status === 'error' && (
          <div className='absolute inset-0 bg-red-500/20 flex items-center justify-center'>
            <AlertCircle className='h-6 w-6 text-red-600' />
          </div>
        )}
      </div>

      {/* Details */}
      <div className='flex-1 min-w-0'>
        <div className='flex items-start justify-between'>
          <div className='flex-1'>
            <p className='font-medium text-gray-900 truncate'>
              {file.file.name}
            </p>
            <p className='text-sm text-gray-500'>
              {sizeInMB}MB •{' '}
              <span className='capitalize'>
                {file.status === 'uploading' ? 'uploading' : file.status}
              </span>
            </p>
          </div>
          {(file.status === 'pending' || file.status === 'error') && (
            <button
              onClick={onRemove}
              className='p-1 hover:bg-gray-200 rounded transition-colors'
              aria-label={`Remove ${file.file.name}`}
              title={`Remove ${file.file.name}`}
            >
              <X className='h-4 w-4 text-gray-500' />
            </button>
          )}
        </div>

        {/* Progress Bar */}
        {(file.status === 'uploading' ||
          (file.status === 'completed' && file.progress < 100)) && (
          <div className='mt-2'>
            <div className='flex justify-between text-xs text-gray-600 mb-1'>
              <span>Progress</span>
              <span>{file.progress}%</span>
            </div>
            <div className='w-full bg-gray-200 rounded-full h-1.5'>
              {/* eslint-disable-next-line @next/next/no-style-jsx-in-document */}
              <div
                className='bg-blue-600 h-1.5 rounded-full transition-all duration-300'
                style={{ width: `${file.progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Error Message */}
        {file.status === 'error' && file.error && (
          <p className='mt-2 text-xs text-red-600'>{file.error}</p>
        )}
      </div>
    </div>
  );
}
