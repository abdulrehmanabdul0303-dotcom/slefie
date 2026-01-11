'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useAsyncOperation } from '@/lib/hooks/useAsyncOperation';
import { GridSkeleton } from '@/components/ui/LoadingComponents';
import axios from 'axios';

interface ImageData {
  id: string;
  filename: string;
  original_filename: string;
  upload_date: string;
  file_size: number;
  thumbnail_url?: string;
  image_url: string;
  width?: number;
  height?: number;
  mime_type: string;
}

interface ImageListResponse {
  results: ImageData[];
  count: number;
  next: string | null;
  previous: string | null;
}

interface ImageGalleryProps {
  pageSize?: number;
}

/**
 * Responsive image gallery with lazy loading and pagination
 *
 * @example
 * ```tsx
 * import { ImageGallery } from '@/components/gallery/ImageGallery';
 *
 * export default function GalleryPage() {
 *   return (
 *     <ProtectedRoute>
 *       <ImageGallery pageSize={20} />
 *     </ProtectedRoute>
 *   );
 * }
 * ```
 */
export function ImageGallery({ pageSize = 20 }: ImageGalleryProps) {
  const [images, setImages] = useState<ImageData[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const { execute, isLoading } = useAsyncOperation();

  useEffect(() => {
    const load = async () => {
      try {
        const data = await execute(async () => {
          const response = await axios.get<ImageListResponse>('/api/images/', {
            params: { page, page_size: pageSize },
            withCredentials: true,
          });
          return response.data;
        });
        if (data) {
          setImages(data.results);
          setTotal(data.count);
        }
      } catch (error) {
        console.error('Failed to load images:', error);
      }
    };

    load();
  }, [page, pageSize, execute]);

  if (isLoading && images.length === 0) {
    return <GridSkeleton />;
  }

  if (images.length === 0) {
    return (
      <div className='flex flex-col items-center justify-center py-12'>
        <div className='text-gray-400 mb-4'>
          <svg
            className='h-12 w-12'
            fill='none'
            stroke='currentColor'
            viewBox='0 0 24 24'
          >
            <path
              strokeLinecap='round'
              strokeLinejoin='round'
              strokeWidth={2}
              d='M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z'
            />
          </svg>
        </div>
        <h3 className='text-lg font-medium text-gray-900 mb-1'>
          No images yet
        </h3>
        <p className='text-sm text-gray-500 mb-4'>
          Upload your first image to get started
        </p>
        <Link
          href='/upload'
          className='text-blue-600 hover:text-blue-700 font-medium'
        >
          Upload Images
        </Link>
      </div>
    );
  }

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className='space-y-6'>
      {/* Grid */}
      <div className='grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4'>
        {images.map(image => (
          <ImageCard key={image.id} image={image} />
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className='flex items-center justify-center gap-2'>
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className={`
              px-4 py-2 rounded-lg font-medium transition-colors
              ${
                page === 1
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }
            `}
          >
            Previous
          </button>

          <div className='flex items-center gap-2'>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map(p => (
              <button
                key={p}
                onClick={() => setPage(p)}
                className={`
                  px-3 py-2 rounded-lg font-medium transition-colors
                  ${
                    page === p
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }
                `}
              >
                {p}
              </button>
            ))}
          </div>

          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className={`
              px-4 py-2 rounded-lg font-medium transition-colors
              ${
                page === totalPages
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }
            `}
          >
            Next
          </button>
        </div>
      )}

      {/* Status */}
      <div className='text-center text-sm text-gray-600'>
        Showing {(page - 1) * pageSize + 1}-{Math.min(page * pageSize, total)} of{' '}
        {total} images
      </div>
    </div>
  );
}

/**
 * Individual image card in gallery
 */
interface ImageCardProps {
  image: ImageData;
}

function ImageCard({ image }: ImageCardProps) {
  const [imageError, setImageError] = useState(false);

  return (
    <Link href={`/images/${image.id}`}>
      <div className='group relative aspect-square rounded-lg overflow-hidden bg-gray-100 cursor-pointer'>
        {!imageError ? (
          <Image
            src={image.thumbnail_url || image.image_url}
            alt={image.original_filename}
            className='h-full w-full object-cover transition-transform duration-300 group-hover:scale-105'
            fill
            sizes='(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 25vw'
            onError={() => setImageError(true)}
          />
        ) : (
          <div className='h-full w-full flex items-center justify-center bg-gray-200'>
            <svg
              className='h-8 w-8 text-gray-400'
              fill='none'
              stroke='currentColor'
              viewBox='0 0 24 24'
            >
              <path
                strokeLinecap='round'
                strokeLinejoin='round'
                strokeWidth={2}
                d='M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z'
              />
            </svg>
          </div>
        )}

        {/* Overlay */}
        <div className='absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors duration-300 flex items-center justify-center'>
          <div className='opacity-0 group-hover:opacity-100 transition-opacity duration-300'>
            <svg
              className='h-8 w-8 text-white'
              fill='none'
              stroke='currentColor'
              viewBox='0 0 24 24'
            >
              <path
                strokeLinecap='round'
                strokeLinejoin='round'
                strokeWidth={2}
                d='M15 12a3 3 0 11-6 0 3 3 0 016 0z'
              />
              <path
                strokeLinecap='round'
                strokeLinejoin='round'
                strokeWidth={2}
                d='M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z'
              />
            </svg>
          </div>
        </div>

        {/* Info Badge */}
        <div className='absolute bottom-0 left-0 right-0 bg-linear-to-t from-black/50 to-transparent p-2 translate-y-full group-hover:translate-y-0 transition-transform duration-300'>
          <p className='text-white text-xs truncate'>
            {image.original_filename}
          </p>
        </div>
      </div>
    </Link>
  );
}
