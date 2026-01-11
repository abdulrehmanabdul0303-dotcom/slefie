import React from 'react';
import { cn } from '@/lib/utils/cn';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helpText?: string;
}

/**
 * Input Component
 * Reusable form input with label and error handling
 */
export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, helpText, type = 'text', ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-white mb-2">
            {label}
          </label>
        )}
        <input
          type={type}
          className={cn(
            'w-full px-4 py-2.5 rounded-xl glass text-white placeholder:text-white/50',
            'focus:outline-none focus:ring-2 focus:ring-white/20',
            'transition-all duration-200',
            error && 'ring-2 ring-red-500/50',
            className
          )}
          ref={ref}
          {...props}
        />
        {error && <p className="text-red-400 text-sm mt-1">{error}</p>}
        {helpText && !error && <p className="text-white/50 text-sm mt-1">{helpText}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';
