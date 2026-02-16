'use client';

/**
 * Internationalization (i18n) context and hooks.
 *
 * Provides translation functions and locale management for the application.
 */

import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  ReactNode,
} from 'react';
import logger from '@/lib/logger';

// Import locale files
import jaMessages from '@/locales/ja.json';
import enMessages from '@/locales/en.json';
import zhMessages from '@/locales/zh.json';

export type Locale = 'ja' | 'en' | 'zh';

type Messages = typeof jaMessages;
type MessagePath = string;

const messages: Record<Locale, Messages> = {
  ja: jaMessages,
  en: enMessages,
  zh: zhMessages,
};

export const localeNames: Record<Locale, string> = {
  ja: '日本語',
  en: 'English',
  zh: '中文',
};

interface I18nContextValue {
  /** Current locale */
  locale: Locale;
  /** Set the current locale */
  setLocale: (locale: Locale) => void;
  /** Translation function */
  t: (key: MessagePath, params?: Record<string, string | number>) => string;
  /** Available locales */
  locales: Locale[];
  /** Locale display names */
  localeNames: Record<Locale, string>;
}

const I18nContext = createContext<I18nContextValue | null>(null);

const LOCALE_STORAGE_KEY = 'ai-interviewer-locale';

/**
 * Get nested value from object using dot notation path.
 */
function getNestedValue(obj: Record<string, unknown>, path: string): string | undefined {
  const keys = path.split('.');
  let current: unknown = obj;

  for (const key of keys) {
    if (current && typeof current === 'object' && key in current) {
      current = (current as Record<string, unknown>)[key];
    } else {
      return undefined;
    }
  }

  return typeof current === 'string' ? current : undefined;
}

/**
 * Replace parameters in a message string.
 */
function interpolate(
  message: string,
  params?: Record<string, string | number>
): string {
  if (!params) return message;

  return Object.entries(params).reduce((result, [key, value]) => {
    return result.replace(new RegExp(`\\{${key}\\}`, 'g'), String(value));
  }, message);
}

interface I18nProviderProps {
  children: ReactNode;
  defaultLocale?: Locale;
}

/**
 * I18n Provider component.
 *
 * Provides translation context to the application.
 */
export function I18nProvider({
  children,
  defaultLocale = 'ja',
}: I18nProviderProps) {
  const [locale, setLocaleState] = useState<Locale>(defaultLocale);

  // Load saved locale from localStorage on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedLocale = localStorage.getItem(LOCALE_STORAGE_KEY) as Locale | null;
      if (savedLocale && savedLocale in messages) {
        setLocaleState(savedLocale);
      } else {
        // Try to detect browser language
        const browserLang = navigator.language.split('-')[0];
        if (browserLang in messages) {
          setLocaleState(browserLang as Locale);
        }
      }
    }
  }, []);

  // Save locale to localStorage when it changes
  const setLocale = useCallback((newLocale: Locale) => {
    setLocaleState(newLocale);
    if (typeof window !== 'undefined') {
      localStorage.setItem(LOCALE_STORAGE_KEY, newLocale);
    }
  }, []);

  // Translation function
  const t = useCallback(
    (key: MessagePath, params?: Record<string, string | number>): string => {
      const message = getNestedValue(messages[locale] as unknown as Record<string, unknown>, key);

      if (!message) {
        // Fallback to Japanese, then English
        const fallbackJa = getNestedValue(messages.ja as unknown as Record<string, unknown>, key);
        if (fallbackJa) {
          return interpolate(fallbackJa, params);
        }

        const fallbackEn = getNestedValue(messages.en as unknown as Record<string, unknown>, key);
        if (fallbackEn) {
          return interpolate(fallbackEn, params);
        }

        // Return key if no translation found
        logger.warn(`Missing translation: ${key}`);
        return key;
      }

      return interpolate(message, params);
    },
    [locale]
  );

  const value: I18nContextValue = {
    locale,
    setLocale,
    t,
    locales: Object.keys(messages) as Locale[],
    localeNames,
  };

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

/**
 * Hook to access i18n context.
 *
 * @returns I18n context value
 * @throws Error if used outside I18nProvider
 */
export function useI18n(): I18nContextValue {
  const context = useContext(I18nContext);

  if (!context) {
    throw new Error('useI18n must be used within an I18nProvider');
  }

  return context;
}

/**
 * Hook to get translation function only.
 *
 * @returns Translation function
 */
export function useTranslation() {
  const { t, locale } = useI18n();
  return { t, locale };
}

/**
 * Hook to get and set locale.
 *
 * @returns Locale state and setter
 */
export function useLocale() {
  const { locale, setLocale, locales, localeNames } = useI18n();
  return { locale, setLocale, locales, localeNames };
}
