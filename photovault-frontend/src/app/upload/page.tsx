import { ProtectedRoute } from '@/components/ui/ProtectedRoute';
import { ToastContainer } from '@/components/ui/ToastContainer';
import { ImageUploadWidget } from '@/components/images/ImageUploadWidget';

/**
 * Image Upload Page
 *
 * Example of:
 * - ImageUploadWidget component
 * - Drag-drop file upload
 * - Progress tracking
 * - Toast notifications
 */
export default function UploadPage() {
  return (
    <ProtectedRoute>
      <ToastContainer />
      <div className='max-w-4xl mx-auto px-4 py-8'>
        <div className='mb-8'>
          <h1 className='text-3xl font-bold text-gray-900 mb-2'>
            Upload Images
          </h1>
          <p className='text-gray-600'>
            Add new photos to your PhotoVault. You can drag and drop files here
            or click to browse.
          </p>
        </div>

        <ImageUploadWidget />
      </div>
    </ProtectedRoute>
  );
}
