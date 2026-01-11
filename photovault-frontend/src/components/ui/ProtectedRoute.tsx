'use client';

import { useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/hooks/useAuth';
import { Spinner } from './Spinner';

interface ProtectedRouteProps {
  children: ReactNode;
}

/**
 * Protected Route Wrapper
 * Ensures user is authenticated before rendering content
 */
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const router = useRouter();
  const { token, user, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && !token) {
      router.push('/auth/login');
    }
  }, [token, isLoading, router]);

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Spinner size="lg" className="mx-auto mb-4" />
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  // Redirect if not authenticated
  if (!token) {
    return null;
  }

  // Render protected content
  return <>{children}</>;
};
