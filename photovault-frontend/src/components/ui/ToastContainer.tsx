'use client';

import { useEffect, useState } from 'react';
import { Toast, subscribeToToasts } from '@/lib/hooks/useToast';

/**
 * Toast Container Component
 * Displays toast notifications in the top-right corner
 */
export const ToastContainer: React.FC = () => {
  const [toasts, setToasts] = useState<Map<string, Toast>>(new Map());

  useEffect(() => {
    const unsubscribe = subscribeToToasts((toast) => {
      setToasts((prev) => {
        const next = new Map(prev);
        if (toast.message === '') {
          // Remove toast
          next.delete(toast.id);
        } else {
          // Add or update toast
          next.set(toast.id, toast);
        }
        return next;
      });
    });

    return unsubscribe;
  }, []);

  return (
    <div className="fixed top-4 right-4 z-50 space-y-3 max-w-sm">
      {Array.from(toasts.values()).map((toast) => (
        <ToastItem key={toast.id} toast={toast} />
      ))}
    </div>
  );
};

interface ToastItemProps {
  toast: Toast;
}

const ToastItem: React.FC<ToastItemProps> = ({ toast }) => {
  const typeConfig = {
    success: {
      bg: 'bg-green-500/90',
      border: 'border-green-400/50',
      icon: '✓',
      iconClass: 'text-green-200',
    },
    error: {
      bg: 'bg-red-500/90',
      border: 'border-red-400/50',
      icon: '✕',
      iconClass: 'text-red-200',
    },
    info: {
      bg: 'bg-blue-500/90',
      border: 'border-blue-400/50',
      icon: 'ⓘ',
      iconClass: 'text-blue-200',
    },
    warning: {
      bg: 'bg-amber-500/90',
      border: 'border-amber-400/50',
      icon: '⚠',
      iconClass: 'text-amber-200',
    },
  };

  const config = typeConfig[toast.type];

  return (
    <div
      className={`
        flex items-center gap-3 px-4 py-3 rounded-lg
        ${config.bg} border ${config.border}
        backdrop-blur-md shadow-lg text-white text-sm
        animate-in fade-in slide-in-from-top-2 duration-300
      `}
    >
      <span className={`shrink-0 font-bold text-lg ${config.iconClass}`}>
        {config.icon}
      </span>
      <p className="flex-1">{toast.message}</p>
    </div>
  );
};
