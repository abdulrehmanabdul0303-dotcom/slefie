'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/hooks/useAuth';
import { ErrorBoundary, Sidebar, Topbar } from '@/components';
import { Spinner } from '@/components/ui/Spinner';

export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}): React.ReactNode {
  const router = useRouter();
  const { token, isLoading } = useAuth();

  useEffect(() => {
    // Redirect to login if not authenticated
    if (!isLoading && !token) {
      router.push('/auth/login');
    }
  }, [token, isLoading, router]);

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center">
        <div className="text-center">
          <Spinner size="lg" className="mx-auto mb-4" />
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't render protected content if not authenticated
  if (!token) {
    return null;
  }

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-slate-950 text-white">
        <div className="flex">
          {/* Sidebar */}
          <Sidebar />

          {/* Main content */}
          <div className="flex-1 flex flex-col md:ml-64">
            {/* Topbar */}
            <Topbar userName="User" />

            {/* Page content */}
            <main className="flex-1 overflow-auto bg-gradient-to-b from-slate-900 to-slate-950 p-4 md:p-6">
              {children}
            </main>
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
}
