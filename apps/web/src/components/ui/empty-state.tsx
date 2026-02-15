import type { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/cn';
import { Button } from './button';

interface EmptyStateAction {
  label: string;
  onClick?: () => void;
  href?: string;
}

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: EmptyStateAction;
  variant?: 'default' | 'search';
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  variant = 'default',
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-12 px-6 text-center',
        className
      )}
    >
      <div
        className={cn(
          'p-4 rounded-2xl mb-4',
          variant === 'search'
            ? 'bg-blue-500/10'
            : 'bg-surface-100 dark:bg-surface-800'
        )}
      >
        <Icon
          className={cn(
            'w-8 h-8',
            variant === 'search'
              ? 'text-blue-500'
              : 'text-surface-400 dark:text-surface-500'
          )}
        />
      </div>

      <h3 className="text-lg font-semibold text-surface-900 dark:text-surface-50 mb-2">
        {title}
      </h3>

      <p className="text-sm text-surface-500 dark:text-surface-400 max-w-sm mb-6">
        {description}
      </p>

      {action && (
        action.href ? (
          <a href={action.href}>
            <Button variant="accent" size="sm">
              {action.label}
            </Button>
          </a>
        ) : (
          <Button variant="accent" size="sm" onClick={action.onClick}>
            {action.label}
          </Button>
        )
      )}
    </div>
  );
}
