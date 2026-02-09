'use client';

import { useState, useRef, useEffect } from 'react';
import { Globe, ChevronDown, Check } from 'lucide-react';
import { useLocale, Locale } from '@/lib/i18n';
import { cn } from '@/lib/cn';

interface LanguageSelectorProps {
  compact?: boolean;
  className?: string;
}

export function LanguageSelector({
  compact = false,
  className = '',
}: LanguageSelectorProps) {
  const { locale, setLocale, locales, localeNames } = useLocale();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') setIsOpen(false);
    }
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, []);

  const handleSelect = (newLocale: Locale) => {
    setLocale(newLocale);
    setIsOpen(false);
  };

  return (
    <div className={cn('relative', className)} ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'flex items-center gap-2 rounded-lg text-surface-500 hover:text-surface-700 dark:hover:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors',
          compact ? 'p-2' : 'px-3 py-2'
        )}
        aria-label="Select language"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
      >
        <Globe className="w-5 h-5" />
        {!compact && (
          <>
            <span className="text-sm font-medium">{localeNames[locale]}</span>
            <ChevronDown
              className={cn('w-4 h-4 transition-transform', isOpen && 'rotate-180')}
            />
          </>
        )}
      </button>

      {isOpen && (
        <div
          className="absolute right-0 mt-2 py-1 w-40 bg-white dark:bg-surface-850 rounded-lg shadow-lg border border-surface-200 dark:border-surface-700 z-50 animate-scale-in"
          role="listbox"
          aria-label="Language options"
        >
          {locales.map((loc) => (
            <button
              key={loc}
              onClick={() => handleSelect(loc)}
              className={cn(
                'w-full flex items-center justify-between px-4 py-2 text-sm text-left hover:bg-surface-50 dark:hover:bg-surface-800 transition-colors',
                locale === loc
                  ? 'text-accent-500 bg-accent-50 dark:bg-accent-900/20'
                  : 'text-surface-700 dark:text-surface-300'
              )}
              role="option"
              aria-selected={locale === loc}
            >
              <span>{localeNames[loc]}</span>
              {locale === loc && <Check className="w-4 h-4" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default LanguageSelector;
