'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Menu,
  X,
  LayoutDashboard,
  Images,
  Album,
  Users,
  Search,
  Settings,
  LogOut,
} from 'lucide-react';
import { Button } from './ui';

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: <LayoutDashboard className="w-5 h-5" /> },
  { label: 'Albums', href: '/albums', icon: <Album className="w-5 h-5" /> },
  { label: 'Images', href: '/images', icon: <Images className="w-5 h-5" /> },
  { label: 'People', href: '/persons', icon: <Users className="w-5 h-5" /> },
  { label: 'Search', href: '/search', icon: <Search className="w-5 h-5" /> },
  { label: 'Settings', href: '/settings', icon: <Settings className="w-5 h-5" /> },
];

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export function Sidebar({ isOpen = true, onClose }: SidebarProps): React.ReactNode {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleClose = () => {
    setMobileOpen(false);
    onClose?.();
  };

  const isActive = (href: string): boolean => {
    return pathname.startsWith(href);
  };

  const content = (
    <nav className="flex-1 px-4 py-6 space-y-2">
      {navItems.map((item) => {
        const active = isActive(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={handleClose}
            className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
              active
                ? 'bg-gradient-to-r from-blue-500/20 to-cyan-500/20 border border-blue-500/30 text-white'
                : 'text-gray-400 hover:bg-white/5 hover:text-gray-300'
            }`}
          >
            {item.icon}
            <span className="font-medium">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="fixed md:hidden top-4 left-4 z-50 p-2 rounded-lg bg-white/10 backdrop-blur-md border border-white/20 hover:bg-white/20 transition-colors"
      >
        {mobileOpen ? (
          <X className="w-6 h-6 text-white" />
        ) : (
          <Menu className="w-6 h-6 text-white" />
        )}
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-40 w-64 bg-gradient-to-b from-slate-900/95 via-slate-800/95 to-slate-900/95 backdrop-blur-xl border-r border-white/10 flex flex-col transition-transform duration-300 transform ${
          !mobileOpen && 'max-md:-translate-x-full'
        }`}
      >
        {/* Logo section */}
        <div className="px-6 py-6 border-b border-white/10">
          <Link href="/dashboard" onClick={handleClose} className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
              <span className="text-white font-bold text-lg">📸</span>
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">PhotoVault</h1>
              <p className="text-xs text-gray-400">2090</p>
            </div>
          </Link>
        </div>

        {/* Navigation */}
        {content}

        {/* Logout button */}
        <div className="px-4 py-6 border-t border-white/10">
          <Button
            variant="ghost"
            fullWidth
            className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
            onClick={() => {
              // TODO: Implement logout
              window.location.href = '/login';
            }}
          >
            <LogOut className="w-5 h-5 mr-2" />
            Logout
          </Button>
        </div>
      </aside>
    </>
  );
}
