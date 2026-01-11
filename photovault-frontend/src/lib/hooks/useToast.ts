import { useCallback } from 'react';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
  duration?: number;
}

// Global toast store
let toastListeners: ((toast: Toast) => void)[] = [];
let toastId = 0;

export const useToast = () => {
  const addToast = useCallback((message: string, type: ToastType = 'info', duration = 3000) => {
    const id = `toast-${++toastId}`;
    const toast: Toast = { id, message, type, duration };
    
    // Notify all listeners
    toastListeners.forEach(listener => listener(toast));
    
    // Auto remove after duration
    if (duration > 0) {
      setTimeout(() => removeToast(id), duration);
    }
    
    return id;
  }, []);

  const success = useCallback((message: string, duration = 3000) => {
    return addToast(message, 'success', duration);
  }, [addToast]);

  const error = useCallback((message: string, duration = 4000) => {
    return addToast(message, 'error', duration);
  }, [addToast]);

  const info = useCallback((message: string, duration = 3000) => {
    return addToast(message, 'info', duration);
  }, [addToast]);

  const warning = useCallback((message: string, duration = 3500) => {
    return addToast(message, 'warning', duration);
  }, [addToast]);

  return { addToast, success, error, info, warning };
};

export const removeToast = (id: string) => {
  // Notify all listeners to remove this toast
  toastListeners.forEach(listener => listener({ id, message: '', type: 'info', duration: 0 }));
};

export const subscribeToToasts = (listener: (toast: Toast) => void) => {
  toastListeners.push(listener);
  return () => {
    toastListeners = toastListeners.filter(l => l !== listener);
  };
};
