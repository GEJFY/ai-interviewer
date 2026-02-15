import Link from 'next/link';
import { ChevronRight } from 'lucide-react';
import { cn } from '@/lib/cn';

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
  className?: string;
}

export function Breadcrumb({ items, className }: BreadcrumbProps) {
  return (
    <nav aria-label="パンくずリスト" className={cn('flex items-center gap-1 text-sm', className)}>
      {items.map((item, index) => {
        const isLast = index === items.length - 1;

        return (
          <div key={index} className="flex items-center gap-1">
            {index > 0 && (
              <ChevronRight className="w-4 h-4 text-surface-400 flex-shrink-0" />
            )}
            {isLast || !item.href ? (
              <span className="font-medium text-surface-900 dark:text-surface-50 truncate max-w-48">
                {item.label}
              </span>
            ) : (
              <Link
                href={item.href}
                className="text-surface-500 dark:text-surface-400 hover:text-accent-500 dark:hover:text-accent-400 transition-colors truncate max-w-48"
              >
                {item.label}
              </Link>
            )}
          </div>
        );
      })}
    </nav>
  );
}
