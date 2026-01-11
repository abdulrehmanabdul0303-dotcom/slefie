/**
 * Feature Flags Utility
 * Control optional features like 2090 AI Mode
 */

export interface FeatureFlags {
  aiMode: boolean;
  emotion: boolean;
  timeTravel: boolean;
  vr3d: boolean;
}

// Default flags - can be overridden via environment variables
const DEFAULT_FLAGS: FeatureFlags = {
  aiMode: process.env.NEXT_PUBLIC_AI_MODE === 'true',
  emotion: process.env.NEXT_PUBLIC_EMOTION === 'true',
  timeTravel: process.env.NEXT_PUBLIC_TIME_TRAVEL === 'true',
  vr3d: process.env.NEXT_PUBLIC_VR_3D === 'true',
};

// Local storage key for user preferences
const FLAGS_STORAGE_KEY = 'feature_flags';

/**
 * Get current feature flags
 * Combines default flags with user preferences from localStorage
 */
export function getFeatureFlags(): FeatureFlags {
  if (typeof window === 'undefined') return DEFAULT_FLAGS;

  try {
    const stored = localStorage.getItem(FLAGS_STORAGE_KEY);
    if (stored) {
      return { ...DEFAULT_FLAGS, ...JSON.parse(stored) };
    }
  } catch (error) {
    console.warn('Failed to parse feature flags:', error);
  }

  return DEFAULT_FLAGS;
}

/**
 * Check if a specific feature is enabled
 */
export function isFeatureEnabled(feature: keyof FeatureFlags): boolean {
  return getFeatureFlags()[feature];
}

/**
 * Toggle a feature flag
 * Persists to localStorage
 */
export function toggleFeature(feature: keyof FeatureFlags): void {
  if (typeof window === 'undefined') return;

  try {
    const flags = getFeatureFlags();
    flags[feature] = !flags[feature];
    localStorage.setItem(FLAGS_STORAGE_KEY, JSON.stringify(flags));
    
    // Trigger storage event for cross-tab sync
    window.dispatchEvent(new CustomEvent('featureFlagsChanged', { detail: flags }));
  } catch (error) {
    console.error('Failed to toggle feature flag:', error);
  }
}

/**
 * Set feature flags programmatically
 */
export function setFeatureFlags(flags: Partial<FeatureFlags>): void {
  if (typeof window === 'undefined') return;

  try {
    const current = getFeatureFlags();
    const updated = { ...current, ...flags };
    localStorage.setItem(FLAGS_STORAGE_KEY, JSON.stringify(updated));
    window.dispatchEvent(new CustomEvent('featureFlagsChanged', { detail: updated }));
  } catch (error) {
    console.error('Failed to set feature flags:', error);
  }
}

/**
 * Reset to default flags
 */
export function resetFeatureFlags(): void {
  if (typeof window === 'undefined') return;

  try {
    localStorage.removeItem(FLAGS_STORAGE_KEY);
    window.dispatchEvent(new CustomEvent('featureFlagsChanged', { detail: DEFAULT_FLAGS }));
  } catch (error) {
    console.error('Failed to reset feature flags:', error);
  }
}
