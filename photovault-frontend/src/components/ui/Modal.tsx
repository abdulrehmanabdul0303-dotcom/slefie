import React from 'react';
import { cn } from '@/lib/utils/cn';
import { X } from 'lucide-react';

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  closeButton?: boolean;
  className?: string;
}

/**
 * Modal Component
 * Reusable modal dialog with overlay
 */
export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  closeButton = true,
  className,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Overlay */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal Content */}
      <div
        className={cn(
          'relative glass rounded-2xl p-6 max-w-md w-full',
          'animate-in fade-in zoom-in duration-200',
          className
        )}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        {(title || closeButton) && (
          <div className="flex items-center justify-between mb-4">
            {title && <h2 className="text-xl font-semibold text-white">{title}</h2>}
            {closeButton && (
              <button
                onClick={onClose}
                className="text-white/60 hover:text-white transition-colors"
              >
                <X size={24} />
              </button>
            )}
          </div>
        )}

        {/* Body */}
        <div className="text-white">{children}</div>
      </div>
    </div>
  );
};

Modal.displayName = 'Modal';
