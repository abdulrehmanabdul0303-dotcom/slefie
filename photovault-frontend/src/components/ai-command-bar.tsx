'use client';

import { useState, useEffect } from 'react';
import { Sparkles, Command } from 'lucide-react';
import { Modal, Button } from './ui';
import { isFeatureEnabled } from '@/lib/features/flags';

export interface Intent {
  action: string;
  query?: string;
  filters?: Record<string, string>;
}

interface AICommandBarProps {
  onExecute?: (intent: Intent) => Promise<void>;
  isOpen?: boolean;
  onClose?: () => void;
}

// Simple intent parser for demonstration
function parseIntent(query: string): Intent {
  const lowerQuery = query.toLowerCase().trim();

  // Search intents
  if (lowerQuery.startsWith('search ')) {
    return { action: 'search', query: query.substring(7) };
  }

  // Album intents
  if (lowerQuery.includes('create album')) {
    return { action: 'createAlbum' };
  }

  if (lowerQuery.startsWith('show album')) {
    return { action: 'showAlbum', query: query.substring(10) };
  }

  // Person intents
  if (lowerQuery.includes('find')) {
    return { action: 'findPerson', query: query.substring(4) };
  }

  // Share intents
  if (lowerQuery.includes('share')) {
    return { action: 'share', query };
  }

  // Date intents
  if (lowerQuery.includes('from') || lowerQuery.includes('between')) {
    return { action: 'filterByDate', query };
  }

  // Default
  return { action: 'search', query };
}

export function AICommandBar({
  onExecute,
  isOpen = false,
  onClose,
}: AICommandBarProps): React.ReactNode {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);

  const commandSuggestions = [
    'Search photos...',
    'Create album',
    'Show album [name]',
    'Find person [name]',
    'Share photo',
    'Filter by date [range]',
    'Show memories from [year]',
  ];

  useEffect(() => {
    if (!query) {
      setSuggestions(commandSuggestions);
      return;
    }

    // Filter suggestions based on query
    const filtered = commandSuggestions.filter((s) =>
      s.toLowerCase().includes(query.toLowerCase())
    );
    setSuggestions(filtered);
  }, [query, commandSuggestions]);

  const handleExecute = async () => {
    if (!query.trim()) return;

    setIsLoading(true);
    try {
      const intent = parseIntent(query);
      await onExecute?.(intent);
      setQuery('');
      onClose?.();
    } catch (error) {
      console.error('Command execution failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isFeatureEnabled('aiMode')) {
    return null;
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose || (() => {})} title="AI Command Bar">
      <div className="space-y-4">
        {/* Command input */}
        <div>
          <label className="block text-sm font-medium text-white mb-2 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-blue-400" />
            What do you want to do?
          </label>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleExecute();
              if (e.key === 'Escape') onClose?.();
            }}
            placeholder="Try: 'Search vacation photos' or 'Create album'"
            autoFocus
            className="w-full px-4 py-3 rounded-xl glass text-white bg-white/10 border border-white/20 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
          />
        </div>

        {/* Suggestions */}
        {suggestions.length > 0 && (
          <div>
            <p className="text-xs text-white/50 mb-2">Suggestions:</p>
            <div className="space-y-2">
              {suggestions.slice(0, 4).map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => setQuery(suggestion)}
                  className="w-full text-left px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-white/80 hover:text-white text-sm transition-colors"
                >
                  <Command className="w-3 h-3 inline mr-2 text-blue-400" />
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Parse result preview */}
        {query && (
          <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
            <p className="text-xs text-blue-300 font-mono">
              Intent: <span className="text-blue-200">{parseIntent(query).action}</span>
            </p>
            {parseIntent(query).query && (
              <p className="text-xs text-blue-300 font-mono mt-1">
                Query: <span className="text-blue-200">{parseIntent(query).query}</span>
              </p>
            )}
          </div>
        )}

        {/* Action buttons */}
        <div className="flex gap-3 pt-2">
          <Button
            variant="secondary"
            fullWidth
            onClick={onClose}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            fullWidth
            onClick={handleExecute}
            loading={isLoading}
            disabled={!query.trim() || isLoading}
          >
            <Sparkles className="w-4 h-4 mr-2" />
            Execute
          </Button>
        </div>
      </div>
    </Modal>
  );
}
