'use client';

import React from 'react';
import { cn } from '@/lib/utils/cn';

interface LoadingOverlayProps {
  isLoading: boolean;
  message?: string;
  fullScreen?: boolean;
  className?: string;
}

/**
 * Loading Overlay Component
 * Displays a loading state over content
 */
export const LoadingOverlay: React.FC<LoadingOverlayProps & { children?: React.ReactNode }> = ({
  isLoading,
  message = 'Loading...',
  fullScreen = false,
  className,
  children,
}) => {
  if (!isLoading) {
    return <>{children}</>;
  }

  return (
    <div
      className={cn(
        'flex items-center justify-center bg-black/50 backdrop-blur-sm',
        fullScreen ? 'fixed inset-0 z-50' : 'absolute inset-0 rounded-lg',
        className
      )}
    >
      <div className="text-center">
        <div className="mb-4">
          <div className="mx-auto w-12 h-12 border-4 border-white/30 border-t-white rounded-full animate-spin" />
        </div>
        {message && (
          <p className="text-white text-sm font-medium">{message}</p>
        )}
      </div>
    </div>
  );
};

export interface SkeletonCardProps {
  className?: string;
  height?: string;
  count?: number;
}

/**
 * Skeleton Card Component
 * Enhanced loading placeholder for cards
 */
export const SkeletonCard: React.FC<SkeletonCardProps> = ({
  className,
  height = 'h-48',
  count = 1,
}) => {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={cn(
            'bg-white/10 rounded-lg animate-pulse border border-white/10',
            height,
            className
          )}
        />
      ))}
    </>
  );
};

interface SkeletonLineProps {
  count?: number;
  className?: string;
  width?: string;
}

/**
 * Skeleton Line Component
 * For text loading placeholders
 */
export const SkeletonLine: React.FC<SkeletonLineProps> = ({
  count = 1,
  className,
  width = 'w-full',
}) => {
  return (
    <div className="space-y-2">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={cn(
            'h-4 bg-white/10 rounded animate-pulse',
            i === count - 1 && 'w-3/4',
            width,
            className
          )}
        />
      ))}
    </div>
  );
};

interface GridSkeletonProps {
  columns?: number;
  rows?: number;
  className?: string;
}

/**
 * Grid Skeleton Component
 * Loading state for grid layouts
 */
export const GridSkeleton: React.FC<GridSkeletonProps> = ({
  columns = 3,
  rows = 2,
  className,
}) => {
  return (
    <div
      // eslint-disable-next-line
      className={cn(
        `grid gap-4`,
        `grid-cols-${columns}`,
        className
      )}
      style={{
        gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`,
      }}
    >
      {Array.from({ length: columns * rows }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
};
