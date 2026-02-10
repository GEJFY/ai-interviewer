import { cn } from '@/lib/cn';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export function Input({
  className,
  label,
  error,
  helperText,
  id,
  ...props
}: InputProps) {
  const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-2"
        >
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={cn(
          'w-full px-4 py-2.5 border rounded-lg transition-all duration-200',
          'bg-white dark:bg-surface-800',
          'text-surface-900 dark:text-surface-100',
          'placeholder:text-surface-400 dark:placeholder:text-surface-500',
          'focus:outline-none focus:ring-2 focus:ring-accent-500/50 focus:border-accent-500',
          'disabled:bg-surface-50 disabled:text-surface-400 disabled:cursor-not-allowed dark:disabled:bg-surface-900 dark:disabled:text-surface-600',
          error
            ? 'border-red-500 focus:ring-red-500/50 focus:border-red-500'
            : 'border-surface-300 dark:border-surface-600',
          className
        )}
        {...props}
      />
      {error && <p className="mt-1 text-sm text-red-500">{error}</p>}
      {helperText && !error && (
        <p className="mt-1 text-sm text-surface-500 dark:text-surface-400">{helperText}</p>
      )}
    </div>
  );
}
