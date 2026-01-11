'use client';

import { useEffect, useState } from 'react';
import { isFeatureEnabled } from '@/lib/features/flags';

/**
 * Hook for AI Command Bar
 * Handles keyboard shortcuts and command execution
 */
export function useAICommandBar() {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (!isFeatureEnabled('aiMode')) {
      return;
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd+K or Ctrl+K to open command bar
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(true);
      }

      // Escape to close
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return {
    isOpen,
    open: () => setIsOpen(true),
    close: () => setIsOpen(false),
    toggle: () => setIsOpen((prev) => !prev),
  };
}

/**
 * Hook for Emotion Shell
 * Detects user interaction patterns and adjusts mood
 */
export function useEmotionShell() {
  const [mood, setMood] = useState<'calm' | 'happy' | 'excited' | 'focused' | 'creative'>(
    'calm'
  );
  const [intensity, setIntensity] = useState(30);

  useEffect(() => {
    if (!isFeatureEnabled('emotion')) {
      return;
    }

    const handleMouseMove = () => {
      // Increase intensity on interaction
      setIntensity((prev) => Math.min(prev + 5, 100));
    };

    const handleMouseStop = () => {
      // Decrease intensity when idle
      const timer = setTimeout(() => {
        setIntensity((prev) => Math.max(prev - 2, 30));
      }, 2000);

      return () => clearTimeout(timer);
    };

    window.addEventListener('mousemove', handleMouseMove);
    const idleTimer = setInterval(handleMouseStop, 3000);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      clearInterval(idleTimer);
    };
  }, []);

  const setMoodByAction = (action: string) => {
    if (!isFeatureEnabled('emotion')) return;

    const moodMap: Record<string, typeof mood> = {
      search: 'focused',
      create: 'creative',
      upload: 'excited',
      share: 'happy',
      view: 'calm',
    };

    const detectedMood = moodMap[action] || 'calm';
    setMood(detectedMood);
    setIntensity(70);
  };

  return { mood, intensity, setMoodByAction };
}

/**
 * Hook for Time Travel
 * Manages temporal navigation state
 */
export function useTimeTravel() {
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [selectedDateRange, setSelectedDateRange] = useState<[Date, Date]>([
    new Date(new Date().getFullYear(), 0, 1),
    new Date(new Date().getFullYear(), 11, 31),
  ]);

  return {
    selectedYear,
    setSelectedYear,
    selectedDateRange,
    setSelectedDateRange,
  };
}
