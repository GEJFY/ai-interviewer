'use client';

/**
 * Language selector dropdown component.
 *
 * Allows users to switch between supported languages.
 */

import { useState, useRef, useEffect } from 'react';
import { Globe, ChevronDown, Check } from 'lucide-react';
import { useLocale, Locale } from '@/lib/i18n';

interface LanguageSelectorProps {
  /** Compact mode (icon only) */
  compact?: boolean;
  /** Additional CSS class */
  className?: string;
}

export function LanguageSelector({
  compact = false,
  className = '',
}: LanguageSelectorProps) {
  const { locale, setLocale, locales, localeNames } = useLocale();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
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

  // Close on escape key
  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    }

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, []);

  const handleSelect = (newLocale: Locale) => {
    setLocale(newLocale);
    setIsOpen(false);
  };

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`
          flex items-center gap-2 px-3 py-2 rounded-lg
          text-secondary-600 hover:bg-secondary-100
          transition-colors duration-200
          ${compact ? 'p-2' : ''}
        `}
        aria-label="Select language"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
      >
        <Globe className="w-5 h-5" />
        {!compact && (
          <>
            <span className="text-sm font-medium">{localeNames[locale]}</span>
            <ChevronDown
              className={`w-4 h-4 transition-transform ${
                isOpen ? 'rotate-180' : ''
              }`}
            />
          </>
        )}
      </button>

      {isOpen && (
        <div
          className="
            absolute right-0 mt-2 py-1 w-40
            bg-white rounded-lg shadow-lg border border-secondary-200
            z-50 animate-in fade-in slide-in-from-top-2 duration-200
          "
          role="listbox"
          aria-label="Language options"
        >
          {locales.map((loc) => (
            <button
              key={loc}
              onClick={() => handleSelect(loc)}
              className={`
                w-full flex items-center justify-between
                px-4 py-2 text-sm text-left
                hover:bg-secondary-50 transition-colors
                ${locale === loc ? 'text-primary-600 bg-primary-50' : 'text-secondary-700'}
              `}
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
