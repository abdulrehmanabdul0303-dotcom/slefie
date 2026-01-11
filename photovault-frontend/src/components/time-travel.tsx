'use client';

import { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, Calendar } from 'lucide-react';
import { Button } from './ui';
import { isFeatureEnabled } from '@/lib/features/flags';

interface TimelineYear {
  year: number;
  photoCount: number;
}

interface TimeTravelProps {
  onYearSelect?: (year: number) => void;
  onDateRangeSelect?: (startDate: Date, endDate: Date) => void;
  years?: TimelineYear[];
  currentYear?: number;
}

export function TimeTravel({
  onYearSelect,
  onDateRangeSelect,
  years = [],
  currentYear,
}: TimeTravelProps): React.ReactNode {
  const [selectedYear, setSelectedYear] = useState(currentYear || new Date().getFullYear());
  const [showYearPicker, setShowYearPicker] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth());

  const minYear = Math.min(...years.map((y) => y.year), new Date().getFullYear() - 10);
  const maxYear = Math.max(...years.map((y) => y.year), new Date().getFullYear());

  const handleYearChange = (year: number) => {
    if (year >= minYear && year <= maxYear) {
      setSelectedYear(year);
      onYearSelect?.(year);
    }
  };

  const handleMonthSelect = (month: number) => {
    const startDate = new Date(selectedYear, month, 1);
    const endDate = new Date(selectedYear, month + 1, 0);
    setSelectedMonth(month);
    onDateRangeSelect?.(startDate, endDate);
  };

  if (!isFeatureEnabled('timeTravel')) {
    return null;
  }

  const photosThisYear = years.find((y) => y.year === selectedYear)?.photoCount || 0;

  return (
    <div className="space-y-4 p-4 rounded-2xl border border-white/10 bg-white/5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <Calendar className="w-5 h-5 text-blue-400" />
          Time Travel
        </h3>
        <span className="text-sm text-white/60">{photosThisYear} photos</span>
      </div>

      {/* Year navigation */}
      <div className="flex items-center justify-between gap-3">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => handleYearChange(selectedYear - 1)}
          disabled={selectedYear <= minYear}
        >
          <ChevronLeft className="w-4 h-4" />
        </Button>

        <div className="flex-1 text-center">
          <button
            onClick={() => setShowYearPicker(!showYearPicker)}
            className="text-2xl font-bold text-white hover:text-blue-400 transition-colors"
          >
            {selectedYear}
          </button>
          <p className="text-xs text-white/50 mt-1">
            {selectedYear === new Date().getFullYear() ? 'This Year' : 'Past Year'}
          </p>
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={() => handleYearChange(selectedYear + 1)}
          disabled={selectedYear >= maxYear}
        >
          <ChevronRight className="w-4 h-4" />
        </Button>
      </div>

      {/* Year picker */}
      {showYearPicker && (
        <div className="grid grid-cols-4 gap-2">
          {Array.from({ length: maxYear - minYear + 1 }, (_, i) => minYear + i).map(
            (year) => (
              <button
                key={year}
                onClick={() => {
                  handleYearChange(year);
                  setShowYearPicker(false);
                }}
                className={`px-2 py-2 rounded-lg text-sm font-medium transition-all ${
                  year === selectedYear
                    ? 'bg-blue-500/40 text-white border border-blue-500/50'
                    : 'bg-white/5 text-white/70 hover:bg-white/10'
                }`}
              >
                {year}
              </button>
            )
          )}
        </div>
      )}

      {/* Month selector */}
      <div>
        <label className="block text-sm font-medium text-white mb-2">Select Month</label>
        <div className="grid grid-cols-3 gap-2">
          {[
            'Jan',
            'Feb',
            'Mar',
            'Apr',
            'May',
            'Jun',
            'Jul',
            'Aug',
            'Sep',
            'Oct',
            'Nov',
            'Dec',
          ].map((month, idx) => (
            <button
              key={idx}
              onClick={() => handleMonthSelect(idx)}
              className={`px-2 py-2 rounded-lg text-sm font-medium transition-all ${
                idx === selectedMonth
                  ? 'bg-blue-500/40 text-white border border-blue-500/50'
                  : 'bg-white/5 text-white/70 hover:bg-white/10'
              }`}
            >
              {month}
            </button>
          ))}
        </div>
      </div>

      {/* Timeline bar */}
      <div className="space-y-2">
        <p className="text-xs text-white/50">Photos over time</p>
        <div className="flex gap-1 h-8 rounded-lg overflow-hidden bg-white/5 border border-white/10">
          {Array.from({ length: 12 }, (_, i) => {
            // Use deterministic value based on month index instead of Math.random()
            const monthPhotos = Math.floor(photosThisYear / 12 * ((i + 1) / 12));
            const intensity = (monthPhotos / (photosThisYear / 6)) * 100;
            return (
              <div
                key={i}
                className="flex-1 bg-gradient-to-t from-blue-500 to-cyan-500 hover:opacity-80 cursor-pointer transition-opacity"
                style={{ opacity: Math.min(intensity / 100, 1) }}
                title={`Month ${i + 1}: ${monthPhotos} photos`}
              />
            );
          })}
        </div>
      </div>

      {/* Info */}
      <div className="text-xs text-white/50 p-2 rounded-lg bg-white/5 border border-white/10">
        📅 Use time travel to explore your photos across different periods in your life
      </div>
    </div>
  );
}
