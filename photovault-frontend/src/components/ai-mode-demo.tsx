'use client';

import { useState } from 'react';
import { Sparkles } from 'lucide-react';
import { Button } from './ui';
import { AICommandBar, EmotionShell, EmotionStatus, TimeTravel } from './index';
import { useAICommandBar, useEmotionShell, useTimeTravel } from '@/lib/hooks/use-ai-mode';
import { isFeatureEnabled } from '@/lib/features/flags';

/**
 * AI Mode Demo Component
 * Shows how to use the 2090 AI Mode features together
 * This is for demonstration/integration purposes
 */
export function AIModeDemo(): React.ReactNode {
  const aiCommandBar = useAICommandBar();
  const emotionShell = useEmotionShell();


  const hasAIModeEnabled = isFeatureEnabled('aiMode');

  if (!hasAIModeEnabled) {
    return null;
  }

  return (
    <>
      {/* Emotion Shell Background */}
      <EmotionShell mood={emotionShell.mood} intensity={emotionShell.intensity} />

      {/* AI Command Bar Modal */}
      <AICommandBar
        isOpen={aiCommandBar.isOpen}
        onClose={aiCommandBar.close}
        onExecute={async (intent) => {
          console.log('Executing intent:', intent);
          emotionShell.setMoodByAction(intent.action);
          // Handle the intent based on its action
        }}
      />

      {/* Keyboard Shortcut Hint */}
      <div className="fixed bottom-6 right-6 z-50 pointer-events-none">
        <button
          onClick={aiCommandBar.toggle}
          className="pointer-events-auto flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-500/20 border border-blue-500/30 text-blue-300 hover:bg-blue-500/30 transition-colors"
          title="Cmd+K to open AI Command Bar"
        >
          <Sparkles className="w-4 h-4" />
          <span className="text-sm">Cmd+K</span>
        </button>
      </div>

      {/* Emotion Status Display */}
      {isFeatureEnabled('emotion') && (
        <div className="fixed top-20 left-6 z-40 pointer-events-none">
          <EmotionStatus mood={emotionShell.mood} intensity={emotionShell.intensity} />
        </div>
      )}
    </>
  );
}

/**
 * AI Mode Control Panel
 * For testing and demonstrating AI Mode features
 */
export function AIModeControlPanel(): React.ReactNode {
  const [isExpanded, setIsExpanded] = useState(false);
  const aiCommandBar = useAICommandBar();
  const emotionShell = useEmotionShell();
  const timeTravel = useTimeTravel();

  return (
    <div className="fixed bottom-6 right-6 z-50 space-y-2">
      {isExpanded && (
        <div className="bg-slate-800/95 border border-white/10 rounded-xl p-4 w-64 backdrop-blur-xl space-y-3">
          <h4 className="text-sm font-semibold text-white">AI Mode Controls</h4>

          {/* AI Command Bar */}
          {isFeatureEnabled('aiMode') && (
            <Button
              variant="secondary"
              size="sm"
              fullWidth
              onClick={aiCommandBar.toggle}
            >
              <Sparkles className="w-4 h-4 mr-2" />
              Command Bar (Cmd+K)
            </Button>
          )}

          {/* Emotion Shell Controls */}
          {isFeatureEnabled('emotion') && (
            <div className="space-y-2">
              <p className="text-xs text-white/60">Mood Control</p>
              <div className="grid grid-cols-2 gap-2">
                {(['calm', 'happy', 'excited', 'focused'] as const).map((mood) => (
                  <Button
                    key={mood}
                    variant="secondary"
                    size="sm"
                    onClick={() => emotionShell.setMoodByAction(mood)}
                  >
                    {mood}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {/* Time Travel Controls */}
          {isFeatureEnabled('timeTravel') && (
            <div className="space-y-2">
              <p className="text-xs text-white/60">Time Travel</p>
              <Button
                variant="secondary"
                size="sm"
                fullWidth
                onClick={() => timeTravel.setSelectedYear(timeTravel.selectedYear - 1)}
              >
                Previous Year
              </Button>
            </div>
          )}
        </div>
      )}

      <Button
        variant="primary"
        size="sm"
        onClick={() => setIsExpanded(!isExpanded)}
        title="Toggle AI Mode Controls"
      >
        {isExpanded ? '✕' : '⚙️'} AI
      </Button>
    </div>
  );
}
