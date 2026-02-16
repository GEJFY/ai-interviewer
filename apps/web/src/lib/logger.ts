/**
 * Application logger that suppresses output in production.
 *
 * In development/test, delegates to the browser console.
 * In production builds, all calls are no-ops to avoid leaking
 * information and cluttering the console.
 */

const isDev = process.env.NODE_ENV !== 'production';

function noop() {}

const logger = {
  error: isDev ? console.error.bind(console) : noop,
  warn: isDev ? console.warn.bind(console) : noop,
  info: isDev ? console.info.bind(console) : noop,
  debug: isDev ? console.debug.bind(console) : noop,
} as const;

export default logger;
