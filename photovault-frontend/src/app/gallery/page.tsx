import Link from 'next/link';
import { ProtectedRoute } from '@/components/ui/ProtectedRoute';
import { ImageGallery } from '@/components/gallery/ImageGallery';

/**
 * Gallery Page
 *
 * Example of:
 * - ImageGallery component
 * - Responsive grid layout
 * - Pagination
 * - Loading states with GridSkeleton
 */
export default function GalleryPage() {
  return (
    <ProtectedRoute>
      <div className='max-w-7xl mx-auto px-4 py-8'>
        <div className='flex items-center justify-between mb-8'>
          <div>
            <h1 className='text-3xl font-bold text-gray-900 mb-2'>
              Your Gallery
            </h1>
            <p className='text-gray-600'>
              Browse and manage all your uploaded images
            </p>
          </div>
          <Link
            href='/upload'
            className='px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium'
          >
            Upload Images
          </Link>
        </div>

        <ImageGallery pageSize={20} />
      </div>
    </ProtectedRoute>
  );
}
