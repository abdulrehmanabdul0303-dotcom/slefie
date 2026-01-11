'use client';

import { useState } from 'react';
import { Search, X, Calendar, Album } from 'lucide-react';
import { Input, Button } from './ui';

export interface SearchFilters {
  query?: string;
  startDate?: string;
  endDate?: string;
  albumId?: string;
  personId?: string;
  tags?: string[];
}

interface SearchFiltersProps {
  onFilterChange?: (filters: SearchFilters) => void;
  albums?: Array<{ id: string; name: string }>;
  people?: Array<{ id: string; name: string }>;
}

export function SearchFiltersComponent({
  onFilterChange,
  albums = [],
  people = [],
}: SearchFiltersProps): React.ReactNode {
  const [query, setQuery] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [selectedAlbum, setSelectedAlbum] = useState('');
  const [selectedPerson, setSelectedPerson] = useState('');

  const handleSearch = () => {
    const filters: SearchFilters = {
      ...(query && { query }),
      ...(startDate && { startDate }),
      ...(endDate && { endDate }),
      ...(selectedAlbum && { albumId: selectedAlbum }),
      ...(selectedPerson && { personId: selectedPerson }),
    };
    onFilterChange?.(filters);
  };

  const handleReset = () => {
    setQuery('');
    setStartDate('');
    setEndDate('');
    setSelectedAlbum('');
    setSelectedPerson('');
    onFilterChange?.({});
  };

  return (
    <div className="space-y-4">
      {/* Main search */}
      <div className="relative">
        <Input
          type="text"
          placeholder="Search photos, albums, people..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSearch();
          }}
          className="pl-10"
        />
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
      </div>

      {/* Advanced filters toggle */}
      <button
        onClick={() => setShowAdvanced(!showAdvanced)}
        className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
      >
        {showAdvanced ? 'Hide advanced filters' : 'Show advanced filters'}
      </button>

      {/* Advanced filters */}
      {showAdvanced && (
        <div className="space-y-4 p-4 rounded-xl bg-white/5 border border-white/10">
          {/* Date range */}
          <div className="grid grid-cols-2 gap-3">
            <Input
              type="date"
              label="Start Date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
            <Input
              type="date"
              label="End Date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>

          {/* Album filter */}
          {albums.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-white mb-2">Album</label>
              <select
                value={selectedAlbum}
                onChange={(e) => setSelectedAlbum(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl glass text-white bg-white/10 border border-white/20 focus:outline-none focus:ring-2 focus:ring-white/20 transition-all"
              >
                <option value="">All albums</option>
                {albums.map((album) => (
                  <option key={album.id} value={album.id}>
                    {album.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Person filter */}
          {people.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-white mb-2">Person</label>
              <select
                value={selectedPerson}
                onChange={(e) => setSelectedPerson(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl glass text-white bg-white/10 border border-white/20 focus:outline-none focus:ring-2 focus:ring-white/20 transition-all"
              >
                <option value="">All people</option>
                {people.map((person) => (
                  <option key={person.id} value={person.id}>
                    {person.name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-3">
        <Button variant="primary" fullWidth onClick={handleSearch}>
          <Search className="w-4 h-4 mr-2" />
          Search
        </Button>
        <Button variant="secondary" fullWidth onClick={handleReset}>
          <X className="w-4 h-4 mr-2" />
          Reset
        </Button>
      </div>
    </div>
  );
}
