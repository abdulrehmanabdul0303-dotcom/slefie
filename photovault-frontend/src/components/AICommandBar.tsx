"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Sparkles, X } from "lucide-react";
import { parseIntent, Intent } from "@/lib/intent";

interface AICommandBarProps {
  onIntent: (intent: Intent) => void;
  placeholder?: string;
}

/**
 * Global AI Command Bar - Primary navigation interface
 * No buttons, just natural language input
 */
export function AICommandBar({ onIntent, placeholder = "Meri photos dikhao..." }: AICommandBarProps) {
  const [input, setInput] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  // Common suggestions
  const commonQueries = [
    "Meri last Eid wali photos dikhao",
    "Happy moments dikhao",
    "Family photos",
    "Timeline 2023",
    "Recent photos"
  ];

  useEffect(() => {
    // Show suggestions when typing
    if (input.length > 0) {
      const filtered = commonQueries.filter(q => 
        q.toLowerCase().includes(input.toLowerCase())
      );
      setSuggestions(filtered.slice(0, 3));
    } else {
      setSuggestions([]);
    }
  }, [input]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const intent = parseIntent(input);
    onIntent(intent);
    setInput("");
    setSuggestions([]);
    inputRef.current?.blur();
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
    const intent = parseIntent(suggestion);
    onIntent(intent);
    setInput("");
    setSuggestions([]);
  };

  return (
    <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 w-full max-w-2xl px-4">
      <motion.form
        onSubmit={handleSubmit}
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="relative"
      >
        <div className="relative">
          {/* Glassmorphism input */}
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setTimeout(() => setIsFocused(false), 200)}
            placeholder={placeholder}
            className="w-full px-6 py-4 pl-14 pr-14 rounded-2xl glass text-white placeholder:text-white/50 focus:outline-none focus:ring-2 focus:ring-white/20 text-lg"
          />
          
          {/* AI Icon */}
          <div className="absolute left-4 top-1/2 -translate-y-1/2">
            <Sparkles className="w-5 h-5 text-white/60" />
          </div>
          
          {/* Clear button */}
          {input && (
            <motion.button
              type="button"
              onClick={() => {
                setInput("");
                inputRef.current?.focus();
              }}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className="absolute right-4 top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-white/10 transition-colors"
            >
              <X className="w-4 h-4 text-white/60" />
            </motion.button>
          )}
        </div>

        {/* Suggestions dropdown */}
        <AnimatePresence>
          {isFocused && suggestions.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="absolute top-full mt-2 w-full glass rounded-xl overflow-hidden"
            >
              {suggestions.map((suggestion, idx) => (
                <motion.button
                  key={idx}
                  type="button"
                  onClick={() => handleSuggestionClick(suggestion)}
                  whileHover={{ backgroundColor: "rgba(255, 255, 255, 0.1)" }}
                  className="w-full px-4 py-3 text-left text-white/80 hover:text-white transition-colors flex items-center gap-2"
                >
                  <Search className="w-4 h-4 text-white/40" />
                  <span>{suggestion}</span>
                </motion.button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.form>
    </div>
  );
}

