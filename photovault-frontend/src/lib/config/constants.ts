/**
 * Centralized configuration constants for PhotoVault frontend
 * 
 * All magic numbers, timeouts, limits, and retry configurations are defined here
 * for easier maintenance and tuning.
 */

// ============================================================================
// API Configuration
// ============================================================================

/** Default API request timeout in milliseconds */
export const API_TIMEOUT_MS = 30000; // 30 seconds

/** Token refresh request timeout in milliseconds */
export const TOKEN_REFRESH_TIMEOUT_MS = 10000; // 10 seconds

/** Public API request timeout in milliseconds (for unauthenticated requests) */
export const PUBLIC_API_TIMEOUT_MS = 10000; // 10 seconds

// ============================================================================
// Request Deduplication & Caching
// ============================================================================

/** Request cache TTL in milliseconds (prevents duplicate requests) */
export const REQUEST_CACHE_TTL_MS = 1000; // 1 second

/** Public share request cache TTL in milliseconds */
export const PUBLIC_SHARE_CACHE_TTL_MS = 5000; // 5 seconds

// ============================================================================
// Retry Configuration
// ============================================================================

/** Maximum number of retry attempts for failed requests */
export const MAX_RETRY_ATTEMPTS = 3;

/** Initial retry delay in milliseconds (exponential backoff starts here) */
export const RETRY_DELAY_MS = 1000; // 1 second

// ============================================================================
// Pagination Configuration
// ============================================================================

/** Default pagination limit for image lists */
export const DEFAULT_IMAGE_PAGE_SIZE = 50;

/** Pagination limit for album image picker */
export const IMAGE_PICKER_PAGE_SIZE = 200;

/** Pagination limit for search results */
export const SEARCH_PAGE_SIZE = 20;

/** Maximum pagination limit (backend may enforce this) */
export const MAX_PAGE_SIZE = 100;

// ============================================================================
// Server-Sent Events (SSE) Configuration
// ============================================================================

/** Initial SSE reconnection delay in milliseconds */
export const SSE_INITIAL_RETRY_DELAY_MS = 1000; // 1 second

/** Maximum SSE reconnection delay in milliseconds */
export const SSE_MAX_RETRY_DELAY_MS = 30000; // 30 seconds

/** Maximum SSE connection attempts before giving up */
export const SSE_MAX_ATTEMPTS = 3;

// ============================================================================
// Upload Configuration
// ============================================================================

/** Maximum file size for uploads in bytes (50MB) */
export const MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024; // 50MB

/** Accepted image MIME types for upload */
export const ACCEPTED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"];

// ============================================================================
// UI Configuration
// ============================================================================

/** Debounce delay for search input in milliseconds */
export const SEARCH_DEBOUNCE_MS = 300;

/** Toast notification duration in milliseconds */
export const TOAST_DURATION_MS = 3000; // 3 seconds

/** Auto-redirect delay after email verification in milliseconds */
export const EMAIL_VERIFY_REDIRECT_DELAY_MS = 2000; // 2 seconds

// ============================================================================
// Environment-based Configuration
// ============================================================================

/** Check if running in development mode */
export const IS_DEV = process.env.NODE_ENV === "development";

/** Check if running in production mode */
export const IS_PROD = process.env.NODE_ENV === "production";

