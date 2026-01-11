"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Calendar } from "lucide-react";
import { GlassCard } from "./GlassCard";

interface TimeSliderProps {
  onYearChange: (year: number) => void;
  minYear?: number;
  maxYear?: number;
}

/**
 * Time-Travel UI - Bottom timeline slider
 * Scrubbing loads memories by time
 */
export function TimeSlider({ 
  onYearChange, 
  minYear = 2020, 
  maxYear = new Date().getFullYear() 
}: TimeSliderProps) {
  const [currentYear, setCurrentYear] = useState(maxYear);
  const [isDragging, setIsDragging] = useState(false);

  const years = Array.from({ length: maxYear - minYear + 1 }, (_, i) => minYear + i);

  useEffect(() => {
    onYearChange(currentYear);
  }, [currentYear, onYearChange]);

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const year = parseInt(e.target.value);
    setCurrentYear(year);
  };

  return (
    <motion.div
      initial={{ y: 100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ type: "spring", stiffness: 200, damping: 25 }}
      className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 w-full max-w-4xl px-4"
    >
      <GlassCard className="p-4">
        <div className="flex items-center gap-4">
          <Calendar className="w-5 h-5 text-white/60 flex-shrink-0" />
          
          {/* Year display */}
          <div className="flex-shrink-0 min-w-[80px] text-center">
            <motion.span
              key={currentYear}
              initial={{ scale: 1.2, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="text-2xl font-semibold text-white"
            >
              {currentYear}
            </motion.span>
          </div>

          {/* Slider */}
          <div className="flex-1 relative">
            <input
              type="range"
              min={minYear}
              max={maxYear}
              value={currentYear}
              onChange={handleSliderChange}
              onMouseDown={() => setIsDragging(true)}
              onMouseUp={() => setIsDragging(false)}
              onTouchStart={() => setIsDragging(true)}
              onTouchEnd={() => setIsDragging(false)}
              className="w-full h-2 bg-white/10 rounded-full appearance-none cursor-pointer slider"
              style={{
                background: `linear-gradient(to right, rgba(255, 255, 255, 0.3) 0%, rgba(255, 255, 255, 0.3) ${((currentYear - minYear) / (maxYear - minYear)) * 100}%, rgba(255, 255, 255, 0.1) ${((currentYear - minYear) / (maxYear - minYear)) * 100}%, rgba(255, 255, 255, 0.1) 100%)`
              }}
            />
            
            {/* Year markers */}
            <div className="flex justify-between mt-2 text-xs text-white/40">
              {[minYear, Math.floor((minYear + maxYear) / 2), maxYear].map((year) => (
                <span key={year}>{year}</span>
              ))}
            </div>
          </div>
        </div>
      </GlassCard>

      <style jsx>{`
        .slider::-webkit-slider-thumb {
          appearance: none;
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: white;
          cursor: pointer;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
          transition: transform 0.2s;
        }
        
        .slider::-webkit-slider-thumb:hover {
          transform: scale(1.2);
        }
        
        .slider::-moz-range-thumb {
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: white;
          cursor: pointer;
          border: none;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }
      `}</style>
    </motion.div>
  );
}

