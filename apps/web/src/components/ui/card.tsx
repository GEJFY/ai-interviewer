import { cn } from '@/lib/cn';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'glass' | 'elevated';
  hover?: boolean;
}

export function Card({
  className,
  variant = 'default',
  hover = false,
  children,
  ...props
}: CardProps) {
  const variants = {
    default:
      'bg-white dark:bg-surface-850 border border-surface-200 dark:border-surface-700',
    glass: 'glass',
    elevated:
      'bg-white dark:bg-surface-850 border border-surface-200 dark:border-surface-700 shadow-lg dark:shadow-surface-950/50',
  };

  return (
    <div
      className={cn(
        'rounded-xl transition-all duration-300',
        variants[variant],
        hover && 'hover:border-accent-500/30 hover:shadow-lg hover:shadow-accent-500/5 dark:hover:shadow-accent-500/10',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('px-6 py-4', className)} {...props}>
      {children}
    </div>
  );
}

export function CardContent({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('px-6 py-4', className)} {...props}>
      {children}
    </div>
  );
}

export function CardFooter({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'px-6 py-4 border-t border-surface-200 dark:border-surface-700',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
