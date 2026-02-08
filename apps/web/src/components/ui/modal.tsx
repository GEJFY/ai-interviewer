'use client';

import { Fragment, ReactNode } from 'react';
import { X } from 'lucide-react';
import { clsx } from 'clsx';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export function Modal({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
}: ModalProps) {
  if (!isOpen) return null;

  const sizes = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div
          className={clsx(
            'relative w-full bg-white rounded-xl shadow-xl transform transition-all',
            sizes[size]
          )}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          {title && (
            <div className="flex items-center justify-between px-6 py-4 border-b border-secondary-200">
              <h2 className="text-lg font-semibold text-secondary-900">
                {title}
              </h2>
              <button
                onClick={onClose}
                className="p-1 text-secondary-400 hover:text-secondary-600 hover:bg-secondary-100 rounded-lg transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          )}

          {/* Content */}
          <div className={clsx(!title && 'pt-6')}>{children}</div>
        </div>
      </div>
    </div>
  );
}

interface ModalBodyProps {
  children: ReactNode;
  className?: string;
}

export function ModalBody({ children, className }: ModalBodyProps) {
  return <div className={clsx('px-6 py-4', className)}>{children}</div>;
}

interface ModalFooterProps {
  children: ReactNode;
  className?: string;
}

export function ModalFooter({ children, className }: ModalFooterProps) {
  return (
    <div
      className={clsx(
        'px-6 py-4 border-t border-secondary-200 flex justify-end gap-3',
        className
      )}
    >
      {children}
    </div>
  );
}
