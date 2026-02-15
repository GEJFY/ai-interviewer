import { cn } from '@/lib/cn';

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        'animate-pulse rounded-lg bg-surface-200 dark:bg-surface-700',
        className
      )}
    />
  );
}

export function SkeletonCard({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        'rounded-xl border border-surface-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-6',
        className
      )}
    >
      <div className="animate-pulse">
        <div className="h-6 bg-surface-200 dark:bg-surface-700 rounded w-3/4 mb-4" />
        <div className="h-4 bg-surface-200 dark:bg-surface-700 rounded w-1/2 mb-2" />
        <div className="h-4 bg-surface-200 dark:bg-surface-700 rounded w-1/3" />
      </div>
    </div>
  );
}

interface SkeletonListItemProps {
  count?: number;
  className?: string;
}

export function SkeletonListItem({ count = 1, className }: SkeletonListItemProps) {
  return (
    <div className={cn('space-y-3', className)}>
      {[...Array(count)].map((_, i) => (
        <div
          key={i}
          className="flex items-center gap-4 p-4 rounded-xl border border-surface-200 dark:border-surface-800 bg-white dark:bg-surface-900"
        >
          <div className="animate-pulse flex items-center gap-4 w-full">
            <div className="h-10 w-10 rounded-lg bg-surface-200 dark:bg-surface-700 flex-shrink-0" />
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-surface-200 dark:bg-surface-700 rounded w-1/3" />
              <div className="h-3 bg-surface-200 dark:bg-surface-700 rounded w-1/2" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
