/**
 * Utility for conditionally joining class names.
 * Avoids adding a dependency for a ~10-line function.
 */

export function cn(...inputs: (string | undefined | null | false)[]): string {
  return inputs.filter(Boolean).join(" ");
}
