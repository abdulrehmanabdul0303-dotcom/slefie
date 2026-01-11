'use client';

import { ReactNode } from 'react';
import { ToastContainer } from '@/components/ui/ToastContainer';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { ProtectedRoute } from '@/components/ui/ProtectedRoute';

interface ProtectedLayoutProps {
  children: ReactNode;
}

/**
 * Protected Layout Wrapper
 * Wraps protected pages with auth guard, error boundary, and toasts
 */
export const ProtectedLayout: React.FC<ProtectedLayoutProps> = ({ children }) => {
  return (
    <ErrorBoundary>
      <ProtectedRoute>
        <ToastContainer />
        {children}
      </ProtectedRoute>
    </ErrorBoundary>
  );
};
