'use client';

import { useState, useRef, useCallback } from 'react';
import { cn } from '@/lib/cn';

export interface TooltipProps {
  content: string;
  children: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  className?: string;
  delay?: number;
}

export function Tooltip({
  content,
  children,
  position = 'top',
  className,
  delay = 300,
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const show = useCallback(() => {
    timeoutRef.current = setTimeout(() => setIsVisible(true), delay);
  }, [delay]);

  const hide = useCallback(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setIsVisible(false);
  }, []);

  const positionClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  };

  const arrowClasses = {
    top: 'top-full left-1/2 -translate-x-1/2 border-t-surface-800 dark:border-t-surface-200 border-x-transparent border-b-transparent',
    bottom: 'bottom-full left-1/2 -translate-x-1/2 border-b-surface-800 dark:border-b-surface-200 border-x-transparent border-t-transparent',
    left: 'left-full top-1/2 -translate-y-1/2 border-l-surface-800 dark:border-l-surface-200 border-y-transparent border-r-transparent',
    right: 'right-full top-1/2 -translate-y-1/2 border-r-surface-800 dark:border-r-surface-200 border-y-transparent border-l-transparent',
  };

  return (
    <span className="relative inline-flex" onMouseEnter={show} onMouseLeave={hide} onFocus={show} onBlur={hide}>
      {children}
      {isVisible && (
        <span
          role="tooltip"
          className={cn(
            'absolute z-50 px-3 py-1.5 text-xs font-medium rounded-lg whitespace-nowrap',
            'bg-surface-800 text-surface-50 dark:bg-surface-200 dark:text-surface-900',
            'shadow-lg animate-fade-in pointer-events-none',
            positionClasses[position],
            className
          )}
        >
          {content}
          <span className={cn('absolute w-0 h-0 border-4', arrowClasses[position])} />
        </span>
      )}
    </span>
  );
}
