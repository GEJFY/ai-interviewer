import { cn } from '@/lib/cn';
import { ChevronDown } from 'lucide-react';

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  helperText?: string;
  options: SelectOption[];
  placeholder?: string;
}

export function Select({
  className,
  label,
  error,
  helperText,
  options,
  placeholder,
  id,
  ...props
}: SelectProps) {
  const selectId = id || label?.toLowerCase().replace(/\s+/g, '-');

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={selectId}
          className="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-2"
        >
          {label}
        </label>
      )}
      <div className="relative">
        <select
          id={selectId}
          className={cn(
            'w-full px-4 py-2.5 border rounded-lg appearance-none cursor-pointer transition-all duration-200',
            'bg-white dark:bg-surface-800',
            'text-surface-900 dark:text-surface-100',
            'focus:outline-none focus:ring-2 focus:ring-accent-500/50 focus:border-accent-500',
            'disabled:bg-surface-50 disabled:text-surface-400 disabled:cursor-not-allowed dark:disabled:bg-surface-900 dark:disabled:text-surface-600',
            error
              ? 'border-red-500 focus:ring-red-500/50 focus:border-red-500'
              : 'border-surface-300 dark:border-surface-600',
            className
          )}
          {...props}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-surface-400 pointer-events-none" />
      </div>
      {error && <p className="mt-1 text-sm text-red-500">{error}</p>}
      {helperText && !error && (
        <p className="mt-1 text-sm text-surface-500 dark:text-surface-400">{helperText}</p>
      )}
    </div>
  );
}
