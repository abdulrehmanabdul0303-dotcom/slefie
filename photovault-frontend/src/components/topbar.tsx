'use client';

import { useState } from 'react';
import { Search, Moon, Sun, Bell, LogOut, Settings, User } from 'lucide-react';
import { Button, Input } from './ui';
import { useTheme } from 'next-themes';
import { useAuth } from '@/lib/auth/auth-provider';

interface TopbarProps {
  onSearch?: (query: string) => void;
  // userName prop is deprecated in favor of useAuth
  userName?: string;
}

export function Topbar({ onSearch }: TopbarProps): React.ReactNode {
  const [searchQuery, setSearchQuery] = useState('');
  const [profileOpen, setProfileOpen] = useState(false);
  const { theme, setTheme } = useTheme();
  const { user, logout } = useAuth();

  const displayName = user?.name || user?.email?.split('@')[0] || 'User';

  const handleSearch = () => {
    if (searchQuery.trim()) {
      onSearch?.(searchQuery);
    }
  };

  return (
    <header className="sticky top-0 z-40 bg-gradient-to-r from-slate-900/95 via-slate-800/95 to-slate-900/95 backdrop-blur-xl border-b border-white/10">
      <div className="px-6 py-4 flex items-center justify-between gap-4">
        {/* Search bar - hidden on mobile, visible on desktop */}
        <div className="hidden md:flex flex-1 max-w-md">
          <div className="relative w-full">
            <Input
              type="text"
              placeholder="Search photos, albums..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleSearch();
                }
              }}
              className="pl-10"
            />
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          </div>
        </div>

        {/* Right side actions */}
        <div className="flex items-center gap-2 md:gap-3">
          {/* Mobile search button */}
          <Button
            variant="ghost"
            size="sm"
            className="md:hidden"
            onClick={() => {
              // TODO: Open search modal on mobile
            }}
          >
            <Search className="w-5 h-5" />
          </Button>

          {/* Notifications */}
          <Button
            variant="ghost"
            size="sm"
            className="relative"
            onClick={() => {
              // TODO: Open notifications
            }}
          >
            <Bell className="w-5 h-5" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
          </Button>

          {/* Theme toggle */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          >
            {theme === 'dark' ? (
              <Sun className="w-5 h-5" />
            ) : (
              <Moon className="w-5 h-5" />
            )}
          </Button>

          {/* Profile dropdown */}
          <div className="relative">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setProfileOpen(!profileOpen)}
              className="gap-2"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-white text-sm font-bold">
                {displayName.charAt(0).toUpperCase()}
              </div>
              <span className="hidden md:inline text-sm text-gray-300">{displayName}</span>
            </Button>

            {/* Profile menu */}
            {profileOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-slate-800/95 backdrop-blur-md border border-white/10 rounded-lg shadow-xl overflow-hidden">
                <div className="px-4 py-3 border-b border-white/10">
                  <p className="text-sm font-medium text-white">{displayName}</p>
                  <p className="text-xs text-gray-400 mt-1">{user?.email || 'user@example.com'}</p>
                </div>

                <button
                  onClick={() => {
                    setProfileOpen(false);
                    // TODO: Navigate to profile
                  }}
                  className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-white/10 flex items-center gap-2 transition-colors"
                >
                  <User className="w-4 h-4" />
                  Profile
                </button>

                <button
                  onClick={() => {
                    setProfileOpen(false);
                    // TODO: Navigate to settings
                  }}
                  className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-white/10 flex items-center gap-2 transition-colors"
                >
                  <Settings className="w-4 h-4" />
                  Settings
                </button>

                <div className="border-t border-white/10 px-4 py-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    fullWidth
                    className="text-red-400 hover:text-red-300 hover:bg-red-500/10 justify-start"
                    onClick={() => {
                      setProfileOpen(false);
                      logout();
                    }}
                  >
                    <LogOut className="w-4 h-4 mr-2" />
                    Logout
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
