/**
 * Utility function to combine classNames conditionally
 * Similar to clsx or classnames library
 */
export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}
