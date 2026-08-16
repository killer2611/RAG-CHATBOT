/**
 * Environment configuration.
 * Centralizes access to environment variables so components never read
 * process.env directly.
 */

export const config = {
  /** Backend API base URL — set via NEXT_PUBLIC_API_URL */
  apiBaseUrl: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
} as const;
