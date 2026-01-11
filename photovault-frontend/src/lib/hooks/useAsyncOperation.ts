import { useState, useCallback } from 'react';

/**
 * Hook for managing async loading states
 * Simplifies async operation state management
 */
export const useAsyncOperation = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const execute = useCallback(async <T,>(
    operation: () => Promise<T>
  ): Promise<T | null> => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await operation();
      setIsLoading(false);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      setIsLoading(false);
      throw error;
    }
  }, []);

  const reset = useCallback(() => {
    setIsLoading(false);
    setError(null);
  }, []);

  return { isLoading, error, execute, reset };
};
