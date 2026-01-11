'use client';

import React, { ReactNode } from 'react';
import { Button } from './ui';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    console.error('ErrorBoundary caught:', error, errorInfo);
    // In production, log error to service like Sentry
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: undefined });
    window.location.href = '/dashboard';
  };

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center min-h-screen bg-linear-to-br from-slate-900 via-slate-800 to-slate-900 px-4">
          <div className="max-w-md w-full">
            {/* Glass morphism card */}
            <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-8 shadow-2xl">
              {/* Icon */}
              <div className="flex justify-center mb-6">
                <div className="w-16 h-16 bg-linear-to-br from-red-500/30 to-rose-500/30 rounded-full flex items-center justify-center border border-red-500/50">
                  <svg
                    className="w-8 h-8 text-red-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 9v2m0 4v2m0 0v-2m0 2v2m0-4v2m0-4v2m0 4H9m3 0h3"
                    />
                  </svg>
                </div>
              </div>

              {/* Content */}
              <h1 className="text-2xl font-bold text-center text-white mb-2">
                Something went wrong
              </h1>
              <p className="text-center text-gray-300 mb-6 text-sm">
                We encountered an unexpected error. Please try again or return to the dashboard.
              </p>

              {/* Error details (dev only) */}
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6">
                  <p className="text-xs text-red-300 font-mono wrap-break-word">
                    {this.state.error.message}
                  </p>
                </div>
              )}

              {/* Buttons */}
              <div className="flex gap-3">
                <Button
                  variant="secondary"
                  fullWidth
                  onClick={() => window.location.reload()}
                >
                  Reload Page
                </Button>
                <Button
                  variant="primary"
                  fullWidth
                  onClick={this.handleReset}
                >
                  Go to Dashboard
                </Button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
