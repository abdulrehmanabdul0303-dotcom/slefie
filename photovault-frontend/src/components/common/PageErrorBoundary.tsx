"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertCircle, RefreshCw, Home } from "lucide-react";
import Link from "next/link";

interface Props {
  children: ReactNode;
  pageName?: string;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * Page-level error boundary for individual pages.
 * Prevents one page crash from taking down the entire app.
 */
export class PageErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(`PageErrorBoundary caught an error in ${this.props.pageName || "page"}:`, error, errorInfo);
    this.setState({ errorInfo });
    
    // TODO: Send to error tracking service (Sentry, etc.)
    // Example: Sentry.captureException(error, { contexts: { react: { componentStack: errorInfo.componentStack } } });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-[400px] flex items-center justify-center p-6">
          <div className="max-w-md w-full bg-white border border-red-200 rounded-xl p-6 text-center shadow-sm">
            <div className="flex justify-center mb-4">
              <AlertCircle className="w-12 h-12 text-red-500" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              {this.props.pageName ? `${this.props.pageName} Error` : "Page Error"}
            </h2>
            <p className="text-sm text-gray-600 mb-1">
              Something went wrong on this page.
            </p>
            {this.state.error?.message && (
              <p className="text-xs text-gray-500 mb-4 font-mono bg-gray-50 p-2 rounded">
                {this.state.error.message}
              </p>
            )}
            <div className="flex gap-2 mt-6">
              <button
                onClick={this.handleReset}
                className="flex-1 flex items-center justify-center gap-2 bg-black text-white rounded-md py-2 text-sm hover:bg-gray-800 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Try Again
              </button>
              <Link
                href="/dashboard"
                className="flex-1 flex items-center justify-center gap-2 bg-gray-100 text-gray-700 rounded-md py-2 text-sm hover:bg-gray-200 transition-colors"
              >
                <Home className="w-4 h-4" />
                Go Home
              </Link>
            </div>
            {process.env.NODE_ENV === "development" && this.state.errorInfo && (
              <details className="mt-4 text-left">
                <summary className="text-xs text-gray-500 cursor-pointer">Error Details</summary>
                <pre className="text-xs text-gray-400 mt-2 p-2 bg-gray-50 rounded overflow-auto max-h-40">
                  {this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

