'use client';

import { useState, useEffect } from 'react';
import { Heart, Smile, Zap } from 'lucide-react';
import { isFeatureEnabled } from '@/lib/features/flags';

export type MoodType = 'calm' | 'happy' | 'excited' | 'focused' | 'creative';

interface EmotionShellProps {
  mood?: MoodType;
  intensity?: number; // 0-100
  enableAnimation?: boolean;
}

// Mood color mappings
const MOOD_COLORS: Record<MoodType, { bg: string; border: string; glow: string }> = {
  calm: {
    bg: 'from-blue-500/10 to-cyan-500/10',
    border: 'border-blue-500/30',
    glow: 'shadow-blue-500/20',
  },
  happy: {
    bg: 'from-yellow-500/10 to-orange-500/10',
    border: 'border-yellow-500/30',
    glow: 'shadow-yellow-500/20',
  },
  excited: {
    bg: 'from-pink-500/10 to-rose-500/10',
    border: 'border-pink-500/30',
    glow: 'shadow-pink-500/20',
  },
  focused: {
    bg: 'from-purple-500/10 to-indigo-500/10',
    border: 'border-purple-500/30',
    glow: 'shadow-purple-500/20',
  },
  creative: {
    bg: 'from-green-500/10 to-emerald-500/10',
    border: 'border-green-500/30',
    glow: 'shadow-green-500/20',
  },
};

const MOOD_ICONS: Record<MoodType, React.ReactNode> = {
  calm: <Heart className="w-4 h-4 text-blue-400" />,
  happy: <Smile className="w-4 h-4 text-yellow-400" />,
  excited: <Zap className="w-4 h-4 text-pink-400" />,
  focused: <Zap className="w-4 h-4 text-purple-400" />,
  creative: <Heart className="w-4 h-4 text-green-400" />,
};

export function EmotionShell({
  mood = 'calm',
  intensity = 50,
  enableAnimation = true,
}: EmotionShellProps): React.ReactNode {
  const [detectedMood, setDetectedMood] = useState<MoodType>(mood);
  const [animatedIntensity, setAnimatedIntensity] = useState(intensity);

  useEffect(() => {
    setDetectedMood(mood);
  }, [mood]);

  useEffect(() => {
    if (!enableAnimation) {
      setAnimatedIntensity(intensity);
      return;
    }

    const timer = setTimeout(() => {
      setAnimatedIntensity(intensity);
    }, 100);

    return () => clearTimeout(timer);
  }, [intensity, enableAnimation]);

  if (!isFeatureEnabled('emotion')) {
    return null;
  }

  const colors = MOOD_COLORS[detectedMood];
  const opacityPercent = Math.min(animatedIntensity, 100);
  const blurAmount = Math.max(0, 20 - opacityPercent / 5);

  return (
    <div
      className={`fixed inset-0 pointer-events-none transition-all duration-500 ${
        enableAnimation ? 'duration-500' : ''
      }`}
      style={{
        background: `linear-gradient(135deg, ${colors.bg})`,
        opacity: opacityPercent / 100,
        backdropFilter: `blur(${blurAmount}px)`,
        zIndex: -1,
      }}
    >
      {/* Animated background layer */}
      <div
        className={`absolute inset-0 ${
          enableAnimation ? 'animate-pulse' : ''
        }`}
        style={{
          opacity: 0.1,
        }}
      />
    </div>
  );
}

/**
 * Emotion Shell Status Display Component
 * Shows current mood and intensity
 */
export function EmotionStatus({
  mood = 'calm',
  intensity = 50,
  className = '',
}: {
  mood?: MoodType;
  intensity?: number;
  className?: string;
}): React.ReactNode {
  if (!isFeatureEnabled('emotion')) {
    return null;
  }

  const colors = MOOD_COLORS[mood];

  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg border ${colors.border} bg-gradient-to-r ${colors.bg} backdrop-blur-md ${className}`}
    >
      {MOOD_ICONS[mood]}
      <span className="text-sm font-medium text-white capitalize">{mood}</span>
      <div className="w-16 h-2 bg-white/10 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-blue-400 to-cyan-400 transition-all duration-300"
          style={{ width: `${intensity}%` }}
        />
      </div>
      <span className="text-xs text-white/70 w-8 text-right">{intensity}%</span>
    </div>
  );
}
