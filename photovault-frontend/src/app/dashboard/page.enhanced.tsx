'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';
import { motion } from 'framer-motion';
import { ProtectedRoute } from '@/components/ui/ProtectedRoute';
import { ToastContainer } from '@/components/ui/ToastContainer';
import { GridSkeleton } from '@/components/ui/LoadingComponents';
import { useToast } from '@/lib/hooks/useToast';
import { useAsyncOperation } from '@/lib/hooks/useAsyncOperation';

/**
 * Example Protected Dashboard Page
 * Demonstrates PHASE 3 UI Foundation integration
 * Features:
 * - Protected route guard
 * - Loading skeletons
 * - Async operations
 * - Toast notifications
 */

interface ImageData {
  id: string;
  name: string;
  url: string;
}

export default function DashboardPage() {
  const [images] = useState<ImageData[]>([]);
  const { success, error: toastError } = useToast();
  const { isLoading, execute } = useAsyncOperation();

  // Simulate loading images
  useEffect(() => {
    const loadImages = async () => {
      try {
        await execute(async () => {
          // In real implementation, fetch from API
          // const res = await fetch('/api/images');
          // const data = await res.json();
          // setImages(data);

          // Simulated delay
          await new Promise((resolve) => setTimeout(resolve, 1000));
          success('Images loaded!');
        });
      } catch (err) {
        toastError(
          err instanceof Error ? err.message : 'Failed to load images'
        );
      }
    };

    loadImages();
  }, [execute, success, toastError]);

  return (
    <ProtectedRoute>
      <ToastContainer />

      <motion.div
        className="min-h-screen bg-black"
        initial="hidden"
        animate="show"
        variants={{
          hidden: { opacity: 0 },
          show: { opacity: 1, transition: { staggerChildren: 0.1 } }
        }}
      >
        {/* Header */}
        <motion.div
          className="p-6 border-b border-white/10"
          variants={{ hidden: { opacity: 0, y: -20 }, show: { opacity: 1, y: 0 } }}
        >
          <h1 className="text-3xl font-bold text-white">Dashboard</h1>
          <p className="text-white/60 mt-2">View and manage your photos</p>
        </motion.div>

        {/* Content */}
        <div className="p-6">
          <motion.div
            className="mb-4"
            variants={{ hidden: { opacity: 0, x: -20 }, show: { opacity: 1, x: 0 } }}
          >
            <h2 className="text-xl font-semibold text-white mb-4">
              Recent Photos
            </h2>
          </motion.div>

          {/* Loading State: Show skeleton grid */}
          {isLoading ? (
            <motion.div variants={{ hidden: { opacity: 0 }, show: { opacity: 1 } }}>
              <GridSkeleton columns={3} rows={2} />
            </motion.div>
          ) : images.length > 0 ? (
            /* Loaded State: Show actual content */
            <motion.div
              className="grid grid-cols-3 gap-4"
              variants={{
                hidden: { opacity: 0 },
                show: { opacity: 1, transition: { staggerChildren: 0.05 } }
              }}
            >
              {images.map((image) => (
                <motion.div
                  key={image.id}
                  className="aspect-square rounded-lg overflow-hidden bg-white/10 relative"
                  variants={{ hidden: { opacity: 0, scale: 0.9 }, show: { opacity: 1, scale: 1 } }}
                  whileHover={{ scale: 1.02 }}
                  transition={{ type: "spring", stiffness: 300, damping: 20 }}
                >
                  <Image
                    src={image.url}
                    alt={image.name}
                    fill
                    className="object-cover"
                  />
                </motion.div>
              ))}
            </motion.div>
          ) : (
            /* Empty State */
            <motion.div
              className="text-center py-12"
              variants={{ hidden: { opacity: 0, scale: 0.95 }, show: { opacity: 1, scale: 1 } }}
            >
              <p className="text-white/60">No photos yet</p>
            </motion.div>
          )}
        </div>
      </motion.div>
    </ProtectedRoute>
  );
}
