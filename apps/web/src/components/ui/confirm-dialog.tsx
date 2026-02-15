'use client';

import { AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/cn';
import { Modal, ModalBody, ModalFooter } from './modal';
import { Button } from './button';

interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'warning' | 'default';
  isLoading?: boolean;
}

export function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = '確認',
  cancelLabel = 'キャンセル',
  variant = 'default',
  isLoading = false,
}: ConfirmDialogProps) {
  const iconColors = {
    danger: 'text-red-500 bg-red-500/10',
    warning: 'text-amber-500 bg-amber-500/10',
    default: 'text-surface-500 bg-surface-100 dark:bg-surface-800',
  };

  const buttonVariant = variant === 'danger' ? 'danger' : 'accent';

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} size="sm">
      <ModalBody>
        <div className="flex gap-4">
          <div className={cn('p-2 rounded-lg h-fit flex-shrink-0', iconColors[variant])}>
            <AlertTriangle className="w-5 h-5" />
          </div>
          <p className="text-sm text-surface-600 dark:text-surface-300">
            {message}
          </p>
        </div>
      </ModalBody>
      <ModalFooter>
        <Button variant="outline" onClick={onClose} disabled={isLoading}>
          {cancelLabel}
        </Button>
        <Button
          variant={buttonVariant}
          onClick={onConfirm}
          isLoading={isLoading}
        >
          {confirmLabel}
        </Button>
      </ModalFooter>
    </Modal>
  );
}
